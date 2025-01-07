from hardware.opentrons.http_communications import Opentrons_http_api
from hardware.opentrons.configuration import Configuration

api = Opentrons_http_api()
api.initialise()

config = Configuration(http_api=api)
labware = config.load_labware()
pipettes = config.load_pipettes()
containers = config.load_containers()
destinations = config.load_destinations()

right_pipette = pipettes["right"]

## excutable robot commands
api.home()
right_pipette.pick_up_tip()
# right_pipette.aspirate(containers["water"], 400)
right_pipette.transfer(containers["water"], destinations["4A1"], 100)
right_pipette.drop_tip(return_tip=True)
# print(right_pipette)
# right_pipette.dispense(destinations["4A1"], 100)
# right_pipette.drop_tip(return_tip=True)
# print(right_pipette.volume)
# print(containers["water"])
# right_pipette.aspirate(containers["water"], 400)
# print(right_pipette.volume)
# print(containers["water"])
# right_pipette.aspirate(containers["water"], 400)
# print(right_pipette.volume)
# print()
# right_pipette.drop_tip(return_tip=True)
