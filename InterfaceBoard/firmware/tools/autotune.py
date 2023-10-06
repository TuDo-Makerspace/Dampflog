import serial
import time
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import argparse
import mido
from matplotlib import pyplot as plt

#####################################################
# Constants/Parameters
#####################################################

# DAC

MAX_DAC_VAL = 0x0FFF

# MIDI

MAX_MIDI_NOTE = 127
UART_MIDI_BAUDRATE = 31250

# Sysex

SYSEX_MANUFACTURER_ID = 0x7D
SYSEX_START = 0xF0
SYSEX_END = 0xF7

SYSEX_CMD_SET_DAC = 0x01
SYSEX_CMD_SET_GATE = 0x02
SYSEX_CMD_SET_GATE_CLOSE = 0x00
SYSEX_CMD_SET_GATE_OPEN = 0x01
SYSEX_WRITE_MIDI_2_DAC_LUT = 0x03

# Recording

MIDO_WAIT_TIME = 0.1        # seconds
# ATTACK_TIME = 0.01          # seconds
ATTACK_TIME = 0             # MIDO_WAIT_TIME aleardy does the job
RECORD_DURATION = 0.3       # seconds
RECORD_SAMPLE_RATE = 44100  # Hz
RECORD_CHANNELS = 1         # mono

# Oscillator Parameters

OSC_MIN_NOTE = 46 # A#2
OSC_MAX_NOTE = 76 # E5
OSC_STARTUP_SETTLE_TIME = 3 # seconds

#####################################################
# Step Table
#####################################################

# The step table stores the "expected" differences in DAC
# values (based on previous tuning) between each MIDI note.
# It allows the tuning algorithm to make an educated guess
# for the DAC value of the next note and then proceeds to
# fine tune from there. This saves a lot of time as the algorithm
# doesn't have to increment through every single DAC value.
# The step table has been generated from prior tuning.

STEP_TABLE = [
    1600,
    245,
    101,
    91,
    86,
    81,
    75,
    69,
    65,
    62,
    58,
    55,
    51,
    50,
    45,
    44,
    42,
    40,
    38,
    38,
    38,
    38,
    39,
    40,
    44,
    49,
    54,
    69,
    56,
    96,
    50
]

#####################################################
# Helper Functions
#####################################################

######## Recording ########

# Records a sample from the default input device
def record_sample(duration):
    myrecording = sd.rec(
        int(duration * RECORD_SAMPLE_RATE),
        samplerate=RECORD_SAMPLE_RATE,
        channels=1,
        dtype="float64",
    )
    sd.wait()
    return myrecording

# Plays a recorded sample (see record_sample)
def play_sample(sample):
    sd.play(sample, RECORD_SAMPLE_RATE)
    sd.wait()

######## Frequency Analysis ########

# Determines the frequency of a sample via postive zero intercepts
def get_freq(sample):
    positive_zero_intercepts = []
    for i in range(len(sample)):
        if i == 0:
            continue
        if sample[i] > 0 and sample[i - 1] < 0:
            positive_zero_intercepts.append(i)

    diffs = []
    for i in range(len(positive_zero_intercepts)):
        if i == 0:
            continue
        diffs.append(positive_zero_intercepts[i] - positive_zero_intercepts[i - 1])

    return RECORD_SAMPLE_RATE / np.mean(diffs)

# Determines the error in cents between a target frequency and a measured frequency
def error_in_cents(target_freq, measured_freq):
    return 1200 * np.log2(measured_freq / target_freq)

######## MIDI ########

WELL_TEMPERED_A = 440

# Converts a MIDI note number to a frequency
def midi_note_to_freq(note):
    return WELL_TEMPERED_A * 2 ** ((note - 69) / 12)

# Determines the closest MIDI note number to a frequency
def closest_midi_note_to_freq(freq):
    closest_note = int(round(12 * np.log2(freq / WELL_TEMPERED_A) + 69))
    error = freq - midi_note_to_freq(closest_note)
    return closest_note, error

# Converts a MIDI note number to a note name and octave (ex. 46 becomes A#2)
def midi_note_to_name_oct(midinote):
    notes = [
        "C",
        "C#",
        "D",
        "D#",
        "E",
        "F",
        "F#",
        "G",
        "G#",
        "A",
        "A#",
        "B",
    ]
    return notes[midinote % 12] + str(midinote // 12 - 1)

######## DAC ########

def uint14_to_midi_data(val):
    return [val >> 7, val & 0x7F]

# Sets the DAC value via sysex
def set_dac(port, value):
    if value < 0 or value > MAX_DAC_VAL:
        raise ValueError("DAC value out of range")
    d = uint14_to_midi_data(value)
    msg = mido.Message("sysex", data=[SYSEX_MANUFACTURER_ID, SYSEX_CMD_SET_DAC, d[0], d[1]])
    port.send(msg)
    time.sleep(MIDO_WAIT_TIME)

######## MIDI to DAC Look-up Table ########

def write_dac(note, value):
    if value < 0 or value > MAX_DAC_VAL:
        raise ValueError("DAC value out of range")
    d = uint14_to_midi_data(value)
    msg = mido.Message("sysex", data=[SYSEX_MANUFACTURER_ID, SYSEX_WRITE_MIDI_2_DAC_LUT, note, d[0], d[1]])
    port.send(msg)
    time.sleep(MIDO_WAIT_TIME)

######## GATE ########

# Sets the gate via sysex
def set_gate(port, value):
    if value:
        value = SYSEX_CMD_SET_GATE_OPEN
    else:
        value = SYSEX_CMD_SET_GATE_CLOSE
    msg = mido.Message("sysex", data=[SYSEX_MANUFACTURER_ID, SYSEX_CMD_SET_GATE, value])
    port.send(msg)

######## Tuning ########

# Measures the frequency after a DAC value change.
# Measurements begin after the attack time has passed
# The duration determines how long the sample to be measured is
def msr_after_dac_chng(ser, value, attack, duration):
    set_dac(ser, value)
    time.sleep(attack)
    sample = record_sample(duration)
    return get_freq(sample)

# Attempts to find a DAC value that produces a frequency close to the target frequency
# with the given step size.
# Returns the DAC value afer execution, the overshoot (Hz), and the undershoot (Hz)
def dac_target_freq(ser, start, step, target_freq):
    dac_val = start
    prev_f = 0

    while True:
        if dac_val == start:
            prev_f = msr_after_dac_chng(ser, dac_val, ATTACK_TIME, RECORD_DURATION)
        else:
            f = msr_after_dac_chng(ser, dac_val, ATTACK_TIME, RECORD_DURATION)

            if (step > 0 and f > target_freq) or (step < 0 and f < target_freq):
                overshoot_error = error_in_cents(target_freq, f)
                undershoot_error = error_in_cents(target_freq, prev_f)
                return dac_val, overshoot_error, undershoot_error

            prev_f = f
        dac_val += step

        if dac_val == MAX_DAC_VAL:
            break

    return None

# Performs a coarse, then fine tune to find a DAC value that produces a frequency
# close to the target frequency.
# Returns the DAC value that yields the closest frequency to the target frequency
# and the error in cents.
def coarse_fine_tune(ser, start, coarse_step, fine_step, target_freq):
    incr = True
    start_f = msr_after_dac_chng(ser, start, ATTACK_TIME, RECORD_DURATION)    
    
    if start_f > target_freq:
        incr = False
        coarse_step = -coarse_step
    
    dac_val, overshoot, undershoot = dac_target_freq(
        ser, start, coarse_step, target_freq
    )

    overshot = abs(overshoot) < abs(undershoot)

    if (incr and overshot) or (not incr and not overshot):
        fine_step = -fine_step

    if not overshot:
        dac_val -= coarse_step

    dac_val, overshoot, undershoot = dac_target_freq(
        ser, dac_val, fine_step, target_freq
    )

    if abs(overshoot) > abs(undershoot):
        dac_val -= fine_step
        error = undershoot
    else:
        error = overshoot
    
    return dac_val, error

#####################################################
# Argument Parsing
#####################################################

parser = argparse.ArgumentParser(
    description="Automatically tunes the Dampflog"
)

# parser.add_argument(
#     "-o", "--output", type=str, help="Output for lookup table header", required=True
# )

parser.add_argument(
    "-m", "--manual", type=int, help="Manually tune a specific MIDI note", required=False
)

args = parser.parse_args()

#####################################################
# Intialization
#####################################################

manual_note = args.manual

if manual_note is None:
    print("██████   █████  ███    ███ ██████  ███████ ██       ██████   ██████  ")
    print("██   ██ ██   ██ ████  ████ ██   ██ ██      ██      ██    ██ ██       ")
    print("██   ██ ███████ ██ ████ ██ ██████  █████   ██      ██    ██ ██   ███ ")
    print("██   ██ ██   ██ ██  ██  ██ ██      ██      ██      ██    ██ ██    ██ ")
    print("██████  ██   ██ ██      ██ ██      ██      ███████  ██████   ██████  ")
    print("                                                                     ")
    print("                                                                     ")
    print("████████ ██    ██ ███    ██ ███████ ██████                           ")
    print("   ██    ██    ██ ████   ██ ██      ██   ██                          ")
    print("   ██    ██    ██ ██ ██  ██ █████   ██████                           ")
    print("   ██    ██    ██ ██  ██ ██ ██      ██   ██                          ")
    print("   ██     ██████  ██   ████ ███████ ██   ██                          ")
    print("                                                                     ")
    print("                 _-====-__-======-__-========-_____-============-__")
    print("               _(                                                 _)")
    print("            OO(           _/_ _  _  _/_   _/_ _  _  _/_           )_")
    print("           0  (_          (__(_)(_) (__   (__(_)(_) (__            _)")
    print("         o0     (_                                                _)")
    print("        o         '=-___-===-_____-========-___________-===-dwb-='")
    print("      .o                                _________")
    print("     . ______          ______________  |         |      _____")
    print("   _()_||__|| ________ |            |  |_________|   __||___||__")
    print("  (BNSF 1995| |      | |            | __Y______00_| |_         _|")
    print(" /-OO----OO\"=\"OO--OO\"=\"OO--------OO\"=\"OO-------OO\"=\"OO-------OO\"=P")
    print("#####################################################################")
    print("                                                                     ")
    print("Preperation:")
    print("- Ensure the Dampflog is connected to the computer via MIDI")
    print("- Ensure the volume is turned down, but is NOT muted")
    print("- Ensure the audio output of the Dampflog is connected to the computer (ex. via an audio interface)")
    print("- Ensure the Dampflog output is selected as default input device on the computer")
    print("- Please ensure PORTAMENTO has been turned off before tuning")
    print("")

# ser = serial.Serial("/dev/ttyUSB0", UART_MIDI_BAUDRATE)
print("Available MIDI ports:")
while True:
    outputs = mido.get_output_names()
    n_outputs = len(outputs)
    for i in range(n_outputs):
        print("{}. {}".format(i, outputs[i]))
    print("")
    sel = int(input("Select MIDI output port: "))
    if sel < n_outputs:
        port = mido.open_output(outputs[sel])
        break
    print ("Invalid port number")
    print("")

if manual_note is not None:
    if manual_note < 0 or manual_note > MAX_MIDI_NOTE:
        print("Invalid MIDI note")
        exit(1)
    dac_val = int(input("Enter manual DAC value: "))
    if dac_val < 0 or dac_val > MAX_DAC_VAL:
        print("Invalid DAC value")
        exit(1)
    write_dac(manual_note, dac_val)
    print("Assigned DAC value {} to MIDI note {}".format(dac_val, manual_note))
    exit(0)

print("Press enter to begin the tuning process: ")
input()

#####################################################
# Tuning process
#####################################################

while True:
    midi_2_dac = {}

    # Open/Enable GATE
    set_gate(port, True)
    print("GATE opened")

    print("Waiting for oscillator to settle...")
    time.sleep(OSC_STARTUP_SETTLE_TIME)

    print("Beginning tuning process...")
    # Set DAC to 0 and give it a second to settle
    freq = msr_after_dac_chng(port, 0, 1, RECORD_DURATION)

    #####################################################
    # Determine first note
    #####################################################

    # Determining the first note is treated as a special case because
    # the DAC must first enter the transistors operating region, meaning
    # the first few hundred DAC values are guaranteed to be useless.
    # Additionally, the CV to frequency response around the first note (A#2)
    # is very low, meaning we don't have to be very precise to tune the first note.

    dac_val = 0

    # Sometimes the min. Note is already slightly greater than A#2
    if freq >= midi_note_to_freq(OSC_MIN_NOTE):
        midi_2_dac[OSC_MIN_NOTE] = 0
        print(
            "MIDI note: {} ({})   \tDAC value: {} \t\tError (cents): {}".format(
                midi_note_to_name_oct(OSC_MIN_NOTE), OSC_MIN_NOTE, dac_val, error_in_cents(midi_note_to_freq(OSC_MIN_NOTE), freq)
            )
        )
        dac_val = STEP_TABLE[0] # Pretend first note succeeded as second note is not as flaky
    else:
        dac_val, error = coarse_fine_tune(
            port, dac_val, STEP_TABLE[0], 10, midi_note_to_freq(OSC_MIN_NOTE)
        )

        midi_2_dac[OSC_MIN_NOTE] = dac_val

        print(
            "MIDI note: {} ({})\tDAC value: {} \tError (cents): {}".format(
                midi_note_to_name_oct(OSC_MIN_NOTE), OSC_MIN_NOTE, dac_val, error
            )
        )

    #####################################################
    # Determine remaining notes
    #####################################################

    second_note = OSC_MIN_NOTE + 1
    fine_step = 1

    for i in range(second_note, OSC_MAX_NOTE + 1):
        dac_val, error = coarse_fine_tune(
            port, dac_val, STEP_TABLE[i - OSC_MIN_NOTE], fine_step, midi_note_to_freq(i)
        )

        midi_2_dac[i] = dac_val

        print(
            "MIDI note: {} ({})   \tDAC value: {} \tError (cents): {}".format(
                midi_note_to_name_oct(i), i, dac_val, error
            )
        )

    set_gate(port, False)
    print("GATE closed")

    brk = True

    while True:
        answer = input("Do you wish to tune the device again? (y/N): ")
        if answer.lower() == "y":
            brk = False
            break
        elif answer.lower() == "n" or answer == "":
            break
        else:
            print("Invalid input")

    if brk:
        break

#####################################################
# Write results into MIDI to DAC look-up table
#####################################################
print("Writing results into MIDI to DAC look-up table...")
for i in range(0, MAX_MIDI_NOTE + 1):
    if i < OSC_MIN_NOTE:
        write_dac(i, 0)
    elif i > OSC_MAX_NOTE:
        write_dac(i, MAX_DAC_VAL)
    else:
        write_dac(i, midi_2_dac[i])

port.close()

print("Tuning complete!")

#####################################################
# Generate C header file
#####################################################

# with open(args.output, "w") as f:
#     guard = "MIDI_2_DAC_INCLUDED"
#     f.write("#ifndef " + guard + "\n")
#     f.write("#define " + guard + "\n")
#     f.write("// This file is autogenerated by tune.py\n")
#     f.write("// MIDI to DAC lookup table\n")
#     f.write("#include <stdint.h>\n")
#     f.write("#include <midirx_msg.h>\n")
#     f.write("const uint16_t midi_2_dac[MIDI_DATA_MAX_VAL + 1] = {")
#     f.write("\n")

#     for i in range(128):
#         if i < OSC_MIN_NOTE:
#             f.write("0")
#         elif i > OSC_MAX_NOTE:
#             f.write(str(MAX_DAC_VAL))
#         else:
#             f.write(str(midi_2_dac[i]))
        
#         if i < 127:
#             f.write(", ")
        
#         f.write("\t// " + midi_note_to_name_oct(i))
#         f.write("\n")

#     f.write("};\n")
#     f.write("#endif\n")

# print("Generated C header file: " + args.output)
# print("Tuning complete!")