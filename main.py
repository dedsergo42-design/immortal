import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO
import base64
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

last_click = {"x": None, "y": None, "time": 0}

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>System Panel</title>
    <style>
        body { background-color: #111; color: #eee; font-family: 'Segoe UI', sans-serif; text-align: center; margin: 0; padding: 20px; }
        h1 { color: #ff3333; margin-bottom: 5px; }
        .container { max-width: 1200px; margin: 0 auto; }
        #screen { max-width: 100%; max-height: 70vh; border: 2px solid #333; border-radius: 8px; cursor: crosshair; background: #000; }
        .controls { margin: 15px 0; }
        button { background: #333; color: white; border: 1px solid #555; padding: 10px 20px; cursor: pointer; border-radius: 4px; font-size: 16px; margin: 0 5px; }
        button:hover { background: #555; }
        button.active { background: #ff3333; border-color: #ff3333; }
        .status { margin-top: 10px; color: #888; font-size: 14px; }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
</head>
<body>
    <div class="container">
        <h1>REMOTE CONTROL</h1>
        <div class="status" id="status">Waiting for connection...</div>
        
        <div class="controls">
            <button id="btnScreen" onclick="setMode('screen')">View Screen</button>
            <button id="btnCamera" onclick="setMode('camera')">View Camera</button>
        </div>

        <img id="screen" src="" alt="No signal">
    </div>

    <script>
        var socket = io();
        var currentMode = 'screen';
        var mouseControlEnabled = false;
        
        document.getElementById('btnScreen').classList.add('active');

        socket.on('frame', function(data) {
            var img = document.getElementById('screen');
            img.src = "data:image/jpeg;base64," + data;
            document.getElementById('status').innerText = "Receiving frames (" + currentMode + ")";
        });

        function setMode(mode) {
            currentMode = mode;
            document.getElementById('btnScreen').classList.toggle('active', mode === 'screen');
            document.getElementById('btnCamera').classList.toggle('active', mode === 'camera');
            socket.emit('set_mode', {mode: mode});
        }

        document.getElementById('screen').onclick = function(e) {
            var rect = this.getBoundingClientRect();
            var x = (e.clientX - rect.left) / rect.width;
            var y = (e.clientY - rect.top) / rect.height;
            socket.emit('mouse_click', {x: x, y: y});
            document.getElementById('status').innerText = "Click sent: " + Math.round(x*100) + "%, " + Math.round(y*100) + "%";
        };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/api/frame', methods=['POST'])
def api_frame():
    data = request.json
    if not data or 'image' not in data:
        return jsonify({"status": "error"}), 400
    socketio.emit('frame', data['image'])
    return jsonify({"status": "ok"})

@app.route('/api/get_mode', methods=['GET'])
def get_mode():
    # По умолчанию скриншот. Можно расширить для возврата режима от браузера.
    return jsonify({"mode": "screen"})

@app.route('/api/get_click', methods=['GET'])
def get_click():
    global last_click
    if last_click['x'] is not None and (time.time() - last_click['time'] < 2):
        res = last_click.copy()
        last_click = {"x": None, "y": None, "time": 0}
        return jsonify(res)
    return jsonify({"x": None, "y": None})

@socketio.on('mouse_click')
def handle_click(data):
    global last_click
    last_click = {"x": data['x'], "y": data['y'], "time": time.time()}
    print(f"Click queued: {last_click}")

@socketio.on('set_mode')
def handle_mode(data):
    socketio.emit('mode_changed', data['mode'])

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)
