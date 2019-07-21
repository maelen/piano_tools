#!/usr/bin/env python3

import logging
import argparse
from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo
from lxml import etree

notes_base_value = {'C':12, 'D':14, 'E':16, 'F':17, 'G':19, 'A':21, 'B':23}


def xmlconversion(xml_file):
    midi_events = []
    tree = etree.parse(xml_file)
    part = tree.xpath('/score-partwise/part')
    event_start = [0, 0]
    tick = [0, 0]
    for measure in part[0].xpath("measure"):
        attributes = measure.find('attributes')
        if attributes is not None:
            time = attributes.find('time')
            if time is not None:
                numerator = int(time.find('beats').text)
                denominator = int(time.find('beat-type').text)

                midi_events.append({'tick':tick[0], 'event':MetaMessage('time_signature',
                          numerator=numerator,
                          denominator=denominator)})
            staves = attributes.find('staves')
            if staves is not None:
                staves = int(staves.text)

        direction = measure.find('direction')
        if direction is not None:
            sound = direction.find('sound')
            if sound is not None:
                tempo = float(sound.get('tempo'))
                midi_events.append({'tick':tick[0], 'event':MetaMessage('set_tempo', tempo=bpm2tempo(tempo))})
            if  direction.xpath('direction-type/rehearsal'):
                midi_events.append({'tick':tick[0], 'event':MetaMessage('marker', text="0")})

        for note in measure.xpath("note"):
            duration = note.find("duration")
            duration = int(duration.text) if duration is not None else 0
            staff = note.find('staff')
            if staff is not None:
                staff = int(staff.text) - 1
            rest = note.find('rest')
            pitch = note.find('pitch')
            if rest is not None:
                tick[staff] += duration
            elif pitch is not None:
                chord = note.find('chord')
                if chord is None:
                    event_start[staff] = tick[staff]
                step = pitch.find('step')
                step = step.text if step is not None else ''
                alter = pitch.find('alter')
                alter = int(alter.text) if alter is not None else 0
                octave = pitch.find('octave')
                octave = int(octave.text) if octave is not None else 0
                midi_value = octave * 12 + notes_base_value[step] + alter
                midi_events.append({'tick':event_start[staff], 'event':Message('note_on',
                                  channel=3 if staff == 0 else 2,
                                  note=midi_value,
                                  velocity=80)})
                if chord is None:
                    tick[staff] += duration
                midi_events.append({'tick':tick[staff] - 1,
                           'event': Message('note_off',
                                            channel=3 if staff == 0 else 2,
                                            note=midi_value,
                                            velocity=80)})
    return midi_events


def write_midi(midi_events, midi_file):
    division = 768
    mid = MidiFile(type=0, ticks_per_beat=division)
    track = MidiTrack()
    mid.tracks.append(track)
    previous_tick = 0
    for entry in sorted(midi_events, key=lambda i: i['tick']) :
        updated_event = entry['event'].copy(time=entry['tick'] - previous_tick)
        track.append(updated_event)
        logging.info('E {}:{}'.format(entry['tick'], updated_event))
        previous_tick = entry['tick']
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
    midi_events = xmlconversion(args.input)
    output = args.output if args.output is not None else args.input.rsplit('.', 1)[0] + ".mid"
    write_midi(midi_events, output)


if __name__ == "__main__":
    main()

