#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
"""
import binascii

from datetime import datetime

from filters.FinanceFilter import FilterError, FinanceFilter

class BankFilter(FinanceFilter):
    def __init__(self):
        super().__init__()
        self.filter_type = 'BankFilter'

        self.acctype = 'SAVINGS'

        self.trntype = {
            # 入金
            '利息': 'INT',
            '配当': 'DIV',
            '振込入金': 'DIRECTDEP',
            '取立入金': 'DIRECTDEP',
            '自動引落の戻し入金': 'DIRECTDEP',
            # 出金
            '出金': 'PAYMENT',
            '自動引落': 'PAYMENT',
            '振込': 'CASH',
            '現金引出': 'ATM',
            'カードによる引出': 'CHECK',
            '小切手関連取引': 'DEBIT',
        }

    def append_fitid(self, item_list, key):
        def gen_fitid(x, y, z):
            return x.strftime('%Y%m%d') + '-' + str(y).zfill(3) + '-' + z

        def gen_hash(x):
            data = ''
            if x.get('Desc') is not None:
                data = data + x['Desc']
            if x.get('Income') is not None:
                data = data + str(x['Income'])
            if x.get('Outgo') is not None:
                data = data + str(x['Outgo'])

            return (binascii.crc32(data.encode(), 0) & 0xffffffff)

        # リストをソートする
        item_list.sort(key=lambda x: x[key])

        # fitidを追加する
        item_list[0]['fitid'] = gen_fitid(item_list[0][key],
                                          0,
                                          str(gen_hash(item_list[0])))
        fitid = 0
        for index in range(1, len(item_list)):
            if item_list[index][key].date() == item_list[index-1][key].date():
                fitid = fitid + 1
            else:
                fitid = 0

            gen_hash(item_list[index])
            item_list[index]['fitid'] = gen_fitid(item_list[index][key],
                                                  fitid,
                                                  str(gen_hash(item_list[index])))

        return item_list

    def delete_invalid_row(self, data):
        def is_invalid(d):
            return d.get('Income') or d.get('Outgo')
        items = [x for x in data if is_invalid(x)]
        return items

    def gen_bankmsgsrsv1(self, data, financial, account):
        stmttrnrs = []
        for row in data.values():
            items = [item for item in row if item.get('Date') is not None]
            new_stmttrnrs = self.gen_stmttrnrs(items, financial, account)
            if new_stmttrnrs is not None:
                stmttrnrs.append(new_stmttrnrs)

        return {'stmttrnrs': stmttrnrs}

    def gen_stmttrn(self, data, financial, account):

        items = self.delete_invalid_row(data)
        if not items:
            return None

        items = self.append_fitid(items, self.sortkey)

        for value in items:

            if value.get('Date') is not None:
                value['dtposted'] = value['Date']

            if value.get('Desc') is not None:
                value['name'] = value['Desc']

            if value.get('Memo') is not None:
                value['memo'] = value['Memo']

            if value.get('Balance') is not None:
                value['balance'] = value['Balance']

            value['trnamt'] = 0
            if value.get('Income') is not None:
                value['trnamt'] = value['trnamt'] + value['Income']

            if value.get('Outgo') is not None:
                value['trnamt'] = value['trnamt'] - value['Outgo']

            if value.get('trntype') is None:

                # self.trntype = Noneにすれば全てをOTHERに設定
                # OTHERとすることで、TRNAMTが正なら入金、負なら出金の扱い
                if self.trntype is None:
                    value['trntype'] = 'OTHER'
                else:
                    if value.get('name') is not None:
                        for key, trntype in self.trntype.items():
                            if key in value['name'] or key == '*':
                                value['trntype'] = trntype
                                break

                    if value.get('trntype') is None:
                        if value['trnamt'] > 0:
                            value['trntype'] = 'DEP'
                        else:
                            value['trntype'] = 'DEBIT'

        return items

    def gen_balamt(self, data, financial, account):
        self.history.record(data[-1]['Date'],
                            data[-1]['balance'],
                            data[-1]['balance'])

        return data[-1]['balance']

    def gen_stmttrnrs(self, data, financial, account):

        item_list = self.gen_stmttrn(data, financial, account)
        if not item_list:
            return None

        bankacctfrom = {
            'bankid': financial.bankid,
            'branchid': account['store'],
            'acctid': account['account'],
            'accttype': financial.acctype,
        }

        banktranlist = {
            'dtstart': item_list[0]['dtposted'],
            'dtend': item_list[-1]['dtposted'],
            'stmttrn': item_list
        }

        ledgerbal = {
            'balamt': self.gen_balamt(item_list, financial, account),
            'dtasof': datetime.now(self.timezone)
        }

        stmtrs = {
            'curdef': self.curdef,
            'bankacctfrom': bankacctfrom,
            'banktranlist': banktranlist,
            'ledgerbal': ledgerbal,
            'mktginfo': financial.name,
        }

        return {'stmtrs': stmtrs}

    def field_convert(self, field, value):

        if field in ['Date']:
            return self.to_datetime(value)

        elif field in ['Income', 'Balance', 'Outgo', 'Usage']:
            value = value.replace(',', '')
            return int(value)

        elif field in ['Id']:
            return int(value)

        elif field in ['Desc', 'Memo']:
            return value

        else:
            raise FilterError('CSVフォーマットの読込に失敗しました')


# -------------------------------------


def main():
    pass


if (__name__ == '__main__'):
    main()
