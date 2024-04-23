import cv2
from flask import render_template, request
from flask import Flask, Response

app = Flask(__name__)

# List of RTSP URLs for your cameras
camera_urls = [
    "rtsp://localhost:8554/vid8",
    "rtsp://localhost:8554/vid7",
    "rtsp://localhost:8554/vid2",
    "rtsp://localhost:8554/vid9",
    "rtsp://localhost:8554/vid1_500_400",
    "rtsp://localhost:8554/vid5",
    "rtsp://localhost:8554/vid3",
    "rtsp://localhost:8554/vid6",
    "rtsp://localhost:8554/vid4",
    # "rtsp://localhost:8554/cam_stream",
    # "rtsp://localhost:8554/stream_1"
]

def get_camera_stream(rtsp_url):
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        print(f"Error opening camera stream: {rtsp_url}")
        return None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error reading camera stream")
            cap.release()
            return None

        # Encode the frame as JPEG
        ret, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

    cap.release()

@app.route('/camera/<int:camera_id>')
def stream_camera(camera_id):
    # color_mode = request.args.get('color_mode', 'rgb')
    print("initialize")
    if camera_id < 0 or camera_id >= len(camera_urls):
        return "Invalid camera ID"

    rtsp_url = camera_urls[camera_id]
    return Response(get_camera_stream(rtsp_url),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
