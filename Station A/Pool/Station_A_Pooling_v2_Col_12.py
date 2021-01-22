from opentrons import types

metadata = {
    'protocolName': 'Plate Filling with 4 tuberacks',
    'author': 'Chaz w/ SMK Changes',
    'source': 'Covid Workstation',
    'apiLevel': '2.7'
}

NUM_COLS = 12  # variable can be used to change the number of pooled columns (1-12)


def run(protocol):
    # load labware
    [tip1, tip2, tip3, tip4, tip5] = [
        protocol.load_labware(
            'tipone_tiprack_adapter_300ul', s) for s in [
                '1', '4', '7', '10', '9']]
    tips = [tip1, tip2, tip3, tip4]
    usedtips = [
        well for row in [
            tip5, tip1, tip2, tip3] for well in row.rows()[0]]
    tuberacks = [protocol.load_labware(
        'biobank_96_tuberack_1ml', str(s)) for s in range(2, 12, 3)]
    deepplate = protocol.load_labware('nest_96_wellplate_2ml_deep', '3')
    p300 = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=tips)

    deepwells = deepplate.rows()[0][:NUM_COLS]

    num_utips = 0

    def drop_tip():
        nonlocal num_utips
        p300.drop_tip(usedtips[num_utips])
        num_utips += 1

    for rack in tuberacks:
        rackwells = rack.rows()[0][:NUM_COLS]
        for src, dest in zip(rackwells, deepwells):
            p300.pick_up_tip()
            p300.aspirate(100, src.bottom(20))
            p300.move_to(src.top().move(types.Point(x=0, y=0, z=-6)))
            p300.move_to(src.top().move(types.Point(x=3.75, y=0, z=-6)))
            p300.move_to(src.top().move(types.Point(x=0, y=0, z=-6)))
            p300.dispense(100, dest.bottom(2))
            p300.blow_out(dest.bottom(2))
            p300.move_to(dest.top().move(types.Point(x=0, y=0, z=-6)))
            p300.move_to(dest.top().move(types.Point(x=3.25, y=0, z=-6)))
            p300.move_to(dest.top().move(types.Point(x=0, y=0, z=-6)))
            drop_tip()
