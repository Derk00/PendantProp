from hardware.cameras import PendantDropCamera
import time

camera = PendantDropCamera()
camera.initialize_measurement(well_id="4A1")
camera.start_capture()

time.sleep(5)
print(camera.image4feed)
# camera.initialize_measurement(well_id="4A2")
time.sleep(5)
camera.stop_capture()
