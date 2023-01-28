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

    def __init__(self, entries_storage):
        super().__init__()
        self.wm_title('Links & Passwords')
        self.wm_minsize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.wm_resizable(width=False, height=False)

        self._entries_storage = entries_storage
        try:
            self._entries_storage.connect()
        except FileNotFoundError:
            self._is_new = True
            self._entries_storage.create()

        self._ask_password()

    def _app_exit(self):
        answer = messagebox.askyesnocancel(
            'Quit', 'Quitting. Save the changes?')
        if answer is None:
            return
        if answer == True:
            self._entries_storage.save(self._password)
        self.destroy()

    def _paint(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self._entries_frame = tk.Frame(
            self, width=self.WINDOW_WIDTH, height=self.WINDOW_HEIGHT)
        self._entries_frame.grid(
            row=0, column=0, padx=self.PADDING, pady=self.PADDING)
        self._entries_canvas = tk.Canvas(
            self._entries_frame, width=self.WINDOW_WIDTH, height=self.WINDOW_HEIGHT)
        self._entries_canvas.grid(
            row=0, column=0, padx=self.PADDING, pady=self.PADDING)

        self._entries_scrollbar = tk.Scrollbar(
            self._entries_frame, orient='vertical', command=self._entries_canvas.yview)
        self._entries_scrollbar.grid(row=0, column=1, sticky='ns')

        self._entries_scrollable_frame = tk.Frame(self._entries_canvas)
        self._entries_scrollable_frame.grid(
            row=0, column=0, padx=self.PADDING, pady=self.PADDING)
        self._entries_scrollable_frame.bind(
            '<Configure>',
            lambda _: self._entries_canvas.configure(
                scrollregion=self._entries_canvas.bbox('all')
            )
        )

        self._entries_canvas.create_window(
            (0, 0), window=self._entries_scrollable_frame, anchor='nw')
        self._entries_canvas.configure(
            yscrollcommand=self._entries_scrollbar.set)

        self._entries_scrollable_frame.grid_columnconfigure(0, weight=0)
        self._entries_scrollable_frame.grid_columnconfigure(1, weight=1)
        self._entries_scrollable_frame.grid_columnconfigure(2, weight=0)

        self._command_frame = tk.Frame(self)
        self._command_frame.grid(row=1, column=0, pady=self.PADDING)

        self._command_frame.grid_columnconfigure(0, weight=1)
        self._command_frame.grid_columnconfigure(1, weight=1)
        self._command_frame.grid_columnconfigure(2, weight=1)
        self._command_frame.grid_columnconfigure(3, weight=1)

        self._save_button = tk.Button(
            self._command_frame, text='Save', command=self._ask_save)
        self._save_button.grid(row=0, column=0, padx=self.PADDING)

        self._add_button = tk.Button(
            self._command_frame, text='Add new', command=self._ask_add_entry)
        self._add_button.grid(row=0, column=1, padx=self.PADDING)

        self._search_entry = tk.Entry(self._command_frame)
        self._search_entry.bind(
            '<KeyRelease>', lambda _: self._search_entries())
        self._search_entry.grid(row=0, column=2, padx=self.PADDING)
        self._search_label = tk.Label(self._command_frame, text='Search')
        self._search_label.grid(row=0, column=3, padx=self.PADDING)

    def _paint_entries(self):
        for child in self._entries_scrollable_frame.winfo_children():
            child.destroy()

        row_index = 0
        entries = self._entries_storage.get_filtered(
        ) if self._entries_storage.query != '' else self._entries_storage.get_all()
        for entry_id, entry_data in entries.items():
            shown_index = row_index + 1
            entry_id_label = tk.Label(
                self._entries_scrollable_frame, text=shown_index, width=self.NUMBER_WIDTH, justify='left')
            entry_id_label.grid(row=row_index, column=0)
            entry_link_readonly_entry = tk.Entry(
                self._entries_scrollable_frame, bd=0)
            entry_link_readonly_entry.insert(0, entry_data.get('link'))
            entry_link_readonly_entry.configure(state='readonly')
            entry_link_readonly_entry.grid(row=row_index, column=1)
            entry_open_link_button = tk.Button(
                self._entries_scrollable_frame, text='Open', command=lambda link=entry_data.get('link'): webbrowser.open_new_tab(link))
            entry_open_link_button.grid(row=row_index, column=2)
            entry_copy_password_button = tk.Button(
                self._entries_scrollable_frame, text='Copy password', command=lambda password=entry_data.get('password'): pyperclip.copy(password))
            entry_copy_password_button.grid(row=row_index, column=3)
            entry_delete_button = tk.Button(
                self._entries_scrollable_frame, text='Delete', command=lambda shown_index=shown_index, entry_id=entry_id: self._ask_delete_entry(shown_index, entry_id))
            entry_delete_button.grid(row=row_index, column=4)
            entry_update_button = tk.Button(
                self._entries_scrollable_frame, text='Update', command=lambda entry_id=entry_id: self._ask_update_entry(entry_id))
            entry_update_button.grid(row=row_index, column=5)
            row_index += 1

    def _ask_password(self):
        def _paint_app():
            self.protocol('WM_DELETE_WINDOW', self._app_exit)
            self._paint()
            self._paint_entries()

        def _confirm_command(password):
            if self._is_new:
                self._entries_storage.save(password)
            else:
                self._entries_storage.load(password)
            self._password = password

        password_window = ModalWindow(
            is_closable=True, command_on_close=lambda: self.destroy())
        password_window.set_password_entry(can_toggle_show=False)
        password_window.set_repaint_function(_paint_app)
        password_window.set_confirm_button(text='Confirm the password' + (' as new' if self._is_new else ''), command=lambda **kwargs: _confirm_command(kwargs['password']),
                                           error_message='The password is not correct', will_destroy_on_error=False)
        password_window.paint()

    def _search_entries(self):
        self._entries_storage.query = self._search_entry.get()
        self._paint_entries()

    def _ask_save(self):
        answer = messagebox.askquestion('Save', 'Save the changes?')
        if answer == 'yes':
            self._entries_storage.save(self._password)

    def _ask_delete_entry(self, shown_index, entry_id):
        answer = messagebox.askquestion(
            'Delete', f'Delete entry #{shown_index}?')
        if answer == 'no':
            return
        self._entries_storage.delete_entry(entry_id)
        self._paint_entries()

    def _ask_add_entry(self):
        add_entry_window = ModalWindow()
        add_entry_window.set_repaint_function(self._paint_entries)
        add_entry_window.set_link_entry()
        add_entry_window.set_password_entry()
        add_entry_window.set_confirm_button(
            text='Add new entry', command=self._entries_storage.add_entry)
        add_entry_window.paint()

    def _ask_update_entry(self, entry_id):
        initial_entry = self._entries_storage.get_by_id(entry_id)
        update_entry_window = ModalWindow()
        update_entry_window.set_repaint_function(self._paint_entries)
        update_entry_window.set_link_entry(default=initial_entry.get('link'))
        update_entry_window.set_password_entry(
            default=initial_entry.get('password'))
        update_entry_window.set_confirm_button(
            text='Update the entry', command=lambda **kwargs: self._entries_storage.update_entry(entry_id, **kwargs))
        update_entry_window.paint()


class ModalWindow(tk.Toplevel):
    PADDING = 10
    _inputs = {'link': {'label': None, 'entry': None},
               'password': {'label': None, 'entry': None}}
    _show_password = {'button': None, 'is_shown': None}
    _confirm = {'button': None, 'text': None, 'command': None,
                'error_message': None, 'will_destroy_on_error': None}

    def __init__(self, is_resizable=False, is_closable=True, command_on_close=None):
        super().__init__()
        self.wm_resizable(width=is_resizable, height=is_resizable)
        if is_closable == False:
            self.protocol('WM_DELETE_WINDOW', lambda: None)
        if command_on_close:
            self.protocol('WM_DELETE_WINDOW', command_on_close)

    def _confirm_command(self):
        link = '' if self._inputs['link']['entry'] is None else self._inputs['link']['entry'].get(
        )
        password = '' if self._inputs['password']['entry'] is None else self._inputs['password']['entry'].get(
        )
        try:
            self._confirm['command'](link=link, password=password)
        except Exception as e:
            messagebox.showerror(
                'Error', self._confirm['error_message'] or str(e))
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
        self._confirm['button'] = tk.Button(
            self, text=text, command=self._confirm_command)
        self._confirm['error_message'] = error_message
        self._confirm['will_destroy_on_error'] = will_destroy_on_error

    def set_repaint_function(self, repaint_function):
        self._repaint = repaint_function

    def set_password_entry(self, is_shown=False, can_toggle_show=True, default=''):
        self._inputs['password']['label'] = tk.Label(self, text='Password')
        self._inputs['password']['entry'] = tk.Entry(
            self, show='' if is_shown else '*')
        self._inputs['password']['entry'].insert(0, default)
        if can_toggle_show:
            self._show_password['is_shown'] = is_shown
            self._show_password['button'] = tk.Button(
                self, text='Show', command=self._toggle_password_show)

    def set_link_entry(self, default=''):
        self._inputs['link']['label'] = tk.Label(self, text='Link')
        self._inputs['link']['entry'] = tk.Entry(self)
        self._inputs['link']['entry'].insert(0, default)

    def paint(self):
        if self._inputs['link']['label'] and self._inputs['link']['entry']:
            self._inputs['link']['label'].grid(
                row=0, column=0, pady=self.PADDING, padx=self.PADDING)
            self._inputs['link']['entry'].grid(
                row=0, column=1, pady=self.PADDING, padx=self.PADDING)
        if self._inputs['password']['label'] and self._inputs['password']['entry']:
            self._inputs['password']['label'].grid(
                row=1, column=0, pady=self.PADDING, padx=self.PADDING)
            self._inputs['password']['entry'].grid(
                row=1, column=1, pady=self.PADDING, padx=self.PADDING)
        if self._show_password['button']:
            self._show_password['button'].grid(
                row=1, column=3, pady=self.PADDING, padx=self.PADDING)
        if self._confirm['button']:
            self._confirm['button'].grid(
                row=2, columnspan=4, pady=self.PADDING, padx=self.PADDING)


class FernetEncryptor:
    _backend = backends.default_backend()
    ITERATIONS = 200_000

    def _derive_key(self, password, salt, iterations=ITERATIONS):
        kdf = pbkdf2.PBKDF2HMAC(algorithm=hashes.SHA512(
        ), length=32, salt=salt, iterations=iterations, backend=self._backend)
        return b64encode(kdf.derive(password))

    def encrypt(self, data, password, iterations=ITERATIONS):
        salt = secrets.token_bytes(16)
        key = self._derive_key(password.encode(), salt)
        encrypted_data = b"%b%b%b" % (salt, iterations.to_bytes(
            4, 'big'), b64decode(fernet.Fernet(key).encrypt(data.encode())))
        return encrypted_data

    def decrypt(self, token, password):
        salt, iterations, token = token[: 16], token[16: 20], b64encode(
            token[20:])
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
            raise FileNotFoundError(
                'The database is not found in the directory with the app running.')
        with open(self.DATABASE_FILE_NAME, 'rb') as encrypted_file:
            self._data = encrypted_file.read()

    def create(self):
        open(self.DATABASE_FILE_NAME, 'wb').close()

    def load(self, password):
        try:
            self._entries = json.loads(
                self._encryptor.decrypt(self._data, password))
        except:
            raise PasswordNotCorrectError()

    def save(self, password):
        self._data = self._encryptor.encrypt(
            json.dumps(self._entries), password)
        with open(self.DATABASE_FILE_NAME, 'wb') as encrypted_file:
            encrypted_file.write(self._data)

    def add_entry(self, link='', password=''):
        self._entries[str(uuid.uuid4())] = {
            'link': link,
            'password': password,
        }

    def delete_entry(self, entry_id):
        self._entries.pop(entry_id)

    def update_entry(self, entry_id, link='', password=''):
        self._entries[entry_id]['link'] = link
        self._entries[entry_id]['password'] = password

    def get_all(self):
        return self._entries

    def get_filtered(self):
        filtered_items = filter(lambda item: self._query in item[1].get(
            'link'), self._entries.items())
        return {key: value for key, value in filtered_items}

    def get_by_id(self, entry_id):
        return self._entries.get(entry_id)


class PasswordNotCorrectError(Exception):
    def __init__(self, message='The given password is not correct'):
        super().__init__(message)


if __name__ == '__main__':
    app = App(EntriesStorage(FernetEncryptor()))
    app.mainloop()
