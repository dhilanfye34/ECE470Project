import grpc
from concurrent import futures
import json
import random
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../gRPC")))

import rest_pb2
import rest_pb2_grpc

USERS = {"m1": "manager", "s1": "server", "c1": "chef"}

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
    return role in ["manager", "server", "chef"]

def user_ok(user_id, role):
    return str(user_id) in USERS and USERS[str(user_id)] == role

def build_menu_items(menu):
    items = []
    for item in menu:
        items.append(
            rest_pb2.MenuItem(
                itemId=str(item.get("itemId", "")),
                name=str(item.get("name", "")),
                category=str(item.get("category", "")),
                price=float(item.get("price", 0.0)),
            )
        )
    return items

def menu_dict(menu):
    d = {}
    for item in menu:
        d[str(item.get("itemId", ""))] = item
    return d

def next_order_id():
    return str(random.randint(1, 1000000))

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

        order_id = next_order_id()
        orders = load_orders()
        orders.append(
            {
                "orderId": order_id,
                "orderType": "dine-in",
                "status": "confirmed",
                "tableNumber": int(request.tableNumber),
                "guestName": "",
                "guestCount": int(request.guestCount),
                "guests": all_guest_orders,
                "items": [],
                "total": float(total),
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

            total_qty += qty
            price = float(md[item_id].get("price", 0.0))
            total += price * qty
            line_items.append({"itemId": item_id, "quantity": qty})

        if total_qty > 10:
            return rest_pb2.OrderResponse(requestId=request.requestId, status="error", message="takeout max is 10 items", orderId="", total=0)

        order_id = next_order_id()
        orders = load_orders()
        orders.append(
            {
                "orderId": order_id,
                "orderType": "takeout",
                "status": "confirmed",
                "tableNumber": 0,
                "guestName": str(request.guestName),
                "guestCount": 0,
                "guests": [],
                "items": line_items,
                "total": float(total),
            }
        )
        save_orders(orders)

        print(f"Kitchen notified: Order {order_id} (takeout) {request.guestName}")
        return rest_pb2.OrderResponse(requestId=request.requestId, status="success", message="order placed", orderId=order_id, total=float(total))

    def list_orders(self, request, context):
        if request.role not in ["server", "chef"]:
            return rest_pb2.ListOrdersResponse(requestId=request.requestId, status="error", message="not authorized", orders=[])
        if not user_ok(request.userId, request.role):
            return rest_pb2.ListOrdersResponse(requestId=request.requestId, status="error", message="invalid user", orders=[])

        orders = load_orders()
        summaries = []
        for o in orders:
            summaries.append(
                rest_pb2.OrderSummary(
                    orderId=str(o.get("orderId", "")),
                    orderType=str(o.get("orderType", "")),
                    status=str(o.get("status", "")),
                    tableNumber=int(o.get("tableNumber", 0)),
                    guestName=str(o.get("guestName", "")),
                    total=float(o.get("total", 0.0)),
                )
            )

        return rest_pb2.ListOrdersResponse(requestId=request.requestId, status="success", message="orders listed", orders=summaries)

    def mark_order_ready(self, request, context):
        if request.role != "chef":
            return rest_pb2.MarkOrderReadyResponse(requestId=request.requestId, status="error", message="not authorized")
        if not user_ok(request.userId, request.role):
            return rest_pb2.MarkOrderReadyResponse(requestId=request.requestId, status="error", message="invalid user")
        if request.orderId.strip() == "":
            return rest_pb2.MarkOrderReadyResponse(requestId=request.requestId, status="error", message="missing orderId")

        orders = load_orders()
        found = False
        for o in orders:
            if str(o.get("orderId", "")) == request.orderId:
                o["status"] = "ready"
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