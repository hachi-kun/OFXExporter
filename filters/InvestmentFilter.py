#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
"""
import decimal
from datetime import datetime

from filters.BankFilter import BankFilter
from filters.FinanceFilter import FinanceFilter


class InvestmentFilter(FinanceFilter):
    def __init__(self):
        super().__init__()
        self.filter_type = 'InvestmentFilter'

    def analyze(self, data):
        '''
        未実装 (オーバーライドで使用を想定）
        '''
        return None

    def gen_invstmtmsgsrsv1(self, data, financial, account):

        # 'Invtran'と'Invpos'から'Invbal'情報を作成する
        invstmt = {}
        if data.get('Invtran') is not None:
            invstmt['Invtran'] = data['Invtran'][:]
            for inv in invstmt['Invtran']:
                # 全rowデータにinvtypeを追加する
                # 未テスト テストデータ待ち
                # invtype = {　
                #            'INVEST' : 買付・売付
                #            'REINVEST' : 再投資
                #            'INVBANKTRAN' : 現金取引
                #            }
                pass

        if data.get('Invpos') is not None:
            invstmt['Invpos'] = data['Invpos'][:]

        return {'invstmttrnrs': [self.gen_invstmttrnrs(invstmt,
                                                       financial, account)]}

    def gen_seclistmsgsrsv1(self, data, financial, account):

        if data.get('Invpos') is None:
            return None

        seclist = [self.gen_seclist(data, financial, account)]

        return {'seclist': seclist}

    def field_convert(self, field, value):

        if field in ['Date', 'Debtdate']:
            return self.to_datetime(value)

        elif field in ['Units', 'Mktval', 'Parvalue', 'Taxes', 'Fees']:
            value = value.replace(',')
            return int(value)

        elif field in ['Couponrt', 'Price', ]:
            value = value.replace(',', '')
            return float(value)

        elif field in ['Heldinacct', 'Postype', 'Memo', 'Debttype']:
            return value

        else:
            # invbanktranのフォーマットはBankFilter（stmttrn）と同じなので流用する
            bankfilter = BankFilter()
            return bankfilter(bankfilter.field_convert(field, value))

    def gen_invtranlist(self, data, financial, account):
        '''
        資産取引情報
        未テスト テストデータ待ち
        invtypeを使用して対応の処理を分岐する
        invtypeの値は事前に設定されている必要がある
        '''
        invtranlist = {}
        invstock = []
        invmf = []
        invdebt = []
        reinvest = []
        invbanktran = []

        # 証券関連処理
        for invtran in data:
            if invtran['invtype'] == 'INVEST':
                inv_data = self.gen_invpos(invtran, financial, account)
                inv_type = inv_data['secid']['uniqueidtype']

                if inv_data['units'] > 0:
                    selltype = 'BUY'
                else:
                    selltype = 'SELL'

                if selltype == 'BUY':
                    units = inv_data['units']
                else:
                    units = -inv_data['units']

                # 投資信託は'unitprice'の値は10000口単位
                if inv_type == 'JP:ITAJ':
                    inv_data['unitprice'] = float(inv_data['unitprice']/10000)

                inv_data['total'] = decimal.Decimal(
                    units * inv_data['unitprice']
                    - inv_data['taxes']
                    - inv_data['fees']
                )

                if inv_type == 'JP:SIC':
                    invstock.append({
                        'invest': inv_data,
                        'selltype': selltype
                    })
                elif inv_type == 'JP:ITAJ':
                    invmf.append({
                        'invest': inv_data,
                        'selltype': selltype
                    })
                else:
                    invdebt.append({
                        'invest': inv_data,
                        'selltype': selltype
                    })

            elif invtran['invtype'] == 'REINVEST':
                inv_data = self.gen_invpos(invtran, financial, account)
                inv_data['total'] = -decimal.Decimal(inv_data['units']
                                                     * inv_data['unitprice']
                                                     - inv_data['taxes']
                                                     - inv_data['fees'])
                invmf.append(inv_data)

        # 現金処理はまとめて実施
        for invtran in data:
            if invtran['invtype'] == 'INVBANKTRAN':
                invbanktran.append(invtran[:])

        if invstock:
            invtranlist['invstock'] = invstock

        if invmf:
            invtranlist['invmf'] = invmf

        if invdebt:
            invtranlist['invdebt'] = invdebt

        if reinvest:
            invtranlist['reinvest'] = reinvest

        if invbanktran:
            # invbanktranのフォーマットの一部はBankFilter（stmttrn）と同じなので流用する
            bankfilter = BankFilter()
            if self.update_trntype is None:
                bankfilter.update_trntype(self.update_trntype)

            invtranlist['invbanktran'] = bankfilter.gen_stmttrn(invbanktran,
                                                                financial,
                                                                account)

        return invtranlist

    def gen_secid(self, data, financial=None, account=None):
        def invpos_type(uniqueid):
            '''
            暫定的に証券IDの桁数でタイプを判定
            ETFのように両方の値を持つもの別銘柄として処理する
                番号が４桁　：　株式 (証券コード)
                番号が８桁　：　投資信託 (協会コード)
            ※新証券コードには未対応
            '''
            if len(uniqueid) == 4:
                return 'JP:SIC'
            elif len(uniqueid) == 8:
                return 'JP:ITAJ'
            else:
                return 'JP:HC'

        secid = {
            'uniqueid': data['Uniqueid'],
            'uniqueidtype': invpos_type(data['Uniqueid'])
        }

        return secid

    def gen_invpos(self, data, financial, account):

        invpos = {'secid': self.gen_secid(data)}

        if data.get('Heldinacct') is not None:
            invpos['heldinacct'] = data['Heldinacct']

        if data.get('Postype') is not None:
            invpos['postype'] = data['Postype']

        if data.get('Units') is not None:
            invpos['units'] = data['Units']

        if data.get('Price') is not None:
            invpos['unitprice'] = data['Price']

        if data.get('Date') is not None:
            invpos['dtpriceasof'] = data['Date']

        if data.get('Memo') is not None:
            invpos['memo'] = data['Memo']

        # invstockのみ
        if data.get('Taxes') is not None:
            invpos['taxes'] = data['Taxes']

        if data.get('Fees') is not None:
            invpos['fees'] = data['Fees']

        return invpos

    def gen_invposlist(self, data, financial, account):
        '''
        保有資産情報
        '''

        invposlist = {}
        posstock = []
        posmf = []
        posdebt = []

        for invpos in data:
            inv_data = self.gen_invpos(invpos, financial, account)
            inv_type = inv_data['secid']['uniqueidtype']

            # 投資信託は'unitprice'の値は10000口単位
            if inv_type == 'JP:ITAJ':
                inv_data['unitprice'] = float(inv_data['unitprice']/10000)

            inv_data['mktval'] = inv_data['units'] * \
                inv_data['unitprice']
            if inv_type == 'JP:SIC':
                posstock.append({'invpos': inv_data})
            elif inv_type == 'JP:ITAJ':
                posmf.append({'invpos': inv_data})
            else:
                posdebt.append({'invpos': inv_data})

        if posstock:
            invposlist['posstock'] = posstock

        if posmf:
            invposlist['posmf'] = posmf

        if posdebt:
            invposlist['posdebt'] = posdebt

        return invposlist

    def gen_invstmtrs(self, data, financial, account):
        invstmtrs = {
            'dtasof': datetime.now(self.timezone),
            'curdef': self.curdef,
            'invacctfrom': {
                'brokerid': financial.bankid,
                'acctid': account['account']
            },

            'mktginfo': financial.name
        }
        if data.get('Invtran') is not None:
            invstmtrs['invtranlist'] = self.gen_invtranlist(data['Invtran'],
                                                            financial,
                                                            account)

        if data.get('Invpos') is not None:
            invstmtrs['invposlist'] = self.gen_invposlist(data['Invpos'],
                                                          financial,
                                                          account)

        return invstmtrs

    def gen_invstmttrnrs(self, data, financial, account):
        invstmtrs = self.gen_invstmtrs(data, financial, account)

        # 現金残高を計算する(未実装）
        margin = 0

        # 証拠金残高を計算する(未実装）
        cash = 0

        # 短期残高を計算する(未実装）
        short = 0

        invstmtrs['invbal'] = {
            'availcash': cash,
            'marginbalance': margin,
            'shortbalance': short,
        }

        return {'invstmtrs': invstmtrs}

    def gen_seclist(self, data, financial, account):
        seclist = {}

        stockinfo = []
        mfinfo = []
        debtinfo = []

        for inv_data in data['Invpos']:
            secinfo = {
                'secid': self.gen_secid(inv_data),
                'secname': inv_data['Secname'],
            }
            secinfo_type = secinfo['secid']['uniqueidtype']
            sec_data = {'secinfo': secinfo}

            if secinfo_type == 'JP:SIC':
                stockinfo.append(sec_data)
            elif secinfo_type == 'JP:ITAJ':
                mfinfo.append(sec_data)
            else:
                if inv_data.get('Parvalue') is not None:
                    sec_data['parvalue'] = inv_data['Parvalue']

                if inv_data.get('Debttype') is not None:
                    sec_data['debttype'] = inv_data['Debttype']

                if inv_data.get('Couponrt') is not None:
                    sec_data['couponrt'] = inv_data['Couponrt']

                if inv_data.get('Debtdate') is not None:
                    sec_data['dtmat'] = inv_data['Debtdate']

                debtinfo.append(sec_data)

        if stockinfo:
            seclist['stockinfo'] = stockinfo
        if mfinfo:
            seclist['mfinfo'] = mfinfo
        if debtinfo:
            seclist['debtinfo'] = debtinfo

        return seclist


# -------------------------------------


def main():
    pass


if (__name__ == '__main__'):
    main()
