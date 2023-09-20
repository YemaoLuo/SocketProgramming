import gzip
import threading
import time
from io import BytesIO

import cv2
import numpy as np
import pyautogui
from PIL import ImageGrab, UnidentifiedImageError
from flask import Flask, render_template, request
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app)
connected_users = []
screen_width, screen_height = pyautogui.size()


def emit_screen_capture():
    while True:
        try:
            start_time = time.time()
            screen_image = capture_screen()
            _, img_encoded = cv2.imencode('.jpg', screen_image)
            compressed_image_bytes = compress_bytes(img_encoded.tobytes())

            socketio.emit('refresh_frame', compressed_image_bytes)

            elapsed_time = time.time() - start_time
            delay = max(0, 1 / 30 - elapsed_time)
            time.sleep(delay)
        except UnidentifiedImageError:
            break


def compress_bytes(data):
    with BytesIO() as buf:
        with gzip.GzipFile(fileobj=buf, mode='wb') as f:
            f.write(data)
        compressed_data = buf.getvalue()
    return compressed_data


def capture_screen():
    img = ImageGrab.grab(bbox=(0, 0, screen_width, screen_height))
    img = img.resize((1920, 1080))
    img = np.array(img)
    resized_array = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    return resized_array


def emit_user_count():
    while True:
        socketio.emit('refresh_user_count', len(connected_users))
        time.sleep(5)


@socketio.on('connect')
def handle_connect():
    client_ip = request.remote_addr
    connected_users.append(client_ip)
    print(f'WebSocket connection established from {client_ip}. Online user count: {len(connected_users)}.')


@socketio.on('disconnect')
def handle_disconnect():
    client_ip = request.remote_addr
    connected_users.remove(client_ip)
    print(f'WebSocket connection disconnect from {client_ip}. Online user count: {len(connected_users)}.')


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    emit_screen_capture_thread = threading.Thread(target=emit_screen_capture)
    emit_screen_capture_thread.daemon = True
    emit_screen_capture_thread.start()
    emit_user_count_thread = threading.Thread(target=emit_user_count)
    emit_user_count_thread.daemon = True
    emit_user_count_thread.start()
    app.run(host='0.0.0.0', port='8080', debug=True)
