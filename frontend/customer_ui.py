import tkinter as tk
from tkinter import messagebox
import rest_pb2


def build_customer_dashboard(self):
    self.clear_window()
    self.build_header("Customer Ordering", "Online pickup orders for The Hurricane Grill")

    frame = tk.Frame(self.root, bg=self.bg_color)
    frame.pack(fill="both", expand=True, padx=18, pady=18)

    tk.Label(
        frame,
        text="Welcome to The Hurricane Grill",
        font=("Arial", 19, "bold"),
        fg=self.text_dark,
        bg=self.bg_color
    ).pack(anchor="w", pady=(0, 4))

    tk.Label(
        frame,
        text="Browse the menu, build your cart, and place an online pickup order.",
        font=("Arial", 11),
        fg=self.text_muted,
        bg=self.bg_color
    ).pack(anchor="w", pady=(0, 12))

    button_frame = tk.Frame(frame, bg=self.bg_color)
    button_frame.pack(anchor="w", pady=(0, 10))

    self.neutral_button(button_frame, "Browse Menu", self.customer_get_menu).pack(side="left", padx=5)
    self.primary_button(button_frame, "Place Online Order", self.customer_order_popup).pack(side="left", padx=5)

    lookup_frame = tk.Frame(
        button_frame,
        bg=self.cream,
        highlightthickness=1,
        highlightbackground=self.border_color
    )
    lookup_frame.pack(side="left", padx=5)

    tk.Label(
        lookup_frame,
        text="🔎",
        bg=self.cream,
        fg=self.text_dark,
        font=("Arial", 13, "bold")
    ).pack(side="left", padx=(10, 0), pady=6)

    tk.Button(
        lookup_frame,
        text="Order Lookup",
        command=self.customer_status_popup,
        width=15,
        bg=self.cream,
        fg=self.text_dark,
        activebackground=self.cream,
        activeforeground=self.text_dark,
        relief="flat",
        bd=0,
        font=("Arial", 10, "bold"),
        pady=7
    ).pack(side="left", padx=(2, 8), pady=2)

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
        text="Available items for online pickup orders.",
        font=("Arial", 10),
        fg=self.text_muted,
        bg=self.card_color
    ).pack(anchor="w", padx=14, pady=(2, 4))

    table_wrap = tk.Frame(card, bg=self.card_color)
    table_wrap.pack(fill="both", expand=True, padx=14, pady=(4, 10))

    self.customer_table = self.create_menu_table(table_wrap)

    self.customer_status = tk.Label(
        frame,
        text="",
        fg=self.green,
        bg=self.bg_color,
        font=("Arial", 10, "bold")
    )
    self.customer_status.pack(anchor="w", pady=10)


def customer_get_menu(self):
    try:
        response = self.stub.get_menu(
            rest_pb2.MenuRequest(
                requestId=self.next_request_id(),
                userId=self.user_id,
                role=self.role
            )
        )

        if response.status != "success":
            self.customer_status.config(text=response.message, fg="red")
            return

        for row in self.customer_table.get_children():
            self.customer_table.delete(row)

        for item in response.items:
            if item.availability:
                self.customer_table.insert(
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

        self.customer_status.config(text="Menu loaded successfully.", fg=self.green)

    except Exception as e:
        self.customer_status.config(text="Error loading menu.", fg="red")
        print("Customer get menu error:", e)


def customer_order_popup(self):
    popup = tk.Toplevel(self.root)
    popup.title("Place Online Order")
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
        text="Online Pickup Order",
        font=("Arial", 18, "bold"),
        fg=self.green,
        bg=self.card_color
    ).pack(pady=(0, 10))

    tk.Label(card, text="Customer Name", bg=self.card_color, fg=self.text_dark, font=("Arial", 11, "bold")).pack(anchor="w")
    name_entry = tk.Entry(card, font=("Arial", 11))
    name_entry.pack(fill="x", pady=(5, 12), ipady=5)

    tk.Label(card, text="Pickup Info", bg=self.card_color, fg=self.text_dark, font=("Arial", 11, "bold")).pack(anchor="w")

    tk.Label(
        card,
        text="Any notes about your order, pickup time, or allergies.",
        bg=self.card_color,
        fg=self.text_muted,
        font=("Arial", 9)
    ).pack(anchor="w", pady=(2, 5))

    pickup_entry = tk.Entry(card, font=("Arial", 11))
    pickup_entry.pack(fill="x", pady=(0, 12), ipady=5)

    tk.Label(card, text="Item ID", bg=self.card_color, fg=self.text_dark, font=("Arial", 11, "bold")).pack(anchor="w")
    item_entry = tk.Entry(card, font=("Arial", 11))
    item_entry.pack(fill="x", pady=(5, 12), ipady=5)

    tk.Label(card, text="Quantity", bg=self.card_color, fg=self.text_dark, font=("Arial", 11, "bold")).pack(anchor="w")
    qty_entry = tk.Entry(card, font=("Arial", 11))
    qty_entry.pack(fill="x", pady=(5, 12), ipady=5)

    status_label = tk.Label(card, text="", bg=self.card_color, fg="red", font=("Arial", 10))
    status_label.pack(pady=(0, 8))

    tk.Label(card, text="Cart", bg=self.card_color, fg=self.text_dark, font=("Arial", 11, "bold")).pack(anchor="w")

    cart_listbox = tk.Listbox(card, height=7, font=("Arial", 10))
    cart_listbox.pack(fill="both", expand=True, pady=(5, 10))

    order_items = []

    def add_item():
        item_id = item_entry.get().strip()
        qty_raw = qty_entry.get().strip()

        if item_id == "":
            status_label.config(text="Enter an item ID.", fg="red")
            return

        try:
            quantity = int(qty_raw)
        except ValueError:
            status_label.config(text="Quantity must be a number.", fg="red")
            return

        if quantity < 1:
            status_label.config(text="Quantity must be at least 1.", fg="red")
            return

        total_qty = quantity
        for existing_item in order_items:
            total_qty += existing_item.quantity

        if total_qty > 10:
            status_label.config(text="Online orders can have at most 10 total items.", fg="red")
            return

        line_item = rest_pb2.OrderLineItem(itemId=item_id, quantity=quantity)
        order_items.append(line_item)

        cart_listbox.insert(tk.END, "Item ID: " + item_id + " | Quantity: " + str(quantity))
        item_entry.delete(0, tk.END)
        qty_entry.delete(0, tk.END)
        item_entry.focus_set()
        status_label.config(text="Item added.", fg=self.green)

    def remove_selected_item():
        selected = cart_listbox.curselection()

        if not selected:
            status_label.config(text="Select an item to remove.", fg="red")
            return

        index = selected[0]
        cart_listbox.delete(index)
        del order_items[index]
        status_label.config(text="Item removed.", fg=self.green)

    def submit_order():
        customer_name = name_entry.get().strip()
        pickup_info = pickup_entry.get().strip()

        if customer_name == "":
            status_label.config(text="Enter a customer name.", fg="red")
            return

        if pickup_info == "":
            status_label.config(text="Enter pickup info.", fg="red")
            return

        if len(order_items) == 0:
            status_label.config(text="Add at least one item.", fg="red")
            return

        try:
            response = self.stub.place_online_order(
                rest_pb2.OnlineOrderRequest(
                    requestId=self.next_request_id(),
                    userId=self.user_id,
                    role=self.role,
                    customerName=customer_name,
                    items=order_items,
                    pickupInfo=pickup_info
                )
            )

            if response.status == "success":
                messagebox.showinfo(
                    "Order Placed",
                    "Order ID: " + response.orderId + "\nTotal: $" + format(response.total, ".2f")
                )
                self.customer_status.config(text="Online order placed successfully.", fg=self.green)
                popup.destroy()
            else:
                status_label.config(text=response.message, fg="red")

        except Exception as e:
            status_label.config(text="Error placing online order.", fg="red")
            print("Online order error:", e)

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
        text="Submit Online Order",
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

    name_entry.focus_set()
    item_entry.bind("<Return>", lambda event: qty_entry.focus_set())
    qty_entry.bind("<Return>", lambda event: add_item())
    popup.bind("<Command-Return>", lambda event: submit_order())


def customer_status_popup(self):
    popup = tk.Toplevel(self.root)
    popup.title("Order Lookup")
    popup.geometry("440x320")
    popup.minsize(420, 300)
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
        text="Order Lookup",
        font=("Arial", 18, "bold"),
        fg=self.green,
        bg=self.card_color
    ).pack(pady=(0, 12))

    tk.Label(
        card,
        text="Check Status",
        bg=self.card_color,
        fg=self.text_muted,
        font=("Arial", 10, "bold")
    ).pack(pady=(0, 10))

    tk.Label(card, text="Order ID", bg=self.card_color, fg=self.text_dark, font=("Arial", 11, "bold")).pack(anchor="w")
    order_entry = tk.Entry(card, font=("Arial", 11))
    order_entry.pack(fill="x", pady=(5, 12), ipady=5)

    result_label = tk.Label(card, text="", bg=self.card_color, fg=self.text_dark, font=("Arial", 10), justify="left")
    result_label.pack(pady=8)

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
                result_label.config(
                    text="Order ID: " + response.orderId +
                         "\nStatus: " + response.currentStatus +
                         "\nType: " + response.orderType +
                         "\nCreated: " + response.createdTime,
                    fg=self.text_dark
                )
            else:
                result_label.config(text=response.message, fg="red")

        except Exception as e:
            result_label.config(text="Error checking order status.", fg="red")
            print("Customer status lookup error:", e)

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
    ).pack(pady=8)

    order_entry.focus_set()
    order_entry.bind("<Return>", lambda event: lookup_status())
