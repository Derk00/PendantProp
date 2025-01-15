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
# print(containers)


# # ## excutable robot commands
api.home()
left_pipette.pick_up_tip()
left_pipette.measure_pendant_drop(
    source=containers["water"],
    destination=containers["drop_stage"],
    drop_volume=10,
    delay=10,
    dispense_rate=100,
)
left_pipette.drop_tip(return_tip=True)

# api.home()
# left_pipette.pick_up_tip()
# right_pipette.pick_up_tip()
# # # print(right_pipette)
# right_pipette.transfer(
#     volume=100,
#     source=containers["water"],
#     destination=containers["4A1"],
#     touch_tip=True,
# )
# right_pipette.drop_tip(return_tip=True)
