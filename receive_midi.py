#!/usr/bin/env python3

# import logging
# import argparse
# import subprocess
# import tempfile
# import os
# import sys
# import threading
# import mido
# from lxml import etree
# import time
# import multitimer
from midi_conversion import  MidiHandler

# notes_base_value = {'C':12, 'D':14, 'E':16, 'F':17, 'G':19, 'A':21, 'B':23}

# Read XML file
# Put values in a list
# PLayon keyboard
# Compare performance with original

# class MidiHandler():
#
#     def __init__(self, port=None, bpm=None):
#         self.bpm = bpm
#         self.port = port
#         self.tick = 0
#
#     def get_beat_time(self):
#         return self.bpm / (24 * 60)
#
#     def process_midi_events(self):
#         self.tick += 1
#         for msg in self.port.iter_pending():
#             print(self.tick)
#             print(self.tick, msg)


def main():
    # port = mido.open_input('VMPK Output')
    bpm = 80
    midi_handler = MidiHandler(port='VMPK Output', bpm=bpm)
    # t = multitimer.MultiTimer(midi_handler.get_beat_time(), midi_handler.process_midi_events)

    # print(mido.get_input_names())

    midi_handler.start()


if __name__ == "__main__":
    main()
