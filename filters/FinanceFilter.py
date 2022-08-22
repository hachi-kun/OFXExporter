#!/usr/bin/python
# -*- coding: utf-8 -*-

"""  csv変換フィルタ
"""
import configparser
import csv
import os

from datetime import datetime, timedelta, timezone
from itertools import zip_longest


class FilterError(Exception):
    pass


class HistoryList(dict):
    config = None
    history_dir = None

    @classmethod
    def configure(cls, config):
        cls.config = configparser.ConfigParser()
        cls.config.read(config)

        cls.history_dir = cls.config['BASE']['history_dir']
        if not os.path.isdir(cls.history_dir):
            os.mkdir(cls.history_dir)

    def __init__(self, name):
        super().__init__()

        self.acct = name
        self.filename = HistoryList.history_dir + '/' + self.acct

        if os.path.isfile(self.filename + '.txt'):
            with open(self.filename + '.txt', 'r') as f:
                reader = csv.reader(f)

                self.update({row[0]: (datetime.strptime(row[0], '%Y/%m/%d'),
                                      int(row[1]), int(row[2]))
                             for row in reader})

    def record(self, date, balamt1, balamt2):
        date_str = datetime.strftime(date, '%Y/%m/%d')

        self[date_str] = (date, balamt1, balamt2)

        # ファイルへ追加
        with open(self.filename + '.txt', 'a+') as f:
            value = [date_str, balamt1, balamt2]
            writer = csv.writer(f, lineterminator='\n')
            writer.writerow(value)

    def sync(self):

        if os.path.isfile(self.filename + '.txt'):
            with open(self.filename + '.txt', 'r') as f:
                reader = csv.reader(f)
                history = [row for row in reader]
                if len(self.values()) == len(history):
                    return True

            os.replace(self.filename + '.txt', self.filename + '.bak')

        items = [value for value in self.values()]
        items.sort(key=lambda x: x[0])

        with open(self.filename + '.txt', 'w') as f:
            writer = csv.writer(f, lineterminator='\n')
            data = [[datetime.strftime(row[0], '%Y/%m/%d'), row[1], row[2]]
                    for row in items]
            writer.writerows(data)


class FinanceFilter():
    config = None

    @ classmethod
    def configure(cls, config):
        cls.config = configparser.ConfigParser()
        cls.config.read(config)

    def __init__(self):
        self.filter_type = None
        self.name = ''
        self.bankid = None
        self.trntype = None
        self.curdef = 'JPY'
        self.encoding = None

        self.csv_format = []
        self.separator = ','
        self.date_format = None
        self.timezone = timezone(timedelta(hours=9))
        self.sortkey = 'Date'

        self.history = None

    def update_trntype(self, data):
        '''
        trntypeの先頭に新しいtrntype情報を追加する。
        python 3.7以降は辞書の順序が保持されるらしい。
        保持されない場合は再検討
        '''
        new_trntype = dict(data)
        if self.trntype is not None:
            new_trntype.update(self.trntype)
        self.trntype = new_trntype

    def analyze(self, data):
        slice_line = self.slice_tops(data, self.csv_format)
        if slice_line:
            start_line = slice_line[:]
            if len(slice_line) >= 1:
                end_line = slice_line[1:]
            else:
                end_line = []

            # cvsデータの先頭までスキップする
            data_list = []
            for start, end in zip_longest(start_line, end_line):
                data_list.append({'data': data[start + 1: end]})

            return data_list
        else:
            return None

    def parse(self, parse_data, name, financial, account):
        item_list = []

        if not self.csv_format:
            raise FilterError('フォーマット定義情報が見つかりません')

        # print('name : ', name)
        # print('account : ', account)
        self.history = HistoryList(name)
        # print('history : ', self.history)

        # 辞書のリスト形式に変換
        self.skip_row = 0
        for row in parse_data:
            try:
                date_val = ['', '', '']
                item = {}
                fields = [x[1] for x in self.csv_format]
                for field, value in zip(fields, row):
                    if value == '':
                        continue

                    if field is not None:

                        # 日時データがカラムに分解されている場合はまとめてdateとして処理
                        if field == 'Year':
                            date_val[0] = value
                        elif field == 'Month':
                            date_val[1] = value
                        elif field == 'Day':
                            date_val[2] = value

                            if self.date_format is None:
                                date_str = '-'.join(date_val)
                            else:
                                date = datetime(year=int(date_val[0]),
                                                month=int(date_val[1]),
                                                day=int(date_val[2]))
                                date_str = date.strftime(self.date_format)

                                item['Date'] = self.field_convert('Date',
                                                                  date_str)

                        else:
                            item[field] = self.field_convert(field, value)

                item_list.append(item)

            except Exception:
                self.skip_row = self.skip_row + 1

        # 日付情報が無いデータを削除する
        return [row for row in item_list if row.get('Date')]

    def gen_bankmsgsrsv1(self, data, financial, account):
        return None

    def gen_creditcardmsgsrsv1(self, data, financial, account):
        return None

    def gen_invstmtmsgsrsv1(self, data, financial, account):
        return None

    def gen_seclistmsgsrsv1(self, data, financial, account):
        return None

    def post_parse(self, data, financial, account):
        ofx_data = {}

        if self.filter_type == 'BankFilter':
            # bankmsgsrsv1を生成する
            node = self.gen_bankmsgsrsv1(data, financial, account)
            if node is not None:
                ofx_data['bankmsgsrsv1'] = node

        if self.filter_type == 'CreditFilter':
            # creditcardmsgsrsv1を生成する
            node = self.gen_creditcardmsgsrsv1(data, financial, account)
            if node is not None:
                ofx_data['creditcardmsgsrsv1'] = node

        if self.filter_type == 'InvestmentFilter':
            # invstmtmsgsrsv1を生成する
            node = self.gen_invstmtmsgsrsv1(data, financial, account)
            if node is not None:
                ofx_data['invstmtmsgsrsv1'] = node

                # seclistmsgsrsv1を生成する
                node = self.gen_seclistmsgsrsv1(data, financial, account)
                if node is not None:
                    ofx_data['seclistmsgsrsv1'] = node

        return ofx_data

    def field_convert(self, field, value):
        return value

    def to_datetime(self, date_str):
        if self.date_format is None:
            # 時刻フォーマットの自動判定
            if '/' in date_str:
                self.date_format = '%Y/%m/%d'
            elif '-' in date_str:
                self.date_format = '%Y-%m-%d'
            elif '日' in date_str:
                self.date_format = '%Y年%m月%d日'
            elif date_str.isdecimal():
                self.date_format = '%Y%m%d'
            else:
                raise FilterError('時刻フォーマットが判定出来ません')
        return datetime.strptime(date_str,
                                 self.date_format).replace(tzinfo=self.timezone)

    def slice_tops(self, data, title):
        tops = []

        # カラム情報がなければエラー
        column_text = [x[0] for x in title]
        if not column_text:
            return tops

        for index, row in enumerate(data):

            # タイトル情報より項目が小さければ読み飛ばす
            if len(row) < len(column_text):
                continue

            # rowデータをスライスして比較
            value = row[0:len(column_text)]
            if value == column_text:
                tops.append(index)

        return tops


# -------------------------------------


def main():
    pass


if (__name__ == '__main__'):
    main()
