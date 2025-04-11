from flask import Flask, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from user_services import user_bp
from payment_services import payment_bp
from Order_Service import order_bp
from shared import orderNote


app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # Kích hoạt WebSocket

# Đăng ký các Blueprint
app.register_blueprint(user_bp, url_prefix="/user")
app.register_blueprint(payment_bp, url_prefix="/payment")
app.register_blueprint(order_bp, url_prefix="/order")

# Route gốc
@app.route('/')
def home():
    return render_template('login.html')

# Sự kiện WebSocket
@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

@socketio.on('message')
def handle_message(msg):
    print(f"Received message: {msg}")
    socketio.send(f"Server received: {msg}")  # Phản hồi lại client

@socketio.on('new_order')
def handle_new_order(order):
    order_id = order.get('order_id')
    note = order.get('note', '')
    # Lưu ghi chú tạm vào bộ nhớ
    orderNote[order_id] = note
    emit('new_order', order, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
