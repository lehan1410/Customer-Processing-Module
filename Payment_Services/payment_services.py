from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# Kết nối DB với Connection Pool
def get_payment_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="payment_services",
            pool_name="mypool",
            pool_size=5
        )
        return conn
    except Error as e:
        print(f"Lỗi kết nối MySQL: {e}")
        return None

# API lấy danh sách hóa đơn
@app.route('/invoices', methods=['GET'])
def get_invoices():
    conn = get_payment_db()
    if conn is None:
        return jsonify({"error": "Không thể kết nối DB"}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM invoices")
    invoices = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(invoices)


# Các chức năng thanh toán
# Xem lịch sử phiếu tính tiền
@app.route('/view_invoices')
def view_invoices():
    response = requests.get(f"{PAYMENT_SERVICE_URL}/invoices")
    invoices = response.json()
    return render_template('invoices.html', invoices=invoices)

# Tổng hợp phiếu tính tiền
@app.route('/invoices_summary')
def invoices_summary():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM invoices")
    billing_records = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('invoices_summary.html')


if __name__ == '__main__':
    app.run(port=5001, debug=True)
