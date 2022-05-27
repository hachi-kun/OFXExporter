#!/usr/bin/python
# -*- coding: utf-8 -*-

""" filter情報の初期化を実施する
"""
import inspect

from filters import BankLists, CreditLists, InvestmentLists


class FilterTable(dict):
    basetable = {}

    @classmethod
    def append(cls, table):
        cls.basetable.update(table)

    def __init__(self):
        super().__init__()

        self.update(dict(FilterTable.basetable))

        filter_names = [
            BankLists,        # 銀行系　(from BankLists.py)
            CreditLists,      # クレジットカード系 (from CreditLists.py)
            InvestmentLists,  # 証券系 (from InvestmentLists.py)
        ]

        # 各ファイルのクラス情報を読み出しリストに格納する
        for name in filter_names:
            table = map(lambda x: (x[0], x[1]()),
                        inspect.getmembers(name, inspect.isclass))
            self.update(dict(list(table)))

        # 継承元クラスの登録を削除する
        self.pop('BankFilter')
        self.pop('CreditFilter')
        self.pop('InvestmentFilter')

# -------------------------------------


def main():
    from filters import DummyFilter

    def test_keys():
        table = FilterTable()
        for key in table.keys():
            print(key)

    def test_values():
        table = FilterTable()
        for value in table.values():
            print(value.name)

    FilterTable.append({'DummyFilter': DummyFilter.DummyFilter()})
    test_keys()
    test_values()


if (__name__ == '__main__'):
    main()
