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
    parser.add_argument("input", help="musicxml or musescore input file")
    parser.add_argument("output", nargs='?', help="optional output file if not using default")
    parser.add_argument("-c", "--channel", type=int, default=3, help="Midi channel used for left hand. Right hand uses next channel")
    parser.add_argument("-nr", "--norepeat", action='store_false', help="Don't reuse last chord for next measures")
    parser.add_argument("-w", "--overwrite", action='store_true', help="Regenerate accompaniment mma file even if it exists")
    parser.add_argument("-d", "--debug", default="WARN", help="Select log level used for debugging")
    args = parser.parse_args()
    return args


def main():
    args = process_args()
    logging.basicConfig(level=logging._nameToLevel[args.debug])
    if not os.path.isfile(args.input):
        print("File does not exist: {}".format(args.input))
        sys.exit(-1)
    with tempfile.NamedTemporaryFile(suffix='.musicxml') as fp:
        try:
            subprocess.run(["musescore3", args.input, "-o", fp.name])
        except:
            print("Partition midi file not generated. Is musescore in your search path ?")
            sys.exit(1)
        midi_track = MidiConversion.midi_conversion(fp.name,192,args.channel)
        output = args.output if args.output is not None else args.input.rsplit('.', 1)[0]
        write_midi(midi_track, f"{output}_mel.mid")
        if args.overwrite or not os.path.exists(f"{output}.mma"):
          mma_file = open(f"{output}.mma", "w")
          mma_file.write(MmaConversion.mma_conversion(fp.name, repeat_chord=args.norepeat))
          mma_file.close()
        try:
            subprocess.run(["mma", f"{output}.mma", "-xNOCREDIT", "-f", f"{output}_acc.mid"])
        except:
            print("Accompaniment not generated. Is mma in your search path ?")
            sys.exit(1)
        merged_mid = merge_midi(f"{output}_mel.mid", f"{output}_acc.mid")
        merged_mid.save(f"{output}.mid")
        print(f"{output}.mid has been created\n")
        os.remove(f"{output}_acc.mid")
        os.remove(f"{output}_mel.mid")


if __name__ == "__main__":
    main()

