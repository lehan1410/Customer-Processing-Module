import flask
from flask import request, jsonify, render_template, redirect, url_for, Blueprint
import mysql.connector
import datetime
from flask_cors import CORS
from flask_socketio import emit
from shared import orderNote


order_bp = Blueprint("order", __name__)
CORS(order_bp)


# def get_db_connection():
#     return mysql.connector.connect(
#         host="han312.mysql.pythonanywhere-services.com",
#         user="han312",
#         password="SOA2025@",
#         database="han312$Order_Services"
#     )


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="Order_Services"
    )
#Lấy đơn hàng cho chef
@order_bp.route('/get_orders', methods=['GET'])

def get_orders():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Lấy đơn đang chờ phục vụ hoặc đang chuẩn bị
        cursor.execute("""
            SELECT o.order_id, o.table_id, o.package_id, o.status,
                   oi.food_id, oi.quantity, m.food_name
            FROM Orders o
            LEFT JOIN Order_Items oi ON o.order_id = oi.order_id
            LEFT JOIN Menu m ON oi.food_id = m.food_id
            WHERE o.status IN ('Đang chờ phục vụ', 'Đang chuẩn bị')
        """)
        rows = cursor.fetchall()
        cursor.close()
        connection.close()

        # Gom nhóm theo order_id
        grouped_orders = {}
        for row in rows:
            order_id = row["order_id"]
            if order_id not in grouped_orders:
                grouped_orders[order_id] = {
                    "id": order_id,
                    "table_id": row["table_id"],
                    "status": row["status"],
                    "note": orderNote.get(order_id, "Không có ghi chú"),
                    "items": []
                }
            if row["food_name"]:  # Có thể có dòng NULL do LEFT JOIN
                grouped_orders[order_id]["items"].append({
                    "name": row["food_name"],
                    "quantity": row["quantity"]
                })

        # Chuyển thành list
        return jsonify({"orders": list(grouped_orders.values())}), 200

    except Exception as e:
        print(f"Error fetching orders: {e}")
        return jsonify({"message": f"Error: {e}"}), 500



# Tạo đơn (POST)
@order_bp.route('/create_order_post', methods=['POST'])
def create_order_post():
    try:
        data = request.form
        table_id = data.get('table_id')
        package_id = data.get('package_id')
        user_id = data.get('user_id')


        if not table_id:
            return jsonify({"message": "Missing table_id"}), 400
        if not user_id:
            return jsonify({"message": "Missing user_id"}), 400
        if not package_id:
            return jsonify({"message": "Missing package_id"}), 400
        
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM Orders")
        order_count = cursor.fetchone()[0] + 1
        order_id = f"ORD{order_count:03d}"

        created_at = datetime.datetime.now().strftime('%Y-%m-%d')

        # Lưu đơn hàng vào database
        cursor.execute(
            "INSERT INTO Orders (order_id, table_id, package_id, user_id, created_at, status) VALUES (%s, %s, %s, %s, %s, %s)",
            (order_id, table_id, package_id, user_id, created_at, "Đang chọn món")
        )
        connection.commit()

        cursor.close()
        connection.close()

        # Chuyển hướng sang trang Menu với order_id
        return redirect(url_for('order.menu', order_id=order_id))

    except mysql.connector.Error as db_err:
        print(f"Database error: {db_err}")
        return jsonify({"message": f"Database error: {db_err}"}), 500
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"message": f"Server error: {e}"}), 500

# Trang Menu
@order_bp.route('/menu/<order_id>', methods=['GET'])
def menu(order_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Lấy thông tin đơn hàng
    cursor.execute("SELECT table_id, package_id FROM Orders WHERE order_id = %s", (order_id,))
    order = cursor.fetchone()

    cursor.execute("SELECT price FROM Package WHERE package_id = %s", (order['package_id'],))
    package_result = cursor.fetchone()
    package_price = int(package_result["price"]) if package_result else 0

    
    


    if order['package_id'] == "4":
        cursor.execute("SELECT food_id, food_name, price, info, img_url, status FROM Menu WHERE status = 1")
        menu_items = cursor.fetchall()
        cursor.close()
          # Chuyển đổi thành danh sách từ điển
        package = [{"food_id": item['food_id'], "food_name": item["food_name"], "price": item["price"], 
                        "info": item["info"], "image_url": item["img_url"]} 
                       for item in menu_items]

        # Tách thành hai danh sách
        alacarte_items = [item for item in menu_items]
        return render_template('order_service/menu.html', order_id=order_id, alacarte_items=alacarte_items, order=order,package_price=0, type="1")
    
    elif order['package_id'] == "1" or order['package_id'] == "2" or order['package_id'] == "3":
            cursor.execute("""
                            SELECT Menu.food_id, food_name, price, info, img_url, status
                            FROM Menu join Package_Menu on menu.food_id = package_menu.food_id
                            WHERE status = 1 and package_id = %s""", (order['package_id'],)
                            )
            menu_items = cursor.fetchall()
            
            # Chuyển đổi thành danh sách từ điển
            package = [{"food_id": item['food_id'], "food_name": item["food_name"], "price": item["price"], 
                            "info": item["info"], "image_url": item["img_url"]} 
                        for item in menu_items]

            # Tách thành hai danh sách
            buffet_items = [item for item in package]


            # Món khác
            cursor.execute("""
                            SELECT DISTINCT Menu.food_id, food_name, price, info, img_url, status
                FROM Menu
                WHERE Menu.food_id NOT IN (
                    SELECT food_id 
                    FROM Package_Menu 
                    WHERE package_id = %s
                )""", (order['package_id'],))
            other_items = cursor.fetchall()
            cursor.close()
            # Chuyển đổi thành danh sách từ điển
            package = [{"food_id": item['food_id'], "food_name": item["food_name"], "price": item["price"], 
                            "info": item["info"], "image_url": item["img_url"]} 
                        for item in other_items]

            # Tách thành hai danh sách
            other_items = [item for item in package]

            return render_template('order_service/menu.html', order_id=order_id,other_items=other_items, buffet_items=buffet_items, order=order,package_price=package_price, type="2")
    elif order['package_id'] == "5" or order['package_id'] == "6" or order['package_id'] == "7":
            cursor.execute("""
                            SELECT Menu.food_id, food_name, price, info, img_url, status
                            FROM Menu join Package_Menu on menu.food_id = package_menu.food_id
                            WHERE package_id = %s""", (order['package_id'],))
            menu_items = cursor.fetchall()
            # Chuyển đổi thành danh sách từ điển
            package = [{"food_id": item['food_id'], "food_name": item["food_name"], "price": item["price"], 
                            "info": item["info"], "image_url": item["img_url"]} 
                        for item in menu_items]

            combo_items = [item for item in package]
            

            cursor.execute("""
                            SELECT DISTINCT Menu.food_id, food_name, price, info, img_url, status
                FROM Menu
                WHERE Menu.food_id NOT IN (
                    SELECT food_id 
                    FROM Package_Menu 
                    WHERE package_id = %s
                )""", (order['package_id'],))
            other_items = cursor.fetchall()
            cursor.close()
            # Chuyển đổi thành danh sách từ điển
            package = [{"food_id": item['food_id'], "food_name": item["food_name"], "price": item["price"], 
                            "info": item["info"], "image_url": item["img_url"]} 
                        for item in other_items]

            # Tách thành hai danh sách
            other_items = [item for item in package]
            cursor.execute("Select package_name from Package")
            package_name = cursor.fetchone()
            
            return render_template('order_service/menu.html', order_id=order_id, other_items=other_items,combo_items=combo_items, order=order,package_price=package_price,package_name=package_name, type="3")
        
 


    # Lấy danh sách món ăn theo package_id
    cursor.execute("""
        SELECT Menu.food_id, food_name, price, info, img_url, status
        FROM Menu join Package_Menu on menu.food_id = package_menu.food_id
        WHERE package_id = %s
    """, (order['package_id'],))
    menu_items = cursor.fetchall()
    cursor.close()
    connection.close()

    # Chuyển đổi thành danh sách từ điển
    package = [{"food_id": item['food_id'], "food_name": item["food_name"], "price": item["price"], 
                        "info": item["info"], "image_url": item["img_url"]} 
                       for item in menu_items]
    
    # Tách thành hai danh sách
    other_items = [item for item in menu_items if item["price"] > 0]

    return render_template('order_service/menu.html', order_id=order_id, other_items=other_items, order=order)

# Xác nhận đơn hàng và gửi vào bếp
@order_bp.route('/confirm_order', methods=['POST'])
def confirm_order():    
    try:
        data = request.form
        order_id = data.get('order_id')
        note = request.form.get("note", "").strip()
        orderNote[order_id] = note
        if not order_id:
            return jsonify({"message": "Missing order_id"}), 400

        connection = get_db_connection()
        cursor = connection.cursor()

        # Tạo order_item_id tự động
        cursor.execute("SELECT COUNT(*) FROM Order_Items")
        item_count = cursor.fetchone()[0] + 1

        # Lưu các món ăn được chọn với số lượng
        selected_items = False
        for key, quantity in data.items():
            if key.startswith('food_items[') and int(quantity) > 0:
                food_id = key.split('[')[1].rstrip(']')
                order_item_id = f"OIT{item_count:03d}"
                cursor.execute(
                    "INSERT INTO Order_Items (order_item_id, order_id, food_id, quantity) VALUES (%s, %s, %s, %s)",
                    (order_item_id, order_id, food_id, int(quantity))
                )
                item_count += 1
                selected_items = True

        if not selected_items:
            cursor.close()
            connection.close()
            return jsonify({"message": "No items selected"}), 400

        # Cập nhật trạng thái đơn hàng
        cursor.execute("UPDATE Orders SET status = %s WHERE order_id = %s", ("Đang chờ phục vụ", order_id))
        connection.commit()
        # Cập nhật trạng thái bàn
        cursor.execute("UPDATE Tables SET status = %s WHERE table_id = (SELECT table_id FROM Orders WHERE order_id = %s)", (1, order_id))
        connection.commit()
        # Chuẩn bị dữ liệu gửi qua WebSocket
        cursor.execute("SELECT table_id, package_id, user_id FROM Orders WHERE order_id = %s", (order_id,))
        order_data = cursor.fetchone()
        if not order_data:
            raise Exception("Order not found in database")

        order = {
            "id": order_id,
            "item": f"Package {order_data[1]}",
            "status": "Đang chờ phục vụ",
            "table_id": order_data[0],
            "note": orderNote[order_id],
        }

        # Gửi đơn hàng qua WebSocket
        try:
            from app import socketio
            socketio.emit('new_order', order, namespace='/')
        except Exception as e:
            print(f"WebSocket error: {e}")

        cursor.close()
        connection.close()

        # Trả về redirect_url với user_id từ Orders
        return jsonify({
            "message": "Order confirmed and sent to kitchen",
        })

    except mysql.connector.Error as db_err:
        print(f"Database error: {db_err}")
        return jsonify({"message": f"Database error: {db_err}"}), 500
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"message": f"Server error: {e}"}), 500

# Cập nhật trạng thái đơn hàng (dành cho Chef)
@order_bp.route('/update_status', methods=['POST'])
def update_order_status():
    data = request.get_json()
    order_id = data['order_id']
    new_status = data['status']

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE Orders SET status = %s WHERE order_id = %s", (new_status, order_id))
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "Status updated"}), 200

# Lấy thông tin đơn hàng
@order_bp.route('/get_order_info/<order_id>', methods=['GET'])
def get_order_info(order_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Lấy thông tin đơn hàng
    cursor.execute("SELECT table_id, package_id, user_id FROM Orders WHERE order_id = %s", (order_id,))
    order = cursor.fetchone()

    # Lấy danh sách món ăn trong đơn hàng
    cursor.execute("""
        SELECT Order_Items.food_id, Menu.food_name, Order_Items.quantity
        FROM Order_Items
        JOIN Menu ON Order_Items.food_id = Menu.food_id
        WHERE Order_Items.order_id = %s
    """, (order_id,))
    items = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify({"order": order, "items": items}), 200


# Lấy thông tin thanh toán
@order_bp.route('/payment_data/<order_id>', methods=['GET'])
def get_payment_data(order_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Lấy thông tin đơn hàng và package_id
        cursor.execute("""
            SELECT o.order_id, o.table_id, p.package_id, p.package_name, p.price AS package_price
            FROM Orders o
            JOIN Package p ON o.package_id = p.package_id
            WHERE o.order_id = %s
        """, (order_id,))
        order = cursor.fetchone()

        if not order:
            cursor.close()
            connection.close()
            return jsonify({"message": "Order not found"}), 404

        # Lấy danh sách món trong đơn hàng, bao gồm giá từ bảng Menu
        cursor.execute("""
            SELECT oi.food_id, m.food_name, oi.quantity, m.price
            FROM Order_Items oi
            JOIN Menu m ON oi.food_id = m.food_id
            WHERE oi.order_id = %s
        """, (order_id,))
        order_items = cursor.fetchall()

        # Xác định loại gói dựa trên package_id
        package_id = int(order["package_id"])
        if package_id == 4:
            package_type = "alacarte"
        elif package_id in [1, 2, 3]:
            package_type = "buffet"
        elif package_id in [5, 6, 7]:
            package_type = "combo"
        else:
            package_type = "unknown"

        # Tính total_amount dựa trên loại gói
        total_amount = 0

        if package_type == "alacarte":
            # Trường hợp A-la-carte: Tổng tiền = Giá mỗi món × Số lượng
            for item in order_items:
                total_amount += item["price"] * item["quantity"]
        elif package_type in ["buffet", "combo"]:
            # Trường hợp Buffet hoặc Combo: Tổng tiền = Giá gói + (Giá món gọi thêm × Số lượng)
            package_price = order.get("package_price", 0)  # Giá của Buffet/Combo
            total_amount += package_price  # Cộng giá gói vào tổng tiền

            # Kiểm tra từng món trong Order_Items để xác định món gọi thêm
            for item in order_items:
                # Kiểm tra xem món có thuộc gói hay không
                cursor.execute("""
                    SELECT COUNT(*) AS count
                    FROM Package_Menu pm
                    WHERE pm.package_id = %s AND pm.food_id = %s
                """, (package_id, item["food_id"]))
                result = cursor.fetchone()
                is_in_package = result["count"] > 0

                # Nếu món không thuộc gói, đó là món gọi thêm (tính phí riêng)
                if not is_in_package:
                    total_amount += item["price"] * item["quantity"]

                # Thêm thuộc tính is_extra_cost vào item để trả về cho client
                item["is_extra_cost"] = not is_in_package
        else:
            # Trường hợp package_id không xác định
            cursor.close()
            connection.close()
            return jsonify({"message": f"Invalid package_id: {package_id}"}), 400

        cursor.close()
        connection.close()

        # Chuẩn bị dữ liệu trả về
        payment_data = {
            "order_id": order["order_id"],
            "table_id": order["table_id"],
            "total_amount": total_amount,  # total_amount được tính động
            "package_name": order["package_name"],
            "package_type": package_type,  # Trả về loại gói (alacarte, buffet, combo)
            "order_items": [
                {
                    "food_id": item["food_id"],
                    "food_name": item["food_name"],
                    "quantity": item["quantity"],
                    "price": item["price"],
                    "is_extra_cost": item.get("is_extra_cost", True)  # Mặc định là True cho A-la-carte
                } for item in order_items
            ]
        }
        # Gửi dữ liệu thanh toán qua WebSocket
        try:
            from app import socketio
            socketio.emit('payment_data', payment_data, namespace='/')

        except Exception as e:
            print(f"WebSocket error: {e}")
        # Trả về dữ liệu thanh toán

        return jsonify(payment_data), 200

    except mysql.connector.Error as db_err:
        print(f"Database error: {db_err}")
        return jsonify({"message": f"Database error: {db_err}"}), 500
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"message": f"Server error: {e}"}), 500
    
@order_bp.route('/get_orders_payment', methods=['GET'])
def get_orders_payment():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # ✅ Truy vấn đơn hàng có trạng thái "Đang chờ thanh toán"
        cursor.execute("""
            SELECT o.order_id, o.table_id, o.status, i.invoice_id
            FROM Orders o
            LEFT JOIN Payment_Services.Invoices i ON o.order_id = i.order_id
            WHERE o.status = 'Đang chờ thanh toán'
        """)
        orders = cursor.fetchall()

        if not orders:
            cursor.close()
            connection.close()
            return jsonify([]), 200

        # ✅ Gắn danh sách món ăn cho từng đơn hàng
        for order in orders:
            cursor.execute("""
                SELECT oi.food_id, m.food_name AS name, oi.quantity
                FROM Order_Items oi
                JOIN Menu m ON oi.food_id = m.food_id
                WHERE oi.order_id = %s
            """, (order['order_id'],))
            items = cursor.fetchall()
            order['items'] = items
        cursor.close()
        connection.close()
        
        return jsonify(orders), 200

    except mysql.connector.Error as db_err:
        print(f"Database error: {db_err}")
        return jsonify({"message": f"Database error: {db_err}"}), 500
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"message": f"Server error: {e}"}), 500
@order_bp.route('/order_status/<order_id>', methods=['GET'])
def check_order_status(order_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT status FROM Orders WHERE order_id = %s", (order_id,))
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        if result:
            return jsonify({"status": result["status"]}), 200
        else:
            return jsonify({"message": "Order not found"}), 404

    except Exception as e:
        return jsonify({"message": f"Server error: {e}"}), 500
