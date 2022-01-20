#!/usr/bin/env python3

import logging
import argparse
from mido import MidiFile, merge_tracks, second2tick
import subprocess
import tempfile
import time
import os
import sys
from midi_conversion import  MidiConversion
from mma_conversion import  MmaConversion

def merge_midi(mid1_filename, mid2_filename):
    mid1 = MidiFile(mid1_filename, clip=True)
    mid2 = MidiFile(mid2_filename, clip=True)
    mid_list = []
    mid_list.append(mid1)
    mid_list.append(mid2)
    merged_track = merge_tracks(mid_list)
    merged_mid = MidiFile(type=1, ticks_per_beat=mid1.ticks_per_beat, clip=True)
    merged_mid.tracks.append(merged_track)
    tempo=500000
    for message in merged_mid.tracks[0]:
        if type(message.time) == float:
            message.time = round(second2tick(second=message.time, ticks_per_beat=mid1.ticks_per_beat,tempo=tempo))
        elif message.type == 'set_tempo':
            tempo = message.tempo
    return merged_mid

def write_midi(track, midi_file):
    midi_attributes = {'divisions':192}
    mid = MidiFile(type=0, ticks_per_beat=midi_attributes['divisions'])
    mid.tracks.append(track)
    mid.save(midi_file)


def process_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output", nargs='?')
    parser.add_argument("-d", "--debug", default="WARN")
    args = parser.parse_args()
    return args


def main():
    args = process_args()
    logging.basicConfig(level=logging._nameToLevel[args.debug])
    if not os.path.isfile(args.input):
        print("File does not exist: {}".format(args.input))
        sys.exit(-1)
    with tempfile.NamedTemporaryFile(suffix='.musicxml') as fp:
        subprocess.run(["musescore3", args.input, "-o", fp.name])
        midi_track = MidiConversion.midi_conversion(fp.name,192)
        output = args.output if args.output is not None else args.input.rsplit('.', 1)[0]
        write_midi(midi_track, f"{output}_mel.mid")
        mma_file = open(f"{output}.mma", "w")
        mma_file.write(MmaConversion.mma_conversion(fp.name))
        mma_file.close()
        subprocess.run(["mma", f"{output}.mma", "-xNOCREDIT", "-f", f"{output}_acc.mid"])
        merged_mid = merge_midi(f"{output}_mel.mid", f"{output}_acc.mid")
        merged_mid.save(f"{output}.mid")
        print(f"{output}.mid has been created\n")
        os.remove(f"{output}_acc.mid")
        os.remove(f"{output}_mel.mid")


if __name__ == "__main__":
    main()

