from opentrons import types

metadata = {
    'protocolName': 'Plate Filling No Pooling',
    'author': 'Chaz w/ SMK Changes',
    'source': 'Covid Workstation',
    'apiLevel': '2.7'
}

NUM_COLS = 7  # variable can be used to change the number of columns (12 per plate)


def run(protocol):
    # load labware
    [tip1, tip2, tip3, tip4, tip5] = [
        protocol.load_labware(
            'opentrons_96_filtertiprack_200ul', s) for s in [
                '1', '4', '7', '10', '9']]
    tips = [tip1, tip2, tip3, tip4]
    usedtips = [
        well for row in [
            tip5, tip1, tip2, tip3] for well in row.rows()[0]]
    tuberacks = [protocol.load_labware(
        'biobank_96_tuberack_1ml', str(s)) for s in range(2, 12, 3)]
    deepplate = protocol.load_labware('nest_96_wellplate_2ml_deep', '3')
    p300 = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=tips)

    tubewells = [well for plate in tuberacks for well in plate.rows()[0]][:NUM_COLS]

    #p300.default_speed = 400 #400 is default
    #p300.flow_rate.aspirate = 50  #300 is default
    
    #Controls Gantry-Speed ('A' Right, 'Z' Left)

    rsvr_hts = [18, 18]
    x = 0
    for idx, (src, utip) in enumerate(zip(tubewells, usedtips)):
        p300.pick_up_tip()
        for i in range(1):
            protocol.max_speeds['Z'] = 50 #125 default 
            p300.aspirate(100, src.bottom(rsvr_hts[x % 2]))
            protocol.delay(seconds=2)
            p300.move_to(src.top().move(types.Point(x=0, y=0, z=-4)))
            p300.move_to(src.top().move(types.Point(x=3.75, y=0, z=-4)))
            p300.move_to(src.top().move(types.Point(x=0, y=0, z=-4)))
            p300.move_to(src.top().move(types.Point(x=0, y=0, z=-4)))
            p300.move_to(src.top().move(types.Point(x=-3.75, y=0, z=-4)))
            p300.move_to(src.top().move(types.Point(x=0, y=0, z=-4)))
            protocol.delay(seconds=2)
            protocol.max_speeds['Z'] = 125 #125 default 
            p300.dispense(200, deepplate.rows()[0][idx % 12].bottom(2))
            p300.blow_out(deepplate.rows()[0][idx % 12].bottom(2))
            p300.move_to(deepplate.rows()[0][idx % 12].top().move(types.Point(x=0, y=0, z=-4)))
            p300.move_to(deepplate.rows()[0][idx % 12].top().move(types.Point(x=3.6, y=0, z=-4)))
            p300.move_to(deepplate.rows()[0][idx % 12].top().move(types.Point(x=0, y=0, z=-4)))
            x += 1
        p300.drop_tip(utip)
