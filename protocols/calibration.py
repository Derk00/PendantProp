from opentrons.execute import protocol_api
# from src.customfunctions import measure_well
metadata = {
    "protocolName": "Calibration",
    "author": "Pim Dankloff",
    "description": "Calibration for pendant drop camera",
    "apiLevel": "2.14",
}


def run(protocol: protocol_api.ProtocolContext):

    # load labware
    tips_20 = protocol.load_labware("opentrons_96_tiprack_20ul", 3)
    # load instruments
    left_pipette = protocol.load_instrument(
        "p20_single_gen2", "left", tip_racks=[tips_20]
    )

    # protocol
    left_pipette.pick_up_tip()
    left_pipette.drop_tip()
