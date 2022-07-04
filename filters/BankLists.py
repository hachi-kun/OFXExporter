#!/usr/bin/python
# -*- coding: utf-8 -*-

""" 銀行系 変換フィルタ
"""

from filters.BankFilter import BankFilter


class MUFJBankFilter(BankFilter):

    def __init__(self):
        super().__init__()
        self.name = '三菱UFJ銀行'
        self.bankid = '0005'
        self.csv_format = [
            ('日付', 'Date'),
            ('摘要', 'Desc'),
            ('摘要内容', 'Memo'),
            ('支払い金額', 'Outgo'),
            ('預かり金額', 'Income'),
            ('差引残高', 'Balance'),
            ('メモ', None),
            ('未資金化区分', None),
            ('入払区分', None),
        ]

    def gen_stmttrn(self, data, financial, account):
        items = super().gen_stmttrn(data, financial, account)

        # FeliCa2Moneyとの互換の為に、'Desc'(name)と'Memo'(memo)の内容を入れ替える
        for row in items:
            name = '' if row.get('name') is None else row['name']
            memo = '' if row.get('memo') is None else row['memo']
            row['name'] = memo
            row['memo'] = name

        return items


class MUFJBankFilter_CHECKING(MUFJBankFilter):

    def __init__(self):
        super().__init__()
        self.name = '三菱UFJ銀行（当座）'
        self.acctype = 'CHECKING'


class SMBCBankFilter(BankFilter):

    def __init__(self):
        super().__init__()
        self.name = '三井住友銀行'
        self.bankid = '0009'
        self.csv_format = [
            ('年月日', 'Date'),
            ('お引出し', 'Outgo'),
            ('お預入れ', 'Income'),
            ('お取り扱い内容', 'Desc'),
            ('残高', 'Balance'),
            ('メモ', 'Memo'),
            ('ラベル', None)
        ]


class SMBCBankFilter_CHECKING(SMBCBankFilter):

    def __init__(self):
        super().__init__()
        self.name = '三井住友銀行（当座）'
        self.acctype = 'CHECKING'


class SumishinNetBankFilter(BankFilter):

    def __init__(self):
        super().__init__()
        self.name = '住信SBIネット銀行'
        self.bankid = '0038'
        self.csv_format = [
            ('日付', 'Date'),
            ('内容', 'Desc'),
            ('出金金額(円)', 'Outgo'),
            ('入金金額(円)', 'Income'),
            ('残高(円)', 'Balance'),
            ('メモ', 'Memo'),
        ]


class JibunBankFilter(BankFilter):

    def __init__(self):
        super().__init__()
        self.name = 'じぶん銀行'
        self.bankid = '0039'
        self.csv_format = [
            ('年月日', 'Date'),
            ('お取引内容', 'Desc'),
            ('出金', 'Outgo'),
            ('入金', 'Income'),
            ('残高', 'Balance'),
            ('メモ', 'Memo'),
        ]

    def analyze(self, data):
        if len(data) >= 2:
            if len(data[1]) >= 1:
                newest = '新しい順' in data[1][0]
            else:
                newest = False
        else:
            newest = False

        items = super().analyze(data)

        # 古い取引順にする為に必要ならばリスト順を反転する
        # print('items : ', items)
        if newest and items is not None:
            for item in items:
                item['data'].reverse()

        return items

class  AUCardWalletFilter(BankFilter):
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


# -------------------------------------


def main():
    pass


if (__name__ == '__main__'):
    main()
