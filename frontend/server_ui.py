import tkinter as tk
import rest_pb2


def build_server_dashboard(self):
    self.clear_window()
    self.build_header("Server Dashboard", "Fast order support for dine-in and takeout")

    frame = tk.Frame(self.root, bg=self.bg_color)
    frame.pack(fill="both", expand=True, padx=18, pady=18)

    tk.Label(
        frame,
        text="Welcome, " + self.user_id,
        font=("Arial", 19, "bold"),
        fg=self.text_dark,
        bg=self.bg_color
    ).pack(anchor="w", pady=(0, 4))

    tk.Label(
        frame,
        text="Use the menu to support customer ordering and service flow.",
        font=("Arial", 11),
        fg=self.text_muted,
        bg=self.bg_color
    ).pack(anchor="w", pady=(0, 12))

    button_frame = tk.Frame(frame, bg=self.bg_color)
    button_frame.pack(anchor="w", pady=(0, 10))

    self.neutral_button(button_frame, "Get Menu", self.server_get_menu).pack(side="left", padx=5)

    card = self.build_card(frame)

    tk.Label(
        card,
        text="Order Menu",
        font=("Arial", 14, "bold"),
        fg=self.text_dark,
        bg=self.card_color
    ).pack(anchor="w", padx=14, pady=(14, 0))

    tk.Label(
        card,
        text="Browse current menu options for dine-in and takeout order entry.",
        font=("Arial", 10),
        fg=self.text_muted,
        bg=self.card_color
    ).pack(anchor="w", padx=14, pady=(2, 4))

    table_wrap = tk.Frame(card, bg=self.card_color)
    table_wrap.pack(fill="both", expand=True, padx=14, pady=(4, 10))

    self.server_table = self.create_menu_table(table_wrap)

    self.server_status = tk.Label(
        frame,
        text="",
        fg=self.green,
        bg=self.bg_color,
        font=("Arial", 10, "bold")
    )
    self.server_status.pack(anchor="w", pady=10)


def server_get_menu(self):
    try:
        response = self.stub.get_menu(
            rest_pb2.MenuRequest(
                requestId=self.next_request_id(),
                userId=self.user_id,
                role=self.role
            )
        )

        if response.status != "success":
            self.server_status.config(text=response.message, fg="red")
            return

        for row in self.server_table.get_children():
            self.server_table.delete(row)

        for item in response.items:
            self.server_table.insert(
                "",
                "end",
                values=(item.itemId, item.name, item.category, f"${item.price:.2f}")
            )

        self.server_status.config(text="Menu loaded successfully.", fg=self.green)

    except Exception as e:
        self.server_status.config(text="Error loading menu.", fg="red")
        print("Server get menu error:", e)
