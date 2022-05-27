#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import re
from datetime import datetime

import dicttoxml
import xmltodict

from filters.BankFilter import BankFilter
from filters.CreditFilter import CreditFilter
from filters.InvestmentFilter import InvestmentFilter

""" デバック用テストフィルタ・データ
"""


class TestData():
    encoding = 'utf8'

    @staticmethod
    def test_data(file_name, date_key='Date'):
        with open(file_name, 'r', encoding=TestData.encoding) as fp:
            data = json.load(fp)
            for value in data:
                if date_key in value:
                    value[date_key] = datetime.strptime(
                        value[date_key],
                        '%Y/%m/%d')
            return data

        return None

    @staticmethod
    def test_data2(file_name):
        def scan_sub(data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict) or isinstance(value, list):
                        scan_sub(value)
                    else:
                        if key in ['dtasof', 'dtend', 'dtposted',
                                   'dtserver', 'dtstart', 'dttrade',
                                   'dtpriceasof', 'dtmat']:
                            date_str = re.match('(.+)\\[(.+)\\:(.+)\\]', value)
                            date = datetime.strptime(
                                date_str.group(1) + date_str.group(2),
                                '%Y%m%d%H%M%S%z')
                            data[key] = date

            elif isinstance(data, list):
                for value in data:
                    scan_sub(value)
            else:
                raise Exception('data error')

        with open(file_name, 'r', encoding=TestData.encoding) as fp:
            data = json.load(fp)
            for key, value in data.items():
                if isinstance(value, dict) or isinstance(value, list):
                    scan_sub(value)
            return data

        return None


class DummyFilter1(BankFilter):

    def __init__(self):
        super().__init__()

        self.name = 'テスト１'
        self.bankid = '999991'

        self.csv_format = [
            ('日付', 'Date'),
            ('摘要', 'Desc'),
            ('内容', 'Memo'),
            ('出金', 'Outgo'),
            ('入金', 'Income'),
            ('残高', 'Balance'),
            ('メモ', None),
            ('区分1', 'Type'),
            ('区分2', None),
            ('番号', None),
            ('年', 'Year'),
            ('月', 'Month'),
            ('日', 'Day'),
        ]

        self.update_trntype({
            'クレジット': 'DIRECTDEP',
            'カ－ド': 'ATM',
            '口座振替': 'XFER',
        })
        # self.trntype = None

    @staticmethod
    def test_csv_format():
        csv_format = None
        file_name = './tests/sample/sample0_format.json'
        with open(file_name, 'r', encoding=TestData.encoding) as fp:
            csv_format = [(x[0], x[1]) for x in json.load(fp)]
        return csv_format

    @staticmethod
    def test_account():

        file_name = './tests/sample/sample0_account.json'
        with open(file_name, 'r', encoding=TestData.encoding) as fp:
            return json.load(fp)

        return None

    @staticmethod
    def sample0_data():
        return TestData.test_data('./tests/sample/sample0.json')

    @staticmethod
    def bank_data():
        return TestData.test_data2('./tests/sample/bank.json')


class DummyFilter2(CreditFilter):
    encoding = 'utf8'

    def __init__(self):
        super().__init__()

        self.name = 'テスト２'
        self.bankid = '999992'
        self.balamt_mode = 'history'

        self.csv_format = [
            ('利用日', 'Date'),
            ('利用者', None),
            ('利用区分', None),
            ('利用内容', 'Desc'),
            ('新規利用額', 'Outgo1'),
            ('今回請求額', 'Outgo2'),
        ]

    @ staticmethod
    def creditcard_data():
        return TestData.test_data2('./tests/sample/creditcard.json')


class DummyFilter3(InvestmentFilter):
    def __init__(self):
        super().__init__()
        self.name = 'テスト３'
        self.bankid = '999993'

        self.csv_format = [
        ]

    @ staticmethod
    def investment_data():
        return TestData.test_data2('./tests/sample/investment.json')

    @ staticmethod
    def investment_data2():
        return TestData.test_data2('./tests/sample/investment2.json')


# -------------------------------------


def main():

    # print('test_format : ', DummyFilter1().csv_format)
    # print('test_account : ', DummyFilter1.test_account())
    # print('sample0_data : ', DummyFilter1.sample0_data())

    # print('bank_data : ', DummyFilter1.bank_data())
    # print('creditcard_data : ', DummyFilter2.creditcard_data())
    # print('investment_data : ', DummyFilter3.investment_data())
    # print('investment_data2 : ', DummyFilter3.investment_data2())

    pass


if (__name__ == '__main__'):
    main()
