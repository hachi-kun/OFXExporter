#!/usr/bin/python
# -*- coding: utf-8 -*-

""" cvs->OFX 変換　ユーザーインターフェース部
"""
import configparser
import tkinter
from tkinter import messagebox, ttk

import tkinterdnd2


class OFXExporterGuiError(Exception):
    pass


class OFXExporterBase():
    base = None
    config = None

    @classmethod
    def setup(cls, base):
        cls.base = base

    @classmethod
    def configure(cls, config):
        cls.config = configparser.ConfigParser()
        cls.config.read(config)


class OFXExporterDialog(OFXExporterBase):
    enable = True

    @classmethod
    def enable_dialog(cls, mode):
        OFXExporterDialog.enable = mode

    def __init__(self, msg):
        self.msg = msg

    def showerror(self):
        if OFXExporterDialog.enable:
            tkinter.messagebox.showerror('エラー', self.msg)
        else:
            print('エラー : ', self.msg)

    def showinfo(self):
        if OFXExporterDialog.enable:
            tkinter.messagebox.showinfo('情報', self.msg)
        else:
            print('情報 : ', self.msg)

    def askyesno(self):
        if OFXExporterDialog.enable:
            return tkinter.messagebox.askyesno('問い合わせ', self.msg)
        else:
            print('問い合わせ : ', self.msg)
            return True


class AccountCmdUI(OFXExporterBase):
    def __init__(self, title):
        self.window = None
        self.account_update_ui = None
        self.listbox_ui = None
        self.title = title

    def generate(self):
        # アカウント管理ウインドを作成する
        self.window = tkinter.Toplevel()
        self.window.geometry('300x300')
        self.window.title(self.title)

        # リストの作成
        frame = tkinter.Frame(self.window)
        frame.pack(side=tkinter.TOP, anchor=tkinter.N,
                   fill=tkinter.BOTH, expand=1)
        items = tkinter.StringVar(value=self.list_items())
        listbox = tkinter.Listbox(frame, listvariable=items)
        self.listbox_ui = listbox  # リストを記憶しておく
        listbox.pack(fill=tkinter.BOTH, expand=1)

        # ボタンの作成
        frame = tkinter.Frame(self.window)
        frame.pack(anchor=tkinter.S)
        button = tkinter.Button(frame, text='追加', command=self.account_update)
        button.pack(side=tkinter.LEFT)
        button = tkinter.Button(frame, text='変更', command=self.account_modify)
        button.pack(side=tkinter.LEFT)
        button = tkinter.Button(frame, text='削除', command=self.account_delete)
        button.pack(side=tkinter.LEFT)

    def destroy(self):
        if self.window is not None and self.window.winfo_exists():
            self.window.destroy()

    def list_items(self):
        return self.base.get_account_list()

    def list_update(self):
        self.listbox_ui.delete(0, tkinter.END)
        for item in self.list_items():
            self.listbox_ui.insert(tkinter.END, item)

    def account_update(self):
        if self.account_update_ui is not None:
            if self.account_update_ui.window.winfo_exists():
                return

        self.account_update_ui = AccountUpdateUI(title='account追加')
        self.account_update_ui.generate()

    def account_modify(self):
        if self.account_update_ui is not None:
            if self.account_update_ui.window.winfo_exists():
                return

        index = self.listbox_ui.curselection()
        if index:
            key = self.listbox_ui.get(index[0])
            try:
                name, bank, store, account = \
                    self.base.get_account_info(key)

            except Exception as e:
                OFXExporterDialog(e).showerror()
                return

            self.account_update_ui = AccountUpdateUI(title='account更新',
                                                     name=name,
                                                     bank=bank,
                                                     store=store,
                                                     account=account,
                                                     replace=key)
            self.account_update_ui.generate()

    def account_delete(self):
        index = self.listbox_ui.curselection()
        if index > 0:
            try:
                key = self.listbox_ui.get(index[0])
                self.base.account_remove(key)
            except Exception as e:
                OFXExporterDialog(e).showerror()
                return

    def update_notify(self):
        self.list_update()


class AccountUpdateUI(OFXExporterBase):
    def __init__(self, title, name='', bank='', store='', account='', replace=None):
        self.window = None
        self.listbox_ui = None
        self.name_ui = None
        self.bank_ui = None
        self.store_ui = None
        self.account_ui = None
        self.title = title

        self.replace = replace
        self.name = name
        self.bank = bank
        self.store = store
        self.account = account

    def selected(self, event):
        # 選択したアイテムでラベル情報を書き換える
        index = self.listbox_ui.curselection()
        if index:
            self.bank_ui.configure(text=self.listbox_ui.get(index))

    def generate(self):

        # アカウント更新ウインドを作成する
        self.window = tkinter.Toplevel()
        self.window.geometry('300x300')
        self.window.title(self.title)

        # リストの作成
        frame = tkinter.Frame(self.window)
        frame.pack(side=tkinter.TOP, anchor=tkinter.N,
                   fill=tkinter.BOTH, expand=1)
        items = tkinter.StringVar(value=self.list_items())
        listbox = tkinter.Listbox(frame, listvariable=items)
        self.listbox_ui = listbox  # リストを記憶しておく
        listbox.bind("<<ListboxSelect>>", self.selected)
        listbox.pack(fill=tkinter.BOTH, expand=1)

        # 情報入力の作成
        frame = tkinter.Frame(self.window)
        frame.pack()
        sub_frame = tkinter.Frame(frame)
        sub_frame.pack()

        label = tkinter.Label(sub_frame, text='名称 : ')
        label.grid(row=0, column=0)
        entry = tkinter.Entry(sub_frame, width=20)
        entry.insert(0, self.name)
        self.name_ui = entry  # リストと連動させるので記憶しておく
        entry.grid(row=0, column=1)

        label = tkinter.Label(sub_frame, text='機関 : ')
        label.grid(row=1, column=0)
        label = tkinter.Label(sub_frame, text=self.bank, anchor=tkinter.W)
        self.bank_ui = label  # リストと連動させるので記憶しておく
        label.grid(row=1, column=1, sticky=tkinter.W+tkinter.E)

        label = tkinter.Label(sub_frame, text='店番 : ')
        label.grid(row=2, column=0)
        entry = tkinter.Entry(sub_frame, width=20)
        entry.insert(0, self.store)
        self.store_ui = entry  # リストと連動させるので記憶しておく
        entry.grid(row=2, column=1)

        label = tkinter.Label(sub_frame, text='口座 : ')
        label.grid(row=3, column=0)
        entry = tkinter.Entry(sub_frame, width=20)
        entry.insert(0, self.account)
        self.account_ui = entry  # リストと連動させるので記憶しておく
        entry.grid(row=3, column=1)

        # ボタンの作成
        frame = tkinter.Frame(self.window)
        frame.pack(anchor=tkinter.S)
        button = tkinter.Button(frame, text='更新', command=self.update_item)
        button.pack(side=tkinter.LEFT)
        button = tkinter.Button(frame, text='取り消し', command=self.destroy)
        button.pack(side=tkinter.LEFT)

    def destroy(self):
        if self.window is not None and self.window.winfo_exists():
            self.window.destroy()

    def list_items(self):
        return self.base.get_bank_list()

    def update_item(self):
        name = self.name_ui.get().rstrip()
        bank = self.bank_ui.cget('text').rstrip()
        store = self.store_ui.get().rstrip()
        account = self.account_ui.get().rstrip()

        try:
            self.base.account_modify(name=name,
                                     bank=bank,
                                     store=store,
                                     account=account,
                                     replace=self.replace)
        except Exception as e:
            OFXExporterDialog(e).showerror()
            return

        self.destroy()


class MainUI(OFXExporterBase):
    def __init__(self):
        self.window = None
        self.combobox_ui = None
        self.listbox_ui = None
        self.button_ui = None
        self.account_command_ui = None

    def generate(self):

        # ウインドウの作成
        # self.window = tkinter.Tk()
        self.window = tkinterdnd2.TkinterDnD.Tk()  # ドラッグアンドドロップ機能
        self.window.title('OFXExporter')
        self.window.geometry('300x300')

        # メニューの作成
        menu = tkinter.Menu(self.window)
        self.window.config(menu=menu)

        menu_item = tkinter.Menu(self.window)
        menu.add_cascade(label='ファイル', menu=menu_item)

        menu_item.add_command(
            label='アカウント管理', command=self.account_command)
        menu_item.add_command(
            label='終了', command=self.exit_command)

        menu_item = tkinter.Menu(self.window)
        menu.add_cascade(label='ツール', menu=menu_item)
        menu_item.add_command(
            label='価格更新', command=self.price_update)

        # コンボボックスの作成
        frame = ttk.Frame(self.window)
        frame.pack(side=tkinter.TOP, anchor=tkinter.CENTER)
        label = tkinter.Label(frame, text='アカウント : ')
        label.pack(side=tkinter.LEFT)
        account_list = ['Auto']  # 自動判定の選択
        account_list.extend(self.base.get_account_list())
        combobox = ttk.Combobox(frame,
                                values=account_list,
                                state='readonly')
        combobox.current(0)
        combobox.bind('<<ComboboxSelected>>', self.list_reset)
        self.combobox_ui = combobox  # リストを記憶しておく
        combobox.pack(side=tkinter.LEFT)

        # リストの作成
        frame = tkinter.Frame(self.window)
        frame.pack(side=tkinter.TOP, anchor=tkinter.N,
                   fill=tkinter.BOTH, expand=1)
        listbox = tkinter.Listbox(frame,
                                  selectforeground="white",
                                  selectbackground="blue")
        listbox.bind('<<ListboxSelect>>', self.list_select)
        self.listbox_ui = listbox  # リストを記憶しておく
        listbox.drop_target_register(tkinterdnd2.DND_FILES)
        listbox.dnd_bind('<<Drop>>', self.filedrop)
        listbox.pack(fill=tkinter.BOTH, expand=1)

        # ボタンの作成・チェックボックスの作成
        frame = tkinter.Frame(self.window)
        frame.pack(side=tkinter.TOP, anchor=tkinter.S, fill='x')
        button = tkinter.Button(frame, text='変換',
                                command=self.convert_command,
                                state='disabled')
        self.button_ui = button
        button.pack(anchor=tkinter.CENTER)
        if self.base.is_auto_import():
            checkbutton = tkinter.Checkbutton(frame, text='自動読み込み')
            checkbutton.pack(anchor=tkinter.NE)

    def destroy(self):
        self.window.quit()

    def filedrop(self, event):
        file_list = event.data.split(' ')
        analyze_mode = self.combobox_ui.get()

        try:
            # 処理するファイル数のチェック
            if analyze_mode == 'Auto':
                if len(file_list) != 1:
                    raise OFXExporterGuiError('Auto Modeでは\n'
                                              '一つの明細しか扱えません')

            # 初期化する
            self.list_reset()

            result = self.base.analyze_files(file_list, analyze_mode)

            if analyze_mode == 'Auto':
                new_data = [(item, 'True')
                            for item in self.base.get_active_list()]
                self.list_update(new_data, conv_mode=False)

                if not new_data:
                    OFXExporterDialog('対応するフィルタが見つかりません').showinfo()
            else:
                new_data = result
                if not self.list_update(new_data, conv_mode=True):
                    raise OFXExporterGuiError('解析に失敗したファイルがあります。')

        except Exception as e:
            OFXExporterDialog(e).showerror()
            return

    def update_notify(self):
        # コンボボックスの項目を更新する
        account_list = ['Auto']
        account_list.extend(self.base.get_account_list())
        self.combobox_ui['values'] = account_list
        self.combobox_ui.current(0)

        if self.account_command_ui is not None:
            if self.account_command_ui.window.winfo_exists():
                self.account_command_ui.update_notify()

    def list_reset(self, event=None):
        self.listbox_ui.delete(0, tkinter.END)
        self.button_ui['state'] = 'disabled'
        self.base.reset()

    def list_select(self, event):
        curselection = event.widget.curselection()
        if curselection and curselection[0] >= 0:
            self.button_ui['state'] = 'normal'
        else:
            self.button_ui['state'] = 'disabled'

    def list_update(self, new_data, conv_mode=False):

        # 解析結果をリストに表示する
        self.listbox_ui.delete(0, tkinter.END)
        fail = 0
        for index, value in enumerate(new_data):
            self.listbox_ui.insert(tkinter.END, value[0])
            if not value[1]:
                self.listbox_ui.itemconfig(index, {'bg': 'red'})
                fail = fail + 1

        if fail == 0 and conv_mode:
            self.button_ui['state'] = 'normal'
            return True
        else:
            self.button_ui['state'] = 'disabled'
            return False

    def account_command(self):
        if self.account_command_ui is None:
            self.account_command_ui = AccountCmdUI(title='account一覧')
            self.account_command_ui.generate()

    def exit_command(self):
        self.destroy()

    def price_update(self):
        if OFXExporterDialog('価格情報をダウンロードしますか？').askyesno():

            self.base.reset()
            try:
                self.base.price_download()
                OFXExporterDialog('変換しました').showinfo()

            except Exception as e:
                OFXExporterDialog(e).showerror()
            finally:
                # 表示・内部情報をリセットする
                self.base.reset()
                self.list_reset()
                self.update_notify()

    def convert_command(self):

        analyze_mode = self.combobox_ui.get()

        # 変換フィルタを選択する
        if analyze_mode == 'Auto':
            index = self.listbox_ui.curselection()
            if not index:
                return

            key = self.listbox_ui.get(index[0])
        else:
            key = analyze_mode

        # 変換処理を実行する
        try:
            self.base.convert(key)
            OFXExporterDialog('変換しました').showinfo()

            # GUIを最新に更新する
            self.list_reset()
            self.update_notify()

        except Exception as e:
            OFXExporterDialog(e).showerror()

        return


class OFXExporterGui():
    def __init__(self):
        # GUIクラスの共通データを初期化する
        OFXExporterBase.setup(self)

        self.gui = MainUI()
        self.enable = False

    def start(self):
        self.enable = True
        self.gui.generate()
        self.gui.window.mainloop()

    def destroy(self):
        self.enable = False
        self.gui.destroy()

    def update_notify(self):
        '''
        ベースの情報が変更になった場合呼び出される
        GUIは必要なら表示データの再構築をする必要がある
        '''
        if self.enable:
            self.gui.update_notify()

    # 以降のメソッドはオーバライドして使用される
    def is_auto_import(self):
        pass

    def reset(self):
        pass

    def get_active_list(self):
        return []

    def get_account_list(self):
        return []

    def get_bank_list(self):
        return []

    def get_account_info(self, key):
        bank = None
        store = None
        account = None
        return key, bank, store, account

    def account_modify(self, name, bank, store, account, replace):
        super().update_notify()
        pass

    def account_remove(self, key):
        super().update_notify()
        pass

    def analyze_files(self, name):
        return []

    def convert(self, key):
        pass

    def price_download(self):
        pass

# -------------------------------------


class TestOFXExporterGui(OFXExporterGui):
    def __init__(self):
        super().__init__()

    def is_auto_import(self):
        return True

    def get_active_list(self):
        return ['候補 ' + str(x) for x in range(0, 30)]

    def get_account_list(self):
        return ['銀行 ' + str(x) + '-000-00000' for x in range(0, 30)]

    def get_bank_list(self):
        return ['銀行 ' + str(x) for x in range(0, 30)]

    def get_account_info(self, key):
        split_txt = key.split('-')

        bank = split_txt[0]
        store = '000'
        account = '00000'
        return key, bank, store, account

    def convert(self, key):
        print('call convert()')
        return None

    def account_modify(self, name, bank, store, account, replace):
        print('call account_update(' + name + ')')
        super().update_notify()

    def account_remove(self, key):
        print('call account_delete(' + key + ')')
        super().update_notify()

    def analyze_files(self, name):
        print('call analyze_files(' + name + ')')
        return []


def main():
    TestOFXExporterGui().start()


if (__name__ == '__main__'):
    main()
