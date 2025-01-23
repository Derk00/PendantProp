from hardware.opentrons.http_communications import Opentrons_http_api
from hardware.opentrons.configuration import Configuration


def prototcol_surfactant_characterization():
    # initialize
    api = Opentrons_http_api()
    api.initialise()
    config = Configuration(http_api=api)
    labware = config.load_labware()
    pipettes = config.load_pipettes()
    containers = config.load_containers()
    right_pipette = pipettes["right"]
    left_pipette = pipettes["left"]

    # TODO implement
