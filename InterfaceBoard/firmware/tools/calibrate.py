# Steps DAC using key up and down

import argparse
import keyboard
import serial
import sys
import csv
from termios import tcflush, TCIFLUSH

MAX_DAC_VAL = 0x0FFF

UART_MIDI_BAUDRATE = 31250

SYSEX_MANUFACTURER_ID = 0x7D
SYSEX_START = 0xF0
SYSEX_END = 0xF7

SYSEX_CMD_SET_DAC = 0x01

parser = argparse.ArgumentParser(
    description="Steps DAC of Dampflog using key up and down"
)

parser.add_argument(
    "-p", "--port", type=str, default="/dev/ttyUSB0", help="Serial port"
)

parser.add_argument("-o", "--output", type=str, default="midi_2_dac.h", help="Output")

args = parser.parse_args()


def clear_terminal():
    print("\033[H\033[J", end="")


def set_dac(ser, value):
    if value < 0 or value > MAX_DAC_VAL:
        raise ValueError("DAC value out of range")
    msg = bytes(
        [
            SYSEX_START,
            SYSEX_MANUFACTURER_ID,
            SYSEX_CMD_SET_DAC,
            value >> 8,
            value & 0xFF,
            SYSEX_END,
        ]
    )
    ser.write(msg)


ser = serial.Serial(args.port, UART_MIDI_BAUDRATE)
dac_val = 0
first_note_provided = False
note = 0
ignore_next_enter = False


def handle_key(key):
    global dac_val
    global first_note_provided
    global note
    global mutex
    global ignore_next_enter

    if key.name == "up":
        dac_val += 1
        clear_terminal()

    elif key.name == "down":
        dac_val -= 1
        clear_terminal()

    elif key.name == "enter":
        # Workaround for keyboard lib queuing enter key from input()
        if ignore_next_enter:
            ignore_next_enter = False
            return

        if not first_note_provided:
            print("Please specify the midi note number for the first note:")
            tcflush(sys.stdin, TCIFLUSH)
            note = int(input())
            first_note_provided = True
            ignore_next_enter = True
        else:
            note += 1

        if note > 127:
            print(
                "All notes already assigned, please press esc to generate header file"
            )
            return

        midi_2_dac[note] = dac_val
        print("Assigned midi note {} to DAC value {}".format(note, dac_val))
        return

    elif key.name == "esc":
        for i in range(note, 128):
            midi_2_dac[i] = MAX_DAC_VAL

        csv_file = args.output.replace(".h", ".csv")
        print("Generating CSV file at: {}".format(csv_file))
        with open(csv_file, "w") as f:
            writer = csv.writer(f)
            for i in range(128):
                writer.writerow([i, midi_2_dac[i]])

        print("Generating C header with lookup table at: {}".format(args.output))
        with open(args.output, "w") as f:
            guard = args.output.upper().replace(".", "_") + "_INCLUDED"
            f.write("#ifndef " + guard + "\n")
            f.write("#define " + guard + "\n")
            f.write("// This file is autogenerated by calibrate.py\n")
            f.write("// Do not edit\n")
            f.write("#include <stdint.h>\n")
            f.write("const uint16_t midi_2_dac[128] = {")
            for i in range(128):
                f.write(str(midi_2_dac[i]))
                if i < 127:
                    f.write(", ")
                f.write("\n")
            f.write("};\n")
            f.write("#endif\n")
        raise KeyboardInterrupt

    else:
        return

    if dac_val < 0:
        dac_val = 0
    elif dac_val > MAX_DAC_VAL:
        dac_val = MAX_DAC_VAL

    set_dac(ser, dac_val)
    print("DAC value: {}\n".format(dac_val))


midi_2_dac = [0] * 128

print()
print("Dampflog: Calibration of MIDI to DAC values")
print("==========================================")
print("Please connect the Dampflog to a Tuner")
print("To increase the DAC value press the up key")
print("To decrease the DAC value press the down key")
print("To end the calibration press the esc key, a c header file will be generated")
print()
print("Press enter to assign midi notes to the current DAC value")


keyboard.on_press(handle_key)

while True:
    pass
