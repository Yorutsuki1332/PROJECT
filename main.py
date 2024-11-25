import collector
import threading, sqlite3, base64, json, logging, os
import cv2
import numpy as np
from time import time
from datetime import datetime
from flask import Flask, Response, render_template, jsonify, request
from flask_socketio import SocketIO

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
socketio = SocketIO(app)


















### face id ###
class EnhancedFaceID:
    def __init__(self):
        self.face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        self.face_database = {}
        self.recognition_threshold = 0.65
        self.max_users = 10
        
    def detect_face(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60)
        )
        
        if len(faces) == 0:
            return None, 0
            
        best_face = max(faces, key=lambda rect: rect[2] * rect[3])
        x, y, w, h = best_face
        face_rect = (x, y, x + w, y + h)
        confidence = min((w * h) / (frame.shape[0] * frame.shape[1]) * 4, 1.0)
        
        return face_rect, confidence

    def register_face(self, user_id, frame):
        if len(self.face_database) >= self.max_users:
            return False, "Maximum number of users reached"
        
        face_rect, confidence = self.detect_face(frame)
        if face_rect is None:
            return False, "No face detected"
            
        self.face_database[user_id] = frame
        return True, "Face registered successfully"

    def identify_face(self, frame):
        if not self.face_database:
            return False, None
            
        face_rect, confidence = self.detect_face(frame)
        if face_rect is None:
            return False, None
            
        # Simple placeholder for face recognition
        return True, list(self.face_database.keys())[0]

    def get_registered_users(self):
        return list(self.face_database.keys())

# Global variables
face_id = EnhancedFaceID()
camera = None
camera_lock = threading.Lock()

def init_camera():
    global camera
    try:
        # Try different camera indices
        for i in range(2):
            camera = cv2.VideoCapture(i)
            if camera.isOpened():
                logger.info(f"Camera initialized successfully on index {i}")
                camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                return True
        logger.error("No working camera found")
        return False
    except Exception as e:
        logger.error(f"Camera initialization error: {str(e)}")
        return False

def get_frame():
    global camera
    
    try:
        with camera_lock:
            if camera is None or not camera.isOpened():
                if not init_camera():
                    logger.error("Failed to get camera frame - camera not initialized")
                    return None

            success, frame = camera.read()
            if not success:
                logger.error("Failed to read frame from camera")
                return None

            face_rect, _ = face_id.detect_face(frame)
            if face_rect is not None:
                start_x, start_y, end_x, end_y = face_rect
                cv2.rectangle(frame, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                        0.7, (0, 255, 0), 2)

            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ret:
                logger.error("Failed to encode frame")
                return None
                
            return buffer.tobytes()
            
    except Exception as e:
        logger.error(f"Error in get_frame: {str(e)}")
        return None

def generate_frames():
    while True:
        try:
            frame_data = get_frame()
            if frame_data is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in generate_frames: {str(e)}")
            time.sleep(1)

@app.route('/recognition')
def index():
    try:
        return render_template('index_recognition.html')
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return "Server Error", 500

@app.route('/video_feed')
def video_feed():
    try:
        return Response(generate_frames(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        logger.error(f"Error in video_feed route: {str(e)}")
        return "Video Feed Error", 500

@app.route('/register_face', methods=['POST'])
def register_face():
    try:
        user_id = request.form.get('user_id')
        if not user_id:
            return jsonify({"success": False, "message": "No user ID provided"})

        frame_data = get_frame()
        if frame_data is None:
            return jsonify({"success": False, "message": "Failed to capture frame"})

        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        success, message = face_id.register_face(user_id, frame)
        return jsonify({"success": success, "message": message})
    except Exception as e:
        logger.error(f"Error in register_face route: {str(e)}")
        return jsonify({"success": False, "message": "Server error"})

@app.route('/identify_face', methods=['POST'])
def identify_face():
    try:
        frame_data = get_frame()
        if frame_data is None:
            return jsonify({"success": False, "message": "Failed to capture frame"})

        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        is_match, matched_user = face_id.identify_face(frame)
        if is_match:
            return jsonify({"success": True, "user_id": matched_user})
        return jsonify({"success": False, "message": "No match found"})
    except Exception as e:
        logger.error(f"Error in identify_face route: {str(e)}")
        return jsonify({"success": False, "message": "Server error"})

@app.route('/get_users', methods=['GET'])
def get_users():
    try:
        users = face_id.get_registered_users()
        return jsonify({"users": users})
    except Exception as e:
        logger.error(f"Error in get_users route: {str(e)}")
        return jsonify({"users": []})

@app.route('/check_camera')
def check_camera():
    try:
        with camera_lock:
            if camera is None or not camera.isOpened():
                status = init_camera()
            else:
                status = camera.isOpened()
        return jsonify({"camera_working": status})
    except Exception as e:
        logger.error(f"Error in check_camera route: {str(e)}")
        return jsonify({"camera_working": False})


### data collector ###
@app.route('/get_current_data')
def get_current_data():
    conn = sqlite3.connect('sensor_data.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 1''')
    data = c.fetchone()
    conn.close()
    
    if data:
        return jsonify({
            'timestamp': data[0],
            'temperature': data[1],
            'humidity': data[2],
            'light_level': data[3],
            'particle_level': data[4]
        })
    return jsonify({})

@app.route('/get_historical_data')
def get_historical_data():
    conn = sqlite3.connect('sensor_data.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 100''')
    data = c.fetchall()
    conn.close()
    
    return jsonify([{
        'timestamp': row[0],
        'temperature': row[1],
        'humidity': row[2],
        'light_level': row[3],
        'particle_level': row[4]
    } for row in data])

@app.route('/content')
def content():
    return render_template('index_content.html')

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    collector.init_db()
    sensor_thread = threading.Thread(target=collector.collect_sensor_data, daemon=True)
    sensor_thread.start()
    if not init_camera():
        logger.warning("Failed to initialize camera")
    try:
        # Run the Flask app
        socketio.run(app, debug=True, host='0.0.0.0', port=5000, use_reloader = False)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
