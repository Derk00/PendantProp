from hardware.opentrons import Opentrons_API

api = Opentrons_API()
data_file_path = "data\test\meta_data\formulation_file_test_phenolred.csv"
with open(data_file_path, "rb") as file:
    api.data_file = file
api.upload_data()
# api.upload_protocol()
# api.create_run_from_protocol()
# api.run_protocol()
