import cv2
from threading import Thread

# Initialize the webcam
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set width
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Set height
camera.set(cv2.CAP_PROP_FPS, 30)  # Set frame rate

camera = cv2.VideoCapture(0)
if not camera.isOpened():
    raise Exception("Could not open video device")


def capture_frames():
    global current_frame
    while True:
        success, frame = camera.read()
        if success:
            current_frame = frame


# Start the frame capture thread
thread = Thread(target=capture_frames)
thread.daemon = True
thread.start()


def generate_opentron_frames():
    global current_frame
    while True:
        if current_frame is not None:
            # Encode the frame in JPEG format
            ret, buffer = cv2.imencode(".jpg", current_frame)
            frame = buffer.tobytes()

            # Yield the frame in byte format
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")


if __name__ == "__main__":
    generate_opentron_frames()
