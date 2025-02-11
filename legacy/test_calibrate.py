from hardware.cameras import PendantDropCamera
from protocols.calibration import prototcol_calibrate

#TODO fix container loading

pd_cam = PendantDropCamera()
prototcol_calibrate(pd_cam)