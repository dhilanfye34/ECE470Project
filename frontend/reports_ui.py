import tkinter as tk
from tkinter import ttk


def manager_view_reports(self):
    report_window = tk.Toplevel(self.root)
    report_window.title("The Hurricane Grill Reports")
    report_window.geometry("820x560")
    report_window.configure(bg=self.bg_color)

    tk.Label(
        report_window,
        text="The Hurricane Grill Reports",
        font=("Arial", 21, "bold"),
        fg=self.green,
        bg=self.bg_color
    ).pack(pady=(14, 6))

    tk.Label(
        report_window,
        text="Restaurant performance snapshots and ordering trends.",
        font=("Arial", 11),
        fg=self.text_muted,
        bg=self.bg_color
    ).pack()

    notebook = ttk.Notebook(report_window)
    notebook.pack(fill="both", expand=True, padx=16, pady=16)

    top_items_frame = tk.Frame(notebook, bg=self.card_color)
    category_sales_frame = tk.Frame(notebook, bg=self.card_color)
    peak_times_frame = tk.Frame(notebook, bg=self.card_color)

    notebook.add(top_items_frame, text="Top Selling Items")
    notebook.add(category_sales_frame, text="Sales by Category")
    notebook.add(peak_times_frame, text="Peak Order Times")

    self.create_report_table(
        top_items_frame,
        ("Item", "Quantity Sold", "Revenue"),
        [
            ("Grilled Chicken Sandwich", "20", "$299.80"),
            ("Hurricane Burger", "15", "$254.85"),
            ("Loaded Fries", "10", "$69.90")
        ]
    )

    self.create_report_table(
        category_sales_frame,
        ("Category", "Revenue"),
        [
            ("Mains", "$550.00"),
            ("Sides", "$120.00"),
            ("Drinks", "$85.00"),
            ("Desserts", "$60.00")
        ]
    )

    self.create_report_table(
        peak_times_frame,
        ("Hour", "Orders"),
        [
            ("12 PM", "14"),
            ("1 PM", "18"),
            ("6 PM", "22"),
            ("7 PM", "19")
        ]
    )
