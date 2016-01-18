from PIL import Image, ImageFont, ImageDraw
import re
from io import BytesIO
import base64
import os.path
import yaml

class Instruments:
    """Set of instruments we know about, TODO read in from a data file so we can get more"""
    
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
    def __init__(self, data = None, name = ""):
        """ Simple data structure for instruments"""
        if data == None:
            data = {"name": name, "tuning": "unknown"}
            
        self.name = data['name']
        self.tuning = data['tuning']
        
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
        self.chart = None
        self.error = None
        
    def load_chord_chart(self):
        defs_file = self.chord_definitions
        
        if defs_file != None:
            path, file = os.path.split(os.path.realpath(__file__))
            defs_file = os.path.join(path, defs_file)
            if os.path.exists(defs_file):
                self.chart = ChordChart(self.transpose, defs_file)
            else:
                self.error = "Chord defs file not found: %s"  % defs_file

class transposer:
   
    __note_indicies = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "D#": 3,
                     "E" : 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "Ab": 8,
                     "G#": 8, "A" : 9, "Bb": 10, "A#": 10, "B": 11}
        
    __notes = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
    
    def __init__(self, offset = 0):
        self.offset = offset
    
    def transpose_chord(self, chord_string):
        return re.sub("([A-G](\#|b)?)",(lambda x: self.transpose_note(x.group())), chord_string)

               
    def get_note_index(self, note):
        return self.__note_indicies[note] if note in self.__note_indicies else none

    def get_note(self, index):
        return transposer.__notes[index]
   
    def transpose_note(self, note):   
        note_index = self.get_note_index(note)
        new_note = (note_index + self.offset ) % 12
        return self.__notes[new_note] if  note_index != None else note

class Dot:
    """
    Class to represent a single dot in the diagram ie a finger on a fret
    use None To say 'don't play'
    0 for open string'
    """
    def __init__(self, fret, finger = None):
        self.fret = fret 
        self.finger = finger if self.fret != None else 0
        
        
class String:
    """Class to represent all the dots to show on a string, pass in an array of dots """
    def __init__(self, dots):
        self.dots = dots

        
class Fret:
    """Placeholder for a fret class to hold x,y coordinates"""
    def __init__(self, left_x, y, right_x):
        self.left_x = left_x
        self.y = y
        self.right_x = right_x

class ChordVoicings:
    """Container for alternative fingerings/voicings."""
    def __init__(self, grid):
        self.voicings = [grid]

    def append(self, grid):
        self.voicings.append(grid)

    def push_to_front(self, grid):
        self.voicings.insert(0, grid)
        
    def sort_by_playability(self):
        self.voicings.sort(key=lambda x: x.playability, reverse=True)
        


    
class ChordChart:
    def __init__(self, transpose = 0,file = None):
        """Container for a set of chord-grids"""
        self.grids = {}
        self.tuning = None
        self.transposer = transposer(transpose)
        if file != None:
            self.load_file(open(file))
        self.error = None
        
    def load_tuning_by_name(self, instrument_name):
        """
        Takes a string representation of an instrument tuning, eg:
        EADGBE (guitar) or
        GCEA (soprano uke)

        TODO:
        If it can't find the file will try to find a chord chart with the same
        relative tuning eg DGBE should find GCEA

        """
        instruments = Instruments()
        defs_file = instruments.get_chordpro_file_by_name(instrument_name)
        path, file = os.path.split(os.path.realpath(__file__))
        if defs_file != None:
            self.transposer.offset = instruments.get_transpose_by_name(instrument_name)
            f = os.path.join(path, defs_file)
            if os.path.exists(f):
                self.load_file(open(f))
            else:
                print("******** Unable to load %s" % f)
        else:
            self.error = "Instrument not found"
            
    def add_grid(self, definition):
        grid = ChordDiagram()
        grid.parse_definition(definition)
        grid.name = self.normalise_chord_name(grid.name)
        if grid.name not in self.grids:
            self.grids[grid.name] = ChordVoicings(grid)
        else:
            self.grids[grid.name].push_to_front(grid)
        

        
    def load(self, f):
        self.load_file(f.split("\\n"))
                    
    def load_file(self, f):
        self.transposer.offset = 12 - self.transposer.offset
        for line in f:
            if line.startswith("{define:"):
                grid = ChordDiagram()
                grid.parse_definition(line)
                grid.name = self.normalise_chord_name(grid.name)
                if self.transposer.offset > 0:
                    grid.name = self.transposer.transpose_chord(grid.name)
                if grid.name not in self.grids:
                    self.grids[grid.name] = ChordVoicings(grid)
                else:
                    self.grids[grid.name].append(grid)

    def normalise_chord_name(self, chord_name):
        """ Transform chord name as used to a canonical name, means we only have to store a limited set of chords """
        # Allow ! for stacatto chord
        chord_name = re.sub("\!$","", chord_name)
        
        # Allow / / / inside chord diagrams for strumming
        chord_name = re.sub("(/* *)*$","", chord_name)
        
        # Normalise "add" for ninths, elevenths etc - TODO sharps as well
        chord_name = re.sub("add(\d+)","\\1", chord_name)
        tr = transposer(0)
        chord_name = tr.transpose_chord(chord_name)
        return chord_name
                
    def grid_as_md(self, chord_name):
        # TODO: add tests
        chord_name = self.normalise_chord_name(chord_name)
        chord = self.get_default(chord_name)
        if chord != None:
            return chord.to_md()     
        else:
            return(None)

    def get_default(self, chord_name):
        chord_name = self.normalise_chord_name(chord_name)
        if chord_name in self.grids:
            chord = self.grids[chord_name]
            if len(chord.voicings) > 0:
               return chord.voicings[0]
        else:
            return None
     
    def sort_by_playability(self,chord_name):
        if chord_name in self.grids:
            chord = self.grids[chord_name]
            chord.sort_by_playability()

    def to_chordpro(self, chord_name):
        if chord_name in self.grids:
            chordpro = ""
            for grid in self.grids[chord_name].voicings:
                chordpro += "%s\n" % grid.to_chordpro()
            return chordpro

    
class ChordDiagram:
    box_width =  80
    box_height = 100
    top_margin = 10 # Between chord name and zero fret
    default_frets = 5
    default_strings = 4
    bottom_margin = 8 #between last fret and bottom of diagram
    bgcolor = (255,255,255) #whitish
    dot_text_color = (256,256,256) #white
    dot_color = (0,0,0) #black
    
    def __init__(self, name="", strings=[], draw_name=False):
        """ Empty diagram. No strings, no frets, no nothin' """
        self.name = name
        self.strings = strings
        self.draw_name = draw_name
        self.frets = [] #Will contain fret objects
        self.base_fret = 0
        self.setup()
        
    def to_data_URI(self):
        """Convert pic binary data to a data URI for use in web pages"""
        self.draw()
        output = BytesIO()
        self.img.save(output, format='PNG')
        im_data = output.getvalue()
        return('data:image/png;base64,' + base64.b64encode(im_data).decode())
    
    def to_md(self):
        return("<img width='%s' height='%s' alt='%s' src='%s' />" % (self.box_width, self.box_height, self.name, self.to_data_URI()))

    def to_chordpro(self):
        """ Turn into {define: declaration. Warning! Not finished! See tests for current functionality. """
        chordpro = "{define: %s " % self.name;
        if self.base_fret != 0:
            chordpro += "base-fret %s " % str(self.base_fret)
        chordpro += "frets"
        for string in self.strings:
            for dot in string.dots:
                if dot.fret == None:
                    chordpro += " x"
                else:
                    chordpro += " %s" % str(dot.fret)
        chordpro += "}"
        return chordpro #TODO: FINGERS AND EXTRA DOTS!!!        
                
                

            
    def setup(self):
        """
        Calculate everything needed to draw and/or sort this chord
        have exposed a lot of the internal maths to help with testing, hard to test the diagrams but
        we can at least check that frets are not on top of each other, and so on
        """

        self.max_fret = 0
        self.min_fret = 100
        self.open_strings = 0
        self.non_played_strings = 0
        for string in self.strings:
            for dot in string.dots:
                if dot.fret == None:
                    self.non_played_strings += 1
                elif dot.fret == 0:
                    self.open_strings += 1
                else:
                    dot.fret = dot.fret + self.base_fret
                    self.max_fret = max(dot.fret, self.max_fret)
                    self.min_fret = min(dot.fret, self.min_fret)
                
        # Recalculate base_fret
        if self.max_fret > ChordDiagram.default_frets and 100 > self.min_fret > 1:
            self.base_fret = self.min_fret - 1
            for string in self.strings:
                for dot in string.dots:
                    if dot.fret != None and dot.fret != 0:
                        dot.fret = dot.fret - self.base_fret
        else:
            self.base_fret = 0 
       
        #Work out how many frets to draw.
        #This program is not your music teacher! if you put in stupid chords it will
        # draw them
        fret_range = self.max_fret - self.base_fret
        if fret_range > ChordDiagram.default_frets:
            self.num_frets = fret_range
        else:
            self.num_frets = ChordDiagram.default_frets

        #Scale up bounding box if there are lots of strings or frets
        self.num_strings = len(self.strings)
        self.box_height = ChordDiagram.box_height
        self.box_width = ChordDiagram.box_width
        
        if self.num_strings > ChordDiagram.default_strings:
            self.box_width = int((self.box_width / ChordDiagram.default_strings) * self.num_strings)

        if self.num_frets> ChordDiagram.default_frets:
            self.box_height = int((self.box_height / ChordDiagram.default_frets) * self.num_frets)
            
        # Unscientific algorithm for rating chords open is best, not too high up neck good, short reach good, non_played strings not good
        self.playability = self.open_strings * 13 - self.max_fret * 29 - (self.max_fret - self.min_fret) * 7 - self.non_played_strings * 11

        
    def draw(self):
        """
        Render the chord.
        """
        # Commence scribbling
        self.img = Image.new("RGB", (self.box_width, self.box_height), ChordDiagram.bgcolor)
        draw = ImageDraw.Draw(self.img)

        w, h = draw.textsize(self.name)
        top_margin = ChordDiagram.top_margin
        if not self.draw_name:
            (w, h) = (0, 0)
             

        # Look, I can write my own name
        # TODO, bigger, nicer font
        if self.draw_name:
            draw.text(((self.box_width - w) / 2, 0),self.name, (0,0,0))
        
        # Draw plenty of strings evenly placed across the diagram, instrument agnostic,
        self.string_top = h + top_margin
        self.string_bottom = self.box_height - ChordDiagram.bottom_margin     
        self.string_spacing = self.box_width / (self.num_strings + 1)
        for i  in range(0, len(self.strings)):
            string = self.strings[i]
            string.string_x = self.string_spacing * (i + 1)
            coords = (string.string_x, self.string_top, string.string_x, self.string_bottom)
            draw.line(coords, fill=128)

        # Draw just enough frets
        self.fret_spacing = (self.string_bottom - self.string_top) / self.num_frets
        for i in range(0, self.num_frets + 1):
            fret = Fret(self.string_spacing, self.string_top +  i * self.fret_spacing, self.string_spacing * self.num_strings)
            self.frets.append(fret)
            draw.line(( fret.left_x, fret.y, fret.right_x, fret.y ), fill=128)
                
        # Draw the dots, which are stored as an array for each string
        for i in range(0, len(self.strings)):
            string = self.strings[i]
            # TODO deal with dont_play
            for dot in string.dots:
                f = dot.fret
                x = (i + 1) * self.string_spacing
                # OK so I put this in so that fingers > 9 work.
                # who knows, maybe there are two or three people fretting the thing
                # (And Hi 13 to our alien overlords!)
                if dot.finger != None:
                    w, h = draw.textsize(str(dot.finger))
                else:
                    w, h = draw.textsize("8")
                r = w
                
                if dot.fret == None:
                    draw.text((x - w/2, self.string_top - h), "x", self.dot_color)
                elif dot.fret != 0:
                    y = self.string_top + f * self.fret_spacing - r
                    draw.ellipse((x-r, y-r, x+r, y+r), ChordDiagram.dot_color)
                    if dot.finger != None:
                        draw.text((x - w / 2 ,y - h /2 ),
                                  str(dot.finger),
                                  ChordDiagram.dot_text_color)
        #Write in base fret if present
        if self.base_fret != 0:
            w, h = draw.textsize(str(self.base_fret))
            draw.text((0,self.string_top - h/2), str(self.base_fret), ChordDiagram.dot_color)

            
    def show(self):
        """Pop up a chord diagram. Usueful for debugging"""
        self.draw()
        self.img.show()


    def parse_definition(self, definition):
        """ unpack a chordpro chord definition, trying to be as permissive as possible """
       
        frets_re = re.compile("{define: +(\\S+?) *(base-fret (\\d+))? *(frets)? +([\\d x]+)", re.IGNORECASE)
        frets_search = re.search(frets_re, definition)
         
        if frets_search != None:
            self.name = frets_search.group(1)
            self.base_fret = frets_search.group(3)
            if self.base_fret == None:
                self.base_fret = 0
            else:
                self.base_fret = int(self.base_fret)
            #Get rid of basic frets part
            definition = re.sub(frets_re, "", definition)
            
            #Look for optional fingers spec
            fingers_re = re.compile("fingers +([\\d ]+)", re.IGNORECASE)
            fingers_search = re.search(fingers_re, definition)
            fingers = None
            if fingers_search != None:
                fingers = fingers_search.group(1).strip().split(" ")
                definition = re.sub(fingers_re, "", definition)
                    
            self.strings = []
            frets = frets_search.group(5).strip().split(" ")
            
            i = 0
            for fret in frets:
                fret = None if  fret.lower() == 'x' else int(fret)
                finger = None
                if fingers != None:
                    finger = fingers[i] if fingers[i] != 0 else None
                                                        
                self.strings.append(String([Dot(fret, finger)]))
                i += 1
            # Look for additional fingers
            # Could add this to main regex but this was simpler in initial coding
            definition = definition.replace("}","")
            additional = definition.strip().split("add: ")
            for dot_to_add in additional:
                 add_re = re.compile("string +(\d+) +fret +(\d+) +finger +(\d+)")
                 add_search = re.search(add_re, dot_to_add)
                 if add_search != None:
                    string = int(add_search.group(1)) - 1
                    fret = int(add_search.group(2))
                    finger = int(add_search.group(3))
                    if string <= len(frets) and fret > 0:
                        self.strings[string].dots.append(Dot(fret, finger))
                 
        self.setup()
        


        
    


      	  
