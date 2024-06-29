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
    def midi_conversion(cls, musicxml_filename, num_ticks=192, lesson_channel=3):
        lh_channel=lesson_channel-1
        rh_channel=lh_channel+1
        midi_events = [{'divisions':num_ticks}]
        tree = etree.parse(musicxml_filename)
        part = tree.xpath('/score-partwise/part')
        event_start = 0
        tick = 0
        velocity = 90
        multiplier = 1
        tempo = None
        i=0
        measures=part[0].xpath("measure")
        repeat_start = 0
        repeat_direction =  'forward'
        repeat_times = 0
        ending_number = 0
        ending_type = None
        tocoda = False
        dalsegno = False
        segno = {}
        dacapo = 0
        while i < len(measures):
            measure = measures[i]
            print(f"Measure:{measure.get('number')}")
            if tocoda:
                sound = measure.find('.//sound')
                if sound is not None:
                    coda_att = sound.attrib.get('coda', None)
                    if coda_att:
                        tocoda = False
                    else:
                        i += 1
                        continue
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
            elements = measure.xpath("note|backup|forward|barline|direction")
            j=0
            while j < len(elements):
                element = elements[j]
                j += 1
                if ending_number > 0 and ending_number <= repeat_times and element.tag != 'barline':
                    continue
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
                elif element.tag == 'barline':
                    ending = element.find('ending')
                    if ending is not None:
                        ending_number = int(ending.attrib.get('number'))
                        ending_type = ending.attrib.get('type')
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
            sound = measure.find('.//sound')
            if sound is not None:
                segno_att = sound.attrib.get('segno', None)
                if segno_att:
                    if not segno_att in segno:
                        segno[segno_att] = {'measure':i, 'repeat':0}
                    else:
                        segno[segno_att]['measure'] = i
                dalsegno_att = sound.attrib.get('dalsegno', None)
                if dalsegno_att and segno[dalsegno_att]['repeat'] < 2:
                    print(f"dalsegno: {i+1}")
                    dalsegno =  True
                    i = segno[dalsegno_att]['measure']
                    segno[dalsegno_att]['repeat'] += 1
                    continue                                  
                tocoda_att = sound.attrib.get('tocoda', None)
                if tocoda_att:
                    if dalsegno == True:
                        tocoda = True 
                dacapo_att = sound.attrib.get('dacapo', None)
                if dacapo_att and dacapo < 1:
                    dacapo = 1
                    i = 0
                    continue
            if repeat_direction == 'backward':
                i = repeat_start
                repeat_direction = 'forward'
            elif repeat_direction == 'forward':
                i += 1
            if ending_type in ["stop","discontinue"]:
                ending_number = 0
                ending_type = None

        tracks = [MidiTrack(),MidiTrack(),MidiTrack()]
        previous_ticks = [0,0,0]
        midi_events = midi_events[1:]
        for entry in sorted(midi_events, key=lambda i: i['tick']) :
            if entry['event'].is_meta == True:
                track_id = 0 
            elif entry['event'].channel == lh_channel:
                track_id = 1
            elif entry['event'].channel == rh_channel:
                track_id = 2
            updated_event = entry['event'].copy(time=entry['tick'] - previous_ticks[track_id])
            tracks[track_id].append(updated_event)
            previous_ticks[track_id] = entry['tick']        
            logging.info('E {}:{}'.format(entry['tick'], updated_event))

        return tracks

    @classmethod    
    def write_midi(cls, tracks, midi_file, num_ticks=192):
        midi_attributes = {'divisions':num_ticks}
        mid = MidiFile(type=1, ticks_per_beat=midi_attributes['divisions'])
        mid.tracks.extend(tracks)
        mid.save(midi_file)


class MidiComparator:

    def __init__(self):
        pass
