from hardware.opentrons.http_communications import Opentrons_http_api
from hardware.opentrons.configuration import Configuration

def prototcol_calibrate():
    # initialize
    api = Opentrons_http_api()
    api.initialise()
    config = Configuration(http_api=api)
    labware = config.load_labware()
    pipettes = config.load_pipettes()
    containers = config.load_containers()
    right_pipette = pipettes["right"]
    left_pipette = pipettes["left"]

    # parameters
    time_needle_attachment = 60  # s, time for the user to attach the needle to the p20 pipette
    time_calibration = 120 # s, time for the user to measure pixels of needle diameter in FIJI
    height_start = 10  # mm
    height_end = -20  # mm

    # executables
    api.home()
    left_pipette.move_to_well(
        container=containers["drop_stage"], offset={"x": 0, "y": 0, "z": height_start}
    )
    api.delay(time_needle_attachment)
    left_pipette.move_to_well(
        container=containers["drop_stage"], offset={"x": 0, "y": 0, "z": height_end}
    )
    api.delay(time_calibration)
    left_pipette.move_to_well(
        container=containers["drop_stage"], offset={"x": 0, "y": 0, "z": height_start}
    )
    api.delay(time_needle_attachment)