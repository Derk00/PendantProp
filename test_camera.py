from hardware.cameras import PendantDropCamera
import cv2
import time
import threading
import numpy as np

pd_cam = PendantDropCamera()
pd_cam.initialize_measurement(well_id="6A1")

pd_cam.start_video_feed()
frame = pd_cam.generate_frames()
print(frame)