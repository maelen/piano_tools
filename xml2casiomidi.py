#!/usr/bin/env python3

import logging
import argparse
from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo
from lxml import etree

notes_base_value = {'C':12, 'D':14, 'E':16, 'F':17, 'G':19, 'A':21, 'B':23}


def xmlconversion(xml_file):
    midi_events = [{'divisions':768}]
    tree = etree.parse(xml_file)
    part = tree.xpath('/score-partwise/part')
    event_start = [0, 0]
    tick = 0
    velocity = 90
    multiplier = 1
    for measure in part[0].xpath("measure"):
        attributes = measure.find('attributes')
        if attributes is not None:
            divisions = attributes.find('divisions')
            if divisions is not None:
                division = int(divisions.text)
                multiplier = 1  if division == 768 else 768 / division
                midi_events[0]['divisions'] = int(division * multiplier)
            time = attributes.find('time')
            if time is not None:
                numerator = int(time.find('beats').text)
                denominator = int(time.find('beat-type').text)

                midi_events.append({'tick':tick, 'event':MetaMessage('time_signature',
                          numerator=numerator,
                          denominator=denominator)})
            staves = attributes.find('staves')
            if staves is not None:
                staves = int(staves.text)

        directions = measure.findall('direction')
        for direction in directions:
            sound = direction.find('sound')
            if sound is not None:
                tempo = sound.get('tempo')
                if tempo is not None:
                    midi_events.append({'tick':tick, 'event':MetaMessage('set_tempo', tempo=bpm2tempo(float(tempo)))})
                dynamics = sound.get('dynamics')
                if dynamics is not None:
                    velocity = int(round(float(dynamics)))
            if  direction.xpath('direction-type/rehearsal'):
                midi_events.append({'tick':tick, 'event':MetaMessage('marker', text="0")})

        for element in measure.xpath("note|backup|forward"):
            duration = element.find("duration")
            duration = int(int(duration.text) * multiplier) if duration is not None else 0
            if element.tag == 'note':
                staff = element.find('staff')
                if staff is not None:
                    staff = int(staff.text) - 1
                rest = element.find('rest')
                pitch = element.find('pitch')
                if rest is not None:
                    tick += duration
                elif pitch is not None:
                    chord = element.find('chord')
                    if chord is None:
                        event_start = tick
                    step = pitch.find('step')
                    step = step.text if step is not None else ''
                    alter = pitch.find('alter')
                    alter = int(alter.text) if alter is not None else 0
                    octave = pitch.find('octave')
                    octave = int(octave.text) if octave is not None else 0
                    midi_value = octave * 12 + notes_base_value[step] + alter
                    midi_events.append({'tick':event_start, 'event':Message('note_on',
                                      channel=3 if staff == 0 else 2,
                                      note=midi_value,
                                      velocity=velocity)})
                    if chord is None:
                        tick += duration
                    midi_events.append({'tick':tick,
                               'event': Message('note_off',
                                                channel=3 if staff == 0 else 2,
                                                note=midi_value,
                                                velocity=velocity)})
            elif element.tag == 'forward':
                tick += duration
            elif element.tag == 'backup':
                tick -= duration
    return midi_events


def write_midi(midi_events, midi_file):
    track = MidiTrack()
    previous_tick = 0
    midi_attributes = midi_events[0]
    midi_events = midi_events[1:]
    for entry in sorted(midi_events, key=lambda i: i['tick']) :
        updated_event = entry['event'].copy(time=entry['tick'] - previous_tick)
        track.append(updated_event)
        logging.info('E {}:{}'.format(entry['tick'], updated_event))
        previous_tick = entry['tick']
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
    midi_events = xmlconversion(args.input)
    output = args.output if args.output is not None else args.input.rsplit('.', 1)[0] + ".mid"
    write_midi(midi_events, output)


if __name__ == "__main__":
    main()

