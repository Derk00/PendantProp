from hardware.cameras import PendantDropCamera
import time

camera = PendantDropCamera()
# camera.start_stream()
time.sleep(1)
print(camera.generate_frames())
# camera.stop_stream()
# camera.initialize_measurement(well_id="test")
# camera.start_capture()

# time.sleep(2)

# camera.stop_capture()

# print(camera.st_t)
