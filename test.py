from hardware.opentrons import Opentrons_API

api = Opentrons_API()
# api.robot_ip = "169.254.220.146"
api.calibration()
