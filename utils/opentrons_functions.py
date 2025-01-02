"""
A collection of custom functions for OpenTrons protocol
Authors: Mathijs Mabesoone & Pim Dankloff
License: MIT
e-mail: pim.dankloff@ru.nl
"""


def pick_up_tip(pipette):
    pipette.pick_up_tip()


# def transfer(pipette, source, destination, volume, touch_tip_speed=40, blow_out=True):
#     """
#     Transfer liquid from source to destination
#     input:
#         pipette: pipette object
#         source: container object
#         destination: target object
#         volume: float, volume to transfer
#         touch_tip_speed: int, speed of touch tip
#         blow_out: bool, if True, blow out after dispensing
#     return:
#         None
#     """
#     pipette.aspirate(volume, source.aspirate(volume))
#     pipette.touch_tip(speed=touch_tip_speed)
#     pipette.dispense(volume, destination.top())
#     if blow_out:
#         pipette.blow_out(destination.top())
#     pipette.touch_tip(speed=touch_tip_speed)


# def dispense(
#     pipette,
#     destination,
#     volume: float,
#     touch_tip_speed: int = 40,
#     container: bool = True,
# ):
#     """

#     Dispense liquid to destination.
#     input:
#         pipette: pipette object
#         destination: target object
#         volume: float, volume to dispense
#         touch_tip_speed: int, speed of touch tip
#     return:
#         None
#     """
#     if container:
#         pipette.dispense(volume, destination.dispense(volume))
#     else:
#         pipette.dispense(volume, destination.top())

#     pipette.touch_tip(speed=touch_tip_speed)


# def aspirate(pipette, source, volume: float, touch_tip_speed: int = 40):
#     """
#     Aspirate liquid from source
#     input:
#         pipette: pipette object
#         source: container object
#         volume: float, volume to aspirate
#         touch_tip_speed: int, speed of touch tip
#     return:
#         None
#     """
#     pipette.aspirate(volume, source.aspirate(volume))
#     pipette.touch_tip(speed=touch_tip_speed)
