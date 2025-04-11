from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, Blueprint, render_template
import mysql.connector
from flask_cors import CORS

user_bp = Blueprint("user", __name__)
CORS(user_bp)

# Kết nối database
# def get_db_connection():
#     return mysql.connector.connect(
#         host="han312.mysql.pythonanywhere-services.com",
#         user="han312",
#         password="SOA2025@",
#         database="han312$User_Services"
#     )
# def get_db_connection_order():
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
        database="User_Services"
    )
def get_db_connection_order():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="Order_Services"
    )
def get_db_connection_payment():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="Payment_Services"
    )
# Hiển thị trang đăng nhập (GET)
@user_bp.route('/login', methods=['GET'])
def login_page():
    return render_template("login.html")

# Đăng nhập
@user_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return jsonify({"success": False, "message": "Thiếu tên đăng nhập hoặc mật khẩu!"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Users WHERE user_name = %s AND password = %s", (username, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()


    if user:
        role_prefix = user['role_id'][0]
        if role_prefix == 'A':
            return redirect(url_for('user.admin', user_id=user['user_id']))
        elif role_prefix == 'C':
            return redirect(url_for('user.chef', user_id=user['user_id']))
        elif role_prefix == 'W':
            return redirect(url_for('user.waiter', user_id=user['user_id']))
        else:
            return "1"
            flash("Invalid role, please contact the administrator.", "danger")
            return redirect(url_for('user.login'))
    else:
        error_message = "Sai tài khoản hoặc mật khẩu, vui lòng thử lại!"
        return render_template('login.html', error_message=error_message)

# Trang chủ cho từng vai trò
# Nhân viên quản lý
@user_bp.route('/admin/<user_id>')
def admin(user_id):
    user = get_profile(user_id)

    if not user:
        return "User not found", 404
    
    # --- Lấy đơn hàng hôm nay & số món ---
    conn_order = get_db_connection_order()
    cursor_order = conn_order.cursor()
    cursor_order.execute("SELECT COUNT(*) FROM Orders WHERE DATE(created_at) = CURDATE()")
    today_orders = cursor_order.fetchone()[0]

    cursor_order.execute("SELECT COUNT(*) FROM Menu")
    food_count = cursor_order.fetchone()[0]
    cursor_order.close()
    conn_order.close()

    # --- Lấy doanh thu tháng này ---
    conn_pay = get_db_connection_payment()
    cursor_pay = conn_pay.cursor(dictionary=True)
    cursor_pay.execute("""
        SELECT SUM(total_amount) AS monthly_revenue
        FROM Invoices
        WHERE MONTH(issued_at) = MONTH(CURDATE())
          AND YEAR(issued_at) = YEAR(CURDATE())
    """)
    result = cursor_pay.fetchone()
    monthly_revenue = result['monthly_revenue'] if result['monthly_revenue'] else 0
    cursor_pay.close()
    conn_pay.close()

    # --- Lấy số người dùng ---
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS total_users FROM Users")
    user_count = cursor.fetchone()['total_users']
    cursor.close()
    conn.close()

    # --- Render ---
    return render_template('user_service/admin_home.html',
                           user=user,
                           today_orders_count=today_orders,
                           user_count=user_count,
                           monthly_revenue=monthly_revenue,
                           food_count=food_count)
# Nhân viên bếp
@user_bp.route('/chef/<user_id>')
def chef(user_id):
    user = get_profile(user_id)  # Lấy tên người dùng từ bảng User_Profile

    if not user:
        return "User not found", 404

    return render_template('user_service/chef_home.html', user=user)

# Nhân viên phục vụ
@user_bp.route('/waiter/<user_id>')
def waiter(user_id):
    user = get_profile(user_id)
    if not user:
        return "User not found", 404

    # Kết nối database Order_Services để lấy table_numbers và package_ids
    conn = get_db_connection_order()
    cursor = conn.cursor()

    # Lấy danh sách số bàn duy nhất từ Orders
    cursor.execute("SELECT table_id, status FROM Tables")
    tables = cursor.fetchall()

    if not tables:  # Nếu chưa có đơn nào, tạo danh sách mặc định
        tables = list(range(1, 16))

    # Lấy danh sách package_id từ Menu
    cursor.execute("SELECT package_id, package_name FROM package")
    package = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('user_service/waiter_home.html', user=user, tables=tables,package=package)

# Đăng xuất
@user_bp.route('/logout')
def logout():
    return render_template('login.html')

# Xem thông tin cá nhân
# Hàm lấy thông tin
def get_profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM User_Profile WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

@user_bp.route('/profile/<user_id>')
def profile(user_id):
    user = get_profile(user_id)
    return render_template('user_service/profile.html', user=user)



@user_bp.route('/chef_menu/<user_id>', methods=['GET'])
def chef_menu(user_id):
    user = get_profile(user_id)
    connection = get_db_connection_order()
    cursor = connection.cursor(dictionary=True)

    # Lấy danh sách món ăn và trạng thái
    cursor.execute("SELECT food_id, food_name, status FROM Menu")
    menu_items = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('user_service/chef_menu.html', menu_items=menu_items,user=user)
@user_bp.route('/chef/update_status', methods=['POST'])
def update_menu_status():
    try:
        food_id = request.form.get('food_id')
        new_status = request.form.get('status')

        # Kiểm tra input hợp lệ
        if not food_id or new_status not in ['0', '1']:
            return jsonify({"message": "Invalid request parameters"}), 400
        
        new_status = int(new_status)  # Chuyển đổi về số nguyên

        connection = get_db_connection_order()
        cursor = connection.cursor()

        # Kiểm tra xem món ăn có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM Menu WHERE food_id = %s", (food_id,))
        if cursor.fetchone()[0] == 0:
            cursor.close()
            connection.close()
            return jsonify({"message": "Food item not found"}), 404

        # Cập nhật trạng thái món ăn trong database
        cursor.execute("UPDATE Menu SET status = %s WHERE food_id = %s", (new_status, food_id))
        connection.commit()

        # Đóng kết nối database
        cursor.close()
        connection.close()

        return jsonify({
            "message": "Status updated successfully",
            "food_id": food_id,
            "new_status": new_status
        }), 200

    except mysql.connector.Error as db_err:
        return jsonify({"message": f"Database error: {db_err}"}), 500
    except Exception as e:
        return jsonify({"message": f"Server error: {e}"}), 500

# Thanh toán cho khách hàng
@user_bp.route('/payment/<user_id>', methods=['GET'])
def payment(user_id):
    user = get_profile(user_id)
    if not user:
        return "User not found", 404
  
    return render_template('/payment_service/payment.html',user=user)