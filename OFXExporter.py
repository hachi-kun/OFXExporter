#!/usr/bin/python
# -*- coding: utf-8 -*-

""" cvs->OFX 変換
"""

import codecs
import configparser
import csv
import json
import os
import pprint
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone

from chardet import detect

from filters.FilterTable import FilterTable as FilterTable
from filters.FinanceFilter import FinanceFilter as FinanceFilter
from filters.FinanceFilter import HistoryList as HistoryList
from OFXExporterGui import OFXExporterGui
from tools.DownloadStockPrice import GetPriceData as GetPriceData
from tools.OFXGenerator import OFXGenerator as OFXGenerator


class OFXExporterError(Exception):
    pass


class CSVPack(dict):
    def __init__(self, name, account):
        self.name = name
        self.account = account

        # 金融機関情報をID情報からインタンスに変更
        self.filtertable = FilterTable()
        self.financial = self.filtertable.get(self.account['financial'])

    @classmethod
    def read(cls, name, separator=',', encoding=None):
        if os.path.isfile(name):

            if encoding is None:
                # ファイルの文字列コードの判定
                with open(name, 'rb') as f:
                    res = detect(f.read())
                    if res['encoding'] in ['utf-8', 'utf-16', 'utf-32', 'UTF-8-SIG',
                                           'EUC-JP', 'SHIFT_JIS', 'ISO-2022-JP']:
                        encoding = res['encoding']
                    else:
                        encoding = 'CP932'

            # csvデータの読み込み
            with open(name, 'r', encoding=encoding) as f:
                reader = csv.reader(f, delimiter=separator)
                return[data for data in reader]

        else:
            return None

    @classmethod
    def analyze(cls, file_name):
        result = {}
        for key, financial in FilterTable().items():
            try:
                csv_data = CSVPack.read(file_name,
                                        separator=financial.separator,
                                        encoding=financial.encoding)
                result[key] = financial.analyze(csv_data)

            except Exception as e:
                print('Exception : ', e)
                print(traceback.format_exc())
                result[key] = None

        return result

    @classmethod
    def analyzeIO(cls, csv_data):
        result = {}
        for key, financial in FilterTable().items():
            try:
                result[key] = financial.analyze(csv_data)

            except Exception:
                result[key] = None

        return result

    def parse(self):

        # csvのパース処理
        parse_data = {}
        if self:
            for dict_id, data in self.items():
                parse_data[dict_id] = self.financial.parse(data,
                                                           self.name,
                                                           self.financial,
                                                           self.account)
        else:
            raise OFXExporterError('パースするデータがみつかりません')

        return self.financial.post_parse(parse_data,
                                         self.financial,
                                         self.account)

    def parse_by_date(self):

        parse_table = {}

        # date毎にデータを分割する
        for dict_id, data in self.items():
            parse_data = self.financial.parse(data,
                                              self.name,
                                              self.financial,
                                              self.account)

            for row in parse_data:
                date_str = row['Date'].strftime('%Y%m%d')
                if parse_table.get(date_str) is None:
                    parse_table[date_str] = {}

                if parse_table[date_str].get(dict_id) is None:
                    parse_table[date_str][dict_id] = [row]
                else:
                    parse_table[date_str][dict_id].append(row)

        # print(parse_table)

        # dateデータ毎にパース処理を実施する
        result = {}
        for dict_id, parse_data in parse_table.items():
            result[dict_id] = self.financial.post_parse(parse_data,
                                                        self.financial,
                                                        self.account)

        return result


class AccountList(dict):

    def __init__(self, account_file):

        # アカウント情報の読み込み
        self.account_file = account_file
        if os.path.isfile(self.account_file):
            with open(self.account_file, 'r', encoding='utf-8') as f:
                self.update(json.load(f))

        self.filtertable = FilterTable()

    def info(self, key):
        if key in self:
            value = self[key]
            bank_name = self.filtertable.get(value['financial']).name
            return key, bank_name, value['store'], value['account']
        else:
            raise OFXExporterError('アカウントが見つかりません')

    def save(self):

        # json形式でセーブする
        with open(self.account_file, 'w', encoding='utf-8') as f:
            # ファイルをクリアする
            f.truncate(0)

            # JSONファイルを書き出す
            json.dump(self, f, indent=4, ensure_ascii=False)

    def modify(self, name, bank, store, account, replace=None, autogen=False):

        # filtertableのキー情報に変換する
        keys = [key for key, value in self.filtertable.items()
                if value.name == bank]
        if not keys:
            raise OFXExporterError('登録されていない金融機関です')
        key = keys[0]

        if replace is not None:
            # 元のデータを削除する
            del self[replace]

        # 新しいデータを追加する
        self[name] = {
            'financial': key,
            'store': store,
            'account': account,
            'autogen': autogen,
        }

        # json形式でセーブする
        self.save()

        return self[name]

    def remove(self, key):
        if key is not None:
            data = self[key]
            del self[key]

            # json形式でセーブする
            self.save()

            return data
        else:
            return None


class OFXExporter(OFXExporterGui):
    backtrace = True

    def __init__(self, config='./config.ini'):

        # コンフィグレーション
        self.config = configparser.ConfigParser()
        self.config.read_file(codecs.open(config, 'r', 'utf8'))

        self.account_list = AccountList(self.config['BASE']['account_file'])

        self.filtertable = FilterTable()
        self.enable_mnyimprt = False

        self.reset()

        # 使用するクラスをカスタマイズする
        HistoryList.configure(config)
        FinanceFilter.configure(config)
        GetPriceData.configure(config)

        # ヒストリ情報の同期を実施する
        for acct in self.account_list.keys():
            HistoryList(acct).sync()

        super().__init__()

    def reset(self):
        self.active_list = {}

    def is_auto_import(self):
        return self.enable_mnyimprt

    def get_active_list(self):
        return [key for key in self.active_list.keys()]

    def get_account_list(self):
        return [key for key in self.account_list]

    def get_bank_list(self):
        return [bank.name for bank in self.filtertable.values()]

    def get_account_info(self, key):
        return self.account_list.info(key)

    def account_modify(self, name, bank, store, account, replace=None):
        self.account_list.modify(name=name,
                                 bank=bank,
                                 store=store,
                                 account=account,
                                 replace=replace)
        super().update_notify()

    def account_remove(self, key):
        self.account_list.remove(key)
        super().update_notify()

    def analyze_files(self, files, mode):
        result = []
        for name in files:
            analyze = self.analyze(name)

            if mode == 'Auto':
                result.append((os.path.basename(name), len(analyze) != 0))
            else:
                result.append((os.path.basename(name), mode in analyze))

        return result

    def analyze(self, file_name, base=None):

        if file_name is None:
            raise OFXExporterError('ファイルが選択されていません')

        if not os.path.isfile(file_name):
            raise OFXExporterError('ファイルが見つかりません')

        # 全フィルタでcsvファイルのデータをスキャンする
        if base is None:
            key = os.path.basename(file_name).split('.', 1)[0]
        else:
            key = base

        return self.analyzeIO(CSVPack.analyze(file_name), key)

    def analyzeIO(self, analyze, default_key):
        # csvのデータリストを作成する
        enable_account = []
        for key, account in self.account_list.items():
            financial = account['financial']
            csv_pack = analyze[financial]

            if csv_pack is not None:
                enable_account.append(key)

                if self.active_list.get(key) is None:
                    self.active_list[key] = CSVPack(key, account)

                for csv_data in csv_pack:
                    if csv_data.get('key') is None:
                        csv_key = default_key
                    else:
                        csv_key = csv_data['key']

                    if self.active_list[key].get(csv_key) is None:
                        self.active_list[key][csv_key] = csv_data['data']
                    else:
                        self.active_list[key][csv_key].extend(csv_data['data'])

        return enable_account

    def convert(self, key, save_mode=True):
        dir_name = self.config['BASE']['output_dir']
        if not os.path.isdir(dir_name):
            os.mkdir(dir_name)

        csv_data = self.active_list[key]

        try:
            # csvデータをパース処理する
            parse_data = csv_data.parse()

            # csvファイルをOFXファイルに変換する
            generator = OFXGenerator()
            generator.exchange(parse_data)

            if save_mode:
                # ofxファイルを書き出す
                file_name = dir_name + '/OFX_' + key \
                    + '_' + datetime.today().strftime('%Y%m%d') \
                    + '.ofx'
                generator.save(file_name)

        except Exception as e:
            if self.backtrace:
                print(traceback.format_exc())

            raise OFXExporterError(e)

    def price_download(self):
        try:
            output_dir = self.config['BASE']['output_dir']
            stock_list = self.config['DOWNLOAD']['stock_list']
            stock_acct = self.config['DOWNLOAD']['stock_account']
            retry = self.config['DOWNLOAD']['retry']

            with open(stock_list, 'r') as fp:
                stock_list = [data.replace('\n', '')
                              for data in fp.readlines()]

                for stock_data in stock_list:
                    num, name = stock_data.split('-')
                    price_data = GetPriceData(num=num, retry=int(retry))

                    # print('download price: ', stock_data)
                    price_data.download(1)

                    csv_data = price_data.csvdata()

                    analyze = CSVPack.analyzeIO(csv_data)
                    self.analyzeIO(analyze, stock_data)

                    # 次のアクセスの為に１秒待つ（待ち時間は適当）
                    time.sleep(1)

            if stock_acct in self.get_active_list():
                # csvファイルをパースする
                data = self.active_list[stock_acct]
                parse_data = data.parse()

                # OFXファイルを生成する
                generator = OFXGenerator()
                generator.exchange(parse_data)
                file_name = output_dir + '/OFX_' + stock_acct \
                    + '_' + datetime.today().strftime('%Y%m%d') \
                    + '.ofx'
                generator.save(file_name)

        except Exception as e:
            raise OFXExporterError(e)

# -------------------------------------


def main():

    args = sys.argv
    os.chdir(os.path.dirname(args[0]))

    _main = OFXExporter()

    _main.start()
    pass


if (__name__ == '__main__'):
    main()
