import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template_string, request
from flask_socketio import SocketIO
import base64

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>System Panel</title>
    <style>
        body { background-color: #111; color: #eee; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; margin: 0; padding: 20px; }
        h1 { color: #ff3333; margin-bottom: 5px; }
        .container { max-width: 1200px; margin: 0 auto; }
        #screen { max-width: 100%; max-height: 75vh; border: 2px solid #333; border-radius: 8px; cursor: crosshair; background: #000; }
        .controls { margin: 15px 0; }
        button { background: #333; color: white; border: 1px solid #555; padding: 10px 20px; cursor: pointer; border-radius: 4px; font-size: 16px; }
        button:hover { background: #555; }
        .status { margin-top: 10px; color: #888; font-size: 14px; }
        .click-indicator { position: absolute; width: 20px; height: 20px; border: 2px solid red; border-radius: 50%; pointer-events: none; transform: translate(-50%, -50%); display: none; }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
</head>
<body>
    <div class="container">
        <h1>REMOTE CONTROL</h1>
        <div class="status" id="status">Waiting for frames...</div>
        
        <div class="controls">
            <button onclick="sendClickMode()">Toggle Mouse Control</button>
        </div>

        <img id="screen" src="" alt="No signal">
        <div class="click-indicator" id="clicker"></div>
    </div>

    <script>
        var socket = io();
        var mouseControlEnabled = false;
        var lastFrameTime = Date.now();
        
        socket.on('frame', function(data) {
            var img = document.getElementById('screen');
            img.src = "data:image/jpeg;base64," + data;
            lastFrameTime = Date.now();
            document.getElementById('status').innerText = "Receiving frames...";
        });

        function sendClickMode() {
            mouseControlEnabled = !mouseControlEnabled;
            document.getElementById('status').innerText = mouseControlEnabled ? "Mouse Control ENABLED" : "Mouse Control DISABLED";
        }

        document.getElementById('screen').onclick = function(e) {
            if (!mouseControlEnabled) return;
            var rect = this.getBoundingClientRect();
            var x = (e.clientX - rect.left) / rect.width;
            var y = (e.clientY - rect.top) / rect.height;
            
            var clicker = document.getElementById('clicker');
            clicker.style.left = e.clientX + 'px';
            clicker.style.top = e.clientY + 'px';
            clicker.style.display = 'block';
            setTimeout(() => { clicker.style.display = 'none'; }, 300);

            socket.emit('mouse_click', {x: x, y: y});
        };
        
        setInterval(function() {
            if (Date.now() - lastFrameTime > 5000) {
                document.getElementById('status').innerText = "Connection lost or PC offline";
            }
        }, 1000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

# API для приема кадров от батника/скрипта
@app.route('/api/frame', methods=['POST'])
def api_frame():
    data = request.json
    if not data or 'image' not in data:
        return {"status": "error", "message": "No image"}, 400
    
    # Отправляем кадр всем подключенным браузерам
    socketio.emit('frame', data['image'])
    return {"status": "ok"}

# Обработка кликов мыши (отправка команд обратно на ПК)
@socketio.on('mouse_click')
def handle_click(data):
    # На Render мы не можем управлять мышью ПК напрямую.
    # Для этого нужен постоянный WebSocket-канал с ПК.
    # Но так как мы используем HTTP POST для кадров, 
    # самый простой способ — хранить последний клик и заставлять ПК опрашивать сервер.
    # (В данной архитектуре мы просто транслируем клик обратно)
    socketio.emit('remote_click', data)
    print(f"Mouse click received: {data}")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)
