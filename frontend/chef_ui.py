import tkinter as tk
import rest_pb2

def build_chef_dashboard(self):
    self.clear_window()
    self.build_header("Chef Dashboard", "Kitchen queue and active order visibility")

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
        text="View incoming orders and keep the kitchen on track.",
        font=("Arial", 11),
        fg=self.text_muted,
        bg=self.bg_color
    ).pack(anchor="w", pady=(0, 12))

    button_frame = tk.Frame(frame, bg=self.bg_color)
    button_frame.pack(fill="x", pady=(0, 10))

    action_frame = tk.Frame(button_frame, bg=self.bg_color)
    action_frame.pack(side="left")

    self.primary_button(action_frame, "List Orders", self.chef_list_orders).pack(side="left", padx=5)
    self.secondary_button(action_frame, "Mark Ready", self.chef_mark_ready).pack(side="left", padx=5)

    lookup_frame = tk.Frame(
        button_frame,
        bg=self.cream,
        highlightthickness=1,
        highlightbackground=self.border_color
    )
    lookup_frame.pack(side="right", padx=5)

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
        command=self.chef_status_lookup_popup,
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
        text="Kitchen Queue",
        font=("Arial", 14, "bold"),
        fg=self.text_dark,
        bg=self.card_color
    ).pack(anchor="w", padx=14, pady=(14, 0))

    tk.Label(
        card,
        text="Orders currently visible to the kitchen team.",
        font=("Arial", 10),
        fg=self.text_muted,
        bg=self.card_color
    ).pack(anchor="w", padx=14, pady=(2, 4))

    table_wrap = tk.Frame(card, bg=self.card_color)
    table_wrap.pack(fill="both", expand=True, padx=14, pady=(4, 10))

    self.chef_table = self.create_orders_table(table_wrap)

    self.chef_status = tk.Label(
        frame,
        text="",
        fg=self.green,
        bg=self.bg_color,
        font=("Arial", 10, "bold")
    )
    self.chef_status.pack(anchor="w", pady=10)


def chef_list_orders(self):
    try:
        response = self.stub.list_orders(
            rest_pb2.ListOrdersRequest(
                requestId=self.next_request_id(),
                userId=self.user_id,
                role=self.role
            )
        )

        if response.status != "success":
            self.chef_status.config(text=response.message, fg="red")
            return

        for row in self.chef_table.get_children():
            self.chef_table.delete(row)

        for order in response.orders:
            extra = f"Table {order.tableNumber}" if order.orderType == "dine-in" else order.guestName
            self.chef_table.insert(
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

        self.chef_status.config(text="Orders loaded successfully.", fg=self.green)

    except Exception as e:
        self.chef_status.config(text="Error loading orders.", fg="red")
        print("Chef list orders error:", e)


def chef_mark_ready(self):
    selected = self.chef_table.selection()

    if not selected:
        self.chef_status.config(text="Select an order first.", fg="red")
        return

    order_values = self.chef_table.item(selected[0], "values")
    order_id = order_values[0]

    try:
        response = self.stub.mark_order_ready(
            rest_pb2.MarkOrderReadyRequest(
                requestId=self.next_request_id(),
                userId=self.user_id,
                role=self.role,
                orderId=order_id
            )
        )

        if response.status == "success":
            self.chef_status.config(text="Order marked ready.", fg=self.green)
            self.chef_list_orders()
        else:
            self.chef_status.config(text=response.message, fg="red")

    except Exception as e:
        self.chef_status.config(text="Error marking order ready.", fg="red")
        print("Chef mark ready error:", e)


def chef_status_lookup_popup(self):
    popup = tk.Toplevel(self.root)
    popup.title("Order Lookup")
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
                details = [
                    "Order ID: " + response.orderId,
                    "Status: " + response.currentStatus,
                ]

                if response.orderType != "":
                    details.append("Type: " + response.orderType)

                if response.createdTime != "":
                    details.append("Created: " + response.createdTime)

                result_label.config(text="\n".join(details), fg=self.text_dark)
                self.chef_status.config(text="Order status retrieved.", fg=self.green)
            else:
                result_label.config(text=response.message, fg="red")

        except Exception as e:
            result_label.config(text="Error checking order status.", fg="red")
            print("Chef status lookup error:", e)

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
