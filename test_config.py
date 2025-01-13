from hardware.opentrons.http_communications import Opentrons_http_api
from hardware.opentrons.configuration import Configuration

api = Opentrons_http_api()
api.initialise()

config = Configuration(http_api=api)

labware = config.load_labware()
pipettes = config.load_pipettes()
containers = config.load_containers()

right_pipette = pipettes["right"]
left_pipette = pipettes["left"]

print(containers["4A1"])
print(containers["water"])

# # ## excutable robot commands
api.home()
right_pipette.pick_up_tip()
right_pipette.transfer(
    volume=100,
    source=containers["water"],
    destination=containers["4A1"],
    touch_tip=True,
)
right_pipette.transfer(
    volume=100,
    source=containers["phenol red"],
    destination=containers["4A1"],
    touch_tip=True,
)

right_pipette.drop_tip(return_tip=True)

print(containers["4A1"])
print(containers["water"])
# right_pipette.touch_tip(container=containers["water"], repeat=3)
# right_pipette.touch_tip(container=containers["4A1"], repeat=2)
# right_pipette.drop_tip(return_tip=True)
