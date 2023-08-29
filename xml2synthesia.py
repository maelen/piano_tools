#!/usr/bin/env python3

import logging
import argparse
import os
import sys
import subprocess
import hashlib
from lxml import etree

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
    @classmethod
    def extract(cls, musicxml_file, mscx_file):
        musicxml_tree = etree.parse(musicxml_file)
        mscx_tree = etree.parse(mscx_file)
        metatag_el = mscx_tree.xpath('/museScore/Score')[0].findall('metaTag')
        metatag = {}
        for element in metatag_el:
            metatag[element.get('name')]=element.text
        title=metatag.get('workTitle')
        subtitle=metatag.get('subtitle')
        rating=metatag.get('rating', 1)
        difficulty=metatag.get('difficulty', 1)
        composer=metatag.get('composer')
        arranger=metatag.get('arranger')
        copy_right=metatag.get('copyright')
        tags=metatag.get('tags')        
        group=metatag.get('group')
        subgroup=metatag.get('subgroup')

        with open(musicxml_file, "rb") as f:
          file_hash = hashlib.md5()
          while chunk := f.read(8192):
              file_hash.update(chunk)
        unique_id=file_hash.hexdigest()

        part = musicxml_tree.xpath('/score-partwise/part')
        tick = 0
        song_fingering = []
        bookmarks = ''
        for measure in part[0].xpath("measure"):
          measure_number=f"{measure.attrib['number']}"
          rehearsal=measure.find('.//rehearsal')
          if rehearsal is not None:
              bookmarks += f'{measure_number},{rehearsal.text};'
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
                        fingering = finger_convert[staff].get(fingering_el.text,'-')
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
        song = f'<Song Version="1" ' + \
               f'UniqueId="{unique_id}" ' + \
               f'Title="{title}" ' + \
               f'Subtitle="{subtitle}" ' + \
               f'Rating="{rating}" ' + \
               f'Difficulty="{difficulty}" ' + \
               f'Composer="{composer}" ' + \
               f'Arranger="{arranger}" ' + \
               f'Copyright="{copy_right}" ' + \
               f'Tags="{tags}" ' + \
               f'Bookmarks="{bookmarks[:-1]}" ' + \
               f'Group="{group}" ' + \
               f'Subgroup="{subgroup}" ' + \
               f'FingerHints="{song_fingering}"/>'
        return song

    @classmethod
    def process(cls, input_file):
        output = input_file.rsplit('.', 1)[0]
        musicxml_filename=f"{output}.musicxml"
        mscx_filename=f"{output}.mscx"
        try:
            subprocess.run(["musescore3", input_file, "-o", musicxml_filename])
            subprocess.run(["musescore3", input_file, "-o", mscx_filename])
        except:
            print("File conversion failed. Is musescore in your search path ?")
            sys.exit(1)
        song_xml = Synthesia.extract(musicxml_filename, mscx_filename)
        os.remove(f"{mscx_filename}")

        return song_xml


def process_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--folder", default=".", help="musescore input file")
    parser.add_argument("-d", "--debug", default="WARN", help="Select log level used for debugging")
    args = parser.parse_args()
    return args

def main():
    args = process_args()
    logging.basicConfig(level=logging._nameToLevel[args.debug])

    songs = []
    for file in os.listdir(args.folder):
        if file.endswith('.mscz'):
            print(file)
            song_xml=Synthesia.process(file)
            songs.append(song_xml)
    songs="<Songs>\n    "+"\n    ".join(songs)+"\n  </Songs>"
    groups=""

    metadata_text = \
f"""
<?xml version="1.0" encoding="UTF-8" ?>
<SynthesiaMetadata Version="1">
  {songs}{groups}
</SynthesiaMetadata>"""   

    with open(f"{args.folder}/metadata.synthesia", "w") as synthesia_file:        
        synthesia_file.write(metadata_text)

if __name__ == "__main__":
    main()
