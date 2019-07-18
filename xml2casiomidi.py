from __future__ import division
from mido import Message, MetaMessage, MidiFile, MidiTrack
from lxml import etree
from io import StringIO, BytesIO
from sortedcontainers import SortedDict

notes_base_value = {'C':12,'D':14,'E':16,'F':17,'G':19,'A':21,'B':23}

track = MidiTrack()
sd = SortedDict()
tree = etree.parse("S03-05.Moonlight_Sonata.xml")
part = tree.xpath('/score-partwise/part')
numerator = 4
denominator = 4
staves_tick = [0,0]
event_start = [0,0]
event_stop = [0,0]
rest_duration = [0,0]
division = 768
for measure in part[0].xpath("measure"):
    #measure_tick = 
    attributes = measure.find('attributes')
    if attributes is not None:
        time = attributes.find('time')
        if time is not None:
            numerator = int(time.find('beats').text)
            denominator = int(time.find('beat-type').text)
 
            sd["{:020d}-time_signature-{}".format(staves_tick[0],numerator)] = \
                MetaMessage('time_signature',
                            numerator=numerator,
                            denominator=denominator,
                            clocks_per_click=250,
                            notated_32nd_notes_per_beat=8)
        staves = attributes.find('staves')
        if staves is not None:
            staves = int(staves.text)
    direction = measure.find('direction')
    if direction is not None:
        if  direction.xpath('direction-type/rehearsal'):
            sd["{:020d}-marker".format(staves_tick[0])] = \
                MetaMessage('marker', text="0")
        
    for note in measure.xpath("note"):
        rest = note.find('rest')
        pitch = note.find('pitch')
        duration = note.find("duration")
        duration = int(duration.text) if duration is not None else 0
        chord = note.find('chord')
        
        staff = note.find('staff')
        if staff is not None:
            staff = int(staff.text) - 1

        if chord is None:
            event_start[staff] = staves_tick[staff]
            staves_tick[staff] += duration//24
            event_stop[staff] = staves_tick[staff]-1 #Append stop to list test if next note start after

        if rest is not None:
            staves_tick[staff] += duration//24
            rest_duration[staff]+=duration//24
            print("Rest {} {}".format(staff, rest_duration[staff]))

        elif pitch is not None:
            step = pitch.find('step')
            step = step.text if step is not None else ''
            alter = pitch.find('alter')
            alter = int(alter.text) if alter is not None else 0
            octave = pitch.find('octave')
            octave = int(octave.text) if octave is not None else 0
            midi_value = octave * 12 + notes_base_value[step] + alter
            sd["{:020d}-note_on-{}".format(event_start[staff],midi_value)] = Message('note_on',
                                                   channel=3 if staff == 0 else 2,
                                                   note=midi_value,
                                                   velocity=80,
                                                   time=rest_duration[staff]+1)
            rest_duration[staff]=0
            sd["{:020d}-note_off-{}".format(event_stop[staff],midi_value)] = Message('note_off',
                                                   channel=3 if staff == 0 else 2,
                                                   note=midi_value,
                                                   velocity=80,
                                                   time=duration)
            
mid = MidiFile(type=0, ticks_per_beat=division)
mid.tracks.append(track)
for key, event in sd.items():
    print('E {}:{}'.format(key,event))
    track.append(event)        
mid.save('new_song.mid')
