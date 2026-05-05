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
    button_frame.pack(anchor="w", pady=(0, 10))

    self.primary_button(button_frame, "List Orders", self.chef_list_orders).pack(side="left", padx=5)
    self.secondary_button(button_frame, "Mark Ready", self.chef_mark_ready).pack(side="left", padx=5)

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
                values=(order.orderId, order.orderType, order.status, extra, f"${order.total:.2f}")
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