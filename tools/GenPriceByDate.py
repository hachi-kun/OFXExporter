#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
"""
import os
import sys
import traceback

from OFXExporter import OFXExporter as OFXExporter

from tools.OFXGenerator import OFXGenerator as OFXGenerator


def main():
    args = sys.argv

    scan_path = ['./prices/']
    if len(args) > 1:
        scan_path.extend(args[1:])

    file_lists = []
    for arg in scan_path:
        if os.path.isfile(arg) and os.path.splitext(arg)[1] == '.csv':
            file_lists.append(arg)
        elif os.path.isdir(arg):
            files = os.listdir(arg)
            for file_name in files:
                path = arg+file_name
                if os.path.isfile(path) and os.path.splitext(path)[1] == '.csv':
                    file_lists.append(path)

    # print(file_lists)
    for path in file_lists:
        stock_name, _ = os.path.splitext(os.path.basename(path))
        split_txt = stock_name.split('-')
        if len(split_txt) != 2 or not split_txt[0].isdigit():
            print('ERROR : 指定されたファイル名のフォーマットに問題があります')
            exit(1)

    target = OFXExporter()

    stock_acct = target.config['DOWNLOAD']['stock_account']
    output_dir = target.config['BASE']['output_dir']
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
        
    try:
        # プライスファイルを解析する
        for path in file_lists:
            target.analyze(path)
        # print(target.active_list)

        if stock_acct in target.get_active_list():
            data = target.active_list[stock_acct]

            parse_data = data.parse_by_date()
            for dict_id, data in parse_data.items():
                # 日毎のデータをOFXデータに変換する
                generator = OFXGenerator()
                generator.exchange(data)

                # OFXデータをファイルとしてセーブする
                file_name = output_dir + '/OFX_' + stock_acct \
                    + '_' + dict_id \
                    + '.ofx'
                generator.save(file_name)
        else:
            print('ERROR : 解析データがありません')

    except Exception as e:
        print('ERROR : ファイルの解析に失敗しました', e)
        print(traceback.format_exc())
        exit(1)

    exit(0)


if (__name__ == '__main__'):
    main()
