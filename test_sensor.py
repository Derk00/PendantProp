from hardware.sensor.sensor_api import SensorApi

api = SensorApi()
sensor_data = api.capture_sensor_data()
print(sensor_data)
