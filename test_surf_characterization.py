from protocols.protocol import Protocol
from hardware.opentrons.http_communications import Opentrons_http_api
from hardware.cameras import PendantDropCamera
from hardware.sensor.sensor_api import SensorApi

opentron_api = Opentrons_http_api()
sensor_api = SensorApi()
pd_cam = PendantDropCamera()
protocol = Protocol(api=opentron_api, sensor_api=sensor_api, pendant_drop_camera=pd_cam)
