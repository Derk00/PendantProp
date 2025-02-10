from hardware.cameras import PendantDropCamera
import cv2
import numpy as np

pd_cam = PendantDropCamera()
pd_cam.initialize_measurement(well_id="6A1")
pd_cam.start_stream()
pd_cam.start_capture()

cv2.namedWindow("Pendant Drop Camera Feed", cv2.WINDOW_NORMAL)

try:
    buffer = b""
    for frame in pd_cam.generate_frames():
        buffer += frame
        start = buffer.find(b"\xff\xd8")  # JPEG start
        end = buffer.find(b"\xff\xd9")  # JPEG end

        if start != -1 and end != -1:
            jpg = buffer[start : end + 2]
            buffer = buffer[end + 2 :]

            # Decode the frame from bytes to a NumPy array
            np_arr = np.frombuffer(jpg, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if img is not None:
                cv2.imshow("Pendant Drop Camera Feed", img)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
finally:
    pd_cam.stop_stream()
    pd_cam.stop_capture()
    cv2.destroyAllWindows()
