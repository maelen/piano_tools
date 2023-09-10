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
    def process_unique_id(cls, mxl_filename):
        with open(mxl_filename, "rb") as f:
            file_hash = hashlib.md5()
            while chunk := f.read(8192):
                file_hash.update(chunk)
        unique_id=file_hash.hexdigest()
        return unique_id
    
    @classmethod
    def process_metadata(cls, mscx_filename):
        mscx_tree = etree.parse(mscx_filename)
        metatag_el = mscx_tree.xpath('/museScore/Score')[0].findall('metaTag')
        metatag = {}
        metadata = {}
        for element in metatag_el:
            metatag[element.get('name')]=element.text
        metadata['title']=metatag.get('workTitle')
        metadata['subtitle']=metatag.get('subtitle')
        metadata['rating']=metatag.get('rating', 1)
        metadata['difficulty']=metatag.get('difficulty', 1)
        metadata['composer']=metatag.get('composer')
        metadata['arranger']=metatag.get('arranger')
        metadata['copy_right']=metatag.get('copyright')
        metadata['tags']=metatag.get('tags')        
        metadata['group']=metatag.get('group')
        metadata['subgroup']=metatag.get('subgroup')
        return metadata

    @classmethod
    def process_musicxml(cls, musicxml_filename):
        musicxml = {}
        musicxml_tree = etree.parse(musicxml_filename)
        part = musicxml_tree.xpath('/score-partwise/part')

        tick = 0
        musicxml = {'song_fingering': [], 'bookmarks': [], 'hand_part': []}
        i=0
        measures=part[0].xpath("measure")
        repeat_start = 0
        repeat_direction =  'forward'
        repeat_times = 0
        while i < len(measures):
          measure = measures[i]
          rehearsal=measure.find('.//rehearsal')
          if rehearsal is not None:
              musicxml['bookmarks'].append(rehearsal.text)
          else:
              musicxml['bookmarks'].append(None)
          musicxml['song_fingering'].append([])
          musicxml['hand_part'].append([])
          for element in measure.xpath("note|backup|forward|barline"):
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
                        fingering=fingering_el.text.split('-')
                        fingering = 's'.join([finger_convert[staff].get(finger,'-') for finger in fingering])
                      else:
                        fingering = "-"
                      hand = "R" if staff == "1" else "L"
                      musicxml['song_fingering'][-1].append({'tick':event_start, 'fingering':fingering})
                      musicxml['hand_part'][-1].append({'tick':event_start, 'hand':hand})
                      #print(f'S:{staff}T:{event_start}:{step}:{fingering} ')
                  if chord is None:
                    tick += duration
            elif element.tag == 'forward':
              tick += duration
            elif element.tag == 'backup':
              tick -= duration
            elif element.tag == 'barline':
              ending = element.find('ending')
              if ending is not None:
                ending_number = ending.find('number')
                ending_type = ending.find('type')
              repeat = element.find('repeat')
              if repeat is not None:
                  repeat_direction = repeat.attrib['direction']
                  if repeat_direction == 'forward':
                    repeat_start = i
                  elif repeat_direction == 'backward':
                    repeat_times_el = repeat.attrib.get('times', '1')
                    if repeat_times < int(repeat_times_el):
                      repeat_times += 1
                    else:
                      repeat_start = 0
                      repeat_direction = 'forward'
                    
          if repeat_direction == 'backward':
            i = repeat_start
            repeat_direction = 'forward'
          elif repeat_direction == 'forward':
            i += 1
        bookmarks = ''
        for i, bookmark in enumerate(musicxml['bookmarks']):
            if bookmark is not None:
              bookmarks += f'{i+1},{bookmark};'
        musicxml['bookmarks'] = bookmarks[:-1]
        for i, measure in enumerate(musicxml['song_fingering']):
            entries_sorted = sorted(measure, key=lambda f: f['tick'])
            fingering_sorted = [ f['fingering'] for f in entries_sorted ]
            musicxml['song_fingering'][i] = f' m{i+1}: {"".join(fingering_sorted)}'
        musicxml['song_fingering'] = "".join(musicxml['song_fingering'])
        for i, measure in enumerate(musicxml['hand_part']):
            entries_sorted = sorted(measure, key=lambda f: f['tick'])
            hand_part_sorted = [ f['hand'] for f in entries_sorted ]
            musicxml['hand_part'][i] = f' m{i+1}: {"".join(hand_part_sorted)}'
        musicxml['hand_part'] = "".join(musicxml['hand_part'])
        return musicxml

    @classmethod
    def process(cls, input_file):
        output = input_file.rsplit('.', 1)[0]
        musicxml_filename=f"{output}.musicxml"
        mscx_filename=f"{output}.mscx"
        mxl_filename=f"{output}.mxl"
        try:
            subprocess.run(["musescore3", input_file, "-o", musicxml_filename])
            subprocess.run(["musescore3", input_file, "-o", mscx_filename])
            subprocess.run(["musescore3", input_file, "-o", mxl_filename])
        except:
            print("File conversion failed. Is musescore in your search path ?")
            sys.exit(1)
                    
        unique_id = Synthesia.process_unique_id(mxl_filename)     
        metadata = Synthesia.process_metadata(mscx_filename)
        musicxml = Synthesia.process_musicxml(musicxml_filename)       
        
        song_xml = '<Song Version="1" ' + \
               'UniqueId="' + unique_id + '" ' + \
               'Title="' + str(metadata['title']) + '" ' + \
               'Subtitle="' + str(metadata['subtitle']) + '" ' + \
               'Rating="' + str(metadata['rating']) + '" ' + \
               'Difficulty="' + str(metadata['difficulty']) + '" ' + \
               'Composer="' + str(metadata['composer']) + '" ' + \
               'Arranger="' + str(metadata['arranger']) + '" ' + \
               'Copyright="' + str(metadata['copy_right']) + '" ' + \
               'Tags="' + str(metadata['tags']) + '" ' + \
               'Parts="' + str(musicxml['hand_part']) + '" ' + \
               'Group="' + str(metadata['group']) + '" ' + \
               'Subgroup="' + str(metadata['subgroup']) + '" ' + \
               'FingerHints="' + str(musicxml['song_fingering']) + '" ' + \
               'Bookmarks="' + musicxml['bookmarks'] + '" ' + '/>'
        os.remove(f"{mscx_filename}")
        os.remove(f"{musicxml_filename}")

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
            song_xml=Synthesia.process(f'{args.folder}/{file}')
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
