#!/usr/bin/python
# -*- coding: utf-8 -*-


'''　OFXファイルの生成
'''

import xml.dom.minidom as md
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from enum import Enum

import ofxtools.models as OFX
from ofxtools.header import make_header as OFXheader


class OFXMsgType(Enum):
    bank = 'bankmsgsrsv1'
    creditcard = 'creditcardmsgsrsv1'
    invstmt = 'invstmtmsgsrsv1'
    seclist = 'seclistmsgsrsv1'


class OFXGenerator():
    version = 200

    def __init__(self):
        self.root = None
        self.timezone = timezone(timedelta(hours=+9), 'JST')
        self.language = 'JPN'

    def __str__(self):
        dom = self.build_dom()
        return(dom.toprettyxml())

    def build_dom(self):
        response = str(OFXheader(version=OFXGenerator.version))
        if self.root is not None:
            message = ET.tostring(self.root.to_etree()).decode()
            response = response + message

        return md.parseString(response)

    def exchange(self, data):
        args = {'signonmsgsrsv1': self.gen_signonmsgsrsv1()}

        for key, value in data.items():
            if key == OFXMsgType.bank.value:
                args[key] = self.gen_bankmsgsrsv1(data[key])
            elif key == OFXMsgType.creditcard.value:
                args[key] = self.gen_creditcardmsgsrsv1(data[key])
            elif key == OFXMsgType.invstmt.value:
                args[key] = self.gen_invstmtmsgsrsv1(data[key])
            elif key == OFXMsgType.seclist.value:
                args[key] = self.gen_seclistmsgsrsv1(data[key])

        self.root = OFX.OFX(**args)

    def save(self, file_name):
        dom = self.build_dom()
        with open(file_name, "w", encoding='utf-8') as fp:
            if dom is not None:
                dom.writexml(writer=fp, encoding='utf-8',
                             newl='\n', addindent='\t')
            else:
                pass

    def set_args(self, data, keys):
        args = {}
        for key in keys:
            if data.get(key) is not None:
                args[key] = data[key]
        return args

    def gen_status(self, data):
        '''
        'code':     常にゼロ
        'severity': 情報取得のみ
        '''
        return OFX.STATUS(code=0, severity='INFO')

    def gen_ledgerbal(self, data):
        '''
        'balamt': 口座情報
        'dtasof': OFXを生成した日時
        '''
        args_list = ['balamt', 'dtasof']

        args = self.set_args(data, args_list)
        return OFX.LEDGERBAL(**args)

    def gen_stmttrn(self, data):
        '''
        'trntype':  取引種目(INT、FEE、SRVCHG、DIRECTDEBIT、PAYMENT、OTHER,,,)
        'dtposted': 日時
        'trnamt':   金額
        'fitid':    明細ID
        'name':     摘要
        'memo':     メモ
        '''
        args_list = ['trntype', 'dtposted', 'trnamt', 'fitid', 'name', 'memo']

        args = self.set_args(data, args_list)
        return OFX.STMTTRN(**args)

    def gen_banktranlist(self, data):
        '''
        'dtstart': 明細の出力対象期間（この日時から）
        'dtend':   明細の出力対象期間（この日時まで）
        '''
        args_list = ['dtstart', 'dtend']
        args = self.set_args(data, args_list)

        banktranlist = OFX.BANKTRANLIST(**args)
        for item in data['stmttrn']:
            banktranlist.append(self.gen_stmttrn(item))

        return banktranlist

    def gen_stmtrs(self, data):
        '''
        'curdef':   国籍
        'mktginfo': 口座情報
        '''
        args_list = ['curdef', 'mktginfo']
        args = self.set_args(data, args_list)

        if data.get('bankacctfrom') is not None:
            args['bankacctfrom'] = self.gen_bankacctfrom(data['bankacctfrom'])

        if data.get('banktranlist') is not None:
            args['banktranlist'] = self.gen_banktranlist(data['banktranlist'])

        if data.get('ledgerbal') is not None:
            args['ledgerbal'] = self.gen_ledgerbal(data['ledgerbal'])

        return OFX.STMTRS(**args)

    def gen_stmttrnrs(self, data):
        args = {
            'trnuid': '0',
            # 'cltcookie': '0',
            # 'ofxextension': OFX.OFXEXTENSION(),
            'status': self.gen_status(None),
        }
        if data.get('stmtrs') is not None:
            args['stmtrs'] = self.gen_stmtrs(data['stmtrs'])

        return OFX.STMTTRNRS(**args)

    def gen_bankacctfrom(self, data):
        '''
        'bankid':   統一金融機関コード
        'branchid': 支店コード
        'acctid':   口座番号
        'accttype': 口座タイプ（”CHECKING", "SAVINGS", "MONEYMRKT", "CREDITLINE", "CD"）
        '''
        args_list = ['bankid', 'branchid', 'acctid', 'accttype']
        args = self.set_args(data, args_list)

        return OFX.BANKACCTFROM(**args)

    def gen_sonrs(self, data):
        '''
        'dtserver':　OFXを生成した日時
        'language':　言語
        'fi': {
            'org':　プログラム名
        }
        '''
        return OFX.SONRS(
            status=self.gen_status(None),
            dtserver=datetime.now(self.timezone),
            language=self.language,
            fi=OFX.FI(org='OFXExporter/1.0'))

    def gen_signonmsgsrsv1(self, data=None):
        return OFX.SIGNONMSGSRSV1(sonrs=self.gen_sonrs(data))

    def gen_bankmsgsrsv1(self, data):
        bankmsgsrsv1 = OFX.BANKMSGSRSV1()
        for item in data['stmttrnrs']:
            bankmsgsrsv1.append(self.gen_stmttrnrs(item))

        return bankmsgsrsv1

    def gen_ccacctfrom(self, data):
        '''
        'acctid':　口座番号
        '''
        args_list = ['acctid']
        args = self.set_args(data, args_list)

        return OFX.CCACCTFROM(**args)

    def gen_ccstmtrs(self, data):
        '''
        'curdef':　  国名
        'mktginfo': 口座情報
        '''
        args_list = ['curdef', 'mktginfo']
        args = self.set_args(data, args_list)

        if data.get('ccacctfrom') is not None:
            args['ccacctfrom'] = self.gen_ccacctfrom(data['ccacctfrom'])

        if data.get('banktranlist') is not None:
            args['banktranlist'] = self.gen_banktranlist(data['banktranlist'])

        if data.get('ledgerbal') is not None:
            args['ledgerbal'] = self.gen_ledgerbal(data['ledgerbal'])

        return OFX.CCSTMTRS(**args)

    def gen_ccstmttrnrs(self, data):
        args = {
            'trnuid': '0',
            'status': self.gen_status(None),
        }

        if data.get('ccstmtrs') is not None:
            args['ccstmtrs'] = self.gen_ccstmtrs(data['ccstmtrs'])

        return OFX.CCSTMTTRNRS(**args)

    def gen_creditcardmsgsrsv1(self, data):

        creditcardmsgsrsv1 = OFX.CREDITCARDMSGSRSV1()

        for item in data['ccstmttrnrs']:
            creditcardmsgsrsv1.append(self.gen_ccstmttrnrs(item))

        return creditcardmsgsrsv1

    def gen_invacctfrom(self, data):
        '''
        'brokerid': 金融機関コード
        'acctid':   証券口座番号
        '''
        args_list = ['brokerid', 'acctid']
        args = self.set_args(data, args_list)

        return OFX.INVACCTFROM(**args)

    def gen_invtran(self, data):
        '''
        'fitid':   明細ID
        'dttrade': 日時
        '''
        args_list = ['fitid', 'dttrade']
        args = self.set_args(data, args_list)

        return OFX.INVTRAN(**args)

    def gen_secid(self, data):
        '''
        'uniqueid':     証券コード
        'uniqueidtype': 証券コード体系　（JP:SIC, JP:ITAJ,JP:HC,JIS&amp;T)
        '''
        args_list = ['uniqueid', 'uniqueidtype']
        args = self.set_args(data, args_list)

        return OFX.SECID(**args)

    def gen_reinvest(self, data):
        '''
        'incometype': 取引種目(INT、FEE、SRVCHG、DIRECTDEBIT、PAYMENT、OTHER)
        'total':      合計金額
        'subacctsec': サブアカウントタイプ("CASH", "MARGIN","SHORT","OTHER")
        'units':      数量
        'unitprice':  単価
        '''
        args_list = ['incometype', 'total', 'subacctsec', 'units', 'unitprice']
        args = self.set_args(data, args_list)

        if data.get('invtran') is not None:
            args['invtran'] = self.gen_invtran(data['invtran'])

        if data.get('secid') is not None:
            args['secid'] = self.gen_secid(data['secid'])

        return OFX.REINVEST(**args)

    def gen_inv_detail(self, data):
        '''
        'units':       数量
        'unitprice':   単価
        'taxes':       税金
        'fees':        手数料
        'total':       合計金額
        'subacctsec':  サブアカウントタイプ("CASH", "MARGIN","SHORT","OTHER")
        'subacctfund': 取引先タイプ("CASH", "MARGIN","SHORT","OTHER")
        '''
        args_list = ['units', 'unitprice', 'taxes',
                     'fees', 'total', 'subacctsec', 'subacctfund']
        args = self.set_args(data, args_list)

        if data.get('invtran') is not None:
            args['invtran'] = self.gen_invtran(data['invtran'])

        if data.get('secid') is not None:
            args['secid'] = self.gen_secid(data['secid'])

        return args

    def gen_invstock(self, data):
        '''
        'selltype': 売買タイプ（BUY,SELL)
        '''
        args_list = ['selltype']
        args = self.set_args(data, args_list)

        detail = self.gen_inv_detail(data['invest'])

        if args['selltype'] == 'BUY':
            args['invbuy'] = OFX.INVBUY(**detail)
            return OFX.BUYSTOCK(**args)
        else:
            args['invsell'] = OFX.INVSELL(**detail)
            return OFX.SELLSTOCK(**args)

    def gen_invmf(self, data):
        '''
        'selltype': 売買タイプ（BUY,SELL)
        '''
        args_list = ['selltype']
        args = self.set_args(data, args_list)

        detail = self.gen_inv_detail(data['invest'])

        if args['selltype'] == 'BUY':
            args['invbuy'] = OFX.INVBUY(**detail)
            return OFX.BUYMF(**args)
        else:
            args['invsell'] = OFX.INVSELL(**detail)
            return OFX.SELLMF(**args)

    def gen_invdebt(self, data):
        '''
        'selltype': 売買タイプ（BUY,SELL)
        '''
        args_list = ['selltype']
        args = self.set_args(data, args_list)

        detail = self.gen_inv_detail(data['invest'])

        if args['selltype'] == 'BUY':
            args['invbuy'] = OFX.INVBUY(**detail)
            return OFX.BUYDEBT(**args)
        else:
            args['invsell'] = OFX.INVSELL(**detail)
            return OFX.SELLDEBT(**args)

    def gen_invbanktran(self, data):
        '''
        'subacctfund':("CASH", "MARGIN","SHORT","OTHER")
        '''
        args_list = ['subacctfund']
        args = self.set_args(data, args_list)

        if data.get('stmttrn') is not None:
            args['stmttrn'] = self.gen_stmttrn(data['stmttrn'])

        return OFX.INVBANKTRAN(**args)

    def gen_invpos(self, data):
        '''
        'heldinacct':  サブアカウントタイプ("CASH", "MARGIN","SHORT","OTHER")
        'postype':     投資タイプ（"SHORT", "LONG"）
        'units':       数量
        'unitprice':   単価
        'mktval':      評価額
        'dtpriceasof': 日時
        'memo':        評価損益
        '''
        args_list = ['heldinacct', 'postype', 'units',
                     'unitprice', 'mktval', 'dtpriceasof', 'memo']
        args = self.set_args(data, args_list)

        if data.get('secid') is not None:
            args['secid'] = self.gen_secid(data['secid'])

        return OFX.INVPOS(**args)

    def gen_posstock(self, data):
        args = {}
        if data.get('invpos') is not None:
            args['invpos'] = self.gen_invpos(data['invpos'])

        return OFX.POSSTOCK(**args)

    def gen_posmf(self, data):
        args = {}
        if data.get('invpos') is not None:
            args['invpos'] = self.gen_invpos(data['invpos'])

        return OFX.POSMF(**args)

    def gen_posdebt(self, data):
        args = {}
        if data.get('invpos') is not None:
            args['invpos'] = self.gen_invpos(data['invpos'])

        return OFX.POSDEBT(**args)

    def gen_invposlist(self, data):
        invposlist = OFX.INVPOSLIST()
        if data.get('posstock') is not None:
            for item in data['posstock']:
                invposlist.append(self.gen_posstock(item))

        if data.get('posmf') is not None:
            for item in data['posmf']:
                invposlist.append(self.gen_posmf(item))

        if data.get('posdebt') is not None:
            for item in data['posdebt']:
                invposlist.append(self.gen_posdebt(item))

        return invposlist

    def gen_invbal(self, data):
        '''
        'availcash':     利用可能な現金残高（AVAILCASH）
        'marginbalance': 証拠金残高（MARGINBALANCE）
        'shortbalance':  短期残高（SHORTBALANCE）
        '''
        args_list = ['availcash', 'marginbalance', 'shortbalance']
        args = self.set_args(data, args_list)

        return OFX.INVBAL(**args)

    def gen_invtranlist(self, data):
        '''
        'dtstart': 明細の出力対象期間（この日時から）
        'dtend':   明細の出力対象期間（この日時まで）
        '''
        args_list = ['dtstart', 'dtend']
        args = self.set_args(data, args_list)

        invtranlist = OFX.INVTRANLIST(**args)

        if data.get('reinvest') is not None:
            for item in data['reinvest']:
                invtranlist.append(self.gen_reinvest(item))

        if data.get('invstock') is not None:
            for item in data['invstock']:
                invtranlist.append(self.gen_invstock(item))

        if data.get('invmf') is not None:
            for item in data['invmf']:
                invtranlist.append(self.gen_invmf(item))

        if data.get('invdebt') is not None:
            for iten in data['invdebt']:
                invtranlist.append(self.gen_invdebt(item))

        if data.get('invbanktran') is not None:
            for item in data['invbanktran']:
                invtranlist.append(self.gen_invbanktran(item))

        return invtranlist

    def gen_invstmtrs(self, data):
        '''
        'dtasof':   OFXを生成した日時
        'curdef':   国籍
        'mktginfo': 証券口座情報
        '''
        args_list = ['dtasof', 'curdef', 'mktginfo']
        args = self.set_args(data, args_list)

        if data.get('invacctfrom') is not None:
            args['invacctfrom'] = self.gen_invacctfrom(data['invacctfrom'])

        if data.get('invtranlist') is not None:
            args['invtranlist'] = self.gen_invtranlist(data['invtranlist'])

        if data.get('invposlist') is not None:
            args['invposlist'] = self.gen_invposlist(data['invposlist'])

        if data.get('invbal') is not None:
            args['invbal'] = self.gen_invbal(data['invbal'])

        return OFX.INVSTMTRS(**args)

    def get_invstmttrnrs(self, data):
        args = {
            'trnuid': '0',
            'status': self.gen_status(None),
        }

        if data.get('invstmtrs') is not None:
            args['invstmtrs'] = self.gen_invstmtrs(data['invstmtrs'])

        return OFX.INVSTMTTRNRS(**args)

    def gen_invstmtmsgsrsv1(self, data):
        invstmtmsgsrsv1 = OFX.INVSTMTMSGSRSV1()
        for item in data['invstmttrnrs']:
            invstmtmsgsrsv1.append(self.get_invstmttrnrs(item))

        return invstmtmsgsrsv1

    def gen_secinfo(self, data):
        '''
        'secname': 証券名称
        '''
        args_list = ['secname']
        args = self.set_args(data, args_list)

        if data.get('secid') is not None:
            args['secid'] = self.gen_secid(data['secid'])

        return OFX.SECINFO(**args)

    def gen_stockinfo(self, data):
        args = {}
        if data.get('secinfo') is not None:
            args['secinfo'] = self.gen_secinfo(data['secinfo'])

        return OFX.STOCKINFO(**args)

    def gen_mfinfo(self, data):
        args = {}
        if data.get('secinfo') is not None:
            args['secinfo'] = self.gen_secinfo(data['secinfo'])
        return OFX.MFINFO(**args)

    def gen_debtinfo(self, data):
        '''
        'parvalue': 額面
        'debttype': 付利体系 (COUPON、ZERO...)
        'couponrt': 金利
        'dtmat':    償還日
        '''
        args_list = ['parvalue', 'debttype', 'couponrt', 'dtmat']
        args = self.set_args(data, args_list)

        if data.get('secinfo') is not None:
            args['secinfo'] = self.gen_secinfo(data['secinfo'])

        return OFX.DEBTINFO(**args)

    def gen_seclist(self, data):

        seclist = OFX.SECLIST()
        if data.get('stockinfo') is not None:
            for item in data['stockinfo']:
                seclist.append(self.gen_stockinfo(item))

        if data.get('mfinfo') is not None:
            for item in data['mfinfo']:
                seclist.append(self.gen_mfinfo(item))

        if data.get('debtinfo') is not None:
            for item in data['debtinfo']:
                seclist.append(self.gen_debtinfo(item))

        return seclist

    def gen_seclistmsgsrsv1(self, data):

        seclistmsgsrsv1 = OFX.SECLISTMSGSRSV1()
        seclistmsgsrsv1.append(OFX.SECLISTTRNRS(trnuid='0',
                                                status=self.gen_status(None)))

        for item in data['seclist']:
            seclistmsgsrsv1.append(self.gen_seclist(item))

        return seclistmsgsrsv1


# -------------------------------------

def main():
    from filters.DummyFilter import DummyFilter1 as DummyFilter1
    from filters.DummyFilter import DummyFilter2 as DummyFilter2
    from filters.DummyFilter import DummyFilter3 as DummyFilter3

    generator = OFXGenerator()

    # テストデータを読み込む
    data = DummyFilter1.bank_data()
    generator.exchange(data)
    # generator.save('OFX_bank_data.ofx')

    data = DummyFilter2.creditcard_data()
    generator.exchange(data)
    # generator.save('OFX_creditcard_data.ofx')

    data = DummyFilter3.investment_data()
    generator.exchange(data)
    # generator.save('OFX_investment_data.ofx')

    data = DummyFilter3.investment_data2()
    generator.exchange(data)
    # generator.save('OFX_investment_data2.ofx')

    print(generator)


if (__name__ == '__main__'):
    main()
