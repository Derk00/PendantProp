from opentrons.execute import protocol_api
import requests


metadata = {
    "protocolName": "Calibration",
    "author": "Pim Dankloff",
    "description": "Calibration for pendant drop camera",
    "apiLevel": "2.14",
}


def run(protocol: protocol_api.ProtocolContext):
    def notify_server(status):
        SERVER_IP = "192.168.0.73:5000"
        url = f"http://{SERVER_IP}/status"
        r = requests.post(url, json={"status": status})

    # load labware
    drop_stage = protocol.load_labware("axygen_1_reservoir_90ml", 10)
    tips_20 = protocol.load_labware("opentrons_96_tiprack_20ul", 3)

    # load instruments
    left_pipette = protocol.load_instrument(
        "p20_single_gen2", "left", tip_racks=[tips_20]
    )

    left_pipette.move_to(drop_stage.well(0).bottom(z=100))
    protocol.delay(seconds=30)
    left_pipette.move_to(drop_stage.well(0).bottom(z=56))  # adjust if needed!
    protocol.delay(seconds=30)
    left_pipette.move_to(drop_stage.well(0).bottom(z=100))

    notify_server(status="Calibration done")
