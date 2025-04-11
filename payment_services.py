import datetime
from flask import Flask, render_template, request, jsonify, Blueprint
import mysql.connector
from mysql.connector import Error
from flask_cors import CORS

payment_bp = Blueprint("payment", __name__)
CORS(payment_bp)

def get_payment_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="Payment_Services"
    )
def get_user_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="User_Services"
    )
def get_order_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="Order_Services"
    )


# Xử lý thanh toán (POST)
@payment_bp.route('/process_payment', methods=['POST'])
def process_payment():
    data = request.get_json()
    order_id = data.get('order_id')
    payment_method = data.get('payment_method')
    total_amount = data.get('total_amount')

    if not all([order_id, payment_method, total_amount]):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_payment_db()
    if conn is None:
        return jsonify({"error": "Không thể kết nối DB"}), 500

    cursor = conn.cursor()

    try:
        # Tạo payment_id tự động
        cursor.execute("SELECT COUNT(*) FROM Payments")
        payment_count = cursor.fetchone()[0] + 1
        payment_id = f"PAY{payment_count:03d}"

        # Lưu vào bảng Payments
        cursor.execute("""
            INSERT INTO Payments (payment_id, order_id, method, amount)
            VALUES (%s, %s, %s, %s)
        """, (payment_id, order_id, payment_method_to_int(payment_method), total_amount))

        # Tạo invoice_id tự động
        cursor.execute("SELECT COUNT(*) FROM Invoices")
        invoice_count = cursor.fetchone()[0] + 1
        invoice_id = f"INV{invoice_count:03d}"

        # Lưu vào bảng Invoices
        cursor.execute("""
            INSERT INTO Invoices (invoice_id, order_id, payment_id, total_amount)
            VALUES (%s, %s, %s, %s, %s)
        """, (invoice_id, order_id, payment_id, total_amount, ))

        # Cập nhật trạng thái đơn hàng trong Order_Services
        conn_order = get_order_db()
        cursor_order = conn_order.cursor()
        cursor_order.execute("UPDATE Orders SET status = 'paid' WHERE order_id = %s", (order_id,))
        
        # Cập nhật trạng thái bàn
        cursor_order.execute("""
            UPDATE Tables SET status = 0
            WHERE table_id = (SELECT table_id FROM Orders WHERE order_id = %s)
        """, (order_id,))

        conn_order.commit()
        cursor_order.close()
        conn_order.close()

        conn.commit()
        return jsonify({"message": "Payment processed successfully", "order_id": order_id}), 200

    except Error as e:
        conn.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    finally:
        cursor.close()
        conn.close()

def payment_method_to_int(method):
    method_map = {'cash': 1, 'card': 2, 'mobile': 3}
    return method_map.get(method, 0)  # Default to 0 if method is invalid


@payment_bp.route('/create_invoice', methods=['POST'])
def create_invoice():
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        table_id = data.get('table_id')
        total_amount = float(data.get('total_amount'))

        if not all([order_id, table_id, total_amount]):
            return jsonify({"message": "Thiếu thông tin bắt buộc"}), 400

        connection = get_payment_db()
        cursor = connection.cursor()

        # Tạo invoice_id
        cursor.execute("SELECT COUNT(*) FROM Invoices")
        invoice_count = cursor.fetchone()[0] + 1
        invoice_id = f"INV{invoice_count:03d}"

        # Tạo bản ghi trong bảng Invoices
        issued_at = datetime.datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT INTO Invoices (invoice_id, order_id, table_id, total_amount, issued_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (invoice_id, order_id, table_id, total_amount, issued_at))

        # Cập nhật trạng thái đơn hàng trong Order_Services
        conn_order = get_order_db()
        cursor_order = conn_order.cursor()
        cursor_order.execute("UPDATE Orders SET status = %s WHERE order_id = %s", ("Đang chờ thanh toán", order_id))
        conn_order.commit()
        cursor_order.close()
        conn_order.close()

    
        # Chuẩn bị dữ liệu gửi qua websocket
        invoice_data = {
            "invoice_id": invoice_id,
            "order_id": order_id,
            "table_id": table_id,
            "total_amount": total_amount,
            "issued_at": issued_at
        }
        # Gửi dữ liệu qua websocket
        from app import socketio
        socketio.emit('send_invoice', invoice_data, namespace='/')
        connection.commit()
        cursor.close()
        connection.close()

        return jsonify(invoice_data), 200

    except mysql.connector.Error as db_err:
        print(f"Database error: {db_err}")
        return jsonify({"message": f"Database error: {db_err}"}), 500
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"message": f"Server error: {e}"}), 500


# Endpoint tạo payment
@payment_bp.route('/create_payment', methods=['POST'])
def create_payment():
    try:
        data = request.get_json()
        invoice_id = data.get('invoice_id')
        payment_method = data.get('payment_method')
        amount = float(data.get('amount'))

        if not all([invoice_id, payment_method, amount]):
            return jsonify({"message": "Thiếu thông tin bắt buộc"}), 400

        connection = get_payment_db()
        cursor = connection.cursor()

        # Kiểm tra xem invoice_id có tồn tại không
        cursor.execute("SELECT * FROM Invoices WHERE invoice_id = %s", (invoice_id,))
        invoice = cursor.fetchone()
        if not invoice:
            cursor.close()
            connection.close()
            return jsonify({"message": "Hóa đơn không tồn tại",
                            "invoice_id": invoice_id
                            }), 404

        # Tạo payment_id tự động
        cursor.execute("SELECT COUNT(*) FROM Payments")
        payment_count = cursor.fetchone()[0] + 1
        payment_id = f"PAY{payment_count:03d}"

        # Tạo bản ghi trong bảng Payments
        paid_at = datetime.datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT INTO Payments (payment_id, invoice_id, payment_method, amount, paid_at, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (payment_id, invoice_id, payment_method, amount, paid_at, 1))

        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({
            "message": "Payment created successfully",
            "payment_id": payment_id
        }), 200

    except mysql.connector.Error as db_err:
        print(f"Database error: {db_err}")
        return jsonify({"message": f"Database error: {db_err}"}), 500
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"message": f"Server error: {e}"}), 500
    

# Endpoint lấy chi tiết hóa đơn
@payment_bp.route('/invoice/<invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    try:
        connection = get_payment_db()
        cursor = connection.cursor(dictionary=True)

        # Lấy thông tin hóa đơn
        cursor.execute("""
            SELECT invoice_id, order_id, table_id, total_amount, issued_at
            FROM Invoices
            WHERE invoice_id = %s
        """, (invoice_id,))
        invoice = cursor.fetchone()

        if not invoice:
            cursor.close()
            connection.close()
            return jsonify({"message": "Hóa đơn không tồn tại"}), 404

        cursor.close()
        connection.close()
        return jsonify(invoice), 200

    except mysql.connector.Error as db_err:
        print(f"Database error: {db_err}")
        return jsonify({"message": f"Database error: {db_err}"}), 500
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"message": f"Server error: {e}"}), 500

# Xác nhận thanh toán
@payment_bp.route('/confirm_payment/<invoice_id>', methods=['POST'])
def confirm_payment(invoice_id):
    try:
        connection = get_payment_db()
        cursor = connection.cursor()

        # Kiểm tra invoice tồn tại
        cursor.execute("SELECT * FROM Payments WHERE invoice_id = %s", (invoice_id,))
        payment = cursor.fetchone()
        if not payment:
            return jsonify({"message": "Không tìm thấy hóa đơn để xác nhận"}), 404

        # Cập nhật trạng thái thanh toán (status = 1)
        cursor.execute("""
            UPDATE Payments SET status = 1 WHERE invoice_id = %s
        """, (invoice_id,))

        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({"message": "Payment confirmed successfully"}), 200

    except mysql.connector.Error as db_err:
        print(f"Database error: {db_err}")
        return jsonify({"message": f"Database error: {db_err}"}), 500
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"message": f"Server error: {e}"}), 500

# Cập nhật trạng thái thanh toán
@payment_bp.route('/update_payment_status/<payment_id>', methods=['POST'])
def update_payment_status(payment_id):
    try:
        data = request.get_json()
        status = data.get('status')

        if status not in [0, 1]:
            return jsonify({"message": "Invalid status"}), 400

        # 1. Cập nhật bảng Payments (payment_service DB)
        payment_conn = get_payment_db()
        payment_cursor = payment_conn.cursor()

        payment_cursor.execute("""
            UPDATE Payments SET status = %s WHERE payment_id = %s
        """, (status, payment_id))
        payment_conn.commit()

        # Lấy order_id, table_id từ payment
        payment_cursor.execute("""
            SELECT order_id, table_id FROM Invoices join Payments
            on Invoices.invoice_id = Payments.invoice_id
            WHERE payment_id = %s
        """, (payment_id,))
        payment_data = payment_cursor.fetchone()

        if not payment_data:
            return jsonify({"message": "Không tìm thấy thanh toán"}), 404

        order_id, table_id = payment_data
        payment_cursor.close()
        payment_conn.close()

        # 2. Cập nhật trạng thái đơn hàng (order_service DB)
        order_conn = get_order_db()
        order_cursor = order_conn.cursor()
    
        # Cập nhật trạng thái đơn hàng
        order_cursor.execute("""
            UPDATE Orders SET status = 'Đã thanh toán' WHERE order_id = %s LiMIT 1
        """, (order_id,))
        order_conn.commit()

        # # 3. Cập nhật trạng thái bàn
        order_cursor.execute("""
            UPDATE Tables SET status = 0
            WHERE table_id = (SELECT table_id FROM Orders WHERE status = 'Đã thanh toán' LIMIT 1) LIMIT 1
        """,)
        order_conn.commit()

        order_cursor.close()    
        order_conn.close()
     

        return jsonify({"message": "Cập nhật trạng thái thanh toán thành công"}), 200

    except mysql.connector.Error as db_err:
        print(f"Database error: {db_err}")
        return jsonify({"message": f"Database error: {db_err}"}), 500
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"message": f"Server error: {e}"}), 500
