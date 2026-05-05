import tkinter as tk
from tkinter import ttk


def clear_window(self):
    for widget in self.root.winfo_children():
        widget.destroy()


def next_request_id(self):
    self.request_id += 1
    return self.request_id


def build_card(self, parent):
    card = tk.Frame(
        parent,
        bg=self.card_color,
        highlightthickness=1,
        highlightbackground=self.border_color,
        bd=0
    )
    card.pack(fill="both", expand=True, padx=6, pady=6)
    return card


def build_header(self, title, subtitle):
    header = tk.Frame(self.root, bg=self.green, height=88)
    header.pack(fill="x")
    header.pack_propagate(False)

    left = tk.Frame(header, bg=self.green)
    left.pack(side="left", padx=22, pady=16)

    tk.Label(
        left,
        text=self.app_name,
        font=("Arial", 24, "bold"),
        fg="white",
        bg=self.green
    ).pack(anchor="w")

    tk.Label(
        left,
        text=subtitle,
        font=("Arial", 11),
        fg="#d9f0e4",
        bg=self.green
    ).pack(anchor="w")

    tk.Label(
        header,
        text=title,
        font=("Arial", 15, "bold"),
        fg="white",
        bg=self.green
    ).pack(side="left", padx=30)

    tk.Button(
        header,
        text="Logout",
        command=self.logout_user,
        bg=self.button_dark,
        fg=self.text_dark,
        activebackground=self.button_dark,
        activeforeground=self.text_dark,
        relief="flat",
        bd=0,
        font=("Arial", 10, "bold"),
        padx=14,
        pady=8
    ).pack(side="right", padx=22, pady=20)


def create_menu_table(self, parent):
    columns = ("Item ID", "Name", "Category", "Price", "Description", "Available")
    table = ttk.Treeview(parent, columns=columns, show="headings", height=12)

    widths = (90, 190, 150, 100, 300, 100)
    for col, width in zip(columns, widths):
        table.heading(col, text=col)
        table.column(col, width=width, anchor="center")

    table.pack(fill="both", expand=True, pady=10)
    return table


def create_orders_table(self, parent):
    columns = ("Order ID", "Type", "Status", "Table/Guest", "Customer", "Pickup Info", "Created", "Total")
    table = ttk.Treeview(parent, columns=columns, show="headings", height=12)

    widths = (95, 90, 110, 130, 140, 170, 160, 95)
    for col, width in zip(columns, widths):
        table.heading(col, text=col)
        table.column(col, width=width, anchor="center")

    table.pack(fill="both", expand=True, pady=10)
    return table


def create_report_table(self, parent, columns, data):
    table = ttk.Treeview(parent, columns=columns, show="headings", height=12)

    for col in columns:
        table.heading(col, text=col)
        table.column(col, width=200, anchor="center")

    for row in data:
        table.insert("", "end", values=row)

    table.pack(fill="both", expand=True, padx=10, pady=10)
    return table


def primary_button(self, parent, text, command):
    return tk.Button(
        parent,
        text=text,
        command=command,
        width=16,
        bg=self.orange,
        fg=self.text_dark,
        activebackground=self.orange,
        activeforeground=self.text_dark,
        relief="flat",
        bd=0,
        font=("Arial", 10, "bold"),
        pady=9
    )


def secondary_button(self, parent, text, command):
    return tk.Button(
        parent,
        text=text,
        command=command,
        width=16,
        bg=self.green,
        fg=self.text_dark,
        activebackground=self.green,
        activeforeground=self.text_dark,
        relief="flat",
        bd=0,
        font=("Arial", 10, "bold"),
        pady=9
    )


def neutral_button(self, parent, text, command):
    return tk.Button(
        parent,
        text=text,
        command=command,
        width=16,
        bg=self.cream,
        fg=self.text_dark,
        activebackground=self.cream,
        activeforeground=self.text_dark,
        relief="flat",
        bd=0,
        font=("Arial", 10, "bold"),
        pady=9
    )
