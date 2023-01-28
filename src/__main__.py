#! /usr/bin/env python3.8
# -*- coding: utf-8 -*-


import tkinter as tk
from tkinter import messagebox
import os
import uuid
import json
import webbrowser
import pyperclip

import secrets
from base64 import urlsafe_b64encode as b64encode, urlsafe_b64decode as b64decode
from cryptography import fernet
from cryptography.hazmat import backends
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf import pbkdf2


class App(tk.Tk):
    PADDING = 10
    NUMBER_WIDTH = 10
    WINDOW_WIDTH = 600
    WINDOW_HEIGHT = 400

    _is_new = False
    _password = None
    _storage = None
    
    _entries = {
        'frame': None,
        'canvas': None,
        'scrollable': None,
        'scrollbar': None,
        'entries': [],
    }
    _commands = {
        'add': {'button': None},
        'save': {'button': None},
        'search': {
            'entry': None,
            'label': None,
        },
    }

    def __init__(self, entries_storage):
        super().__init__()
        self.wm_title('Links & Passwords')
        self.wm_minsize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.wm_resizable(width=False, height=False)

        self._storage = entries_storage
        try:
            self._storage.connect()
        except FileNotFoundError:
            self._is_new = True

        self._ask_password()

    def _app_exit(self):
        answer = messagebox.askyesnocancel(
            'Quit', 'Quitting. Save the changes?')
        if answer is None:
            return
        if answer == True:
            self._storage.save(password=self._password)
        self.destroy()

    def _paint(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self._entries['frame'] = tk.Frame(self, width=self.WINDOW_WIDTH, height=self.WINDOW_HEIGHT)
        self._entries['frame'].grid(row=0, column=0, padx=self.PADDING, pady=self.PADDING)
        self._entries['canvas'] = tk.Canvas(self._entries['frame'], width=self.WINDOW_WIDTH, height=self.WINDOW_HEIGHT)
        self._entries['canvas'].grid(row=0, column=0, padx=self.PADDING, pady=self.PADDING)

        self._entries['scrollbar'] = tk.Scrollbar(self._entries['frame'], orient='vertical', command=self._entries['canvas'].yview)
        self._entries['scrollbar'].grid(row=0, column=1, sticky='ns')

        self._entries['scrollable'] = tk.Frame(self._entries['canvas'])
        self._entries['scrollable'].grid(row=0, column=0, padx=self.PADDING, pady=self.PADDING)
        self._entries['scrollable'].bind(
            '<Configure>',
            lambda _: self._entries['canvas'].configure(
                scrollregion=self._entries['canvas'].bbox('all')
            )
        )
        self._entries['canvas'].create_window((0, 0), window=self._entries['scrollable'], anchor='nw')
        self._entries['canvas'].configure(yscrollcommand=self._entries['scrollbar'].set)

        self._commands['frame'] = tk.Frame(self)
        self._commands['frame'].grid(row=1, column=0, pady=self.PADDING)

        self._commands['frame'].grid_columnconfigure(0, weight=1)
        self._commands['frame'].grid_columnconfigure(1, weight=1)
        self._commands['frame'].grid_columnconfigure(2, weight=1)
        self._commands['frame'].grid_columnconfigure(3, weight=1)

        self._commands['save']['button'] = tk.Button(self._commands['frame'], text='Save', command=self._ask_save)
        self._commands['save']['button'].grid(row=0, column=0, padx=self.PADDING)

        self._commands['add']['button'] = tk.Button(self._commands['frame'], text='Add new', command=self._ask_add_entry)
        self._commands['add']['button'].grid(row=0, column=1, padx=self.PADDING)

        self._commands['search']['entry'] = tk.Entry(self._commands['frame'])
        self._commands['search']['entry'].bind('<KeyRelease>', lambda _: self._search_entries())
        self._commands['search']['entry'].grid(row=0, column=2, padx=self.PADDING)
        self._commands['search']['label'] = tk.Label(self._commands['frame'], text='Search')
        self._commands['search']['label'].grid(row=0, column=3, padx=self.PADDING)

    def _paint_entries(self):
        for child in self._entries['scrollable'].winfo_children():
            child.destroy()

        row_index = 0
        entries = self._storage.get_filtered() if self._storage.query != '' else self._storage.get_all()
        for entry_id, entry_data in entries.items():
            self._entries['entries'].append({
                'id': {'label': None},
                'link': {'entry': None},
                'open': {'button': None},
                'copy': {'button': None},
                'delete': {'button': None},
                'update': {'button': None},
            })
            self._entries['entries'][row_index]['id']['label'] = \
                tk.Label(self._entries['scrollable'], text=row_index + 1, width=self.NUMBER_WIDTH, justify='left')
            self._entries['entries'][row_index]['id']['label'].grid(row=row_index, column=0)
            self._entries['entries'][row_index]['link']['entry'] = tk.Entry(self._entries['scrollable'], bd=0)
            self._entries['entries'][row_index]['link']['entry'].insert(0, entry_data['link'])
            self._entries['entries'][row_index]['link']['entry'].configure(state='readonly')
            self._entries['entries'][row_index]['link']['entry'].grid(row=row_index, column=1)
            self._entries['entries'][row_index]['open']['button'] = \
                tk.Button(self._entries['scrollable'], text='Open',
                          command=lambda link=entry_data['link']: webbrowser.open_new_tab(link))
            self._entries['entries'][row_index]['open']['button'].grid(row=row_index, column=2)
            self._entries['entries'][row_index]['copy']['button'] = \
                tk.Button(self._entries['scrollable'],text='Copy password',
                          command=lambda password=entry_data['password']: pyperclip.copy(password))
            self._entries['entries'][row_index]['copy']['button'].grid(row=row_index, column=3)
            self._entries['entries'][row_index]['delete']['button'] = \
                tk.Button(self._entries['scrollable'], text='Delete',
                          command=lambda entry_id=entry_id: self._ask_delete_entry(entry_id=entry_id))
            self._entries['entries'][row_index]['delete']['button'].grid(row=row_index, column=4)
            self._entries['entries'][row_index]['update']['button'] = \
                tk.Button(self._entries['scrollable'], text='Update',
                          command=lambda entry_id=entry_id: self._ask_update_entry(entry_id=entry_id))
            self._entries['entries'][row_index]['update']['button'].grid(row=row_index, column=5)
            row_index += 1

    def _ask_password(self):
        def _paint_app():
            self.protocol('WM_DELETE_WINDOW', self._app_exit)
            self._paint()
            self._paint_entries()

        def _confirm_command(password):
            if self._is_new:
                self._storage.save(password=password)
            else:
                self._storage.load(password=password)
            self._password = password

        confirm_button_text = 'Create new database' if self._is_new else 'Continue with the existing database'

        password_window = ModalWindow(command_on_close=lambda: self.destroy())
        password_window.set_password_entry(can_toggle_show=False)
        password_window.set_repainter(_paint_app)
        password_window.set_confirm_button(text=confirm_button_text,
                                           command=lambda **kwargs: _confirm_command(kwargs['password']),
                                           error_message='The password is not correct',
                                           will_destroy_on_error=False)
        password_window.paint()

    def _search_entries(self):
        self._storage.query = self._commands['search']['entry'].get()
        self._paint_entries()

    def _ask_save(self):
        answer = messagebox.askquestion('Save', 'Save the changes?')
        if answer == 'yes':
            self._storage.save(password=self._password)

    def _ask_delete_entry(self, entry_id=''):
        answer = messagebox.askquestion(
            'Delete', f'Delete the selected entry?')
        if answer == 'no':
            return
        self._storage.delete_entry(entry_id=entry_id)
        self._paint_entries()

    def _ask_add_entry(self):
        add_entry_window = ModalWindow()
        add_entry_window.set_repainter(self._paint_entries)
        add_entry_window.set_link_entry()
        add_entry_window.set_password_entry()
        add_entry_window.set_confirm_button(text='Add new entry', command=self._storage.add_entry)
        add_entry_window.paint()

    def _ask_update_entry(self, entry_id=''):
        initial_entry = self._storage.get_by_id(entry_id)
        update_entry_window = ModalWindow()
        update_entry_window.set_repainter(self._paint_entries)
        update_entry_window.set_link_entry(placeholder=initial_entry['link'])
        update_entry_window.set_password_entry(placeholder=initial_entry['password'])
        update_entry_window.set_confirm_button(text='Update the entry',
                                               command=lambda **kwargs: self._storage.update_entry(entry_id=entry_id, **kwargs))
        update_entry_window.paint()


class ModalWindow(tk.Toplevel):
    PADDING = 10
    _inputs = {
        'link': {'label': None, 'entry': None},
        'password': {'label': None, 'entry': None},
    }
    _show_password = {
        'button': None,
        'is_shown': None,
    }
    _confirm = {
        'button': None,
        'text': None,
        'command': None,
        'error_message': None,
        'will_destroy_on_error': None
    }

    def __init__(self, is_resizable=False, is_closable=True, command_on_close=None):
        super().__init__()
        self.wm_resizable(width=is_resizable, height=is_resizable)
        if is_closable == False:
            self.protocol('WM_DELETE_WINDOW', lambda: None)
        if command_on_close is not None:
            self.protocol('WM_DELETE_WINDOW', command_on_close)

    def _confirm_command(self):
        link = '' if self._inputs['link']['entry'] is None else self._inputs['link']['entry'].get()
        password = '' if self._inputs['password']['entry'] is None else self._inputs['password']['entry'].get()
        try:
            self._confirm['command'](link=link, password=password)
        except Exception as e:
            messagebox.showerror('Error', self._confirm['error_message'] or str(e))
            if self._confirm['will_destroy_on_error']:
                self.destory()
        else:
            self._repaint()
            self.destroy()

    def _toggle_password_show(self):
        self._show_password['is_shown'] = not self._show_password['is_shown']
        password_mode = '' if self._show_password['is_shown'] else '*'
        password_button_text = 'Hide' if self._show_password['is_shown'] else 'Show'
        self._show_password['button'].configure(text=password_button_text)
        self._inputs['password']['entry'].configure(show=password_mode)

    def set_confirm_button(self, text='Confirm', command=lambda: None, error_message='Error', will_destroy_on_error=True):
        self._confirm['command'] = command
        self._confirm['button'] = tk.Button(self, text=text, command=self._confirm_command)
        self._confirm['error_message'] = error_message
        self._confirm['will_destroy_on_error'] = will_destroy_on_error

    def set_repainter(self, repainter=lambda: None):
        self._repaint = repainter

    def set_password_entry(self, is_shown=False, can_toggle_show=True, placeholder=''):
        self._inputs['password']['label'] = tk.Label(self, text='Password')
        self._inputs['password']['entry'] = tk.Entry(self, show='' if is_shown else '*')
        self._inputs['password']['entry'].insert(0, placeholder)
        if can_toggle_show:
            self._show_password['is_shown'] = is_shown
            self._show_password['button'] = tk.Button(self, text='Show', command=self._toggle_password_show)

    def set_link_entry(self, placeholder=''):
        self._inputs['link']['label'] = tk.Label(self, text='Link')
        self._inputs['link']['entry'] = tk.Entry(self)
        self._inputs['link']['entry'].insert(0, placeholder)

    def paint(self):
        if self._inputs['link']['label'] and self._inputs['link']['entry']:
            self._inputs['link']['label'].grid(row=0, column=0, pady=self.PADDING, padx=self.PADDING)
            self._inputs['link']['entry'].grid(row=0, column=1, pady=self.PADDING, padx=self.PADDING)
        if self._inputs['password']['label'] and self._inputs['password']['entry']:
            self._inputs['password']['label'].grid(row=1, column=0, pady=self.PADDING, padx=self.PADDING)
            self._inputs['password']['entry'].grid(row=1, column=1, pady=self.PADDING, padx=self.PADDING)
        if self._show_password['button']:
            self._show_password['button'].grid(row=1, column=3, pady=self.PADDING, padx=self.PADDING)
        if self._confirm['button']:
            self._confirm['button'].grid(row=2, columnspan=4, pady=self.PADDING, padx=self.PADDING)


class FernetEncryptor:
    ITERATIONS = 200_000
    _backend = backends.default_backend()

    def _derive_key(self, password='', salt='', iterations=ITERATIONS):
        kdf = pbkdf2.PBKDF2HMAC(algorithm=hashes.SHA512(), length=32, salt=salt,
                                iterations=iterations, backend=self._backend)
        return b64encode(kdf.derive(password))

    def encrypt(self, data='', password='', iterations=ITERATIONS):
        salt = secrets.token_bytes(16)
        key = self._derive_key(password.encode(), salt)
        encrypted_data = salt + iterations.to_bytes(4, 'big') + b64decode(fernet.Fernet(key).encrypt(data.encode()))
        return encrypted_data

    def decrypt(self, token=b'', password=''):
        salt, iterations, token = token[:16], token[16:20], b64encode(token[20:])
        iterations = int.from_bytes(iterations, 'big')
        key = self._derive_key(password.encode(), salt, iterations)
        return fernet.Fernet(key).decrypt(token).decode()


class EntriesStorage:
    DATABASE_FILE_NAME = os.path.join(os.path.dirname(__file__), '.database')
    _data = bytes()
    _entries = {}
    _query = ''

    def __init__(self, encryptor):
        self._encryptor = encryptor

    @property
    def query(self):
        return self._query

    @query.setter
    def query(self, value):
        self._query = value

    def connect(self):
        if not os.path.exists(self.DATABASE_FILE_NAME):
            raise FileNotFoundError('The database is not found in the directory with the app running.')
        with open(self.DATABASE_FILE_NAME, 'rb') as database_file:
            self._data = database_file.read()

    def load(self, password=''):
        try:
            self._entries = json.loads(self._encryptor.decrypt(token=self._data, password=password))
        except:
            raise PasswordNotCorrectError()

    def save(self, password=''):
        self._data = self._encryptor.encrypt(data=json.dumps(self._entries), password=password)
        with open(self.DATABASE_FILE_NAME, 'wb') as database_file:
            database_file.write(self._data)

    def add_entry(self, link='', password=''):
        self._entries[str(uuid.uuid4())] = {
            'link': link,
            'password': password,
        }

    def delete_entry(self, entry_id=''):
        self._entries.pop(entry_id)

    def update_entry(self, entry_id, link='', password=''):
        self._entries[entry_id] = {
            'link': link,
            'password': password,
        }

    def get_all(self):
        return self._entries

    def get_filtered(self):
        filtered_items = filter(lambda item: self._query in item[1]['link'], self._entries.items())
        return {key: value for key, value in filtered_items}

    def get_by_id(self, entry_id=''):
        return self._entries.get(entry_id)


class PasswordNotCorrectError(Exception):
    def __init__(self, message='The given password is not correct'):
        super().__init__(message)


if __name__ == '__main__':
    app = App(EntriesStorage(FernetEncryptor()))
    app.mainloop()
