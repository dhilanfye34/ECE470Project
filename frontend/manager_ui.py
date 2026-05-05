import tkinter as tk
from tkinter import messagebox
import rest_pb2


def build_manager_dashboard(self):
    self.clear_window()
    self.build_header("Manager Dashboard", "Menu pricing, reporting, and restaurant oversight")

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
        text="Review the menu, adjust pricing, and track restaurant performance.",
        font=("Arial", 11),
        fg=self.text_muted,
        bg=self.bg_color
    ).pack(anchor="w", pady=(0, 12))

    button_frame = tk.Frame(frame, bg=self.bg_color)
    button_frame.pack(anchor="w", pady=(0, 10))

    self.neutral_button(button_frame, "Get Menu", self.manager_get_menu).pack(side="left", padx=5)
    self.primary_button(button_frame, "Update Price", self.manager_update_price_popup).pack(side="left", padx=5)
    self.secondary_button(button_frame, "View Reports", self.manager_view_reports).pack(side="left", padx=5)

    card = self.build_card(frame)

    tk.Label(
        card,
        text="Menu",
        font=("Arial", 14, "bold"),
        fg=self.text_dark,
        bg=self.card_color
    ).pack(anchor="w", padx=14, pady=(14, 0))

    tk.Label(
        card,
        text="Current menu items visible in The Hurricane Grill.",
        font=("Arial", 10),
        fg=self.text_muted,
        bg=self.card_color
    ).pack(anchor="w", padx=14, pady=(2, 4))

    table_wrap = tk.Frame(card, bg=self.card_color)
    table_wrap.pack(fill="both", expand=True, padx=14, pady=(4, 10))

    self.manager_table = self.create_menu_table(table_wrap)

    self.manager_status = tk.Label(
        frame,
        text="",
        fg=self.green,
        bg=self.bg_color,
        font=("Arial", 10, "bold")
    )
    self.manager_status.pack(anchor="w", pady=10)


def manager_get_menu(self):
    try:
        response = self.stub.get_menu(
            rest_pb2.MenuRequest(
                requestId=self.next_request_id(),
                userId=self.user_id,
                role=self.role
            )
        )

        if response.status != "success":
            self.manager_status.config(text=response.message, fg="red")
            return

        for row in self.manager_table.get_children():
            self.manager_table.delete(row)

        for item in response.items:
            self.manager_table.insert(
                "",
                "end",
                values=(item.itemId, item.name, item.category, f"${item.price:.2f}")
            )

        self.manager_status.config(text="Menu loaded successfully.", fg=self.green)

    except Exception as e:
        self.manager_status.config(text="Error loading menu.", fg="red")
        print("Manager get menu error:", e)


def manager_update_price_popup(self):
    selected = self.manager_table.selection()

    if not selected:
        self.manager_status.config(text="Select a menu item first.", fg="red")
        return

    item_values = self.manager_table.item(selected[0], "values")
    item_id = item_values[0]
    item_name = item_values[1]
    current_price = item_values[3]

    popup = tk.Toplevel(self.root)
    popup.title("Update Menu Price")
    popup.geometry("360x260")
    popup.configure(bg=self.bg_color)

    card = tk.Frame(
        popup,
        bg=self.card_color,
        highlightthickness=1,
        highlightbackground=self.border_color,
        padx=20,
        pady=20
    )
    card.pack(fill="both", expand=True, padx=18, pady=18)

    tk.Label(
        card,
        text="Update Price",
        font=("Arial", 18, "bold"),
        fg=self.green,
        bg=self.card_color
    ).pack(pady=(0, 10))

    tk.Label(card, text="Item: " + str(item_name), bg=self.card_color, fg=self.text_dark, font=("Arial", 11)).pack(pady=4)
    tk.Label(card, text="Current Price: " + str(current_price), bg=self.card_color, fg=self.text_muted, font=("Arial", 11)).pack(pady=4)
    tk.Label(card, text="New Price", bg=self.card_color, fg=self.text_dark, font=("Arial", 11, "bold")).pack(pady=(12, 5))

    price_entry = tk.Entry(card, font=("Arial", 11))
    price_entry.pack(pady=5, ipady=5)
    price_entry.focus_set()

    def submit_price():
        raw = price_entry.get().strip()

        try:
            new_price = float(raw)
        except ValueError:
            messagebox.showerror("Error", "Enter a valid number.")
            return

        try:
            response = self.stub.update_menu_price(
                rest_pb2.UpdateMenuPriceRequest(
                    requestId=self.next_request_id(),
                    userId=self.user_id,
                    role=self.role,
                    itemId=item_id,
                    newPrice=new_price
                )
            )

            if response.status == "success":
                self.manager_status.config(text="Price updated successfully.", fg=self.green)
                popup.destroy()
                self.manager_get_menu()
            else:
                messagebox.showerror("Error", response.message)

        except Exception as e:
            messagebox.showerror("Error", "Could not update price.")
            print("Update price error:", e)

    price_entry.bind("<Return>", lambda event: submit_price())

    tk.Button(
        card,
        text="Submit",
        command=submit_price,            
        bg=self.orange,
        fg=self.text_dark,
        activebackground=self.orange,            
        activeforeground=self.text_dark,
        relief="flat",
        bd=0,
        font=("Arial", 10, "bold"),
        padx=16,
        pady=7
    ).pack(pady=15)