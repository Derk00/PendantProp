from hardware.opentrons.http_communications import Opentrons_http_api

api = Opentrons_http_api()
api.upload_protocol(protocol="hardware\opentrons\protocol_placeholder.py")
api.create_run()
api.add_labware_definition(labware_definition="sarstedt_77_tiprack_1000ul.json")
tips_id = api.load_labware(
    labware_name="sarstedt_77_tiprack_1000ul", location=4, custom_labware=True
)
api.home()
# tips_id = api.load_labware(labware_name="opentrons_96_tiprack_1000ul", location=3)
plate_id = api.load_labware(labware_name="nest_96_wellplate_200ul_flat", location=1)
right_pipette_id = api.load_pipette(name="p1000_single_gen2", mount="right")
# # print(api.get_loaded_labwares())
api.pick_up_tip(tip_labware_id=tips_id, tip_well_name="A1", pipette_id=right_pipette_id)
# api.move_to_well(
#     pipette_id=right_pipette_id,
#     labware_id=plate_id,
#     well="C1",
#     offset=dict(x=0, y=0, z=10),
# )
# api.aspirate(
#     pipette_id=right_pipette_id, labware_id=plate_id, volume=100, well="A1"
# )
# api.dispense(
#     pipette_id=right_pipette_id, labware_id=plate_id, volume=100, well="B1"
# )
# api.blow_out(pipette_id=right_pipette_id, labware_id=plate_id, well="B1", depth=-5)
api.drop_tip(pipette_id=right_pipette_id)

api.delete_run()
