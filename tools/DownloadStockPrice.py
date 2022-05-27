#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
"""
import codecs
import configparser
import csv
import os
import sys
import time
from datetime import datetime
from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal

import requests
from bs4 import BeautifulSoup
from yahoo_finance_api2 import share
from yahoo_finance_api2.exceptions import YahooFinanceError


class DownloadStockPriceError(Exception):
    pass


class GetPriceData():
    base = None
    config = None

    morningstar_map = {}

    @classmethod
    def setup(cls, base):
        cls.base = base

    @classmethod
    def configure(cls, config_file):
        cls.config = configparser.ConfigParser()
        cls.config.read_file(codecs.open(config_file, 'r', 'utf8'))

        if cls.config['DOWNLOAD'].get('morningstar_map'):
            with open(cls.config['DOWNLOAD']['morningstar_map'], 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=',')
                cls.morningstar_map = {
                    data[0]: (data[1], data[2]) for data in reader
                }

    def __init__(self, num, retry):
        self.num = num
        self.retry = retry
        self.dates = None
        self.prices = None

    def download_yahoo_api(self, date_range):
        symbol = self.num + '.T'
        share_data = share.Share(symbol)

        symbol_data = None
        try:
            symbol_data = share_data.get_historical(
                share.PERIOD_TYPE_DAY, date_range,
                share.FREQUENCY_TYPE_DAY, 1)
        except YahooFinanceError as e:
            print(e.message)

        self.dates = [datetime.utcfromtimestamp(int(timestamp)/1000)
                      for timestamp in symbol_data['timestamp']]

        self.prices = [Decimal(close).quantize(Decimal('0'),
                                               rounding=ROUND_HALF_UP)
                       for close in symbol_data['close']]

    def download_morningstar_web(self):
        '''
        現在の基準価額をスクレーピングする。
        過去データは取得しない
        '''
        url_base = 'https://portal.morningstarjp.com/FundData/SnapShot.do?fnc='
        user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0'

        if self.morningstar_map.get(self.num) is None:
            return

        url = url_base + self.morningstar_map[self.num][0]
        header = {
            'User-Agent': user_agent
        }

        for retry in range(self.retry):
            res = requests.get(url, headers=header)
            soup = BeautifulSoup(res.text, "html.parser")

            '''
            サンプル スクレーピング：
            基準価額 : <td><span class="fprice">19,866</span>円</td>
            日時 : <td><span class="ptdate">2022年05月13日</span></td>
            '''
            # 基準価額
            found = soup.find('span', class_='fprice')
            if found.text is None:
                time.sleep(1)
                continue
            self.prices = [Decimal(found.text.replace(',', ''))]

            # 日時
            found = soup.find('span', class_='ptdate')
            if found.text is None:
                time.sleep(1)
                continue
            self.dates = [datetime.strptime(found.text, '%Y年%m月%d日')]
            return

        raise DownloadStockPriceError('モーニングスターからのデータ取得に失敗しました')

    def download(self, date_range):
        # 番号が４桁　：　株式 (証券コード)
        # 番号が８桁　：　投資信託 (協会コード)

        if len(self.num) == 4:
            if self.config['DOWNLOAD']['download_stock'] == 'yahoo_api':
                self.download_yahoo_api(date_range)

        elif len(self.num) == 8:
            if self.config['DOWNLOAD']['download_mf'] == 'morningstar_web':
                self.download_morningstar_web()

    def csvdata(self):
        if len(self.num) == 4:
            output = [['日付', '終値']]
        elif len(self.num) == 8:
            output = [['日付', '基準価額']]
        else:
            return []

        if self.dates is not None and self.prices is not None:
            output.extend([[date.strftime('%Y%m%d'), str(price)]
                           for date, price in zip(self.dates, self.prices)])

        return output

    def save(self, file_name):
        with open(file_name, 'w', encoding='utf-8') as fp:
            writer = csv.writer(fp, delimiter=',',lineterminator="\n")
            writer.writerows(self.csvdata())


# -------------------------------------


if (__name__ == '__main__'):

    GetPriceData.configure('./config.ini')
    output_dir = GetPriceData.config['DOWNLOAD']['output_dir']
    stock_list = GetPriceData.config['DOWNLOAD']['stock_list']
    date_range = GetPriceData.config['DOWNLOAD']['date_range']
    retry = GetPriceData.config['DOWNLOAD']['retry']

    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    with open(stock_list, 'r', encoding='utf-8') as fp:
        stock_list = fp.readlines()
        for stock_data in stock_list:
            num, name = stock_data.replace('\n', '').split('-')
            print('download [%s:%s]...' % (num, name))

            price_data = GetPriceData(num=num, retry=int(retry))
            price_data.download(int(date_range))

            price_data.save(output_dir + '/' + num + '-' + name + '.csv')

            # 次のアクセスの為に１秒待つ（待ち時間は適当）
            time.sleep(1)
