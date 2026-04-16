import grpc
from concurrent import futures
from datetime import datetime, timezone
import json
import random
import os
import sys
import threading

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../gRPC")))

import rest_pb2
import rest_pb2_grpc

USERS = {"m1": "manager", "s1": "server", "s2": "server", "s3": "server", "c1": "chef", "c2": "chef", "cust1": "customer"}

STATUS_RECEIVED = "received"
STATUS_READY = "ready"
STATUS_COMPLETED = "completed"
STATUS_PICKED_UP = "picked_up"

VALID_STATUSES = [STATUS_RECEIVED, STATUS_READY, STATUS_COMPLETED, STATUS_PICKED_UP]

menu_lock = threading.Lock()
orders_lock = threading.Lock()

def load_menu():
    if not os.path.exists("menu.json"):
        return []
    with open("menu.json", "r") as file:
        return json.load(file)

def save_menu(menu):
    with open("menu.json", "w") as file:
        json.dump(menu, file, indent=2)

def load_orders():
    if not os.path.exists("orders.json"):
        return []
    with open("orders.json", "r") as file:
        return json.load(file)

def save_orders(orders):
    with open("orders.json", "w") as file:
        json.dump(orders, file, indent=2)

def role_ok(role):
    return role in ["manager", "server", "chef", "customer"]

def user_ok(user_id, role):
    return str(user_id) in USERS and USERS[str(user_id)] == role

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def normalize_status(status):
    s = str(status).strip().lower()
    if s == "confirmed":
        return STATUS_RECEIVED
    if s == "in_preparation":
        return STATUS_RECEIVED
    if s in VALID_STATUSES:
        return s
    return ""

def status_to_enum(status):
    s = normalize_status(status)
    if s == STATUS_RECEIVED:
        return rest_pb2.RECEIVED
    if s == STATUS_READY:
        return rest_pb2.READY
    if s == STATUS_COMPLETED:
        return rest_pb2.COMPLETED
    if s == STATUS_PICKED_UP:
        return rest_pb2.PICKED_UP
    return rest_pb2.ORDER_STATUS_UNSPECIFIED

def enum_to_status(code):
    if code == rest_pb2.RECEIVED:
        return STATUS_RECEIVED
    if int(code) == 2:
        return STATUS_RECEIVED
    if code == rest_pb2.READY:
        return STATUS_READY
    if code == rest_pb2.COMPLETED:
        return STATUS_COMPLETED
    if code == rest_pb2.PICKED_UP:
        return STATUS_PICKED_UP
    return ""

def valid_status_transition(current_status, new_status):
    transitions = {
        STATUS_RECEIVED: [STATUS_READY],
        STATUS_READY: [STATUS_COMPLETED, STATUS_PICKED_UP],
        STATUS_COMPLETED: [],
        STATUS_PICKED_UP: [],
    }
    if current_status not in transitions:
        return False
    if new_status == current_status:
        return False
    return new_status in transitions[current_status]

def build_menu_items(menu):
    items = []
    for item in menu:
        items.append(
            rest_pb2.MenuItem(
                itemId=str(item.get("itemId", "")),
                name=str(item.get("name", "")),
                category=str(item.get("category", "")),
                price=float(item.get("price", 0.0)),
                description=str(item.get("description", "")),
                availability=bool(item.get("availability", True)),
            )
        )
    return items

def menu_dict(menu):
    d = {}
    for item in menu:
        d[str(item.get("itemId", ""))] = item
    return d

def next_order_id(orders):
    used = set()
    for o in orders:
        used.add(str(o.get("orderId", "")))
    while True:
        oid = str(random.randint(1, 1000000))
        if oid not in used:
            return oid

def validate_item_fields(item_id, name, category, price):
    if str(item_id).strip() == "":
        return "missing itemId"
    if str(name).strip() == "":
        return "missing name"
    if str(category).strip() == "":
        return "missing category"
    if float(price) <= 0:
        return "invalid price"
    return ""

class RestaurantService(rest_pb2_grpc.RestaurantServiceServicer):
    def login(self, request, context):
        if not role_ok(request.role):
            return rest_pb2.LoginResponse(requestId=request.requestId, status="error", message="invalid role")

        if not user_ok(request.userId, request.role):
            return rest_pb2.LoginResponse(requestId=request.requestId, status="error", message="invalid user")

        return rest_pb2.LoginResponse(requestId=request.requestId, status="success", message="logged in")

    def logout(self, request, context):
        if not role_ok(request.role):
            return rest_pb2.LogoutResponse(requestId=request.requestId, status="error", message="invalid role")

        if not user_ok(request.userId, request.role):
            return rest_pb2.LogoutResponse(requestId=request.requestId, status="error", message="invalid user")

        return rest_pb2.LogoutResponse(requestId=request.requestId, status="success", message="logged out")

    def get_menu(self, request, context):
        if not role_ok(request.role):
            return rest_pb2.MenuResponse(requestId=request.requestId, status="error", message="invalid role", items=[])

        if not user_ok(request.userId, request.role):
            return rest_pb2.MenuResponse(requestId=request.requestId, status="error", message="invalid user", items=[])

        with menu_lock:
            menu = load_menu()
        return rest_pb2.MenuResponse(requestId=request.requestId, status="success", message="menu loaded", items=build_menu_items(menu))

    def update_menu_price(self, request, context):
        if request.role != "manager":
            return rest_pb2.UpdateMenuPriceResponse(requestId=request.requestId, status="error", message="not authorized")

        if not user_ok(request.userId, request.role):
            return rest_pb2.UpdateMenuPriceResponse(requestId=request.requestId, status="error", message="invalid user")

        if request.itemId.strip() == "":
            return rest_pb2.UpdateMenuPriceResponse(requestId=request.requestId, status="error", message="missing itemId")

        if request.newPrice <= 0:
            return rest_pb2.UpdateMenuPriceResponse(requestId=request.requestId, status="error", message="invalid price")

        with menu_lock:
            menu = load_menu()
            found = False
            for item in menu:
                if str(item.get("itemId", "")) == request.itemId:
                    item["price"] = float(request.newPrice)
                    found = True
                    break

            if not found:
                return rest_pb2.UpdateMenuPriceResponse(requestId=request.requestId, status="error", message="item not found")

            save_menu(menu)
        return rest_pb2.UpdateMenuPriceResponse(requestId=request.requestId, status="success", message="price updated")

    def add_menu_item(self, request, context):
        if request.role != "manager":
            return rest_pb2.AddMenuItemResponse(requestId=request.requestId, status="error", message="not authorized")

        if not user_ok(request.userId, request.role):
            return rest_pb2.AddMenuItemResponse(requestId=request.requestId, status="error", message="invalid user")

        item_id = str(request.item.itemId).strip()
        name = str(request.item.name).strip()
        category = str(request.item.category).strip()
        price = float(request.item.price)
        description = str(request.item.description)
        availability = bool(request.item.availability)

        msg = validate_item_fields(item_id, name, category, price)
        if msg != "":
            return rest_pb2.AddMenuItemResponse(requestId=request.requestId, status="error", message=msg)

        with menu_lock:
            menu = load_menu()
            for item in menu:
                if str(item.get("itemId", "")) == item_id:
                    return rest_pb2.AddMenuItemResponse(requestId=request.requestId, status="error", message="item already exists")

            menu.append(
                {
                    "itemId": item_id,
                    "name": name,
                    "category": category,
                    "price": price,
                    "description": description,
                    "availability": availability,
                }
            )
            save_menu(menu)

        return rest_pb2.AddMenuItemResponse(requestId=request.requestId, status="success", message="menu item added")

    def remove_menu_item(self, request, context):
        if request.role != "manager":
            return rest_pb2.RemoveMenuItemResponse(requestId=request.requestId, status="error", message="not authorized")

        if not user_ok(request.userId, request.role):
            return rest_pb2.RemoveMenuItemResponse(requestId=request.requestId, status="error", message="invalid user")

        item_id = str(request.itemId).strip()
        if item_id == "":
            return rest_pb2.RemoveMenuItemResponse(requestId=request.requestId, status="error", message="missing itemId")

        with menu_lock:
            menu = load_menu()
            found = False
            new_menu = []
            for item in menu:
                if str(item.get("itemId", "")) == item_id:
                    found = True
                else:
                    new_menu.append(item)

            if not found:
                return rest_pb2.RemoveMenuItemResponse(requestId=request.requestId, status="error", message="item not found")

            save_menu(new_menu)

        return rest_pb2.RemoveMenuItemResponse(requestId=request.requestId, status="success", message="menu item removed")

    def update_menu_item(self, request, context):
        if request.role != "manager":
            return rest_pb2.UpdateMenuItemResponse(requestId=request.requestId, status="error", message="not authorized")

        if not user_ok(request.userId, request.role):
            return rest_pb2.UpdateMenuItemResponse(requestId=request.requestId, status="error", message="invalid user")

        item_id = str(request.item.itemId).strip()
        name = str(request.item.name).strip()
        category = str(request.item.category).strip()
        price = float(request.item.price)
        description = str(request.item.description)
        availability = bool(request.item.availability)

        msg = validate_item_fields(item_id, name, category, price)
        if msg != "":
            return rest_pb2.UpdateMenuItemResponse(requestId=request.requestId, status="error", message=msg)

        with menu_lock:
            menu = load_menu()
            found = False
            for item in menu:
                if str(item.get("itemId", "")) == item_id:
                    item["name"] = name
                    item["category"] = category
                    item["price"] = price
                    item["description"] = description
                    item["availability"] = availability
                    found = True
                    break

            if not found:
                return rest_pb2.UpdateMenuItemResponse(requestId=request.requestId, status="error", message="item not found")

            save_menu(menu)

        return rest_pb2.UpdateMenuItemResponse(requestId=request.requestId, status="success", message="menu item updated")

    def place_dine_in_order(self, request, context):
        if request.role != "server":
            return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="not authorized", orderId="", total=0)

        if not user_ok(request.userId, request.role):
            return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="invalid user", orderId="", total=0)

        if request.guestCount < 1 or request.guestCount > 4:
            return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="guest count must be 1-4", orderId="", total=0)

        if len(request.guests) != request.guestCount:
            return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="guest list does not match guestCount", orderId="", total=0)

        if request.tableNumber < 1 or request.tableNumber > 1000:
            return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="invalid table number", orderId="", total=0)

        with menu_lock:
            menu = load_menu()
        md = menu_dict(menu)

        total = 0.0
        seen_guest_nums = set()
        all_guest_orders = []

        for g in request.guests:
            gn = int(g.guestNumber)
            if gn < 1 or gn > int(request.guestCount):
                return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="invalid guest number", orderId="", total=0)
            if gn in seen_guest_nums:
                return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="duplicate guest number", orderId="", total=0)
            seen_guest_nums.add(gn)

            item_ids = [str(x) for x in g.itemIds]

            if len(item_ids) < 1 or len(item_ids) > 4:
                return rest_pb2.OrderResponse(
                    requestId=request.requestId,
                    status="error",
                    message="each guest must have 1-4 items",
                    orderId="",
                    total=0,
                )
            seen_categories = set()
            # checks if the item is in the menu and if it is, it adds the price to the total
            for item_id in item_ids:
                if item_id not in md:
                    return rest_pb2.OrderResponse(
                        requestId=request.requestId,
                        status="error",
                        message="invalid menu item",
                        orderId="",
                        total=0,
                    )

                if not bool(md[item_id].get("availability", True)):
                    return rest_pb2.OrderResponse(
                        requestId=request.requestId,
                        status="error",
                        message="item unavailable",
                        orderId="",
                        total=0,
                    )

                category = str(md[item_id].get("category", "")).strip().lower()
                if category == "":
                    return rest_pb2.OrderResponse(
                        requestId=request.requestId,
                        status="error",
                        message="menu item missing category",
                        orderId="",
                        total=0,
                    )
                if category in seen_categories:
                    return rest_pb2.OrderResponse(
                        requestId=request.requestId,
                        status="error",
                        message="each guest can only choose one item per category",
                        orderId="",
                        total=0,
                    )
                seen_categories.add(category)
                total += float(md[item_id].get("price", 0.0))

            all_guest_orders.append({"guestNumber": gn, "itemIds": item_ids})

        with orders_lock:
            orders = load_orders()
            order_id = next_order_id(orders)
            orders.append(
                {
                    "orderId": order_id,
                    "orderType": "dine-in",
                    "status": STATUS_RECEIVED,
                    "tableNumber": int(request.tableNumber),
                    "guestName": "",
                    "guestCount": int(request.guestCount),
                    "guests": all_guest_orders,
                    "items": [],
                    "total": float(total),
                    "createdTime": now_iso(),
                    "pickupInfo": "",
                    "customerName": "",
                }
            )
            save_orders(orders)

        print(f"Kitchen notified: Order {order_id} (dine-in) Table {request.tableNumber}")
        return rest_pb2.OrderResponse(requestId=request.requestId, status="success", message="order placed", orderId=order_id, total=float(total))

    def place_takeout_order(self, request, context):
        if request.role != "server":
            return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="not authorized", orderId="", total=0)
        if not user_ok(request.userId, request.role):
            return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="invalid user", orderId="", total=0)

        if request.guestName.strip() == "":
            return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="missing guest name", orderId="", total=0)
        if len(request.items) == 0:
            return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="order must have at least 1 item", orderId="", total=0)

        with menu_lock:
            menu = load_menu()
        md = menu_dict(menu)

        total_qty = 0
        total = 0.0
        line_items = []

        for li in request.items:
            item_id = str(li.itemId)
            qty = int(li.quantity)

            if qty <= 0:
                return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="invalid quantity", orderId="", total=0)
            if item_id not in md:
                return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="invalid menu item", orderId="", total=0)
            if not bool(md[item_id].get("availability", True)):
                return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="item unavailable", orderId="", total=0)

            total_qty += qty
            price = float(md[item_id].get("price", 0.0))
            total += price * qty
            line_items.append({"itemId": item_id, "quantity": qty})

        if total_qty > 10:
            return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="takeout max is 10 items", orderId="", total=0)

        with orders_lock:
            orders = load_orders()
            order_id = next_order_id(orders)
            orders.append(
                {
                    "orderId": order_id,
                    "orderType": "takeout",
                    "status": STATUS_RECEIVED,
                    "tableNumber": 0,
                    "guestName": str(request.guestName),
                    "guestCount": 0,
                    "guests": [],
                    "items": line_items,
                    "total": float(total),
                    "createdTime": now_iso(),
                    "pickupInfo": "",
                    "customerName": "",
                }
            )
            save_orders(orders)

        print(f"Kitchen notified: Order {order_id} (takeout) {request.guestName}")
        return rest_pb2.OrderResponse(requestId=request.requestId, status="success", message="order placed", orderId=order_id, total=float(total))

    def place_online_order(self, request, context):
        if request.role != "customer":
            return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="not authorized", orderId="", total=0)
        if not user_ok(request.userId, request.role):
            return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="invalid user", orderId="", total=0)

        if request.customerName.strip() == "":
            return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="missing customer name", orderId="", total=0)
        if request.pickupInfo.strip() == "":
            return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="missing pickup info", orderId="", total=0)
        if len(request.items) == 0:
            return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="order must have at least 1 item", orderId="", total=0)

        with menu_lock:
            menu = load_menu()
        md = menu_dict(menu)

        total_qty = 0
        total = 0.0
        line_items = []

        for li in request.items:
            item_id = str(li.itemId)
            qty = int(li.quantity)

            if qty <= 0:
                return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="invalid quantity", orderId="", total=0)
            if item_id not in md:
                return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="invalid menu item", orderId="", total=0)
            if not bool(md[item_id].get("availability", True)):
                return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="item unavailable", orderId="", total=0)

            total_qty += qty
            total += float(md[item_id].get("price", 0.0)) * qty
            line_items.append({"itemId": item_id, "quantity": qty})

        if total_qty > 10:
            return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="takeout max is 10 items", orderId="", total=0)

        with orders_lock:
            orders = load_orders()
            order_id = next_order_id(orders)
            orders.append(
                {
                    "orderId": order_id,
                    "orderType": "online",
                    "status": STATUS_RECEIVED,
                    "tableNumber": 0,
                    "guestName": str(request.customerName),
                    "guestCount": 0,
                    "guests": [],
                    "items": line_items,
                    "total": float(total),
                    "createdTime": now_iso(),
                    "pickupInfo": str(request.pickupInfo),
                    "customerName": str(request.customerName),
                }
            )
            save_orders(orders)

        print(f"Kitchen notified: Order {order_id} (online) {request.customerName}")
        return rest_pb2.OrderResponse(requestId=request.requestId, status="success", message="online order placed", orderId=order_id, total=float(total))

    def list_orders(self, request, context):
        if request.role not in ["server", "chef"]:
            return rest_pb2.ListOrdersResponse(requestId=request.requestId, status="error", message="not authorized", orders=[])
        if not user_ok(request.userId, request.role):
            return rest_pb2.ListOrdersResponse(requestId=request.requestId, status="error", message="invalid user", orders=[])

        with orders_lock:
            orders = load_orders()
        summaries = []
        for o in orders:
            status = normalize_status(o.get("status", ""))
            if status == "":
                status = str(o.get("status", ""))
            summaries.append(
                rest_pb2.OrderSummary(
                    orderId=str(o.get("orderId", "")),
                    orderType=str(o.get("orderType", "")),
                    status=status,
                    tableNumber=int(o.get("tableNumber", 0)),
                    guestName=str(o.get("guestName", "")),
                    total=float(o.get("total", 0.0)),
                    createdTime=str(o.get("createdTime", "")),
                    orderStatus=status_to_enum(status),
                    pickupInfo=str(o.get("pickupInfo", "")),
                    customerName=str(o.get("customerName", "")),
                )
            )

        return rest_pb2.ListOrdersResponse(requestId=request.requestId, status="success", message="orders listed", orders=summaries)

    def update_order_status(self, request, context):
        if request.role not in ["manager", "server", "chef"]:
            return rest_pb2.UpdateOrderStatusResponse(
                requestId=request.requestId,
                status="error",
                message="not authorized",
                orderId="",
                previousStatus="",
                currentStatus="",
                currentStatusCode=rest_pb2.ORDER_STATUS_UNSPECIFIED,
            )
        if not user_ok(request.userId, request.role):
            return rest_pb2.UpdateOrderStatusResponse(
                requestId=request.requestId,
                status="error",
                message="invalid user",
                orderId="",
                previousStatus="",
                currentStatus="",
                currentStatusCode=rest_pb2.ORDER_STATUS_UNSPECIFIED,
            )
        if request.orderId.strip() == "":
            return rest_pb2.UpdateOrderStatusResponse(
                requestId=request.requestId,
                status="error",
                message="missing orderId",
                orderId="",
                previousStatus="",
                currentStatus="",
                currentStatusCode=rest_pb2.ORDER_STATUS_UNSPECIFIED,
            )

        new_status = enum_to_status(request.newStatus)
        if new_status == "":
            return rest_pb2.UpdateOrderStatusResponse(
                requestId=request.requestId,
                status="error",
                message="invalid new status",
                orderId=request.orderId,
                previousStatus="",
                currentStatus="",
                currentStatusCode=rest_pb2.ORDER_STATUS_UNSPECIFIED,
            )

        with orders_lock:
            orders = load_orders()
            found = False
            prev_status = ""
            for o in orders:
                if str(o.get("orderId", "")) == request.orderId:
                    found = True
                    prev_status = normalize_status(o.get("status", ""))
                    if prev_status == "":
                        return rest_pb2.UpdateOrderStatusResponse(
                            requestId=request.requestId,
                            status="error",
                            message="unknown current status",
                            orderId=request.orderId,
                            previousStatus=str(o.get("status", "")),
                            currentStatus=str(o.get("status", "")),
                            currentStatusCode=rest_pb2.ORDER_STATUS_UNSPECIFIED,
                        )
                    if not valid_status_transition(prev_status, new_status):
                        return rest_pb2.UpdateOrderStatusResponse(
                            requestId=request.requestId,
                            status="error",
                            message="invalid status transition",
                            orderId=request.orderId,
                            previousStatus=prev_status,
                            currentStatus=prev_status,
                            currentStatusCode=status_to_enum(prev_status),
                        )

                    o["status"] = new_status
                    if str(o.get("createdTime", "")).strip() == "":
                        o["createdTime"] = now_iso()
                    save_orders(orders)
                    break

            if not found:
                return rest_pb2.UpdateOrderStatusResponse(
                    requestId=request.requestId,
                    status="error",
                    message="order not found",
                    orderId=request.orderId,
                    previousStatus="",
                    currentStatus="",
                    currentStatusCode=rest_pb2.ORDER_STATUS_UNSPECIFIED,
                )

        return rest_pb2.UpdateOrderStatusResponse(
            requestId=request.requestId,
            status="success",
            message="order status updated",
            orderId=request.orderId,
            previousStatus=prev_status,
            currentStatus=new_status,
            currentStatusCode=status_to_enum(new_status),
        )

    def get_order_status(self, request, context):
        if not role_ok(request.role):
            return rest_pb2.GetOrderStatusResponse(
                requestId=request.requestId,
                status="error",
                message="invalid role",
                orderId="",
                currentStatus="",
                currentStatusCode=rest_pb2.ORDER_STATUS_UNSPECIFIED,
                orderType="",
                createdTime="",
            )
        if not user_ok(request.userId, request.role):
            return rest_pb2.GetOrderStatusResponse(
                requestId=request.requestId,
                status="error",
                message="invalid user",
                orderId="",
                currentStatus="",
                currentStatusCode=rest_pb2.ORDER_STATUS_UNSPECIFIED,
                orderType="",
                createdTime="",
            )
        if request.orderId.strip() == "":
            return rest_pb2.GetOrderStatusResponse(
                requestId=request.requestId,
                status="error",
                message="missing orderId",
                orderId="",
                currentStatus="",
                currentStatusCode=rest_pb2.ORDER_STATUS_UNSPECIFIED,
                orderType="",
                createdTime="",
            )

        with orders_lock:
            orders = load_orders()
            for o in orders:
                if str(o.get("orderId", "")) == request.orderId:
                    status = normalize_status(o.get("status", ""))
                    if status == "":
                        status = str(o.get("status", ""))
                    return rest_pb2.GetOrderStatusResponse(
                        requestId=request.requestId,
                        status="success",
                        message="order status retrieved",
                        orderId=str(o.get("orderId", "")),
                        currentStatus=status,
                        currentStatusCode=status_to_enum(status),
                        orderType=str(o.get("orderType", "")),
                        createdTime=str(o.get("createdTime", "")),
                    )

        return rest_pb2.GetOrderStatusResponse(
            requestId=request.requestId,
            status="error",
            message="order not found",
            orderId=request.orderId,
            currentStatus="",
            currentStatusCode=rest_pb2.ORDER_STATUS_UNSPECIFIED,
            orderType="",
            createdTime="",
        )

    def generate_report(self, request, context):
        if request.role != "manager":
            return rest_pb2.GenerateReportResponse(
                requestId=request.requestId,
                status="error",
                message="not authorized",
                totalOrders=0,
                totalRevenue=0,
                receivedCount=0,
                readyCount=0,
                completedCount=0,
                pickedUpCount=0,
            )

        if not user_ok(request.userId, request.role):
            return rest_pb2.GenerateReportResponse(
                requestId=request.requestId,
                status="error",
                message="invalid user",
                totalOrders=0,
                totalRevenue=0,
                receivedCount=0,
                readyCount=0,
                completedCount=0,
                pickedUpCount=0,
            )

        with orders_lock:
            orders = load_orders()

        received_count = 0
        ready_count = 0
        completed_count = 0
        picked_up_count = 0
        total_revenue = 0.0

        for o in orders:
            total_revenue += float(o.get("total", 0.0))
            status = normalize_status(o.get("status", ""))
            if status == STATUS_RECEIVED:
                received_count += 1
            elif status == STATUS_READY:
                ready_count += 1
            elif status == STATUS_COMPLETED:
                completed_count += 1
            elif status == STATUS_PICKED_UP:
                picked_up_count += 1

        return rest_pb2.GenerateReportResponse(
            requestId=request.requestId,
            status="success",
            message="report generated",
            totalOrders=len(orders),
            totalRevenue=float(total_revenue),
            receivedCount=received_count,
            readyCount=ready_count,
            completedCount=completed_count,
            pickedUpCount=picked_up_count,
        )

    def mark_order_ready(self, request, context):
        if request.role != "chef":
            return rest_pb2.MarkOrderReadyResponse(requestId=request.requestId, status="error", message="not authorized")
        if not user_ok(request.userId, request.role):
            return rest_pb2.MarkOrderReadyResponse(requestId=request.requestId, status="error", message="invalid user")
        if request.orderId.strip() == "":
            return rest_pb2.MarkOrderReadyResponse(requestId=request.requestId, status="error", message="missing orderId")

        with orders_lock:
            orders = load_orders()
            found = False
            for o in orders:
                if str(o.get("orderId", "")) == request.orderId:
                    current_status = normalize_status(o.get("status", ""))
                    if current_status == "":
                        return rest_pb2.MarkOrderReadyResponse(requestId=request.requestId, status="error", message="unknown current status")
                    if not valid_status_transition(current_status, STATUS_READY):
                        return rest_pb2.MarkOrderReadyResponse(requestId=request.requestId, status="error", message="invalid status transition")

                    o["status"] = STATUS_READY
                    if str(o.get("createdTime", "")).strip() == "":
                        o["createdTime"] = now_iso()
                    found = True
                    break

            if not found:
                return rest_pb2.MarkOrderReadyResponse(requestId=request.requestId, status="error", message="order not found")

            save_orders(orders)
        print(f"Order ready: {request.orderId}")
        return rest_pb2.MarkOrderReadyResponse(requestId=request.requestId, status="success", message="order marked ready")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rest_pb2_grpc.add_RestaurantServiceServicer_to_server(RestaurantService(), server)
    server.add_insecure_port("[::]:50000")
    server.start()
    print("Server running on port 50000")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
