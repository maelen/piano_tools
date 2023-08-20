#!/usr/bin/env python3

import logging
import argparse
import tempfile
import os
import sys
import subprocess
import hashlib
import base64
from lxml import etree
from dicttoxml import dicttoxml
from xml.dom.minidom import parseString

finger_convert = {"1":{"1":"6",
                       "2":"7",
                       "3":"8",
                       "4":"9",
                       "5":"0"},
                  "2":{"1":"1",
                       "2":"2",
                       "3":"3",
                       "4":"4",
                       "5":"5"}}

class Synthesia:
    # <Song Version="1" UniqueId="1234" Title="Some Song Title" Rating="75" Bookmarks="1,Intro;15;24,Chorus;36" />
    @classmethod
    def export_musicxml_to_synthesia(cls, xml_file):
        tree = etree.parse(xml_file)
        work = tree.xpath('/score-partwise/work')
        for element in work:
          title=element.find('work-title').text

        with open(xml_file, "rb") as f:
          file_hash = hashlib.md5()
          while chunk := f.read(8192):
              file_hash.update(chunk)
        unique_id=file_hash.hexdigest()

        part = tree.xpath('/score-partwise/part')
        tick = 0
        song_fingering = []
        for measure in part[0].xpath("measure"):
          measure_number=f"{measure.attrib['number']}"
          song_fingering.append([])
          for element in measure.xpath("note|backup|forward"):
            grace = element.find("grace")
            if grace is not None:
              continue
            duration = element.find("duration")
            if duration is not None:
              duration = int(int(duration.text)) if duration is not None else 0
            if element.tag == 'note':
              staff = element.find('staff').text
              fingering_el = element.find('notations/technical/fingering')
              rest = element.find('rest')
              pitch = element.find('pitch')
              tie_start = element.find('tie[@type="start"]')
              tie_stop = element.find('tie[@type="stop"]')
              if rest is not None:
                  tick += duration
              else:
                if pitch is not None:
                  step = pitch.find('step')
                  step = step.text if step is not None else ''
                  alter = pitch.find('alter')
                  alter = int(alter.text) if alter is not None else 0
                  chord = element.find('chord')
                  if chord is None:
                    event_start = tick
                  if tie_stop is None:
                    if staff in ["1","2"]:
                      if fingering_el is not None:
                        fingering = finger_convert[staff][fingering_el.text]
                      else:
                        fingering = "-"
                      song_fingering[-1].append({'tick':event_start, 'fingering':fingering})
                      #print(f'S:{staff}T:{event_start}:{step}:{fingering} ')
                  if chord is None:
                    tick += duration
            elif element.tag == 'forward':
              tick += duration
            elif element.tag == 'backup':
              tick -= duration

        for i, measure in enumerate(song_fingering):
          entries_sorted = sorted(measure, key=lambda f: f['tick'])
          fingering_sorted = [ f['fingering'] for f in entries_sorted ]
          song_fingering[i] = f' m{i+1}:{"".join(fingering_sorted)}'
        song_fingering = "".join(song_fingering)
        song = f'<Song Version="1" UniqueId="{unique_id}" Title="{title}"  FingerHints="{song_fingering}"/>'
        return song

def process_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="musicxml or musescore input file")
    parser.add_argument("output", nargs='?', help="optional output file if not using default")
    parser.add_argument("-d", "--debug", default="WARN", help="Select log level used for debugging")
    args = parser.parse_args()
    return args

def main():
    args = process_args()
    logging.basicConfig(level=logging._nameToLevel[args.debug])
    output = args.output if args.output is not None else args.input.rsplit('.', 1)[0]

    if not os.path.isfile(args.input):
        print("File does not exist: {}".format(args.input))
        sys.exit(-1)
    musicxml_filename=f"{output}.musicxml"
    try:
        subprocess.run(["musescore3", args.input, "-o", musicxml_filename])
    except:
        print("Partition synthesia file not generated. Is musescore in your search path ?")
        sys.exit(1)
    synthesia_xml = Synthesia.export_musicxml_to_synthesia(musicxml_filename)
    synthesia_file = open(f"{output}.synthesia", "w")
    n = synthesia_file.write(synthesia_xml)
    synthesia_file.close()

    print(f"{output}.synthesia has been created\n")
#    os.remove(f"{output}_acc.mid")
#    os.remove(f"{output}_mel.mid")


if __name__ == "__main__":
    main()
