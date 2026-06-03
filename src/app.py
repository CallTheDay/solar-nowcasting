from flask import Flask, Response, jsonify
import os
import json
app = Flask(__name__)
CAPTURE_FOLDER = "/home/pi/solar-nowcasting/data/sky captures"
RESULT_FOLDER = "/home/pi/solar-nowcasting/data/detection results"
STATS_FILE = "/home/pi/solar-nowcasting/data/stats.json"
@app.route("/")
def index():
    return """
    <html>
    <head>
        <title>Solar Nowcasting Dashboard</title>
        <style>
            body { font-family: 'Segoe UI', Arial; text-align: center; background: #0f0f0f; color: #e0e0e0; margin: 0; padding: 2vw; }
            .container { max-width: 95vw; margin: auto; }
            .image-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; width: 100%; box-sizing: border-box; }
            .img-container { width: 100%; }
            img { width: 100%; height: auto; border-radius: 8px; border: 2px solid #333; box-shadow: 0 4px 15px rgba(0,0,0,0.5); display: block; }
            h1 { font-size: calc(16px + 1.5vw); margin-bottom: 2vh; }
            .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 3vh; }
            .stat-card { background: #1a1a1a; padding: 1.5vh 1vw; border-radius: 8px; border: 1px solid #333; display: flex; flex-direction: column; justify-content: center; }
            .label { color: #888; font-size: calc(10px + 0.4vw); text-transform: uppercase; margin: 0; }
            .value { font-size: calc(14px + 0.6vw); font-weight: bold; margin-top: 5px; color: #00ff99; margin-bottom: 0; }
            @media (max-width: 768px) {
                .image-grid { grid-template-columns: 1fr; gap: 15px; }
                .stats-grid { grid-template-columns: 1fr 1fr; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Solar Nowcasting Dashboard</h1>

            <div class="image-grid">
                <div class="img-container">
                    <img id="cam_raw" src="/latest_capture.jpg">
                </div>
                <div class="img-container">
                    <img id="cam_result" src="/latest_result.jpg">
                </div>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <p class="label">Sky Condition</p>
                    <p class="value" id="condition">-</p>
                </div>
                <div class="stat-card">
                    <p class="label">Wind direction</p>
                    <p class="value" id="wind-dir">-</p>
                </div>
                <div class="stat-card">
                    <p class="label">System Status</p>
                    <p class="value" id="status">Online</p>
                </div>
                <div class="stat-card">
                    <p class="label">Last Frame</p>
                    <p class="value" id="time">--:--:--</p>
                </div>
            </div>
        </div>

        <script>
            function updateDashboard() {
                var timestamp = new Date().getTime();
                document.getElementById("cam_raw").src = "/latest_capture.jpg?t=" + timestamp;
                document.getElementById("cam_result").src = "/latest_result.jpg?t=" + timestamp;

                fetch('/api/stats')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('wind-dir').innerText = data.wind_direction;
                        document.getElementById('condition').innerText = data.sky_condition; // Fixed: Updates the field dynamically
                        document.getElementById('time').innerText = data.last_update;
                    })
                    .catch(err => console.error('Error fetching stats:', err));
            }
            setInterval(updateDashboard, 10000);
            window.onload = updateDashboard;
        </script>
    </body>
    </html>
    """

@app.route("/latest_capture.jpg")
def latest_image():
    path = os.path.join(CAPTURE_FOLDER, "latest_capture.jpg")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return Response(f.read(), mimetype="image/jpeg", headers={"Cache-Control": "no-store"})
    return "No image found", 404

@app.route("/latest_result.jpg")
def latest_result():
    path = os.path.join(RESULT_FOLDER, "latest_result.jpg")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return Response(f.read(), mimetype="image/jpeg", headers={"Cache-Control": "no-store"})
    return "No image found", 404

@app.route("/api/stats")
def get_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                return jsonify(json.load(f))
        except Exception:
            pass
    return jsonify({"wind_direction": "Calculating...", "sky_condition": "Analyzing...", "last_update": "--:--:--"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)