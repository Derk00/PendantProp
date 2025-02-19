from hardware.cameras import PendantDropCamera
from protocol import prototcol_measure_wells

#TODO fix container loading

pd_cam = PendantDropCamera()
prototcol_measure_wells(pd_cam)