from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import mysql.connector
import bcrypt
import requests

PAYMENT_SERVICE_URL = "http://localhost:5001"

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Để sử dụng session

# Kết nối database
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="users_services"
    )

# Hiển thị trang đăng nhập (GET)
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

# Xử lý đăng nhập (POST)
@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']  # Mật khẩu nhập từ form

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_name = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['user'] = user
            flash("Login successful!", "success")

            # Điều hướng dựa trên role_id bằng cách lấy ký tự đầu tiên
            role_prefix = user['role_id'][0]  # Lấy ký tự đầu tiên của role_id

            if role_prefix == 'A':
                return redirect(url_for('admin_home'))
            elif role_prefix == 'C':
                return redirect(url_for('chef_home'))
            elif role_prefix == 'W':
                return redirect(url_for('waiter_home'))
            else:
                flash("Invalid role, please contact the administrator.", "danger")
                return redirect(url_for('login'))
        else:
            error_message = "Sai tài khoản hoặc mật khẩu, vui lòng thử lại!"  
            return render_template('login.html', error_message=error_message)
    return render_template('login.html')

# Trang chủ cho từng vai trò
@app.route('/admin_home')
def admin_home():
    user = session.get('user') 
    if user:
        return render_template('admin_home.html', user=user)
    return redirect(url_for('login'))

@app.route('/chef_home')
def chef_home():
    user = session.get('user')
    if user:
        return render_template('chef_home.html', user=user)
    return redirect(url_for('login'))

@app.route('/waiter_home')
def waiter_home():
    user = session.get('user')
    if user:
        return render_template('waiter_home.html', user=user)
    return redirect(url_for('login'))

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)
    flash("You have been logged out!")
    return redirect(url_for('login')) 

# Xem thông tin người dùng cho admin
@app.route('/user')
def user():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user_profile")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(users) 

# Xem thông tin cá nhân
@app.route('/profile/<user_id>')
def profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user_profile WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('profile.html', user=user)

# Các chức năng thanh toán
# Xem lịch sử phiếu tính tiền
@app.route('/view_invoices')
def view_invoices():
    response = requests.get(f"{PAYMENT_SERVICE_URL}/invoices_summary")
    invoices = response.json()
    return render_template('invoices_summary.html', invoices=invoices)

# Tổng hợp phiếu tính tiền
@app.route('/invoices_summary')
def invoices_summary():
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM invoices")
    billing_records = cursor.fetchall()
    cursor.close()
    conn.close()
    print("Hello")
    # return render_template('invoices_summary.html')


if __name__ == '__main__':
    app.run(debug=True)
