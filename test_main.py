#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
"""

import os
import pprint
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import pytest

from filters.DummyFilter import DummyFilter1 as DummyFilter1
from filters.DummyFilter import DummyFilter2 as DummyFilter2
from filters.DummyFilter import DummyFilter3 as DummyFilter3
from filters.FilterTable import FilterTable as FilterTable
from filters.FinanceFilter import HistoryList as HistoryList
from OFXExporter import CSVPack, OFXExporter
from tools.OFXGenerator import OFXGenerator as OFXGenerator

test_result_dir = './tests/result/'
test_config = './tests/config.ini'
test_account_file = './tests/result/account.json'

test_account = [
    ('口座１', 'じぶん銀行', '001', '001'),
    ('口座２', '三菱UFJ銀行', '002', '002'),
    ('口座３', '三井住友銀行', '003', '003'),
    ('口座４', '価格OFX', '004', '004'),

    ('口座１１', 'テスト１', '011', '011'),
    ('口座１２', 'テスト２', '012', '012'),
    ('口座１３', 'テスト３', '013', '013'),
]


@pytest.fixture(scope='session')
def setup():

    # テスト用アカウントファイルを消す
    if os.path.isfile(test_account_file):
        os.remove(test_account_file)

    # ワークディレクトリを再生成
    if os.path.isdir(test_result_dir):
        shutil.rmtree(test_result_dir)
    os.makedirs(test_result_dir)

    # テストfilterを強制的に設定する
    FilterTable.append({'TestFilter1': DummyFilter1()})
    FilterTable.append({'TestFilter2': DummyFilter2()})
    FilterTable.append({'TestFilter3': DummyFilter3()})


@pytest.fixture(scope='function')
def target():

    target = OFXExporter(config=test_config)
    for account in test_account:
        target.account_modify(*account)

    yield target


def test_read_dummy_data1(target, setup):
    generator = OFXGenerator()
    generator.exchange(DummyFilter1.bank_data())
    tree = ET.fromstring(generator.__str__())
    assert tree.tag == 'OFX'


def test_read_dummy_data2(target, setup):
    generator = OFXGenerator()
    generator.exchange(DummyFilter2.creditcard_data())
    tree = ET.fromstring(generator.__str__())
    assert tree.tag == 'OFX'


def test_read_dummy_data3(target, setup):
    generator = OFXGenerator()
    generator.exchange(DummyFilter3.investment_data())
    tree = ET.fromstring(generator.__str__())
    assert tree.tag == 'OFX'


def test_read_dummy_data4(target, setup):
    generator = OFXGenerator()
    generator.exchange(DummyFilter3.investment_data2())
    tree = ET.fromstring(generator.__str__())
    assert tree.tag == 'OFX'


def test_account_modify(target, setup):
    assert len(target.account_list) == len(test_account)

    assert target.account_list.get('口座１') is not None
    assert target.account_list.get('口座２') is not None
    assert target.account_list.get('口座３') is not None
    assert target.account_list.get('口座４') is not None
    assert target.account_list.get('口座１１') is not None
    assert target.account_list.get('口座１２') is not None
    assert target.account_list.get('口座１３') is not None
    assert target.account_list.get('口座９９') is None

    assert os.path.isfile(test_account_file)


def test_get_bank_list(target, setup):
    ret = target.get_bank_list()
    assert ret.count('テスト１') == 1
    assert ret.count('価格OFX') == 1
    # print('get_bank_list = ', ret, ':', type(ret))


def test_get_account_list(target, setup):
    ret0 = target.get_account_list()
    assert ret0.count('口座１') == 1
    # print('before get_account_list = ', ret, ':', type(ret))

    target.account_remove('口座１')
    ret1 = target.get_account_list()
    assert len(ret1) == len(ret0) - 1
    assert ret1.count('口座１') == 0
    # print('after get_account_list = ', ret, ':', type(ret))


def test_get_account_info(target, setup):
    ret1, ret2, ret3, ret4 = target.get_account_info('口座２')
    assert ret1 == '口座２'
    assert ret2 == '三菱UFJ銀行'
    assert ret3 == '002'
    assert ret4 == '002'
    # print('get_account_info 1 = ', ret1, ':', type(ret1))
    # print('get_account_info 2 = ', ret2, ':', type(ret2))
    # print('get_account_info 3 = ', ret3, ':', type(ret3))
    # print('get_account_info 4 = ', ret4, ':', type(ret4))


def test_generator_1(target, setup):
    target.analyze('./tests/sample/sample0.csv')

    ret = target.get_active_list()
    assert len(ret) == 1
    assert ret.count('口座１１') == 1

    data = target.active_list['口座１１']
    assert data.get('sample0')
    assert len(data['sample0']) == 9
    # print('CSVPack = ', data)

    parse_data = data.parse()
    assert parse_data.get('bankmsgsrsv1')
    assert parse_data['bankmsgsrsv1'].get('stmttrnrs')

    stmttrnrs_data = parse_data['bankmsgsrsv1']['stmttrnrs'][0]
    assert stmttrnrs_data.get('stmtrs')
    assert stmttrnrs_data['stmtrs'].get('bankacctfrom')
    assert stmttrnrs_data['stmtrs'].get('banktranlist')
    assert stmttrnrs_data['stmtrs'].get('curdef')
    assert stmttrnrs_data['stmtrs'].get('ledgerbal')
    assert stmttrnrs_data['stmtrs'].get('mktginfo')
    # pprint.pprint(parse_data)

    generator = OFXGenerator()
    generator.exchange(parse_data)
    # print(generator)
    # generator.save(test_result_dir + 'OFX_口座１１.ofx')

    tree = ET.fromstring(generator.__str__())
    assert tree.tag == 'OFX'


def test_generator_2(target, setup):
    target.analyze('./tests/sample/prices/04315017-ダイワ上場投信_トピックス.csv')
    target.analyze('./tests/sample/prices/7203-トヨタ自動車.csv')

    target.analyze(file_name='./tests/sample/prices/9984-ソフトバンクグループ_1.csv',
                   base='9984-ソフトバンクグループ')
    target.analyze(file_name='./tests/sample/prices/9984-ソフトバンクグループ_2.csv',
                   base='9984-ソフトバンクグループ')

    ret = target.get_active_list()
    assert len(ret) == 1
    assert ret.count('口座４') == 1

    data = target.active_list['口座４']
    assert data.get('04315017-ダイワ上場投信_トピックス')
    assert data.get('7203-トヨタ自動車')
    assert data.get('9984-ソフトバンクグループ')

    assert len(data['04315017-ダイワ上場投信_トピックス']) == 20
    assert len(data['7203-トヨタ自動車']) == 19
    assert len(data['9984-ソフトバンクグループ']) == 19
    # print('CSVPack = ', data)

    parse_data = data.parse()
    # pprint.pprint(parse_data)
    assert parse_data.get('invstmtmsgsrsv1')
    assert parse_data['invstmtmsgsrsv1'].get('invstmttrnrs')

    invstmttrnrs_data = parse_data['invstmtmsgsrsv1'].get('invstmttrnrs')[0]
    assert invstmttrnrs_data['invstmtrs']
    assert invstmttrnrs_data['invstmtrs']['invposlist']['posmf']
    assert invstmttrnrs_data['invstmtrs']['invposlist']['posstock']

    assert len(invstmttrnrs_data['invstmtrs']['invposlist']['posmf']) == 20
    assert len(invstmttrnrs_data['invstmtrs']['invposlist']['posstock']) == 38

    generator = OFXGenerator()
    generator.exchange(parse_data)
    # print(generator)
    # generator.save(test_result_dir + 'OFX_口座４.ofx')

    tree = ET.fromstring(generator.__str__())
    assert tree.tag == 'OFX'


def test_generator_3(target, setup):

    target.analyze('./tests/sample/prices/04315017-ダイワ上場投信_トピックス.csv')
    target.analyze('./tests/sample/prices/7203-トヨタ自動車.csv')
    data = target.active_list['口座４']

    parse_data = data.parse_by_date()
    for dict_id, data in parse_data.items():

        generator = OFXGenerator()
        generator.exchange(data)

        # generator.save(test_result_dir + 'OFX_口座４_' + dict_id + '.ofx')

        tree = ET.fromstring(generator.__str__())
        assert tree.tag == 'OFX'


def test_generator_4(target, setup):

    csv_data = [
        ['日付', '終値'],
        ['20220405', '2218'],
        ['20220406', '2190'],
        ['20220407', '2169'],
        ['20220408', '2096'],
        ['20220411', '2102'],
        ['20220412', '2070'],
    ]
    analyze = CSVPack.analyzeIO(csv_data)
    # print('analyze : ', analyze)
    target.analyzeIO(analyze, '7203-トヨタ自動車')

    data = target.active_list['口座４']
    parse_data = data.parse()
    # print('parse_data = ', parse_data)

    generator = OFXGenerator()
    generator.exchange(parse_data)
    # print(generator)
    # generator.save(test_result_dir + 'OFX_口座４.ofx')

    tree = ET.fromstring(generator.__str__())
    assert tree.tag == 'OFX'


def test_generator_5(target, setup):
    csv_data = [
        ['日付', '摘要', '内容', '出金', '入金', '残高', 'メモ',
         '区分1', '区分2', '番号', '年', '月', '日'],
        ['2022/1/11', 'クレジット', '', '', '', '',
         '', '', '振替支払い', '0001', '2022', '1', '11'],
    ]
    analyze = CSVPack.analyzeIO(csv_data)
    # print('analyze : ', analyze)
    target.analyzeIO(analyze, 'sample1')

    data = target.active_list['口座１１']
    parse_data = data.parse()
    # print('parse_data = ', parse_data)

    generator = OFXGenerator()
    generator.exchange(parse_data)
    # print(generator)
    # generator.save(test_result_dir + 'OFX_口座１１.ofx')

    tree = ET.fromstring(generator.__str__())
    assert tree.tag == 'OFX'


def test_generator_6(target, setup):
    csv_data = [
        ['日付', '摘要', '内容', '出金', '入金', '残高', 'メモ',
         '区分1', '区分2', '番号', '年', '月', '日'],
        ['2022/1/11', 'クレジット', '', '', '', '',
         '', '', '振替支払い', '0001', '2022', '1', '11'],
        ['2022/1/19', 'カ－ド', '', '', '1,000', '41,019',
         '', '', '入金', '0002', '2022', '1', '19'],
    ]
    analyze = CSVPack.analyzeIO(csv_data)
    # print('analyze : ', analyze)
    target.analyzeIO(analyze, 'sample1')

    data = target.active_list['口座１１']
    parse_data = data.parse()
    # print('parse_data = ', parse_data)

    generator = OFXGenerator()
    generator.exchange(parse_data)
    # print(generator)
    # generator.save(test_result_dir + 'OFX_口座１１.ofx')

    tree = ET.fromstring(generator.__str__())
    assert tree.tag == 'OFX'


def test_history(target, setup):
    def linecount(x):
        count = 0
        with open(x, 'r') as f:
            for line in f:
                count += 1

        return count

    history1 = HistoryList('口座９９')
    history1.record(datetime.strptime('2022/05/25', '%Y/%m/%d'), 2000, 2000)
    history1.record(datetime.strptime('2022/05/26', '%Y/%m/%d'), 3000, 3000)
    history1.record(datetime.strptime('2022/05/28', '%Y/%m/%d'), 5000, 5000)

    history1.record(datetime.strptime('2022/05/24', '%Y/%m/%d'), 1000, 1000)
    history1.record(datetime.strptime('2022/05/27', '%Y/%m/%d'), 4000, 4000)
    history1.record(datetime.strptime('2022/05/30', '%Y/%m/%d'), 7000, 7000)
    assert len(history1) == 6
    assert linecount(history1.filename + '.txt') == 6

    history2 = HistoryList('口座９９')
    assert len(history2) == 6
    history2.record(datetime.strptime('2022/05/24', '%Y/%m/%d'), 9000, 9500)
    history2.record(datetime.strptime('2022/05/24', '%Y/%m/%d'), 9100, 9600)
    history2.record(datetime.strptime('2022/05/24', '%Y/%m/%d'), 9200, 9700)
    assert len(history2) == 6
    assert linecount(history2.filename + '.txt') == 9
    history2.sync()

    history3 = HistoryList('口座９９')
    assert linecount(history3.filename + '.txt') == 6

    assert history3['2022/05/24'][1] == 9200
    assert history3['2022/05/24'][2] == 9700


def test_balamt(target, setup):

    result = []
    for csv_file in ['./tests/sample/sample1-1.csv',
                     './tests/sample/sample1-2.csv',
                     './tests/sample/sample1-3.csv']:

        target.reset()
        target.analyze(csv_file)
        data = target.active_list['口座１２']
        parse_data = data.parse()

        generator = OFXGenerator()
        generator.exchange(parse_data)

        # print(generator)

        tree = ET.fromstring(generator.__str__())
        assert tree.tag == 'OFX'

        for child in tree.iter('BALAMT'):
            result.append(int(child.text))
            break

    assert result[0] == -30000
    assert result[1] == -16000
    assert result[2] == -13000

# -------------------------------------
