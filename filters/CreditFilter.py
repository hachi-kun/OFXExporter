#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
"""

from datetime import datetime, timedelta, timezone

from filters.BankFilter import BankFilter


class CreditFilter(BankFilter):
    def __init__(self):
        super().__init__()
        self.filter_type = 'CreditFilter'

        self.bankid = None
        self.trntype = {'*': 'CREDIT'}
        self.balamt_mode = 'total'

    def gen_creditcardmsgsrsv1(self, data, financial, account):
        ccstmttrnrs = []
        for row in data.values():
            items = [item for item in row if item.get('Date') is not None]
            new_ccstmttrnrs = self.gen_ccstmttrnrs(items, financial, account)
            if new_ccstmttrnrs is not None:
                ccstmttrnrs.append(new_ccstmttrnrs)

        return {'ccstmttrnrs': ccstmttrnrs}

    def gen_balamt(self, data, financial, account):

        if account.get('balamt_mode') is None:
            balamt_mode = self.balamt_mode
        else:
            balamt_mode = account.get('balamt_mode')

        if balamt_mode == 'total':
            balamt = sum(
                [row['trnamt']
                    for row in data if row.get('trnamt') is not None]
            )
            total = [balamt, balamt]

        elif balamt_mode == 'history':
            history_total = [0, 0]
            history_list = [val for val in self.history.values()
                            if val[0].replace(tzinfo=self.timezone) < data[-1]['Date']]

            for row in history_list:
                history_total[0] += row[1]
                history_total[1] += row[2]

            total = [0, 0]
            for row in data:
                if row.get('Outgo1') is not None:
                    total[0] -= row['Outgo1']

                if row.get('Outgo2') is not None:
                    total[1] -= row['Outgo2']

            balamt = total[0] + (history_total[0] - history_total[1])

        else:
            balamt = 0
            total = [0, 0]

        self.history.record(data[-1]['Date'], total[0], total[1])

        return balamt

    def gen_stmttrn(self, data, financial, account):
        for item in data:
            if item.get('Outgo') is None and item.get('Outgo1') is not None:
                item['Outgo'] = item['Outgo1']

        return super().gen_stmttrn(data, financial, account)

    def gen_ccstmttrnrs(self, data, financial, account):
        item_list = self.gen_stmttrn(data, financial, account)
        if not item_list:
            return None

        ccacctfrom = {
            'acctid': account['account'],
        }

        banktranlist = {
            'dtstart': item_list[0]['dtposted'],
            'dtend': item_list[-1]['dtposted'],
            'stmttrn': item_list
        }

        ledgerbal = {
            'balamt': self.gen_balamt(data, financial, account),
            'dtasof': datetime.now(self.timezone)
        }

        ccstmtrs = {
            'curdef': self.curdef,
            'ccacctfrom': ccacctfrom,
            'banktranlist': banktranlist,
            'ledgerbal': ledgerbal,
            'mktginfo': financial.name,
        }

        return {'ccstmtrs': ccstmtrs}

    def field_convert(self, field, value):
        if field in ['Outgo1', 'Outgo2']:
            value = value.replace(',', '')
            return int(value)
        else:
            return super().field_convert(field, value)

# -------------------------------------


def main():
    pass


if (__name__ == '__main__'):
    main()
