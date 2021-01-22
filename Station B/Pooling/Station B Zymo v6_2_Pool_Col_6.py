from opentrons import types
import math

metadata = {
    'protocolName': 'Zymo Extraction Station B',
    'author': 'Chaz w SMK Changes',
    'apiLevel': '2.7'
}

NUM_SAMPLES = 48  # the number of samples to run
NUM_COLS = math.ceil(NUM_SAMPLES/8)


def run(protocol):
    # load labware
    magdeck = protocol.load_module('magnetic module gen2', '10')
    magplate = magdeck.load_labware('nest_96_wellplate_2ml_deep')
    waste1 = protocol.load_labware(
        'integra_1_reservoir_300ml', '7').wells()[0].top(-4)
    waste2 = protocol.load_labware(
        'integra_1_reservoir_300ml', '11').wells()[0].top(-4)
    res1 = protocol.load_labware('nest_12_reservoir_15ml', '8')
    res2 = protocol.load_labware('nest_12_reservoir_15ml', '9')


    tips200 = [
        protocol.load_labware(
            'opentrons_96_tiprack_300ul', s) for s in range(1, 7)
        ]
    all_tips = [tr['A'+str(i)] for tr in tips200 for i in range(1, 13)]
    tips1, tips2, tips3, tips4, tips5, tips6 = [
        all_tips[i*12:(i+1)*12] for i in range(6)]

    m300 = protocol.load_instrument('p300_multi_gen2', 'left')

    # create reagent locations as variables
    buffer = [well for well in res1.wells()[:6] for _ in range(2)]
    wb1 = [well for well in res1.wells()[6:10] for _ in range(3)]
    wb2 = [well for well in res2.wells()[:4] for _ in range(3)]
    etoh1 = [well for well in res2.wells()[4:8] for _ in range(3)]
    etoh2 = [well for well in res2.wells()[8:] for _ in range(3)]
    water = res1['A12']

    magsamps = magplate.rows()[0][:NUM_COLS]

    m300.flow_rate.aspirate = 50
    m300.flow_rate.dispense = 150
    m300.flow_rate.blow_out = 300

     # WELL_MIX
    def well_mix(reps, loc, v, side):
        loc1 = loc.bottom().move(types.Point(x=side, y=0, z=3))
        loc2 = loc.bottom().move(types.Point(x=side*-1, y=0, z=0.6))
        m300.aspirate(20, loc1)
        mvol = v-20
        for _ in range(reps-1):
            m300.aspirate(mvol, loc1)
            m300.dispense(mvol, loc2)
        m300.dispense(20, loc2)

    # REMOVE SUPER
    def remove_supernatant(vol, src, dest, side):
        m300.flow_rate.aspirate = 20
        m300.aspirate(10, src.top()) #changed from 20ul
        while vol > 200:
            m300.aspirate(
                200, src.bottom().move(types.Point(x=side, y=0, z=0.5)))
            
            # wait for a moment to allow outer drips to fall above liquid
            m300.move_to(src.top(-6))
            protocol.delay(seconds=1)
            # flick to the side
            m300.move_to(src.top(-6).move(types.Point(x=0, y=0, z=0)))
            m300.move_to(src.top(-6).move(types.Point(x=2, y=0, z=0)))
            m300.move_to(src.top(-6).move(types.Point(x=0, y=0, z=0)))
            m300.dispense(200, dest) #210 makes bubblesv6
            # NEW removed shake from above reservoir
            m300.aspirate(10, dest) #changed from 20ul
            vol -= 200
        m300.aspirate((vol+10), src.bottom().move(types.Point(x=side, y=0, z=0.5)))
        # wait for a moment to allow outer drips to fall above liquid v2
        m300.move_to(src.top(-6))
        protocol.delay(seconds=1)
        m300.dispense((vol+30), dest)
        m300.dispense(50, dest)
        # NEW removed shake from above reservoir
        #m300.move_to(dest.move(types.Point(x=0, y=0, z=0)))
        #m300.move_to(dest.move(types.Point(x=4, y=0, z=0)))
        #m300.move_to(dest.move(types.Point(x=0, y=0, z=0)))
        m300.flow_rate.aspirate = 50

    sides = [-1, 1]*6

    # WASHING STEP
    def wash_step(msg, src, vol, mix, t1, t2, t0, tm, w, t_tips=False, v2=0, mix_before=False):
        """ This is a versatile function that does a lot of the repetive tasks
            msg = message (string)
            src = source wells for reagent
            vol = volume of reagent added (and supernatant removed)*
            mix = the number of times to mix
            t1 = tips to add reagent
            t2 = tips to remove supernatant (tips will be replaced in t1)
            t0 = location to replace t1
            tm = time to incubate on magdeck
            w = waste location
            t_tips = if True, will trash tips after adding reagent (tips1)
            v2 = the volume for supernatant removal (if different than vol)
            mix_before = mix before asp from reservoir
            """
        protocol.comment(f'Adding {vol}uL of {msg} to samples...')
        for well, tip, tret, s, side in zip(magsamps, t1, t0, src, sides):
            m300.pick_up_tip(tip)
            add_vol = vol
            e_vol = 0
            # mix before asp reagent
            if mix_before:
                m300.flow_rate.aspirate = 200
                m300.flow_rate.dispense = 200
                for _ in range(4):
                    m300.mix(1, 200, s.bottom().move(types.Point(x=0, y=2, z=1)))
                    m300.mix(1, 200, s.bottom().move(types.Point(x=0, y=-2, z=1)))
                m300.flow_rate.aspirate = 50
                m300.flow_rate.dispense = 150
            while add_vol > 200:
                m300.aspirate(200, s.bottom(3))
                # wait for a moment to allow outer drips to fall above liquid
                m300.move_to(s.top())
                protocol.delay(seconds=2)
                #Shake to remove drops 
                m300.move_to(s.top().move(types.Point(x=0, y=0, z=0)))
                m300.move_to(s.top().move(types.Point(x=2, y=0, z=0)))
                m300.move_to(s.top().move(types.Point(x=0, y=0, z=0)))
                m300.dispense(220, well.top(-6)) #increased dispense v6
                # SHAKE/WAIT?
                m300.aspirate(10, well.top(-6)) #changed to 10ul
                add_vol -= 200
                e_vol += 20
            m300.aspirate(add_vol, s)
            # wait for a moment to allow outer drips to fall above liquid
            m300.move_to(s.top())
            protocol.delay(seconds=1)
            # shake to remove drops
            m300.move_to(s.top().move(types.Point(x=0, y=0, z=0)))
            m300.move_to(s.top().move(types.Point(x=2, y=0, z=0)))
            m300.move_to(s.top().move(types.Point(x=0, y=0, z=0)))
            
            total_vol = add_vol + e_vol
            m300.dispense(total_vol, well)

            well_mix(mix, well, 200, side)

            #blow out causes a huge bubble? v4
            #m300.blow_out()
            
            # wait for a moment to allow outer drips to fall above liquid
            m300.move_to(well.top(-6))    
            protocol.delay(seconds=2) 
            # shake to remove drops NEW
            m300.move_to(well.top(-6).move(types.Point(x=0, y=0, z=0)))
            m300.move_to(well.top(-6).move(types.Point(x=2, y=0, z=0)))
            m300.move_to(well.top(-6).move(types.Point(x=0, y=0, z=0)))
            # air cushion
            m300.aspirate(20, well.top(-6))           
            if t_tips:
                m300.drop_tip()
            else:
                m300.drop_tip(tret)

        magdeck.engage()
        protocol.comment(f'Engaging Magdeck for {tm} minutes.')
        protocol.delay(minutes=tm)

        protocol.comment('Removing supernatant...')
        supernatant_volume = vol if v2 == 0 else v2
        for well, tip, tret, side in zip(magsamps, t2, t1, sides):
            m300.pick_up_tip(tip)
            remove_supernatant(supernatant_volume, well, w, side)
            m300.aspirate(30, w)
            #ADD TOUCH
            m300.drop_tip(tret)

        magdeck.disengage()

    # START PROTOCOL

    # 1 Adding 800uL of buffer+beads; removing 1200uL of supernatant
    wash_step(
        'Viral Buffer + Beads', buffer, 800, 15, tips1, tips2,
        tips1, 3, waste1, t_tips=True, v2=1200, mix_before=True)

    # 2 Wash Buffer 1
    wash_step('Wash Buffer 1', wb1, 500, 10, tips3, tips4, tips2, 3, waste2)
    # 3 Wash Buffer 2
    wash_step('Wash Buffer 2', wb2, 500, 10, tips5, tips6, tips4, 3, waste2)

	#Pause to remove tips and add elution plate
    m300.move_to(magplate.wells()[0].top(30))

    for _ in range(6):
        protocol.set_rail_lights(not protocol.rail_lights_on)
        protocol.delay(seconds=1)
    protocol.pause('Please remove all tips and waste in slot 7. \
    Replace all tips. Click RESUME when ready')

    del protocol.deck['7']
    pcr_plate = protocol.load_labware(
        'opentrons_96_aluminumblock_nest_wellplate_100ul', '7')
    elutions = pcr_plate.rows()[0][:NUM_COLS]

    # 4 Ethanol wash 1
    wash_step(
        'Ethanol 1', etoh1, 500, 10, tips1, tips2,
        tips1, 3, waste2, t_tips=True)

    # 5 Ethanol wash 2
    wash_step('Ethanol 2', etoh2, 500, 10, tips3, tips4, tips2, 3, waste2)
    
    # 6 Remove excess EtOH
    magdeck.engage()
    protocol.comment('Removing any excess ethanol...')
    m300.flow_rate.aspirate = 25
    for well, tip in zip(magsamps, tips3):
        m300.pick_up_tip(tip)
        m300.aspirate(60, well)
        m300.dispense(60, waste2)
        #Shake to remove drops (needed?)
        m300.move_to(waste2.move(types.Point(x=0, y=0, z=0)))
        m300.move_to(waste2.move(types.Point(x=4, y=0, z=0)))
        m300.move_to(waste2.move(types.Point(x=0, y=0, z=0)))
        m300.aspirate(10, waste2)
        # wait for a moment to allow outer drips to fall?
        m300.drop_tip(tip)

    m300.flow_rate.aspirate = 50
    magdeck.disengage()
    protocol.comment('Letting air dry for 10 minutes...')
    protocol.delay(minutes=10)

    # 7 Elution
    protocol.comment('Adding 50uL of elution buffer to samples...')
    for well, tip, tret, side in zip(magsamps, tips5, tips4, sides):
        loc1 = well.bottom().move(types.Point(x=side, y=0, z=2))
        loc2 = well.bottom().move(types.Point(x=side*-1, y=0, z=0.6))
        m300.pick_up_tip(tip)
        m300.aspirate(50, water)
        m300.dispense(50, loc2)
        for _ in range(8):
            m300.aspirate(30, loc1)
            m300.dispense(30, loc2)
        m300.blow_out()
        #SHAKE?
        m300.drop_tip(tret)

    protocol.comment('Incubating at room temp for 10 minutes.')
    protocol.delay(minutes=10)

    magdeck.engage()
    protocol.comment('Incubating on MagDeck for 2 minutes.')
    protocol.delay(minutes=2)

    #pause to add cold block
    m300.move_to(magplate.wells()[0].top(30))

    for _ in range(6):
        protocol.set_rail_lights(not protocol.rail_lights_on)
        protocol.delay(seconds=1)
    protocol.pause('Please place PCR plate in slot 7. Click RESUME when ready')


    protocol.comment('Transferring elution to final plate...')
    m300.flow_rate.aspirate = 20
    for src, dest, tip, tret, s in zip(magsamps, elutions, tips6, tips5, sides):
        m300.pick_up_tip(tip)
        #slow down asp ?
        m300.aspirate(50, src.bottom().move(types.Point(x=s, y=0, z=0.6)))
        m300.dispense(50, dest)
        #SHAKE?
        m300.drop_tip(tret)


    magdeck.disengage()
    protocol.comment('Congratulations! The protocol is complete!')
