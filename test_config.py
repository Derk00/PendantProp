from hardware.opentrons.http_communications import Opentrons_http_api
from hardware.opentrons.configuration import Configuration

api = Opentrons_http_api()
api.initialise()
config = Configuration(http_api=api)
config_data = config.load_configuration()
print(config_data)
