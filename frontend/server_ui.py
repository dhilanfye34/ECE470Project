import tkinter as tk
from tkinter import messagebox
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
    self.primary_button(button_frame, "Place Takeout", self.server_place_takeout_popup).pack(side="left", padx=5)
    self.secondary_button(button_frame, "List Orders", self.server_list_orders).pack(side="left", padx=5)
    self.secondary_button(button_frame, "Place Dine-In", self.server_place_dinein_popup).pack(side="left", padx=5)
    self.neutral_button(button_frame, "Order Status", self.server_status_lookup_popup).pack(side="left", padx=5)
    self.secondary_button(button_frame, "Update Status", self.server_update_status_popup).pack(side="left", padx=5)
   
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
                values=(
                    item.itemId,
                    item.name,
                    item.category,
                    f"${item.price:.2f}",
                    item.description,
                    "Yes" if item.availability else "No"
                )
            )

        self.server_status.config(text="Menu loaded successfully.", fg=self.green)

    except Exception as e:
        self.server_status.config(text="Error loading menu.", fg="red")
        print("Server get menu error:", e)


def server_place_takeout_popup(self):
    popup = tk.Toplevel(self.root)
    popup.title("Place Takeout Order")
    popup.geometry("540x760")
    popup.minsize(520, 720)
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
        text="Place Takeout Order",
        font=("Arial", 18, "bold"),
        fg=self.green,
        bg=self.card_color
    ).pack(pady=(0, 10))

    tk.Label(
        card,
        text="Add multiple menu items before submitting the order.",
        bg=self.card_color,
        fg=self.text_muted,
        font=("Arial", 10)
    ).pack(pady=(0, 12))

    tk.Label(card, text="Guest Name", bg=self.card_color, fg=self.text_dark, font=("Arial", 11, "bold")).pack(anchor="w")
    guest_entry = tk.Entry(card, font=("Arial", 11))
    guest_entry.pack(fill="x", pady=(5, 12), ipady=5)

    tk.Label(card, text="Item ID", bg=self.card_color, fg=self.text_dark, font=("Arial", 11, "bold")).pack(anchor="w")
    item_entry = tk.Entry(card, font=("Arial", 11))
    item_entry.pack(fill="x", pady=(5, 12), ipady=5)

    tk.Label(card, text="Quantity", bg=self.card_color, fg=self.text_dark, font=("Arial", 11, "bold")).pack(anchor="w")
    qty_entry = tk.Entry(card, font=("Arial", 11))
    qty_entry.pack(fill="x", pady=(5, 12), ipady=5)

    status_label = tk.Label(card, text="", bg=self.card_color, fg="red", font=("Arial", 10))
    status_label.pack(pady=(0, 8))

    tk.Label(card, text="Order Items", bg=self.card_color, fg=self.text_dark, font=("Arial", 11, "bold")).pack(anchor="w")

    cart_listbox = tk.Listbox(card, height=6, font=("Arial", 10))
    cart_listbox.pack(fill="both", expand=True, pady=(5, 10))

    order_items = []

    def add_item():
        item_id = item_entry.get().strip()
        qty_raw = qty_entry.get().strip()

        if item_id == "":
            status_label.config(text="Enter an item ID.")
            return

        try:
            quantity = int(qty_raw)
        except ValueError:
            status_label.config(text="Quantity must be a number.")
            return

        if quantity < 1:
            status_label.config(text="Quantity must be at least 1.")
            return

        total_qty = quantity
        for existing_item in order_items:
            total_qty += existing_item.quantity

        if total_qty > 10:
            status_label.config(text="Takeout orders can have at most 10 total items.")
            return

        line_item = rest_pb2.OrderLineItem(
            itemId=item_id,
            quantity=quantity
        )

        order_items.append(line_item)
        cart_listbox.insert(tk.END, "Item ID: " + item_id + " | Quantity: " + str(quantity))

        item_entry.delete(0, tk.END)
        qty_entry.delete(0, tk.END)
        item_entry.focus_set()
        status_label.config(text="Item added.", fg=self.green)

    def submit_order():
        guest_name = guest_entry.get().strip()

        if guest_name == "":
            status_label.config(text="Enter a guest name.", fg="red")
            return

        if len(order_items) == 0:
            status_label.config(text="Add at least one item.", fg="red")
            return

        try:
            response = self.stub.place_takeout_order(
                rest_pb2.TakeoutOrderRequest(
                    requestId=self.next_request_id(),
                    userId=self.user_id,
                    role=self.role,
                    guestName=guest_name,
                    items=order_items
                )
            )

            if response.status == "success":
                messagebox.showinfo(
                    "Order Placed",
                    "Order ID: " + response.orderId + "\nTotal: $" + format(response.total, ".2f")
                )
                self.server_status.config(text="Takeout order placed successfully.", fg=self.green)
                popup.destroy()
            else:
                status_label.config(text=response.message, fg="red")

        except Exception as e:
            status_label.config(text="Error placing order.", fg="red")
            print("Takeout order error:", e)

    def remove_selected_item():
        selected = cart_listbox.curselection()

        if not selected:
            status_label.config(text="Select an item to remove.", fg="red")
            return

        index = selected[0]
        cart_listbox.delete(index)
        del order_items[index]
        status_label.config(text="Item removed.", fg=self.green)

    button_frame = tk.Frame(card, bg=self.card_color)
    button_frame.pack(pady=8)

    tk.Button(
        button_frame,
        text="Add Item",
        command=add_item,
        bg=self.green,
        fg=self.text_dark,
        activebackground=self.green,
        activeforeground=self.text_dark,
        relief="flat",
        bd=0,
        font=("Arial", 10, "bold"),
        padx=14,
        pady=7
    ).pack(side="left", padx=5)

    tk.Button(
        button_frame,
        text="Remove Item",
        command=remove_selected_item,
        bg=self.cream,
        fg=self.text_dark,
        activebackground=self.cream,
        activeforeground=self.text_dark,
        relief="flat",
        bd=0,
        font=("Arial", 10, "bold"),
        padx=14,
        pady=7
    ).pack(side="left", padx=5)

    tk.Button(
        card,
        text="Submit Order",
        command=submit_order,
        bg=self.orange,
        fg=self.text_dark,
        activebackground=self.orange,
        activeforeground=self.text_dark,
        relief="flat",
        bd=0,
        font=("Arial", 10, "bold"),
        padx=16,
        pady=8
    ).pack(pady=8)

    def handle_enter(event):
        current = popup.focus_get()

        if current == item_entry:
            qty_entry.focus_set()
        elif current == qty_entry:
            add_item()
        else:
            submit_order()

    guest_entry.focus_set()

    guest_entry.bind("<Return>", handle_enter)
    item_entry.bind("<Return>", handle_enter)
    qty_entry.bind("<Return>", handle_enter)
    cart_listbox.bind("<Return>", handle_enter)

    popup.bind("<Command-Return>", lambda event: submit_order())


def server_list_orders(self):
    try:
        response = self.stub.list_orders(
            rest_pb2.ListOrdersRequest(
                requestId=self.next_request_id(),
                userId=self.user_id,
                role=self.role
            )
        )

        if response.status != "success":
            self.server_status.config(text=response.message, fg="red")
            return

        orders_window = tk.Toplevel(self.root)
        orders_window.title("Server Orders")
        orders_window.geometry("1120x560")
        orders_window.configure(bg=self.bg_color)

        tk.Label(
            orders_window,
            text="Current Orders",
            font=("Arial", 20, "bold"),
            fg=self.green,
            bg=self.bg_color
        ).pack(pady=(15, 5))

        tk.Label(
            orders_window,
            text="Orders currently stored in The Hurricane Grill system.",
            font=("Arial", 11),
            fg=self.text_muted,
            bg=self.bg_color
        ).pack()

        card = tk.Frame(
            orders_window,
            bg=self.card_color,
            highlightthickness=1,
            highlightbackground=self.border_color,
            padx=14,
            pady=14
        )
        card.pack(fill="both", expand=True, padx=18, pady=18)

        table = self.create_orders_table(card)

        status_label = tk.Label(card, text="", bg=self.card_color, fg=self.green, font=("Arial", 10, "bold"))
        status_label.pack(anchor="w", pady=(0, 8))

        actions = tk.Frame(card, bg=self.card_color)
        actions.pack(anchor="w", pady=(0, 8))

        def selected_order_id():
            selected = table.selection()

            if not selected:
                status_label.config(text="Select an order first.", fg="red")
                return ""

            return table.item(selected[0], "values")[0]

        def update_selected_status(status_code):
            order_id = selected_order_id()

            if order_id == "":
                return

            try:
                update_response = self.stub.update_order_status(
                    rest_pb2.UpdateOrderStatusRequest(
                        requestId=self.next_request_id(),
                        userId=self.user_id,
                        role=self.role,
                        orderId=order_id,
                        newStatus=status_code
                    )
                )

                if update_response.status == "success":
                    selected = table.selection()[0]
                    values = list(table.item(selected, "values"))
                    values[2] = update_response.currentStatus
                    table.item(selected, values=values)
                    status_label.config(
                        text="Updated " + order_id + " from " + update_response.previousStatus + " to " + update_response.currentStatus + ".",
                        fg=self.green
                    )
                    self.server_status.config(text="Order status updated.", fg=self.green)
                else:
                    status_label.config(text=update_response.message, fg="red")

            except Exception as e:
                status_label.config(text="Error updating order status.", fg="red")
                print("Server selected status update error:", e)

        tk.Button(actions, text="Ready", command=lambda: update_selected_status(rest_pb2.READY), bg=self.green, fg=self.text_dark, activebackground=self.green, activeforeground=self.text_dark, relief="flat", bd=0, font=("Arial", 10, "bold"), padx=14, pady=7).pack(side="left", padx=5)
        tk.Button(actions, text="Completed", command=lambda: update_selected_status(rest_pb2.COMPLETED), bg=self.orange, fg=self.text_dark, activebackground=self.orange, activeforeground=self.text_dark, relief="flat", bd=0, font=("Arial", 10, "bold"), padx=14, pady=7).pack(side="left", padx=5)
        tk.Button(actions, text="Picked Up", command=lambda: update_selected_status(rest_pb2.PICKED_UP), bg=self.cream, fg=self.text_dark, activebackground=self.cream, activeforeground=self.text_dark, relief="flat", bd=0, font=("Arial", 10, "bold"), padx=14, pady=7).pack(side="left", padx=5)

        for order in response.orders:
            extra = f"Table {order.tableNumber}" if order.orderType == "dine-in" else order.guestName
            table.insert(
                "",
                "end",
                values=(
                    order.orderId,
                    order.orderType,
                    order.status,
                    extra,
                    order.customerName,
                    order.pickupInfo,
                    order.createdTime,
                    f"${order.total:.2f}"
                )
            )

        self.server_status.config(text="Orders loaded successfully.", fg=self.green)

    except Exception as e:
        self.server_status.config(text="Error loading orders.", fg="red")
        print("Server list orders error:", e)


def _status_display(response):
    details = [
        "Order ID: " + response.orderId,
        "Status: " + response.currentStatus,
    ]

    if response.orderType != "":
        details.append("Type: " + response.orderType)

    if response.createdTime != "":
        details.append("Created: " + response.createdTime)

    return "\n".join(details)


def server_status_lookup_popup(self):
    popup = tk.Toplevel(self.root)
    popup.title("Order Status")
    popup.geometry("440x330")
    popup.minsize(420, 310)
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
        text="Order Status",
        font=("Arial", 18, "bold"),
        fg=self.green,
        bg=self.card_color
    ).pack(pady=(0, 12))

    tk.Label(card, text="Order ID", bg=self.card_color, fg=self.text_dark, font=("Arial", 11, "bold")).pack(anchor="w")
    order_entry = tk.Entry(card, font=("Arial", 11))
    order_entry.pack(fill="x", pady=(5, 12), ipady=5)

    result_label = tk.Label(card, text="", bg=self.card_color, fg=self.text_dark, font=("Arial", 10), justify="left")
    result_label.pack(fill="x", pady=(0, 12))

    def lookup_status():
        order_id = order_entry.get().strip()

        if order_id == "":
            result_label.config(text="Enter an order ID.", fg="red")
            return

        try:
            response = self.stub.get_order_status(
                rest_pb2.GetOrderStatusRequest(
                    requestId=self.next_request_id(),
                    userId=self.user_id,
                    role=self.role,
                    orderId=order_id
                )
            )

            if response.status == "success":
                result_label.config(text=_status_display(response), fg=self.text_dark)
                self.server_status.config(text="Order status retrieved.", fg=self.green)
            else:
                result_label.config(text=response.message, fg="red")

        except Exception as e:
            result_label.config(text="Error checking order status.", fg="red")
            print("Server status lookup error:", e)

    tk.Button(
        card,
        text="Lookup",
        command=lookup_status,
        bg=self.orange,
        fg=self.text_dark,
        activebackground=self.orange,
        activeforeground=self.text_dark,
        relief="flat",
        bd=0,
        font=("Arial", 10, "bold"),
        padx=16,
        pady=8
    ).pack()

    order_entry.focus_set()
    order_entry.bind("<Return>", lambda event: lookup_status())


def _update_order_status(self, order_id, status_code, status_label):
    try:
        response = self.stub.update_order_status(
            rest_pb2.UpdateOrderStatusRequest(
                requestId=self.next_request_id(),
                userId=self.user_id,
                role=self.role,
                orderId=order_id,
                newStatus=status_code
            )
        )

        if response.status == "success":
            status_label.config(
                text="Updated from " + response.previousStatus + " to " + response.currentStatus + ".",
                fg=self.green
            )
            if self.role == "server" and hasattr(self, "server_status"):
                self.server_status.config(text="Order status updated.", fg=self.green)
            if self.role == "chef" and hasattr(self, "chef_status"):
                self.chef_status.config(text="Order status updated.", fg=self.green)
                self.chef_list_orders()
        else:
            status_label.config(text=response.message, fg="red")

    except Exception as e:
        status_label.config(text="Error updating order status.", fg="red")
        print("Update order status error:", e)


def server_update_status_popup(self):
    popup = tk.Toplevel(self.root)
    popup.title("Update Order Status")
    popup.geometry("540x360")
    popup.minsize(520, 340)
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
        text="Update Order Status",
        font=("Arial", 18, "bold"),
        fg=self.green,
        bg=self.card_color
    ).pack(pady=(0, 12))

    tk.Label(card, text="Order ID", bg=self.card_color, fg=self.text_dark, font=("Arial", 11, "bold")).pack(anchor="w")
    order_entry = tk.Entry(card, font=("Arial", 11))
    order_entry.pack(fill="x", pady=(5, 12), ipady=5)

    status_label = tk.Label(card, text="", bg=self.card_color, fg="red", font=("Arial", 10))
    status_label.pack(pady=(0, 10))

    def update_to(status_code):
        order_id = order_entry.get().strip()

        if order_id == "":
            status_label.config(text="Enter an order ID.", fg="red")
            return

        _update_order_status(self, order_id, status_code, status_label)

    buttons = tk.Frame(card, bg=self.card_color)
    buttons.pack(pady=8)

    tk.Button(buttons, text="Ready", command=lambda: update_to(rest_pb2.READY), bg=self.green, fg=self.text_dark, activebackground=self.green, activeforeground=self.text_dark, relief="flat", bd=0, font=("Arial", 10, "bold"), padx=14, pady=8).pack(side="left", padx=5)
    tk.Button(buttons, text="Completed", command=lambda: update_to(rest_pb2.COMPLETED), bg=self.orange, fg=self.text_dark, activebackground=self.orange, activeforeground=self.text_dark, relief="flat", bd=0, font=("Arial", 10, "bold"), padx=14, pady=8).pack(side="left", padx=5)
    tk.Button(buttons, text="Picked Up", command=lambda: update_to(rest_pb2.PICKED_UP), bg=self.cream, fg=self.text_dark, activebackground=self.cream, activeforeground=self.text_dark, relief="flat", bd=0, font=("Arial", 10, "bold"), padx=14, pady=8).pack(side="left", padx=5)

    order_entry.focus_set()
        
def server_place_dinein_popup(self):
    popup = tk.Toplevel(self.root)
    popup.title("Place Dine-In Order")
    popup.geometry("560x730")
    popup.minsize(540, 700)
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
        text="Place Dine-In Order",
        font=("Arial", 18, "bold"),
        fg=self.green,
        bg=self.card_color
    ).pack(pady=(0, 10))

    tk.Label(
        card,
        text="Enter table information and item IDs for each guest.",
        bg=self.card_color,
        fg=self.text_muted,
        font=("Arial", 10)
    ).pack(pady=(0, 12))

    tk.Label(card, text="Table Number", bg=self.card_color, fg=self.text_dark, font=("Arial", 11, "bold")).pack(anchor="w")
    table_entry = tk.Entry(card, font=("Arial", 11))
    table_entry.pack(fill="x", pady=(5, 12), ipady=5)

    tk.Label(card, text="Guest Count (1-4)", bg=self.card_color, fg=self.text_dark, font=("Arial", 11, "bold")).pack(anchor="w")
    guest_count_entry = tk.Entry(card, font=("Arial", 11))
    guest_count_entry.pack(fill="x", pady=(5, 12), ipady=5)

    tk.Label(
        card,
        text="Guest Item IDs",
        bg=self.card_color,
        fg=self.text_dark,
        font=("Arial", 11, "bold")
    ).pack(anchor="w")

    tk.Label(
        card,
        text="For each guest, enter 1-4 item IDs separated by spaces. Example: 1 4 7",
        bg=self.card_color,
        fg=self.text_muted,
        font=("Arial", 9)
    ).pack(anchor="w", pady=(2, 8))

    guest_entries = []

    guests_frame = tk.Frame(card, bg=self.card_color)
    guests_frame.pack(fill="x", pady=(0, 8))

    for i in range(4):
        row = tk.Frame(guests_frame, bg=self.card_color)
        row.pack(fill="x", pady=3)

        tk.Label(
            row,
            text="Guest " + str(i + 1),
            bg=self.card_color,
            fg=self.text_dark,
            font=("Arial", 10)
        ).pack(side="left", padx=(0, 8))

        entry = tk.Entry(row, font=("Arial", 10))
        entry.pack(side="left", fill="x", expand=True)
        guest_entries.append(entry)

    status_label = tk.Label(card, text="", bg=self.card_color, fg="red", font=("Arial", 10))
    status_label.pack(pady=(8, 8))

    def submit_dinein_order():
        table_raw = table_entry.get().strip()
        guest_count_raw = guest_count_entry.get().strip()

        try:
            table_number = int(table_raw)
        except ValueError:
            status_label.config(text="Table number must be a number.", fg="red")
            return

        try:
            guest_count = int(guest_count_raw)
        except ValueError:
            status_label.config(text="Guest count must be a number.", fg="red")
            return

        if guest_count < 1 or guest_count > 4:
            status_label.config(text="Guest count must be between 1 and 4.", fg="red")
            return

        guests = []

        for i in range(guest_count):
            raw_items = guest_entries[i].get().strip()

            if raw_items == "":
                status_label.config(text="Enter item IDs for Guest " + str(i + 1) + ".", fg="red")
                return

            item_ids = raw_items.split()

            if len(item_ids) < 1 or len(item_ids) > 4:
                status_label.config(text="Each guest must have 1-4 items.", fg="red")
                return

            guests.append(
                rest_pb2.GuestOrder(
                    guestNumber=i + 1,
                    itemIds=item_ids
                )
            )

        try:
            response = self.stub.place_dine_in_order(
                rest_pb2.DineInOrderRequest(
                    requestId=self.next_request_id(),
                    userId=self.user_id,
                    role=self.role,
                    tableNumber=table_number,
                    guestCount=guest_count,
                    guests=guests
                )
            )

            if response.status == "success":
                messagebox.showinfo(
                    "Order Placed",
                    "Order ID: " + response.orderId + "\nTotal: $" + format(response.total, ".2f")
                )
                self.server_status.config(text="Dine-in order placed successfully.", fg=self.green)
                popup.destroy()
            else:
                status_label.config(text=response.message, fg="red")

        except Exception as e:
            status_label.config(text="Error placing dine-in order.", fg="red")
            print("Dine-in order error:", e)

    tk.Button(
        card,
        text="Submit Dine-In Order",
        command=submit_dinein_order,
        bg=self.orange,
        fg=self.text_dark,
        activebackground=self.orange,
        activeforeground=self.text_dark,
        relief="flat",
        bd=0,
        font=("Arial", 10, "bold"),
        padx=16,
        pady=8
    ).pack(pady=10)

    def handle_enter(event):
        submit_dinein_order()

    table_entry.focus_set()
    popup.bind("<Command-Return>", handle_enter)
