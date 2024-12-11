from hardware.opentrons import Opentrons_API

api = Opentrons_API()
api.upload_protocol()
api.create_run_from_protocol()
api.run_protocol()
