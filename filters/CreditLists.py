#!/usr/bin/python
# -*- coding: utf-8 -*-

""" クレジット系 変換フィルタ
"""

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

class  AUCardFilter(CreditFilter):
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

class  AUCardWalletFilter(CreditFilter):
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
            if value in ['払出', '支払']:
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

class  AUCardFilterUsage(CreditFilter):
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

# -------------------------------------


def main():
    pass


if (__name__ == '__main__'):
    main()
