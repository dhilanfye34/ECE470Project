import tkinter as tk
from tkinter import ttk
import rest_pb2


def manager_view_reports(self):
    report_window = tk.Toplevel(self.root)
    report_window.title("The Hurricane Grill Reports")
    report_window.geometry("780x520")
    report_window.minsize(720, 480)
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

    status_label = tk.Label(
        report_window,
        text="",
        font=("Arial", 10, "bold"),
        fg=self.green,
        bg=self.bg_color
    )
    status_label.pack(pady=(8, 0))

    card = tk.Frame(
        report_window,
        bg=self.card_color,
        highlightthickness=1,
        highlightbackground=self.border_color,
        padx=14,
        pady=14
    )
    card.pack(fill="both", expand=True, padx=16, pady=16)

    columns = ("Metric", "Value")
    table = ttk.Treeview(card, columns=columns, show="headings", height=8)

    for col in columns:
        table.heading(col, text=col)
        table.column(col, width=280, anchor="center")

    table.pack(fill="both", expand=True, padx=10, pady=10)

    def load_report():
        try:
            response = self.stub.generate_report(
                rest_pb2.GenerateReportRequest(
                    requestId=self.next_request_id(),
                    userId=self.user_id,
                    role=self.role
                )
            )

            for row in table.get_children():
                table.delete(row)

            if response.status != "success":
                status_label.config(text=response.message, fg="red")
                return

            rows = [
                ("Total Orders", str(response.totalOrders)),
                ("Total Revenue", "$" + format(response.totalRevenue, ".2f")),
                ("Received Orders", str(response.receivedCount)),
                ("Ready Orders", str(response.readyCount)),
                ("Completed Orders", str(response.completedCount)),
                ("Picked Up Orders", str(response.pickedUpCount)),
            ]

            for row in rows:
                table.insert("", "end", values=row)

            status_label.config(text="Report generated from backend data.", fg=self.green)

        except Exception as e:
            status_label.config(text="Error generating report.", fg="red")
            print("Generate report error:", e)

    tk.Button(
        report_window,
        text="Refresh Report",
        command=load_report,
        bg=self.orange,
        fg=self.text_dark,
        activebackground=self.orange,
        activeforeground=self.text_dark,
        relief="flat",
        bd=0,
        font=("Arial", 10, "bold"),
        padx=16,
        pady=8
    ).pack(pady=(0, 16))

    load_report()
