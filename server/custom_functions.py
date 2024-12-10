import os
import cv2
from threading import Thread, Event


def measure_well(start_well: str, end_well: str):
    print(f"Measuring well from {start_well} to {end_well}")


def save_csv_file(exp_name: str, csv_file, app):
    exp_dir = os.path.join(app.config["UPLOAD_FOLDER"], exp_name)
    os.makedirs(exp_dir, exist_ok=True)
    file_path = os.path.join(exp_dir, csv_file.filename)
    csv_file.save(file_path)


############## the opentron live feed ################
# Initialize the webcam
stop_background_threads = Event()

camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set width
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Set height
camera.set(cv2.CAP_PROP_FPS, 30)  # Set frame rate

if not camera.isOpened():
    print("Error: Could not open camera.")

# Global variable to store the current frame
current_frame = None


def capture_frames():
    global current_frame
    while not stop_background_threads.is_set():
        success, frame = camera.read()
        if success:
            current_frame = frame
        else:
            print("Error: Could not read frame.")


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
    print("This is a custom function file")
