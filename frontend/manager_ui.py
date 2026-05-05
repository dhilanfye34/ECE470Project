import tkinter as tk
from tkinter import messagebox, ttk
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
    self.secondary_button(button_frame, "Add Item", self.manager_add_item_popup).pack(side="left", padx=5)
    self.secondary_button(button_frame, "Edit Item", self.manager_edit_item_popup).pack(side="left", padx=5)
    self.neutral_button(button_frame, "Remove Item", self.manager_remove_item).pack(side="left", padx=5)
    self.primary_button(button_frame, "Update Price", self.manager_update_price_popup).pack(side="left", padx=5)
    self.secondary_button(button_frame, "View Reports", self.manager_view_reports).pack(side="left", padx=5)
    self.neutral_button(button_frame, "Server View", self.manager_switch_to_server_view).pack(side="left", padx=5)

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

    self.manager_table = create_manager_menu_table(table_wrap)

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
                values=(
                    item.itemId,
                    item.name,
                    item.category,
                    f"${item.price:.2f}",
                    item.description,
                    "Yes" if item.availability else "No"
                )
            )

        self.manager_status.config(text="Menu loaded successfully.", fg=self.green)

    except Exception as e:
        self.manager_status.config(text="Error loading menu.", fg="red")
        print("Manager get menu error:", e)


def manager_switch_to_server_view(self):
    self.manager_user_id = self.user_id
    self.manager_server_mode = True
    self.user_id = "s1"
    self.role = "server"
    self.build_server_dashboard()


def manager_return_from_server_view(self):
    if self.manager_user_id != "":
        self.user_id = self.manager_user_id

    self.role = "manager"
    self.manager_server_mode = False
    self.build_manager_dashboard()


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
    popup.geometry("420x320")
    popup.minsize(400, 300)
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


def create_manager_menu_table(parent):
    columns = ("Item ID", "Name", "Category", "Price", "Description", "Available")
    table = ttk.Treeview(parent, columns=columns, show="headings", height=12)

    widths = (90, 190, 150, 100, 300, 100)
    for col, width in zip(columns, widths):
        table.heading(col, text=col)
        table.column(col, width=width, anchor="center")

    table.pack(fill="both", expand=True, pady=10)
    return table


def _selected_manager_item(self):
    selected = self.manager_table.selection()

    if not selected:
        self.manager_status.config(text="Select a menu item first.", fg="red")
        return None

    return self.manager_table.item(selected[0], "values")


def _build_menu_item_from_fields(item_id, name, category, price_raw, description, availability):
    price = float(price_raw)
    return rest_pb2.MenuItem(
        itemId=item_id,
        name=name,
        category=category,
        price=price,
        description=description,
        availability=availability
    )


def _menu_item_form_popup(self, title, initial_values, submit_label, submit_callback):
    popup = tk.Toplevel(self.root)
    popup.title(title)
    popup.geometry("540x650")
    popup.minsize(520, 620)
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
        text=title,
        font=("Arial", 18, "bold"),
        fg=self.green,
        bg=self.card_color
    ).pack(pady=(0, 12))

    fields = {}

    for field_key, label_text in (
        ("itemId", "Item ID"),
        ("name", "Name"),
        ("category", "Category"),
        ("price", "Price"),
    ):
        tk.Label(card, text=label_text, bg=self.card_color, fg=self.text_dark, font=("Arial", 11, "bold")).pack(anchor="w")
        entry = tk.Entry(card, font=("Arial", 11))
        entry.pack(fill="x", pady=(5, 10), ipady=5)
        entry.insert(0, initial_values.get(field_key, ""))
        if field_key == "itemId" and initial_values.get("lockItemId", False):
            entry.config(state="disabled")
        fields[field_key] = entry

    tk.Label(card, text="Description", bg=self.card_color, fg=self.text_dark, font=("Arial", 11, "bold")).pack(anchor="w")
    description_text = tk.Text(card, height=4, font=("Arial", 10), relief="solid", bd=1)
    description_text.pack(fill="x", pady=(5, 10))
    description_text.insert("1.0", initial_values.get("description", ""))

    available_var = tk.BooleanVar(value=initial_values.get("availability", True))
    tk.Checkbutton(
        card,
        text="Available",
        variable=available_var,
        bg=self.card_color,
        fg=self.text_dark,
        activebackground=self.card_color,
        font=("Arial", 10, "bold"),
        anchor="w"
    ).pack(anchor="w", pady=(0, 8))

    status_label = tk.Label(card, text="", bg=self.card_color, fg="red", font=("Arial", 10))
    status_label.pack(pady=(0, 8))

    def submit():
        try:
            item = _build_menu_item_from_fields(
                fields["itemId"].get().strip(),
                fields["name"].get().strip(),
                fields["category"].get().strip(),
                fields["price"].get().strip(),
                description_text.get("1.0", "end").strip(),
                available_var.get()
            )
        except ValueError:
            status_label.config(text="Price must be a valid number.")
            return

        submit_callback(item, popup, status_label)

    tk.Button(
        card,
        text=submit_label,
        command=submit,
        bg=self.orange,
        fg=self.text_dark,
        activebackground=self.orange,
        activeforeground=self.text_dark,
        relief="flat",
        bd=0,
        font=("Arial", 10, "bold"),
        padx=16,
        pady=8
    ).pack(pady=4)

    fields["itemId"].focus_set()
    popup.bind("<Command-Return>", lambda event: submit())


def manager_add_item_popup(self):
    def submit_item(item, popup, status_label):
        try:
            response = self.stub.add_menu_item(
                rest_pb2.AddMenuItemRequest(
                    requestId=self.next_request_id(),
                    userId=self.user_id,
                    role=self.role,
                    item=item
                )
            )

            if response.status == "success":
                self.manager_status.config(text="Menu item added.", fg=self.green)
                popup.destroy()
                self.manager_get_menu()
            else:
                status_label.config(text=response.message, fg="red")

        except Exception as e:
            status_label.config(text="Could not add menu item.", fg="red")
            print("Add menu item error:", e)

    _menu_item_form_popup(
        self,
        "Add Menu Item",
        {"availability": True},
        "Add Item",
        submit_item
    )


def manager_edit_item_popup(self):
    item_values = _selected_manager_item(self)
    if item_values is None:
        return

    raw_price = str(item_values[3]).replace("$", "")
    initial_values = {
        "itemId": item_values[0],
        "name": item_values[1],
        "category": item_values[2],
        "price": raw_price,
        "description": item_values[4] if len(item_values) > 4 else "",
        "availability": len(item_values) < 6 or item_values[5] == "Yes",
        "lockItemId": True,
    }

    def submit_item(item, popup, status_label):
        try:
            response = self.stub.update_menu_item(
                rest_pb2.UpdateMenuItemRequest(
                    requestId=self.next_request_id(),
                    userId=self.user_id,
                    role=self.role,
                    item=item
                )
            )

            if response.status == "success":
                self.manager_status.config(text="Menu item updated.", fg=self.green)
                popup.destroy()
                self.manager_get_menu()
            else:
                status_label.config(text=response.message, fg="red")

        except Exception as e:
            status_label.config(text="Could not update menu item.", fg="red")
            print("Update menu item error:", e)

    _menu_item_form_popup(self, "Edit Menu Item", initial_values, "Save Item", submit_item)


def manager_remove_item(self):
    item_values = _selected_manager_item(self)
    if item_values is None:
        return

    item_id = item_values[0]
    item_name = item_values[1]

    confirmed = messagebox.askyesno(
        "Remove Menu Item",
        "Remove " + str(item_name) + " (" + str(item_id) + ")?"
    )

    if not confirmed:
        return

    try:
        response = self.stub.remove_menu_item(
            rest_pb2.RemoveMenuItemRequest(
                requestId=self.next_request_id(),
                userId=self.user_id,
                role=self.role,
                itemId=item_id
            )
        )

        if response.status == "success":
            self.manager_status.config(text="Menu item removed.", fg=self.green)
            self.manager_get_menu()
        else:
            self.manager_status.config(text=response.message, fg="red")

    except Exception as e:
        self.manager_status.config(text="Could not remove menu item.", fg="red")
        print("Remove menu item error:", e)
