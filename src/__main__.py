#! /usr/bin/env python3.8
# -*- coding: utf-8 -*-


import tkinter as tk
from tkinter import messagebox
import os
import json
import pyperclip


class App(tk.Tk):
    PADDING = 10
    WINDOW_WIDTH = 600
    WINDOW_HEIGHT = 400
    SAVE_FILE_NAME = os.path.join(os.path.dirname(__file__), '.db.json')
    _entries = []

    def _app_exit(self):
        answer = messagebox.askyesnocancel(
            'Quit', 'Quitting. Save the changes?')
        if answer is None:
            return
        if answer == True:
            self._save()
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

        self._load()
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

        for index in range(len(self._entries)):
            shown_index = index + 1
            entry_id = tk.Label(
                self._entries_scrollable_frame, text=shown_index)
            entry_id.grid(row=index, column=0)
            entry_link = tk.Entry(self._entries_scrollable_frame, bd=0)
            entry_link.insert(0, self._entries[index].get('link') or '')
            entry_link.configure(state='readonly')
            entry_link.grid(row=index, column=1)
            entry_password = tk.Button(
                self._entries_scrollable_frame, text='Copy password', command=self._copy_entry(index))
            entry_password.grid(row=index, column=2)
            entry_delete = tk.Button(
                self._entries_scrollable_frame, text='Delete', command=self._ask_delete_entry(shown_index))
            entry_delete.grid(row=index, column=3)

    def _load(self):
        if not os.path.isfile(self.SAVE_FILE_NAME):
            self._entries = []
            return
        with open(self.SAVE_FILE_NAME, 'r') as save_file:
            self._entries = json.load(save_file)

    def _save(self):
        with open(self.SAVE_FILE_NAME, 'w') as save_file:
            json.dump(self._entries, save_file)

    def _delete_entry(self, entry_index):
        del self._entries[entry_index]

    def _copy_entry(self, entry_index):
        def _():
            pyperclip.copy(self._entries[entry_index].get('password') or '')
        return _

    def _ask_save(self):
        answer = messagebox.askquestion('Save', 'Save the changes?')
        if answer == 'yes':
            self._save()

    def _ask_delete_entry(self, shown_id):
        def _():
            answer = messagebox.askquestion(
                'Delete', f'Delete entry #{shown_id}?')
            if answer == 'no':
                return
            self._delete_entry(shown_id - 1)
            self._paint_entries()
        return _

    def _add_entry(self, link, password):
        self._entries.append({'link': link, 'password': password})

    def _add_win_command(self):
        link = self._add_win_link_entry.get()
        password = self._add_win_password_entry.get()
        self._add_entry(link, password)
        self._paint_entries()
        self._add_win.destroy()

    def _toggle_password_show(self):
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
            command=self._toggle_password_show)
        self._add_win_password_show_button.grid(
            row=1, column=3, pady=self.PADDING, padx=self.PADDING)
        self._add_win_button = tk.Button(
            self._add_win, text='Add new entry', command=self._add_win_command)
        self._add_win_button.grid(
            row=2, columnspan=4, pady=self.PADDING, padx=self.PADDING)


if __name__ == '__main__':
    app = App()
    app.mainloop()
