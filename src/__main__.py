#! /usr/bin/env python3.8
# -*- coding: utf-8 -*-


import tkinter as tk
from tkinter import messagebox
import os
import json
import uuid
import pyperclip


class App(tk.Tk):
    PADDING = 10
    WINDOW_WIDTH = 600
    WINDOW_HEIGHT = 400

    def _app_exit(self):
        answer = messagebox.askyesnocancel(
            'Quit', 'Quitting. Save the changes?')
        if answer is None:
            return
        if answer == True:
            self._entries_storage.save()
        self.destroy()

    def __init__(self):
        super().__init__()
        self.wm_title('Links & Passwords')
        self.wm_minsize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.wm_resizable(width=False, height=False)

        self.protocol('WM_DELETE_WINDOW', self._app_exit)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self._entries_storage = EntriesStorage()
        self._paint_entries()

        self._command_frame = tk.Frame(self)
        self._command_frame.grid(row=1, column=0, pady=self.PADDING)

        self._save_button = tk.Button(
            self._command_frame, text='Save', command=self._ask_save)
        self._save_button.grid(row=0, column=0)

        self._add_button = tk.Button(
            self._command_frame, text='Add', command=self._ask_add_entry)
        self._add_button.grid(row=0, column=1)

    def _paint_entries(self):
        if hasattr(self, 'entries_frame'):
            self._entries_frame.grid_remove()

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

        row_index = 0
        for entry_id, entry_data in self._entries_storage.get_all().items():
            entry_id_label = tk.Label(
                self._entries_scrollable_frame, text=row_index + 1)
            entry_id_label.grid(row=row_index, column=0)
            entry_link_readonly_entry = tk.Entry(
                self._entries_scrollable_frame, bd=0)
            entry_link_readonly_entry.insert(0, entry_data.get('link'))
            entry_link_readonly_entry.configure(state='readonly')
            entry_link_readonly_entry.grid(row=row_index, column=1)
            entry_copy_password_button = tk.Button(
                self._entries_scrollable_frame, text='Copy password', command=lambda: pyperclip.copy(entry_data.get('password')))
            entry_copy_password_button.grid(row=row_index, column=2)
            entry_delete_button = tk.Button(
                self._entries_scrollable_frame, text='Delete', command=self._ask_delete_entry(row_index + 1, entry_id))
            entry_delete_button.grid(row=row_index, column=3)
            entry_update_button = tk.Button(
                self._entries_scrollable_frame, text='Update', command=self._ask_update_entry(row_index + 1, entry_id))
            entry_update_button.grid(row=row_index, column=4)
            row_index += 1

    def _ask_save(self):
        answer = messagebox.askquestion('Save', 'Save the changes?')
        if answer == 'yes':
            self._entries_storage.save()

    def _ask_delete_entry(self, shown_index, entry_id):
        def _():
            answer = messagebox.askquestion(
                'Delete', f'Delete entry #{shown_index}?')
            if answer == 'no':
                return
            self._entries_storage.delete_entry(entry_id)
            self._paint_entries()
        return _

    def _add_win_command(self):
        link = self._add_win_link_entry.get()
        password = self._add_win_password_entry.get()
        self._entries_storage.add_entry(link, password)
        self._paint_entries()
        self._add_win.destroy()

    def _add_win_toggle_password_show(self):
        self._add_win_password_is_shown = not self._add_win_password_is_shown
        password_mode = '' if self._add_win_password_is_shown else '*'
        password_button_text = 'Hide' if self._add_win_password_is_shown else 'Show'
        self._add_win_password_show_button.configure(text=password_button_text)
        self._add_win_password_entry.configure(show=password_mode)

    def _ask_add_entry(self):
        self._add_win = tk.Toplevel(self)
        self._add_win.wm_resizable(width=False, height=False)
        self._add_win_link_label = tk.Label(self._add_win, text='Link')
        self._add_win_link_label.grid(
            row=0, column=0, pady=self.PADDING, padx=self.PADDING)
        self._add_win_link_entry = tk.Entry(self._add_win)
        self._add_win_link_entry.grid(
            row=0, column=1, pady=self.PADDING, padx=self.PADDING)
        self._add_win_password_label = tk.Label(self._add_win, text='Password')
        self._add_win_password_label.grid(
            row=1, column=0, pady=self.PADDING, padx=self.PADDING)
        self._add_win_password_entry = tk.Entry(self._add_win, show='*')
        self._add_win_password_entry.grid(
            row=1, column=1, pady=self.PADDING, padx=self.PADDING)
        self._add_win_password_is_shown = False
        self._add_win_password_show_button = tk.Button(
            self._add_win, text='Show')
        self._add_win_password_show_button.configure(
            command=self._add_win_toggle_password_show)
        self._add_win_password_show_button.grid(
            row=1, column=3, pady=self.PADDING, padx=self.PADDING)
        self._add_win_button = tk.Button(
            self._add_win, text='Add new entry', command=self._add_win_command)
        self._add_win_button.grid(
            row=2, columnspan=4, pady=self.PADDING, padx=self.PADDING)

    def _update_win_command(self, entry_id):
        def _():
            link = self._update_win_link_entry.get()
            password = self._update_win_password_entry.get()
            self._entries_storage.update_entry(
                entry_id, link=link, password=password)
            self._paint_entries()
            self._update_win.destroy()
        return _

    def _update_win_toggle_password_show(self):
        self._update_win_password_is_shown = not self._update_win_password_is_shown
        password_mode = '' if self._update_win_password_is_shown else '*'
        password_button_text = 'Hide' if self._update_win_password_is_shown else 'Show'
        self._update_win_password_show_button.configure(
            text=password_button_text)
        self._update_win_password_entry.configure(show=password_mode)

    def _ask_update_entry(self, shown_index, entry_id):
        def _():
            initial_entry = self._entries_storage.get_by_id(entry_id)
            self._update_win = tk.Toplevel(self)
            self._update_win.wm_resizable(width=False, height=False)
            self._update_win_head_label = tk.Label(
                self._update_win, text=f'Update entry #{shown_index}')
            self._update_win_head_label.grid(
                row=0, columnspan=4, pady=self.PADDING, padx=self.PADDING)
            self._update_win_link_label = tk.Label(
                self._update_win, text='Link')
            self._update_win_link_label.grid(
                row=1, column=0, pady=self.PADDING, padx=self.PADDING)
            self._update_win_link_entry = tk.Entry(self._update_win)
            self._update_win_link_entry.insert(0, initial_entry.get('link'))
            self._update_win_link_entry.grid(
                row=1, column=1, pady=self.PADDING, padx=self.PADDING)
            self._update_win_password_label = tk.Label(
                self._update_win, text='Password')
            self._update_win_password_label.grid(
                row=2, column=0, pady=self.PADDING, padx=self.PADDING)
            self._update_win_password_entry = tk.Entry(
                self._update_win, show='*')
            self._update_win_password_entry.insert(
                0, initial_entry.get('password'))
            self._update_win_password_entry.grid(
                row=2, column=1, pady=self.PADDING, padx=self.PADDING)
            self._update_win_password_is_shown = False
            self._update_win_password_show_button = tk.Button(
                self._update_win, text='Show')
            self._update_win_password_show_button.configure(
                command=self._update_win_toggle_password_show)
            self._update_win_password_show_button.grid(
                row=2, column=3, pady=self.PADDING, padx=self.PADDING)
            self._update_win_button = tk.Button(
                self._update_win, text='Update the entry', command=self._update_win_command(entry_id))
            self._update_win_button.grid(
                row=3, columnspan=4, pady=self.PADDING, padx=self.PADDING)
        return _


class EntriesStorage:
    SAVE_FILE_NAME = os.path.join(os.path.dirname(__file__), '.db.json')
    _entries = {}

    def __init__(self):
        self._load()

    def _load(self):
        if not os.path.isfile(self.SAVE_FILE_NAME):
            return
        with open(self.SAVE_FILE_NAME, 'r') as save_file:
            self._entries = json.load(save_file)

    def save(self):
        with open(self.SAVE_FILE_NAME, 'w') as save_file:
            json.dump(self._entries, save_file)

    def add_entry(self, link, password):
        self._entries[str(uuid.uuid4())] = {'link': link, 'password': password}

    def delete_entry(self, entry_id):
        self._entries.pop(entry_id)

    def update_entry(self, entry_id, **kwrags):
        for key, value in kwrags.items():
            self._entries[entry_id][key] = value

    def get_all(self):
        return self._entries

    def get_by_id(self, entry_id):
        return self._entries.get(entry_id)


if __name__ == '__main__':
    app = App()
    app.mainloop()
