from hardware.opentrons.http_communications import Opentrons_http_api
from hardware.opentrons.configuration import Configuration
from hardware.cameras import PendantDropCamera


def prototcol_calibrate(pendant_drop_camera: PendantDropCamera):
    # initialize
    api = Opentrons_http_api()
    api.initialise()
    config = Configuration(http_api=api)
    labware = config.load_labware()
    pipettes = config.load_pipettes()
    containers = config.load_containers()
    right_pipette = pipettes["right"]
    left_pipette = pipettes["left"]
    pendant_drop_camera = pendant_drop_camera
    pendant_drop_camera.initialize_measurement(well_id=containers["drop_stage"].WELL_ID)

    # parameters
    time_needle_attachment = (
        20  # s, time for the user to attach the needle to the p20 pipette
    )
    time_calibration = (
        20  # s, time for the user to measure pixels of needle diameter in FIJI
    )
    height_start = 50  # mm
    height_end = 13  # mm

    # executables
    api.home()
    left_pipette.move_to_well(
        container=containers["drop_stage"], offset={"x": 0, "y": 0, "z": height_start}
    )
    api.delay(time_needle_attachment)
    left_pipette.move_to_well(
        container=containers["drop_stage"], offset={"x": 0, "y": 0, "z": height_end}
    )
    pendant_drop_camera.start_capture()
    api.delay(time_calibration)
    pendant_drop_camera.stop_capture()
    left_pipette.move_to_well(
        container=containers["drop_stage"], offset={"x": 0, "y": 0, "z": height_start}
    )
    api.delay(time_needle_attachment)
