import logging
from lxml import etree

class MmaConversion:

    @classmethod
    def get_groove(cls, numerator, denominator):
        text=''
        if numerator == 2:
            if denominator == 2:
                text += 'Groove Metronome2\nVolume ppp\n'
            elif denominator == 4:
                text += 'Groove Metronome24\nVolume ppp\n'
        elif numerator == 3:
            text += 'Groove Metronome3\nVolume ppp\n'
        elif numerator == 4:
            text += 'Groove Metronome4\nVolume ppp\n'
        elif numerator == 6:
            text += 'Groove Metronome68\nVolume ppp\n'
        text += f"TimeSig {numerator} {denominator}\n"
        return text

    @classmethod
    def mma_conversion(cls, xml_file):
        tree = etree.parse(xml_file)
        part = tree.xpath('/score-partwise/part')
        tick = 0
        mma_text = ''
        latest_chord = 'z'
        tempo = 0
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
                    groove_str = cls.get_groove(numerator,denominator)
                    mma_text += groove_str
                staves = attributes.find('staves')
                if staves is not None:
                    staves = int(staves.text)

            directions = measure.findall('direction')
            for direction in directions:
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
                elif element.tag == 'harmony' and staff == 0 and (tick%beat_duration) == 0:
                    root_step=element.find('root').find('root-step')
                    kind=element.find('kind').text
                    kind='m' if kind == 'minor' else ''
                    latest_chord = f'{root_step.text}{kind}' 
                    current_measure[int(current_beat)] = latest_chord     
                elif element.tag == 'forward':
                    tick += duration
                elif element.tag == 'backup':
                    tick -= duration
                current_beat=(tick-measure_start)/beat_duration
            print(f"mn:{measure_number} t:{tick} bd:{beat_duration} cb:{current_beat}\n")
            beat_adjust = ''
            if current_beat != numerator:                
                truncate_side = "Side=Right" if measure_number == "0" and measure_implicit == "yes" else ""
                current_measure=current_measure[slice(int(current_beat-numerator))]
                mma_text += f"Truncate {current_beat} {truncate_side}\n"
                current_measure = ['z'] if current_beat < 1 else ['z']*int(current_beat)
                print(f"CM:{current_measure}")
            current_measure = [latest_chord if b == 'z' else b for b in current_measure ]            
            measure_text += f'{" ".join(current_measure)}\n'
            mma_text += measure_text
            if denominator == 2:
                mma_text += measure_text 

        return mma_text
