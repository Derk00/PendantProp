from hardware.cameras import PendantDropCamera
import cv2
import time
import numpy as np

camera = PendantDropCamera()
camera.initialize_measurement("3A1")
camera.start_stream()
camera.start_capture()
time.sleep(1)

# Create a window to display the frames
cv2.namedWindow("Pendant Drop Camera", cv2.WINDOW_NORMAL)

try:
    while True:
        for frame in camera.generate_frames():
            # Convert the frame bytes to a NumPy array
            np_frame = np.frombuffer(frame.split(b"\r\n\r\n")[1], dtype=np.uint8)
            # Decode the image
            img = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)
            # Display the image
            cv2.imshow("Pendant Drop Camera", img)

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        else:
            continue
        break
finally:
    camera.stop_stream()
    camera.stop_capture()
    cv2.destroyAllWindows()
