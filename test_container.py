from hardware.opentrons.containers import *


mock_labware_info_well = {
    "location": 3,
    "max_volume": 1000,
    "labware_id": "test",
    "labware_name": "Mock labware",
    "well_diameter": 18,
    "depth": 10.9,
}

mock_labware_info_ft15 = {
    "location": 1,
    "max_volume": 15000,
    "labware_id": "test_2",
    "labware_name": "Mock labware ft",
    "well_diameter": 25,
    "depth": 117,
}


well = PlateWell(
    labware_info=mock_labware_info_well,
    well="A1",
)

ft15 = FalconTube15(
    labware_info=mock_labware_info_ft15,
    well="A1",
    initial_volume_mL=10,
    solution_name="water",
)

print(well.height_mm - well.DEPTH)
