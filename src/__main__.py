#! /usr/bin/env python3.8
# -*- coding: utf-8 -*-


import tkinter as tk
import os
import json


class App(tk.Tk):
    save_file = os.path.join(os.path.dirname(__file__), '.db.json')
    entries = []

    def __init__(self):
        super().__init__()
        self.wm_title("Links & Passwords")
        self.wm_minsize(400, 200)

        self.load()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1)

        self.paint_entries()

        self.command_frame = tk.Frame(self)
        self.command_frame.grid(row=1, column=0)

        self.command_frame.grid_columnconfigure(0, weight=1)
        self.command_frame.grid_columnconfigure(1, weight=1)
        self.command_frame.grid_rowconfigure(0, weight=1)

        self.add_button = tk.Button(
            self.command_frame, text='add', command=self.ask_add_entry)
        self.add_button.grid(row=0, column=1)

        self.save_button = tk.Button(
            self.command_frame, text='save', command=self.ask_save)
        self.save_button.grid(row=0, column=0)

    def paint_entries(self):
        if hasattr(self, 'entries_frame'):
            self.entries_frame.grid_remove()

        self.entries_frame = tk.Frame(self)
        self.entries_canvas = tk.Canvas(self.entries_frame)

#         self.entries_frame.grid_columnconfigure(0, weight=1)
#         self.entries_frame.grid_columnconfigure(1, weight=1)
#         self.entries_frame.grid_columnconfigure(2, weight=1)

        self.entries_scrollbar = tk.Scrollbar(
            self.entries_frame, orient='vertical', command=self.entries_canvas.yview)
        self.entries_scrollable_frame = tk.Frame(self.entries_canvas)

        self.entries_scrollable_frame.bind(
            '<Configure>',
            lambda _: self.entries_canvas.configure(
                scrollregion=self.entries_canvas.bbox('all')
            )
        )

        self.entries_canvas.create_window(
            (0, 0), window=self.entries_scrollable_frame, anchor='nw')
        self.entries_canvas.configure(
            yscrollcommand=self.entries_scrollbar.set)

        row_counter = 1
        for entry in self.entries:
            link_textbox = tk.Entry(self.entries_scrollable_frame)
            link_textbox.grid(row=row_counter, column=0)
            link_textbox.insert(0, entry.get('link') or '')
            tk.Label(self.entries_scrollable_frame, text=entry.get('password') or '').grid(
                row=row_counter, column=1)
            row_counter += 1

        self.entries_frame.grid(row=0, column=1)
        self.entries_canvas.grid(row=0, column=0, sticky='ns')
        self.entries_scrollbar.grid(row=0, column=2, sticky='ns')

    def load(self):
        if not os.path.exists(self.save_file):
            return
        with open(self.save_file, 'r') as save_file:
            self.entries = json.load(save_file)

    def save(self):
        with open(self.save_file, 'w') as save_file:
            json.dump(self.entries, save_file)

    def ask_save(self):
        def save_win_save():
            self.save()
            self.save_win.destroy()

        self.save_win = tk.Toplevel(self)
        self.save_win.wm_resizable(width=False, height=False)
        self.save_win_label = tk.Label(self.save_win, text='Save the changes?')
        self.save_win_label.grid(row=0, columnspan=2)
        self.save_win_button_save = tk.Button(
            self.save_win, text='Save', command=save_win_save)
        self.save_win_button_save.grid(row=1, column=0)
        self.save_win_button_cancel = tk.Button(
            self.save_win, text='Cancel', command=self.save_win.destroy)
        self.save_win_button_cancel.grid(row=1, column=1)

    def add_entry(self):
        link = self.add_win_link_entry.get()
        password = self.add_win_password_entry.get()
        self.entries.append({'link': link, 'password': password})
        self.add_win.destroy()
        self.paint_entries()

    def ask_add_entry(self):
        self.add_win = tk.Toplevel(self)
        self.add_win.wm_resizable(width=False, height=False)
        self.add_win_button = tk.Button(
            self.add_win, text='Add new entry', command=self.add_entry)
        self.add_win_link_label = tk.Label(self.add_win, text="Link")
        self.add_win_link_label.grid(row=0, column=0)
        self.add_win_link_entry = tk.Entry(self.add_win, bd=5)
        self.add_win_link_entry.grid(row=0, column=1)
        self.add_win_password_label = tk.Label(self.add_win, text="Password")
        self.add_win_password_label.grid(row=1, column=0)
        self.add_win_password_entry = tk.Entry(self.add_win, bd=5)
        self.add_win_password_entry.grid(row=1, column=1)
        self.add_win_button.grid(row=3, columnspan=2)


if __name__ == '__main__':
    app = App()
    app.mainloop()
