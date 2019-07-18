from __future__ import division
from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo
from lxml import etree
from io import StringIO, BytesIO
from sortedcontainers import SortedDict

notes_base_value = {'C':12,'D':14,'E':16,'F':17,'G':19,'A':21,'B':23}

division = 768
track = MidiTrack()
sd = []
tree = etree.parse("S03-05.Moonlight_Sonata.xml")
part = tree.xpath('/score-partwise/part')
numerator = 4
denominator = 4
event_start = [0,0]
rest_duration = [0,0]
tick=[0,0]
for measure in part[0].xpath("measure"):
    #measure_tick = 
    attributes = measure.find('attributes')
    if attributes is not None:
        time = attributes.find('time')
        if time is not None:
            numerator = int(time.find('beats').text)
            denominator = int(time.find('beat-type').text)
 
            sd.append({'tick':tick[0], 'event':MetaMessage('time_signature',
                      numerator=numerator,
                      denominator=denominator)})
        staves = attributes.find('staves')
        if staves is not None:
            staves = int(staves.text)
    direction = measure.find('direction')
    if direction is not None:
        #sound = direction.find('sound')
        #tempo = float(sound.get('tempo')) if sound is not None else 120
        #sd.append({'tick':tick[0], 'event':MetaMessage('set_tempo', tempo=bpm2tempo(tempo))})
        if  direction.xpath('direction-type/rehearsal'):
            sd.append({'tick':tick[0], 'event':MetaMessage('marker', text="0")})
        
    for note in measure.xpath("note"):
        rest = note.find('rest')
        pitch = note.find('pitch')
        chord = note.find('chord')        
        staff = note.find('staff')
        duration = note.find("duration")
        duration = int(duration.text) if duration is not None else 0
        if staff is not None:
            staff = int(staff.text) - 1

        if chord is None:
            event_start[staff] = tick[staff]
            tick[staff] += duration

        if rest is not None:
            tick[staff] += duration

        elif pitch is not None:
            step = pitch.find('step')
            step = step.text if step is not None else ''
            alter = pitch.find('alter')
            alter = int(alter.text) if alter is not None else 0
            octave = pitch.find('octave')
            octave = int(octave.text) if octave is not None else 0
            midi_value = octave * 12 + notes_base_value[step] + alter
            sd.append({'tick':event_start[staff], 'event':Message('note_on',
                              channel=3 if staff == 0 else 2,
                              note=midi_value,
                              velocity=80,
                              time=0)})
            sd.append({'tick':tick[staff],
                       'event': Message('note_off',
                                        channel=3 if staff == 0 else 2,
                                        note=midi_value,
                                        velocity=80,
                                        time=duration)})

mid = MidiFile(type=0, ticks_per_beat=division)            
mid.tracks.append(track)
previous_tick = 0
for entry in sorted(sd, key = lambda i: i['tick']) :
    print('E {}:{}'.format(entry['tick'],entry['event']))
    track.append(entry['event'].copy(time=entry['tick']-previous_tick))
    previous_tick = entry['tick']
mid.save('new_song.mid')
