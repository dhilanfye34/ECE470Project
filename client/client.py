import grpc
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../gRPC")))

import rest_pb2
import rest_pb2_grpc

USERS = {"m1": "manager", "s1": "server", "c1": "chef"}
ROLES = ["manager", "server", "chef"]

def read_int(prompt, min_val=None, max_val=None):
    while True:
        s = input(prompt).strip()
        try:
            v = int(s)
        except:
            print("Enter a number")
            continue
        if min_val is not None and v < min_val:
            print(f"Must be >= {min_val}")
            continue
        if max_val is not None and v > max_val:
            print(f"Must be <= {max_val}")
            continue
        return v

def read_float(prompt, min_val=None):
    while True:
        s = input(prompt).strip()
        try:
            v = float(s)
        except:
            print("Enter a number")
            continue
        if min_val is not None and v < min_val:
            print(f"Must be >= {min_val}")
            continue
        return v

def print_menu_items(items):
    if len(items) == 0:
        print("Menu is empty")
        return
    print("")
    print("Menu:")
    for it in items:
        print(f"{it.itemId}. {it.name} ({it.category}) - ${it.price:.2f}")
    print("")

def fetch_menu(stub, request_id, user_id, role):
    resp = stub.get_menu(rest_pb2.MenuRequest(requestId=request_id, userId=user_id, role=role))
    if resp.status != "success":
        print(resp.status, "-", resp.message)
        return []
    return list(resp.items)

def manager_loop(stub, user_id):
    role = "manager"
    request_id = 1

    while True:
        print("Manager Actions")
        print("1) Get menu")
        print("2) Update menu item price")
        print("3) Logout")
        choice = read_int("> ", 1, 3)

        if choice == 1:
            request_id += 1
            items = fetch_menu(stub, request_id, user_id, role)
            print_menu_items(items)

        elif choice == 2:
            request_id += 1
            items = fetch_menu(stub, request_id, user_id, role)
            print_menu_items(items)

            item_id = input("Item id to update: ").strip()
            if item_id == "":
                print("Missing item id")
                continue

            new_price = read_float("New price: ", 0.01)

            request_id += 1
            resp = stub.update_menu_price(rest_pb2.UpdateMenuPriceRequest(requestId=request_id, userId=user_id, role=role, itemId=item_id, newPrice=new_price))
            print(resp.status, "-", resp.message)

        else:
            request_id += 1
            resp = stub.logout(rest_pb2.LogoutRequest(requestId=request_id, userId=user_id, role=role))
            print(resp.status, "-", resp.message)
            return

def build_guest_orders(items, guest_count):
    id_to_cat = {}
    valid_ids = set()
    for it in items:
        iid = str(it.itemId)
        valid_ids.add(iid)
        id_to_cat[iid] = str(it.category).strip().lower()

    guests = []

    for g in range(1, guest_count + 1):
        while True:
            raw = input(f"Guest {g} item ids: ").strip()
            if raw == "":
                print("Enter at least 1 item")
                continue

            parts = raw.split()

            if len(parts) < 1 or len(parts) > 4:
                print("Each guest must choose 1-4 items")
                continue

            ok = True
            seen_ids = set()
            for p in parts:
                if p not in valid_ids:
                    ok = False
                    break
                if p in seen_ids:
                    ok = False
                    break
                seen_ids.add(p)

            if not ok:
                print("Invalid item id or duplicate item id")
                continue

            seen_cats = set()
            cat_ok = True
            for p in parts:
                cat = id_to_cat.get(p, "")
                if cat == "":
                    cat_ok = False
                    break
                if cat in seen_cats:
                    cat_ok = False
                    break
                seen_cats.add(cat)

            if not cat_ok:
                print("Each guest can only choose one item per category")
                continue

            guests.append(rest_pb2.GuestOrder(guestNumber=g, itemIds=parts))
            break

    return guests

def build_takeout_items(items):
    valid_ids = set([str(it.itemId) for it in items])
    line_items = []
    total_qty = 0

    while True:
        item_id = input("Item id (or done): ").strip()
        if item_id.lower() == "done":
            break
        if item_id not in valid_ids:
            print("Invalid item id")
            continue
        qty = read_int("Quantity: ", 1, 10)
        if total_qty + qty > 10:
            print("Takeout max is 10 total items")
            continue
        line_items.append(rest_pb2.OrderLineItem(itemId=item_id, quantity=qty))
        total_qty += qty
        if total_qty == 10:
            break

    return line_items

def server_loop(stub, user_id):
    role = "server"
    request_id = 1

    while True:
        print("Server Actions")
        print("1) Get menu")
        print("2) Place dine-in order")
        print("3) Place takeout order")
        print("4) Logout")
        print("5) List orders")
        choice = read_int("> ", 1, 5)

        if choice == 1:
            request_id += 1
            items = fetch_menu(stub, request_id, user_id, role)
            print_menu_items(items)

        elif choice == 2:
            request_id += 1
            items = fetch_menu(stub, request_id, user_id, role)
            print_menu_items(items)

            if len(items) == 0:
                continue

            table_num = read_int("Table number: ", 1, 1000)
            guest_count = read_int("Guest count (1-4): ", 1, 4)
            guests = build_guest_orders(items, guest_count)

            request_id += 1
            resp = stub.place_dine_in_order(rest_pb2.DineInOrderRequest(requestId=request_id, userId=user_id, role=role, tableNumber=table_num, guestCount=guest_count, guests=guests))
            print(resp.status, "-", resp.message)
            if resp.status == "success":
                print("Order ID:", resp.orderId)
                print("Total:", f"${resp.total:.2f}")

        elif choice == 3:
            request_id += 1
            items = fetch_menu(stub, request_id, user_id, role)
            print_menu_items(items)

            if len(items) == 0:
                continue

            guest_name = input("Guest name: ").strip()
            if guest_name == "":
                print("Missing guest name")
                continue

            line_items = build_takeout_items(items)
            if len(line_items) == 0:
                print("Must add at least 1 item")
                continue

            request_id += 1
            resp = stub.place_takeout_order(rest_pb2.TakeoutOrderRequest(requestId=request_id, userId=user_id, role=role, guestName=guest_name, items=line_items))
            print(resp.status, "-", resp.message)
            if resp.status == "success":
                print("Order ID:", resp.orderId)
                print("Total:", f"${resp.total:.2f}")
        elif choice == 5:
            request_id += 1
            resp = stub.list_orders(rest_pb2.ListOrdersRequest(requestId=request_id, userId=user_id, role=role))
            if resp.status != "success":
                print(resp.status, "-", resp.message)
                continue

            if len(resp.orders) == 0:
                print("No orders")
                continue

            print("")
            for o in resp.orders:
                extra = f"Table {o.tableNumber}" if o.orderType == "dine-in" else o.guestName
                print(f"{o.orderId} | {o.orderType} | {o.status} | {extra} | ${o.total:.2f}")
            print("")

        else:
            request_id += 1
            resp = stub.logout(rest_pb2.LogoutRequest(requestId=request_id, userId=user_id, role=role))
            print(resp.status, "-", resp.message)
            return

def chef_loop(stub, user_id):
    role = "chef"
    request_id = 1

    while True:
        print("Chef Actions")
        print("1) List orders")
        print("2) Mark order ready")
        print("3) Logout")
        choice = read_int("> ", 1, 3)

        if choice == 1:
            request_id += 1
            resp = stub.list_orders(rest_pb2.ListOrdersRequest(requestId=request_id, userId=user_id, role=role))
            if resp.status != "success":
                print(resp.status, "-", resp.message)
                continue

            if len(resp.orders) == 0:
                print("No orders")
                continue

            print("")
            for o in resp.orders:
                extra = f"Table {o.tableNumber}" if o.orderType == "dine-in" else o.guestName
                print(f"{o.orderId} | {o.orderType} | {o.status} | {extra} | ${o.total:.2f}")
            print("")

        elif choice == 2:
            order_id = input("Order id: ").strip()
            if order_id == "":
                print("Missing order id")
                continue
            request_id += 1
            resp = stub.mark_order_ready(rest_pb2.MarkOrderReadyRequest(requestId=request_id, userId=user_id, role=role, orderId=order_id))
            print(resp.status, "-", resp.message)

        else:
            request_id += 1
            resp = stub.logout(rest_pb2.LogoutRequest(requestId=request_id, userId=user_id, role=role))
            print(resp.status, "-", resp.message)
            return

def pick_user_and_role():
    user_id = input("User id: ").strip()
    role = input("Role (manager/server/chef): ").strip().lower()

    if user_id == "":
        print("Missing user id")
        return "", ""

    if role == "":
        print("Missing role")
        return "", ""

    if role not in ["manager", "server", "chef"]:
        print("Invalid role (must be manager, server, or chef)")
        return "", ""

    return user_id, role

def run():
    channel = grpc.insecure_channel("localhost:50000")
    stub = rest_pb2_grpc.RestaurantServiceStub(channel)

    user_id, role = pick_user_and_role()
    if user_id == "":
        return

    request_id = 1
    resp = stub.login(rest_pb2.LoginRequest(requestId=request_id, userId=user_id, role=role))
    print(resp.status, "-", resp.message)
    if resp.status != "success":
        return

    if role == "manager":
        manager_loop(stub, user_id)
    elif role == "server":
        server_loop(stub, user_id)
    elif role == "chef":
        chef_loop(stub, user_id)
    else:
        print("error: invalid role")

if __name__ == "__main__":
    run()