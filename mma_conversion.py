import logging
from lxml import etree

class MmaConversion:

    @classmethod
    def convert_kind(cls, kind):
      text_attribute=kind.get('text')
      element_value=kind.text
      if text_attribute is None and element_value == 'major':
        kind=''
      else:
        kind=text_attribute
        kind=kind.replace('Maj','maj')
        kind=kind.replace('min','m')
      return kind

    @classmethod
    def convert_alter(cls, alter):
      if alter is not None:
        alter = int(alter.text)
        if alter == 1:
          alter = '#'
        elif alter > 1:
          alter = '#' + alter
        elif alter == -1:
          alter = 'b'
        elif alter < -1:
          alter = 'b' + abs(alter)
        else:
          alter = ''
      else:
        alter = ''
      return alter

    @classmethod
    def convert_degree(cls, degree):
      if degree is not None:
        degree_value = int(degree.find('degree-value').text)
        degree_type = degree.find('degree-type').get('text')
        degree_type_value = degree.find('degree-type').text
        if degree_type is None:
          if degree_value == 7:
            degree_type = ''
          elif degree_value > 7:
            degree_type = 'add'
          elif degree_type_value == 'alter':
            degree_type = ''
        degree_alter = cls.convert_alter(degree.find('degree-alter'))
        degree = f'{degree_type}{degree_alter}{degree_value}'
      else:
        degree = ''
      return degree

    @classmethod
    def mma_conversion(cls, xml_file, repeat_chord=False):
        tree = etree.parse(xml_file)
        part = tree.xpath('/score-partwise/part')
        tick = 0
        mma_header =  ''
        metronome_seq = {}
        mma_text = ''
        tempo = None
        numerator = 4
        denominator = 4
        latest_chord = 'z'
        for measure in part[0].xpath("measure"):
            measure_number=f"{measure.attrib['number']}"
            measure_implicit=f"{measure.attrib['implicit']}" if "implicit" in measure.attrib else "no"
            measure_start = tick
            attributes = measure.find('attributes')
            if attributes is not None:
                divisions = attributes.find('divisions')
                if divisions is not None:
                    division = int(divisions.text)
                time = attributes.find('time')
                if time is not None:
                    numerator = int(time.find('beats').text)
                    denominator = int(time.find('beat-type').text)
                    beat_duration=division*4/denominator
                    metronome_seq[f"custom_metronome_{numerator}_{denominator}"] = cls.get_metronome_sequence(numerator,denominator)
                    mma_text += cls.get_groove(numerator,denominator)
                staves = attributes.find('staves')
                if staves is not None:
                    staves = int(staves.text)

            directions = measure.findall('direction')
            for direction in directions:
                if tempo is None:
                  sound = direction.find('sound')
                  if sound is not None:
                      tempo_tmp = sound.get('tempo')
                      if tempo_tmp is not None:
                          tempo = int(tempo_tmp)*(denominator/4)
                          tempo_str = f"Tempo {tempo}\n"
                          mma_text += tempo_str
                d_type = direction.find('direction-type')
                if d_type is not None:
                    word = d_type.get('word')
                    if word is not None:
                        mma_text += word.text
            if tempo is None:
                tempo = 120 * denominator/4
                mma_text += f"Tempo {tempo}\n"

            measure_text = f"{measure_number} "
            staff = 0
            current_measure=['z']*numerator
            current_beat=0
            for element in measure.xpath("note|harmony|backup|forward"):
                duration = element.find("duration")
                duration = int(duration.text) if duration is not None else 0
                if element.tag == 'note':
                    staff_el = element.find('staff')
                    if staff_el is not None:
                        staff = int(staff_el.text) - 1
                    rest = element.find('rest')
                    pitch = element.find('pitch')
                    if rest is not None:
                        tick += duration
                    else:
                        if pitch is not None:
                            chord = element.find('chord')
                            if chord is None:
                                tick += duration
                elif element.tag == 'harmony' and staff == 0 and ((tick-measure_start)%beat_duration) == 0:
                    root_step=element.find('root').find('root-step').text
                    kind=cls.convert_kind(element.find('kind'))
                    root_alter=cls.convert_alter(element.find('root').find('root-alter'))
                    degree = cls.convert_degree(element.find('degree'))
                    latest_chord = f'{root_step}{root_alter}{kind}{degree}'
                    bass = element.find('bass')
                    if bass is not None:
                      bass_step=element.find('bass').find('bass-step').text
                      bass_alter=cls.convert_alter(element.find('bass').find('bass-alter'))
                      latest_chord += f'/{bass_step}{bass_alter}'
                    current_measure[int(current_beat)] = f'{latest_chord}'
                elif element.tag == 'forward':
                    tick += duration
                elif element.tag == 'backup':
                    tick -= duration
                current_beat=(tick-measure_start)/beat_duration
            #print(f"mn:{measure_number} t:{tick} bd:{beat_duration} cb:{current_beat}\n")
            beat_adjust = ''
            if current_beat != numerator:
                truncate_side = "Side=Right" if measure_number == "0" and measure_implicit == "yes" else ""
                current_measure=current_measure[slice(int(current_beat)-numerator)]
                mma_text += f"Truncate {current_beat} {truncate_side}\n"
                if current_beat < 1:
                  current_measure = [latest_chord]
                #print(f"CM:{current_measure}")
            if repeat_chord and current_measure.count('z') == len(current_measure):
                current_measure[0] = latest_chord
            measure_text += f'{" ".join(current_measure)}\n'
            mma_text += measure_text

        return mma_header + "\n".join(list(metronome_seq.values())) + mma_text

    @classmethod
    def get_metronome_sequence(cls, numerator, denominator):
        if numerator % 2 == 0:
            m_low_str = f"M1 * {numerator//2}"
            m_hi_str = f"M_Low Shift 1"
        else:
            m_low_str = f"M1"
            m_hi_str = ""
            for i in range(1,numerator):
                m_hi_str += f"M1 shift {i};"

        text = \
f"""
SeqClear
Seqsize 1

Time {numerator}
Timesig {numerator} {denominator}

Begin Chord-Simple
Voice SteelGuitar
Volume mp
Articulate 100
Unify On
Define simple_chord 1 1 100 * {numerator}
Sequence simple_chord
End

Begin Drum Define
    M1 1 0 90
    M_Low {m_low_str}
    M_Hi  {m_hi_str}
End

Begin Drum-Low
  Sequence  M_Low
  Tone  LowWoodBlock
  Volume f
End

Begin Drum-Hi
  Sequence  M_Hi
  Tone HighWoodBlock
  Volume f
End

DefGroove custom_metronome_{numerator}_{denominator}
\n"""
        return text

    @classmethod
    def get_groove(cls, numerator, denominator):
        text = \
f"""
Groove custom_metronome_{numerator}_{denominator}
Timesig {numerator} {denominator}
Volume ppp
\n"""
        return text
