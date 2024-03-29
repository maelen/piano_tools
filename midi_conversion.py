import logging
import mido
from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo
from lxml import etree
import multitimer




class MidiConversion:

    notes_base_value = {'C':12, 'D':14, 'E':16, 'F':17, 'G':19, 'A':21, 'B':23}

    @classmethod
    def get_midi_note(cls,pitch=None):
        step = pitch.find('step')
        step = step.text if step is not None else ''
        alter = pitch.find('alter')
        alter = int(alter.text) if alter is not None else 0
        octave = pitch.find('octave')
        octave = int(octave.text) if octave is not None else 0
        return octave * 12 + cls.notes_base_value[step] + alter

    @classmethod
    def midi_conversion(cls, xml_file, num_ticks=192, lesson_channel=3):
        lh_channel=lesson_channel-1
        rh_channel=lh_channel+1
        midi_events = [{'divisions':num_ticks}]
        tree = etree.parse(xml_file)
        part = tree.xpath('/score-partwise/part')
        event_start = 0
        tick = 0
        velocity = 90
        multiplier = 1
        tempo = None
        for measure in part[0].xpath("measure"):
            attributes = measure.find('attributes')
            if attributes is not None:
                # Midi Divisions
                divisions = attributes.find('divisions')
                if divisions is not None:
                    division = int(divisions.text)
                    multiplier = int(num_ticks // division)
                    midi_events[0]['divisions'] = int(division * multiplier)
                # Midi Time Signature
                time = attributes.find('time')
                if time is not None:
                    numerator = int(time.find('beats').text)
                    denominator = int(time.find('beat-type').text)

                    midi_events.append({'tick':tick, 'event':MetaMessage('time_signature',
                              numerator=numerator,
                              denominator=denominator)})

            staff = 0
            for element in measure.xpath("note|backup|forward|direction"):
                grace = element.find("grace")
                if grace is not None:
                  continue
                duration = element.find("duration")
                if duration is not None:
                    duration = int(int(duration.text) * multiplier) if duration is not None else 0
                if element.tag == 'note':
                    staff_el = element.find('staff')
                    if staff_el is not None:
                        staff = int(staff_el.text) - 1
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
                            midi_value = MidiConversion.get_midi_note(pitch)
                            if tie_stop is None:
                                midi_events.append({'tick':event_start, 'event':Message('note_on',
                                                  channel=rh_channel if staff == 0 else lh_channel,
                                                  note=midi_value,
                                                  velocity=velocity)})
                            if chord is None:
                                tick += duration
                            if tie_start is None:
                                midi_events.append({'tick':tick, 'event': Message('note_off',
                                                   channel=rh_channel if staff == 0 else lh_channel,
                                                   note=midi_value,
                                                   velocity=velocity)})
                elif element.tag == 'forward':
                    tick += duration
                elif element.tag == 'backup':
                    tick -= duration
                elif element.tag == 'direction':
                  sound = element.find('sound')
                  if sound is not None:
                      # Midi Tempo
                      if tempo is None:
                        tempo_tmp = sound.get('tempo')
                        if tempo_tmp is not None:
                            tempo = tempo_tmp
                            midi_events.append({'tick':tick, 'event':MetaMessage('set_tempo', tempo=bpm2tempo(int(tempo)))})
                      # Set Midi Current Velocity
                      dynamics = sound.get('dynamics')
                      if dynamics is not None:
                          velocity = int(round(float(dynamics)))
                  # Midi Marker
                  rehearsal = element.xpath('direction-type/rehearsal')
                  if rehearsal:
                      midi_events.append({'tick':tick, 'event':MetaMessage('marker', text=f'{rehearsal[0].text}')})

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
