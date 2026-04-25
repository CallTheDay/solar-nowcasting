from flask import Flask, Response, jsonify
import os

app = Flask(__name__)

# IMAGE_FOLDER = "/home/pi/solar-nowcasting/data/images"
IMAGE_FOLDER = "/home/pi/solar-nowcasting/data/test"

@app.route("/")
def index():
    return """
    <html>
    <head>
        <title>Solar Nowcasting Dashboard</title>
        <style>
            body { font-family: 'Segoe UI', Arial; text-align: center; background: #0f0f0f; color: #e0e0e0; margin: 0; padding: 20px; }
            .container { max-width: 900px; margin: auto; }
            img { width: 100%; border-radius: 8px; border: 2px solid #333; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
            .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 25px; }
            .stat-card { background: #1a1a1a; padding: 10px; border-radius: 8px; border: 1px solid #333; }
            .label { color: #888; font-size: 14px; text-transform: uppercase; }
            .value { font-size: 24px; font-weight: bold; margin-top: 5px; color: #00ff99; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Solar Nowcasting: Sky Feed</h1>
            <img id="cam" src="/latest_capture.jpg">

            <div class="stats-grid">
                <div class="stat-card">
                    <p class="label">Sky Condition</p>
                    <p class="value" id="condition">Placeholder: Clear</p>
                </div>
                <div class="stat-card">
                    <p class="label">Cardinal direction</p>
                    <p class="value" id="rain">Placeholder: None</p>
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
            function updateImage() {
                // ?t= prevents showing cached old image
                document.getElementById("cam").src = "/latest_capture.jpg?t=" + new Date().getTime();
                document.getElementById("time").innerText = new Date().toLocaleTimeString();
            }
            // image refresh every 10 seconds
            setInterval(updateImage, 1000);
        </script>
    </body>
    </html>
    """

@app.route("/latest_capture.jpg")
def latest_image():
    path = os.path.join(IMAGE_FOLDER, "latest_capture.jpg")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return Response(f.read(), mimetype="image/jpeg", headers={"Cache-Control": "no-store"})
    return "No image found", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)