import logging
import mido
from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo
from lxml import etree
import multitimer




class MidiConversion:

    notes_base_value = {'C':12, 'D':14, 'E':16, 'F':17, 'G':19, 'A':21, 'B':23}

    @classmethod
    def midi_conversion(cls, xml_file, num_ticks=192):
        midi_events = [{'divisions':num_ticks}]
        tree = etree.parse(xml_file)
        part = tree.xpath('/score-partwise/part')
        event_start = 0
        tick = 0
        velocity = 90
        multiplier = 1
        for measure in part[0].xpath("measure"):
            attributes = measure.find('attributes')
            if attributes is not None:
                divisions = attributes.find('divisions')
                if divisions is not None:
                    division = int(divisions.text)
                    multiplier = int(num_ticks // division)
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
                rehearsal = direction.xpath('direction-type/rehearsal')
                if rehearsal:
                    midi_events.append({'tick':tick, 'event':MetaMessage('marker', text=f'{rehearsal[0].text}')})

            for element in measure.xpath("note|backup|forward"):
                duration = element.find("duration")
                duration = int(int(duration.text) * multiplier) if duration is not None else 0
                if element.tag == 'note':
                    staff = element.find('staff')
                    if staff is not None:
                        staff = int(staff.text) - 1
                    rest = element.find('rest')
                    pitch = element.find('pitch')
                    tie_start = element.find('tie[@type="start"]')
                    tie_stop = element.find('tie[@type="stop"]')
                    if rest is not None:
                        tick += duration
                    else:
                        if pitch is not None:
                            chord = element.find('chord')
                            if chord is None:
                                event_start = tick
                            step = pitch.find('step')
                            step = step.text if step is not None else ''
                            if tie_stop is None:
                                alter = pitch.find('alter')
                                alter = int(alter.text) if alter is not None else 0
                                octave = pitch.find('octave')
                                octave = int(octave.text) if octave is not None else 0
                                midi_value = octave * 12 + cls.notes_base_value[step] + alter
                                midi_events.append({'tick':event_start, 'event':Message('note_on',
                                                  channel=3 if staff == 0 else 2,
                                                  note=midi_value,
                                                  velocity=velocity)})
                            if chord is None:
                                tick += duration
                            if tie_start is None:
                                midi_events.append({'tick':tick,
                                           'event': Message('note_off',
                                                            channel=3 if staff == 0 else 2,
                                                            note=midi_value,
                                                            velocity=velocity)})
                elif element.tag == 'forward':
                    tick += duration
                elif element.tag == 'backup':
                    tick -= duration

        track = MidiTrack()
        previous_tick = 0
        midi_events = midi_events[1:]
        for entry in sorted(midi_events, key=lambda i: i['tick']) :
            updated_event = entry['event'].copy(time=entry['tick'] - previous_tick)
            track.append(updated_event)
            logging.info('E {}:{}'.format(entry['tick'], updated_event))
            previous_tick = entry['tick']

        return track


class MidiComparator:

    def __init__(self):
        pass
