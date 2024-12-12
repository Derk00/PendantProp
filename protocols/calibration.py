from opentrons.execute import protocol_api
import pandas as pd
import requests
import sys

# sys.path.append("/var/lib/jupyter/notebooks")
# from opentrons_functions import pick_up_tip

import os

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

    notify_server(status="flag")
    # print location of running directory

    notify_server(status=f"{os.getcwd()}")
    # df = pd.read_csv("/var/lib/jupyter/notebooks/test.csv")  # parametrize?
    # notify_server(status=f"Loaded CSV: {df.head()}")

    # load labware
    tips_20 = protocol.load_labware("opentrons_96_tiprack_20ul", 3)
    # load instruments
    left_pipette = protocol.load_instrument(
        "p20_single_gen2", "left", tip_racks=[tips_20]
    )

    # protocol
    # pick_up_tip(left_pipette)
    # left_pipette.drop_tip()
