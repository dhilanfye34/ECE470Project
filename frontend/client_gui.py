import tkinter as tk
import grpc
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "gRPC")))

import rest_pb2
import rest_pb2_grpc

from frontend.theme import apply_theme, setup_table_style
from frontend.shared_ui import (
    clear_window,
    next_request_id,
    build_card,
    build_header,
    create_menu_table,
    create_orders_table,
    create_report_table,
    primary_button,
    secondary_button,
    neutral_button,
)
from frontend.manager_ui import (
    build_manager_dashboard,
    manager_get_menu,
    manager_update_price_popup,
)
from frontend.server_ui import (
    build_server_dashboard,
    server_get_menu,
)
from frontend.chef_ui import (
    build_chef_dashboard,
    chef_list_orders,
)
from frontend.reports_ui import manager_view_reports


class RestaurantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("The Hurricane Grill")
        self.root.geometry("1100x760")
        self.root.minsize(1000, 680)

        self.user_id = ""
        self.role = ""
        self.request_id = 1

        apply_theme(self)

        self.channel = grpc.insecure_channel("localhost:50000")
        self.stub = rest_pb2_grpc.RestaurantServiceStub(self.channel)

        setup_table_style(self)
        self.build_login_screen()

    def build_login_screen(self):
        self.clear_window()

        outer = tk.Frame(self.root, bg=self.bg_color)
        outer.pack(fill="both", expand=True)

        hero = tk.Frame(outer, bg=self.green, height=170)
        hero.pack(fill="x")
        hero.pack_propagate(False)

        tk.Label(
            hero,
            text=self.app_name,
            font=("Arial", 30, "bold"),
            fg="white",
            bg=self.green
        ).pack(pady=(32, 5))

        tk.Label(
            hero,
            text="Fresh food. Fast service. Miami-inspired flavor.",
            font=("Arial", 13),
            fg="#d9f0e4",
            bg=self.green
        ).pack()

        login_card = tk.Frame(
            outer,
            bg=self.card_color,
            highlightthickness=1,
            highlightbackground=self.border_color,
            padx=35,
            pady=30
        )
        login_card.pack(pady=50)

        tk.Label(
            login_card,
            text="Staff Login",
            font=("Arial", 22, "bold"),
            fg=self.text_dark,
            bg=self.card_color
        ).pack(pady=(0, 10))

        tk.Label(
            login_card,
            text="Log in as a manager, server, or chef.",
            font=("Arial", 11),
            fg=self.text_muted,
            bg=self.card_color
        ).pack(pady=(0, 20))

        tk.Label(
            login_card,
            text="User ID",
            font=("Arial", 11, "bold"),
            fg=self.text_dark,
            bg=self.card_color
        ).pack(anchor="w")

        self.user_entry = tk.Entry(login_card, width=32, font=("Arial", 11), relief="solid", bd=1)
        self.user_entry.pack(pady=(6, 14), ipady=6)

        tk.Label(
            login_card,
            text="Role",
            font=("Arial", 11, "bold"),
            fg=self.text_dark,
            bg=self.card_color
        ).pack(anchor="w")

        self.role_var = tk.StringVar(value="manager")
        role_box = tk.OptionMenu(login_card, self.role_var, "manager", "server", "chef")
        role_box.config(
            font=("Arial", 11),
            bg="white",
            fg=self.text_dark,
            activebackground=self.cream,
            activeforeground=self.text_dark,
            highlightthickness=0,
            relief="flat",
            bd=0,
            width=28
        )

        role_box["menu"].config(
            bg="white",
            fg=self.text_dark,
            activebackground=self.soft_green,
            activeforeground=self.text_dark,
            font=("Arial", 11)
        )

        role_box.pack(pady=(6, 18), ipady=6)

        tk.Button(
            login_card,
            text="Login",
            width=22,
            command=self.login_user,
            bg=self.orange,
            fg=self.text_dark,
            activebackground=self.orange,
            activeforeground=self.text_dark,
            relief="flat",
            bd=0,
            font=("Arial", 11, "bold"),
            pady=8
        ).pack()

        self.login_status = tk.Label(
            login_card,
            text="",
            fg="red",
            bg=self.card_color,
            font=("Arial", 10)
        )
        self.login_status.pack(pady=(14, 0))

    def login_user(self):
        user_id = self.user_entry.get().strip()
        role = self.role_var.get().strip()

        if user_id == "":
            self.login_status.config(text="Enter a user ID.")
            return

        try:
            response = self.stub.login(
                rest_pb2.LoginRequest(
                    requestId=self.next_request_id(),
                    userId=user_id,
                    role=role
                )
            )

            if response.status == "success":
                self.user_id = user_id
                self.role = role

                if role == "manager":
                    self.build_manager_dashboard()
                elif role == "server":
                    self.build_server_dashboard()
                elif role == "chef":
                    self.build_chef_dashboard()
            else:
                self.login_status.config(text=response.message)

        except Exception as e:
            self.login_status.config(text="Could not connect to server.")
            print("Login error:", e)

    def logout_user(self):
        try:
            self.stub.logout(
                rest_pb2.LogoutRequest(
                    requestId=self.next_request_id(),
                    userId=self.user_id,
                    role=self.role
                )
            )
        except Exception as e:
            print("Logout error:", e)

        self.user_id = ""
        self.role = ""
        self.build_login_screen()


RestaurantGUI.clear_window = clear_window
RestaurantGUI.next_request_id = next_request_id
RestaurantGUI.build_card = build_card
RestaurantGUI.build_header = build_header
RestaurantGUI.create_menu_table = create_menu_table
RestaurantGUI.create_orders_table = create_orders_table
RestaurantGUI.create_report_table = create_report_table
RestaurantGUI.primary_button = primary_button
RestaurantGUI.secondary_button = secondary_button
RestaurantGUI.neutral_button = neutral_button

RestaurantGUI.build_manager_dashboard = build_manager_dashboard
RestaurantGUI.manager_get_menu = manager_get_menu
RestaurantGUI.manager_update_price_popup = manager_update_price_popup
RestaurantGUI.manager_view_reports = manager_view_reports

RestaurantGUI.build_server_dashboard = build_server_dashboard
RestaurantGUI.server_get_menu = server_get_menu

RestaurantGUI.build_chef_dashboard = build_chef_dashboard
RestaurantGUI.chef_list_orders = chef_list_orders


if __name__ == "__main__":
    root = tk.Tk()
    app = RestaurantGUI(root)
    root.mainloop()
