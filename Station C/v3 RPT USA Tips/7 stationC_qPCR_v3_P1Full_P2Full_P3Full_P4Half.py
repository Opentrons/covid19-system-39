from opentrons import types

metadata = {
    'protocolName': 'qPCR Protocol Station C',
    'author': 'Chaz w/ SMK Changes',
    'apiLevel': '2.7'
}

NUM_COLS_P1 = 12  # number of columns (plate 1) (from 96 well plate, should be 1-12)
NUM_COLS_P2 = 12  # number of columns (plate 2) (from 96 well plate, should be 1-12)
NUM_COLS_P3 = 12  # number of columns (plate 3) (from 96 well plate, should be 1-12)
NUM_COLS_P4 = 6  # number of columns (plate 4) (from 96 well plate, should be 1-12)


def run(protocol):
    # define labware and pipettes
    tempdeck = protocol.load_module('temperature module gen2', '3')
    qpcrplate = tempdeck.load_labware('integra_alblock_384well')
    plate1, plate2, plate3, plate4 = [
        protocol.load_labware(
            'opentrons_96_aluminumblock_nest_wellplate_100ul', s).rows()[0][:n] for s, n in zip(
                ['2', '5', '8', '11'],
                [NUM_COLS_P1, NUM_COLS_P2, NUM_COLS_P3, NUM_COLS_P4])]

    alblock_mm = protocol.load_labware('eppcoldblock_96_wellplate_200ul', '6')
    #alblock_mm = protocol.load_labware('opentrons_96_aluminumblock_nest_wellplate_100ul', '6')
    mmtips = [protocol.load_labware('tipone_10ul_xl_tiprack', '9')]
    tips20 = [
        protocol.load_labware(
            'tipone_10ul_xl_tiprack', s) for s in ['1', '4', '7', '10']
            ]
    all_tips = [tr['A'+str(i)] for tr in tips20 for i in range(1, 13)]
    # tips1, tips2, tips3, tips4 = [all_tips[i*NUM_COLS:(i+1)*NUM_COLS] for i in range(4)]

    m20 = protocol.load_instrument('p20_multi_gen2', 'left', tip_racks=mmtips)
    p20 = protocol.load_instrument('p20_single_gen2', 'right', tip_racks=mmtips)

    dest_wells = [qpcrplate.rows()[x][i:i+12] for x in [0, 1] for i in [0, 12]]
    mm_wells = alblock_mm.rows()[0][:4]

    drop_counter = 0
    tip_counter = 0

    def m20_drop_tip():
        nonlocal drop_counter
        if drop_counter < 12:
            m20.drop_tip()
        else:
            m20.drop_tip(all_tips[drop_counter-12])
        drop_counter += 1

    def m20_pick_up_tip():
        nonlocal tip_counter
        m20.pick_up_tip(all_tips[tip_counter])
        tip_counter += 1

    # add mastermix
    mm_counter = 0
    p_counter = 1
    for samps, wells, mm in zip([plate1, plate2, plate3, plate4], dest_wells, mm_wells):
        if mm_counter == 0 and not m20.has_tip:
            m20.pick_up_tip()
        if len(samps) != 0:
            protocol.comment(f'Adding 20uL of mastermix to {len(samps)} columns for Plate {p_counter}...')
            m20.mix(5, 20, mm)
        for s, well in zip(samps, wells):
            m20.aspirate(20, mm)
            m20.dispense(20, well)
            m20.blow_out()
            mm_counter += 1
        if mm_counter >= 12:
            m20.drop_tip()
            mm_counter = 0
        p_counter += 1

    if m20.has_tip:
        m20.drop_tip()

    if NUM_COLS_P4 < 12:
        protocol.comment('Adding mastermix for control in P24...')
        p20.pick_up_tip()
        p20.aspirate(20, alblock_mm['H4'])
        p20.dispense(20, qpcrplate['P24'])
        p20.drop_tip()

    # add samples
    p_num = 1

    for plate, col, d_wells in zip([plate1, plate2, plate3, plate4], [NUM_COLS_P1, NUM_COLS_P2, NUM_COLS_P3, NUM_COLS_P4], dest_wells):
        if len(plate) != 0:
            protocol.comment(f'Adding 5uL of sample from {len(plate)} columns of Plate {p_num}')
        for s, d in zip(plate, d_wells):
            m20_pick_up_tip()
            m20.aspirate(5, s)
            m20.dispense(5, d)
            m20.mix(3, 15, d)
            m20_drop_tip()
        p_num += 1

    # add control
    protocol.comment('Adding control to P24...')
    p20.pick_up_tip()
    p20.aspirate(5, alblock_mm['H12'])
    p20.default_speed = 60
    p20.move_to(protocol.deck.position_for('3').move(types.Point(x=135, y=85, z=130)))
    p20.move_to(protocol.deck.position_for('3').move(types.Point(x=135, y=0, z=130)))
    p20.dispense(5, qpcrplate['P24'])
    p20.mix(3, 15, qpcrplate['P24'])
    p20.blow_out()
    p20.move_to(qpcrplate['P24'].top(3))
    p20.move_to(protocol.deck.position_for('3').move(types.Point(x=135, y=0, z=130)))
    p20.move_to(protocol.deck.position_for('3').move(types.Point(x=135, y=85, z=130)))
    p20.default_speed = None
    p20.drop_tip()
