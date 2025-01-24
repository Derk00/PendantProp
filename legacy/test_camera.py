from hardware.cameras import PendantDropCamera
import time

camera = PendantDropCamera()
camera.initialize_measurement(well_id="test")
camera.start_capture()

time.sleep(2)

camera.stop_capture()

print(camera.st_t)
