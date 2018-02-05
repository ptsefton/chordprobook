import os
import re

import yaml

import chordprobook.chords

class Instruments:
    """Class to represent the set of instruments we know about, 
    Assumes the instruments are in a file instruments.yaml in the same directory
    as this one.
    TODO add an option to add more"""
    
    def __init__(self):
        path, file = os.path.split(os.path.realpath(__file__))
        f = open(os.path.join(path,"instruments.yaml"))
        instrument_data = yaml.load(f)
        self.tuning_lookup = {}
        self.name_lookup = {}
        self.instruments = []
        for i in instrument_data:
            inst = Instrument(i)
            self.add_instrument(inst)
        
        
    def add_instrument(self, inst):
        self.instruments.append(inst)
        self.name_lookup[inst.name.lower()] = inst
        for alt in inst.alternate_names:
            # TODO worry about over-writing?
            self.name_lookup[alt.lower()] = inst
        if inst.tuning in self.tuning_lookup:
            self.tuning_lookup[inst.tuning].append(inst)
        else:
            self.tuning_lookup[inst.tuning] = [inst]
            
    def get_instrument_by_name(self, instrument_name):
        instrument_name = instrument_name.lower()
        if instrument_name in self.name_lookup:
            return(self.name_lookup[instrument_name])
        else:
            return None
        
    def get_instruments_by_tuning(self, tuning):
        if tuning in self.tuning_lookup:
            return self.tuning_lookup[tuning]
        else:
            return []
        
    def get_tuning_by_name(self, instrument_name):
        instrument_name = instrument_name.lower()
        if instrument_name in self.name_lookup:
            return(self.name_lookup[instrument_name].tuning)

    def get_chordpro_file_by_name(self, instrument_name):
        instrument_name = instrument_name.lower()
        if instrument_name in self.name_lookup:
            return(self.name_lookup[instrument_name].chord_definitions)

    def get_transpose_by_name(self, instrument_name):
        instrument_name = instrument_name.lower()
        if instrument_name in self.name_lookup:
            return(self.name_lookup[instrument_name].transpose)
        

    def describe(self):
        for instrument in self.instruments:
            print(instrument.name)
            if instrument.alternate_names != []:
                print("AKA: %s" % (", ").join(instrument.alternate_names))
            print("Tuning: %s" % instrument.tuning)
            print("")   
        
class Instrument:
    def __init__(self, data = None, name = "", lefty=False):
        """ Simple data structure for instruments"""
        self.lefty = lefty
        if data == None:
            data = {"name": name, "tuning": "unknown"}
            
        self.name = data['name']
        self.tuning = data['tuning']
        self.notes = []
        pattern = re.compile(r'([A-G][b#]?)')

        for note in re.findall(pattern, self.tuning):
              self.notes.append(chordprobook.chords.Note(note))
    
        
        if 'alternate_names' in data:
            self.alternate_names = data['alternate_names']
        else:
            self.alternate_names = []
            
        if 'chord_definitions' in data:
            self.chord_definitions = data['chord_definitions']
        else:
             self.chord_definitions = None

        if 'transpose' in data:
            self.transpose = int(data['transpose'])
        else:
             self.transpose = 0
        self.chart = chordprobook.chords.ChordChart()
        self.error = None
        
    def load_chord_chart(self, lefty=False):
        defs_file = self.chord_definitions
        if lefty:
            self.lefty = True
        if defs_file != None:
            path, file = os.path.split(os.path.realpath(__file__))
            defs_file = os.path.join(path, "..", "chords", defs_file)           
            self.chart = chordprobook.chords.ChordChart(self.transpose, defs_file, lefty=self.lefty)
           
