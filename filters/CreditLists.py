#!/usr/bin/python
# -*- coding: utf-8 -*-

""" クレジット系 変換フィルタ
"""

import re

from filters.CreditFilter import CreditFilter


class SmartreceiptFilter(CreditFilter):

    def __init__(self):
        super().__init__()
        self.name = '明細：スマートレシート'
        self.separator = '\t'
        self.csv_format = [
            ('日付', 'Date'),
            ('企業名', 'Desc1'),
            ('お店', 'Desc2'),
            ('電話番号', None),
            ('カテゴリー', None),
            ('出金', None),
            ('入金', None),
            ('品名', 'Memo'),
            ('単価', 'Unit'),
            ('数量', 'Num'),
            ('メモ', 'Memo2')
        ]

    def field_convert(self, field, value):
        if field in ['Unit', 'Num']:
            value = value.replace(',', '')
            return int(value)
        elif field in ['Desc1', 'Desc2']:
            return value
        elif field in ['Memo', 'Memo2']:
            return value.replace(' ', '')
        else:
            return super().field_convert(field, value)

    def gen_stmttrn(self, data, financial, account):
        def is_invalid(d):
            return d.get('Unit') is not None and d.get('Num') is not None

        items = [x for x in data if is_invalid(x)]

        for value in items:

            # 単価と数量のデータなので総額を計算する
            # ※数量０は割引でマイナスになるのでそのまま使用する
            if value['Num'] == 0:
                value['Outgo'] = value['Unit']
            else:
                value['Outgo'] = value['Unit'] * value['Num']
                memo = ' @%d円x%d個' % (value['Unit'], value['Num'])
                if value.get('Memo2'):
                    memo = memo + value['Memo2']
                if value.get('Memo'):
                    value['Memo'] = value['Memo'] + memo
                else:
                    value['Memo'] = memo

            # 企業名と店名を連結する
            value['Desc'] = value['Desc1'] + ' ' + value['Desc2']

        # 後処理に渡す
        return super().gen_stmttrn(items, financial, account)


class BTMUVisaFilter(CreditFilter):
    def __init__(self):
        super().__init__()
        self.name = '三菱東京UFJ-VISA'
        self.balamt_mode = 'history'

        self.csv_format = [
            ('利用日', 'Date'),
            ('利用者', None),
            ('利用区分', None),
            ('利用内容', 'Desc'),
            ('新規利用額', 'Outgo1'),
            ('今回請求額', 'Outgo2'),
            ('支払回数', None),
            ('現地通貨額', None),
            ('通貨', None),
            ('為替相場', None),
            ('備考', 'Memo'),
        ]


class AEONCardFilter(CreditFilter):
    def __init__(self):
        super().__init__()
        self.name = 'イオンカード'
        self.date_format = '%Y%m%d'

        self.csv_format = [
            ('ご利用日', 'Date'),
            ('利用者区分', None),
            ('ご利用先', 'Desc'),
            ('支払方法', None),
            ('', None),
            ('', None),
            ('ご利用金額', 'Outgo'),
            ('備考', 'Memo'),
        ]

    def field_convert(self, field, value):
        if field in ['Date']:
            return self.to_datetime('20' + value)
        else:
            return super().field_convert(field, value)


class AUCardFilter(CreditFilter):
    def __init__(self):
        super().__init__()
        self.name = 'au PAY カード'
        self.date_format = '%Y/%m/%d'

        self.csv_format = [
            ('', None),
            ('利用日', 'Date'),
            ('利用店舗', 'Desc'),
            ('利用額（円）', 'Outgo'),
            ('支払い区分', None),
            ('ご利用者', None),
            ('摘要', 'Memo'),
        ]


class AUCardWalletFilter(CreditFilter):
    def __init__(self):
        super().__init__()
        self.name = 'au PAY プリペイドカード'
        self.date_format = '%Y/%m/%d %H:%M'

        self.csv_format = [
            ('', None),
            ('利用日時', 'Date'),
            ('利用店舗', 'Desc'),
            ('種別', 'Type'),
            ('利用額（円）', 'Usage'),
            ('キャンペーン名:キャンペーン額（円）', None),
            ('外貨金額', None),
            ('交換レート', None),
            ('備考', 'Memo'),
        ]

    def field_convert(self, field, value):
        if field in ['Type']:
            if value in ['払出', '支払', '支払い']:
                return 'out'
            else:
                return 'in'
        else:
            return super().field_convert(field, value)

    def gen_stmttrn(self, data, financial, account):

        for value in data:
            if value['Type'] == 'out':
                value['Outgo'] = value['Usage']
            else:
                value['Income'] = value['Usage']

        # 後処理に渡す
        return super().gen_stmttrn(data, financial, account)


class AUCardFilterUsage(CreditFilter):
    def __init__(self):
        super().__init__()
        self.name = 'au PAY カード （支払い請求）'
        self.date_format = '%Y/%m/%d'

        self.csv_format = [
            ('ご利用者', None),
            ('支払区分', None),
            ('利用日', 'Date'),
            ('利用店名', 'Desc'),
            ('利用金額', 'Outgo'),
            ('摘要', 'Memo')
        ]


class AmazonOrderFilter(CreditFilter):
    def __init__(self):
        super().__init__()
        self.name = 'Amazon 注文履歴'
        self.date_format = '%Y/%m/%d'

        self.csv_format = [
            ('注文日', 'Date'),
            ('注文番号', None),
            ('商品名', 'Desc'),
            ('付帯情報', 'Memo'),
            ('価格', None),
            ('個数', None),
            ('商品小計', 'Outgo'),
            ('注文合計', 'Outgo2'),
            ('お届け先', None),
            ('状態', 'Status'),
            ('請求先', None),
            ('請求額', None),
            ('クレカ請求日', None),
            ('クレカ請求額', None),
            ('クレカ種類', None),
            ('注文概要URL', None),
            ('領収書URL', None),
            ('商品URL', None)
        ]

        self.outgo_desc = [
            '（割引）'
        ]

        self.incoming_type = [
            '残高に追加済'
        ]

    def field_convert(self, field, value):
        if field in ['Outgo2']:
            return int(value)
        elif field in ['Status']:
            return value
        elif field in ['Memo']:  # コンディション情報を消す
            if '：' in value:
                value2 = re.split('：', value)
                return value2[1][1: -10]
            else:
                return value
        else:
            return super().field_convert(field, value)

    def gen_stmttrn(self, data, financial, account):
        for value in data:
            if value['Desc'] in self.outgo_desc:
                value['Outgo'] = value['Outgo2']  # 割引情報を記録する
            elif value.get('Status') and value['Status'] in self.incoming_type:
                value['Income'] = value.pop('Outgo')

        # 後処理に渡す
        return super().gen_stmttrn(data, financial, account)


class SmbcVpassFilter(CreditFilter):
    def __init__(self):
        super().__init__()
        self.name = '三井住友カード'
        self.date_format = '%Y/%m/%d'

        self.csv_format = [
            ('ご利用日', 'Date'),
            ('ご利用店名', 'Desc'),
            ('ご利用金額', None),
            ('支払区分', None),
            ('今回回数', None),
            ('お支払い金額', 'Outgo'),
            ('備考', 'Memo')
        ]

    def import_header(self, data, import_csv):
        '''
        vpassではcol説明の為のrow情報が無いのでcsvデータに項目(format)データを追加する
        '''
        new_data = []
        import_header = 0
        header = [format[0] for format in self.csv_format]

        for row in data:
            if len(row) < 3:
                continue

            if row[2] in self.import_csv:
                new_data.append(header)
                import_header = import_header + 1

            new_data.append(row)

        return import_header, new_data


class AmazonMasterCardFilter(SmbcVpassFilter):
    def __init__(self):
        super().__init__()
        self.name = 'AmazonMasterCard'
        self.import_csv = [
            'Ａｍａｚｏｎマスター',
            '三井住友カードｉＤ［専用カード］'
        ]

    def analyze(self, data):

        import_num, new_data = self.import_header(data, self.import_csv)

        if import_num == 0:
            return None

        return super().analyze(new_data)

# -------------------------------------


def main():
    pass


if (__name__ == '__main__'):
    main()
