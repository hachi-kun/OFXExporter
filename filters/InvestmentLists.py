#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
"""
import pprint

from filters.InvestmentFilter import InvestmentFilter


class StockHistoryFilter(InvestmentFilter):
    def __init__(self):
        super().__init__()
        self.name = '価格OFX'
        self.bankid = '900000'

        self.csv_formats = [
            [
                ('日付', 'Date'),
                ('価格', 'Price'),
            ],
            [
                ('日付', 'Data'),
                ('終値', 'Price'),
            ],
            [
                ('日付', 'Data'),
                ('基準価額', 'Price'),
            ]
        ]
        self.csv_format = self.csv_formats[0]

    def analyze(self, data):

        for csv_format in self.csv_formats:
            slice_line = self.slice_tops(data, csv_format)
            if slice_line:
                return [{'data': data[slice_line[0] + 1:]}]

        return None

    def marge_data(self, data):
        '''
        全ての価格情報を連結する。
        この時、各データに資産情報（銘柄コード、名称）を埋め込む
        '''
        new_invpos = []
        for key, invpos in data.items():
            uniqueid, secname = key.split('-')

            work_invpos = invpos[:]
            for price in work_invpos:
                if price.get('Uniqueid') is None:
                    price['Uniqueid'] = uniqueid
                if price.get('Secname') is None:
                    price['Secname'] = secname
                if price.get('Heldinacct') is None:
                    price['Heldinacct'] = 'CASH'
                if price.get('Postype') is None:
                    price['Postype'] = 'LONG'
                if price.get('Units') is None:
                    price['Units'] = 0

            new_invpos.extend(work_invpos)

        return new_invpos

    def gen_invstmtmsgsrsv1(self, data, financial, account):
        '''
        資産価格履歴は複数のファイルの情報を一纏めにして扱う
        '''

        invpos = self.marge_data(data)

        # 日付順にソートする
        invpos.sort(key=lambda x: x['Date'])
        last_date = invpos[-1]['Date']

        # 現在時刻でinvstmtmsgsrsv1用のデータを作成する
        invstmtmsg = super().gen_invstmtmsgsrsv1({'Invpos': invpos},
                                                 financial, account)

        # データ取得した日付を上書きする
        for row in invstmtmsg['invstmttrnrs']:
            row['invstmtrs']['dtasof'] = last_date

        return invstmtmsg

    def gen_seclistmsgsrsv1(self, data, financial, account):
        '''
        資産価格履歴は複数のファイルの情報を一纏めにして扱う
        読み込みファイル名をキー(番号、名称）に設定しているのでキーを分解して渡す
        '''

        # 同じuniqueid情報をまとめる
        invpos = []
        for key in list(set(key.split('_')[0] for key in data)):
            uniqueid, secname = key.split('-')
            invpos.append({
                'Uniqueid': uniqueid,
                'Secname': secname
            })

        return super().gen_seclistmsgsrsv1({'Invpos': invpos},
                                           financial, account)


# -------------------------------------


def main():
    pass


if (__name__ == '__main__'):
    main()
