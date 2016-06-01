#! /usr/bin/env python3
import glob
import re
import argparse
import os, os.path
import subprocess
import pypandoc
import tempfile

import copy
import fnmatch
import math
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import base64
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
        chord_name = re.sub("[aA]dd(\d+)","\\1", chord_name)
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
            
        # Unscientific algorithm for rating chords: open is best, not too high up neck good, short reach good, non_played strings not good
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
        


        
    


      	  




def extract_transposition(text):
    """Find a transpose directive and get rid of it out of a string"""
    tr_re = re.compile("{(tr|transpose): *(.*)}", re.IGNORECASE)
    tr_search = re.search(tr_re, text)
    standard_transpositions = [0]
    if tr_search != None:
        trans = tr_search.group(2).split(" ")
        standard_transpositions += [int(x) for x in trans]
        text = re.sub(tr_re, "", text)
    return text, standard_transpositions



def extract_book_filename(text, book = None):
    """Find a custom chordpro directive: {book: }"""
    book_re = re.compile("{(book:) *(.*?)}", re.IGNORECASE)
    book_search = re.search(book_re, text)
    book_filename = None
    if book_search != None:
        book_filename = book_search.group(2)
        text = re.sub(book_re, "", text)
    return text, book_filename

class TOC:
    ideal_songs_per_page = 40
    max_songs_per_page = 50
    
    def __init__(self, book, start_page):
       
        entries = []
        sets = []
        def chunked(iterable, n):
            
            """
            Split iterable into ``n`` iterables of similar size
            From: http://stackoverflow.com/questions/24483182/python-split-list-into-n-chunks

            """
            chunksize = int(math.ceil(len(iterable) / n))
            return [iterable[i * chunksize:i * chunksize + chunksize] for i in range(n)]
        
        
        song_count = 0
        num_entries = len(book.sets) + len([i for i in book.songs if not i.blank])
        if num_entries > TOC.max_songs_per_page:
            self.target_num_pages = int(math.ceil(num_entries / TOC.ideal_songs_per_page ))
        else:
            self.target_num_pages = 1


        page_count = start_page +  self.target_num_pages
        for song  in book.sets:
            if not song.blank:
                sets.append("Set: %s <span style='float:right'>%s</span>    " % ( song.title, str(page_count)))
            page_count += song.pages
      
            
        for song in book.songs:
            if not song.blank:
                song_count += 1
                entries.append("%s %s <span style='float:right'> %s</span>    " % (song.title, song.get_key_string(), str(page_count)))
            page_count += song.pages

        entries.sort(key= lambda title: re.sub("(?i)^(the|a|\(.*?\)) ", "", title))
        entries = sets + entries
        
        if num_entries > TOC.max_songs_per_page:
            self.pages = chunked(entries,self.target_num_pages)
        else:
            self.pages = [entries]
       
        #Make sure that there isn't a song on the back of a setlist
        if  (len(self.pages) + len(book.sets)) % 2 == 0:
            book.songs.insert(0, cp_song("", title="", blank=True))
     

    def format(self):
        contents = ""
        for page in self.pages:
            contents += """
<div class='song'>
<div class='page'>
<div class='song-page'>
<div class='song-text'>

%s

</div>
</div>
</div>
</div>
""" % "\n".join(page)
        return(contents)
        

class directive:
    """Simple data structure for a directive, with name and optional value"""
    title, subtitle, key, start_chorus, end_chorus, start_tab, end_tab, start_bridge, end_bridge, transpose, new_page, define, grids, comment, instrument, tuning, dirs, files = range(0,18)
    directives = {"t": title,
                  "title": title,
                  "st": subtitle,
                  "subtitle": subtitle,
                  "key": key,
                  "start_of_chorus": start_chorus,
                  "soc": start_chorus,
                  "end_of_chorus": end_chorus,
                  "eoc": end_chorus,
                  "start_of_tab": start_tab,
                  "sot": start_tab,
                  "end_of_tab": end_tab,
                  "eot": end_tab,
                  "start_of_chorus": start_chorus,
                  "sob": start_bridge,
                  "end_of_bridge": end_bridge,
                  "eob": end_bridge,
                  "st": subtitle,
                  "transpose": transpose,
                  "tr": transpose,
                  "new_page": new_page,
                  "np": "new_page",
                  "define": define,
                  "grids": grids,
                  "comment": comment,
                  "c": comment,
                  "instrument": instrument,
                  "tuning": tuning,
                  "dirs": dirs,
                  "files": files}
    
        
    def __init__(self, line):
        """Takes a line of text as input"""
        line = line.strip()
        self.type = None
        if line.startswith("{") and line.endswith("}"):
            name, _, self.value = line[1:-1].partition(":")
            name = name.lower()
            if name in directive.directives:
                self.type = directive.directives[name]
                self.value = self.value.strip()
                
def normalize_chord_markup(line):
        """ Put space around chords before and after word boundaries but not within words """
        line = re.sub("(\w)(\[[^\]]*?\])( |$)","\\1 \\2\\3", line)
        line = re.sub("(^| )(\[[^\]]*?\])(\w)","\\1\\2 \\3", line)
        return line

class cp_song:
    """ Represents a song, with the text, key, chord grids etc"""
    def __init__(self, song, title="Song", transpose=0, blank = False, path = None, instruments = None, instrument_name=None):
        self.blank = blank
        if instruments == None:
            self.instruments = Instruments()
        else:
            self.instruments = instruments
        self.local_instruments = None
        # Look-up
        self.instrument_name = instrument_name
        self.local_instrument_names = []
        self.text = song
        self.key = None
        self.pages = 1
        self.original_key = None
        self.path = path
        self.notes_md = ""
        self.transpose = transpose
        self.transposer = transposer(transpose)
        self.standard_transpositions = [0]
        self.title = ""
        self.parse()
        if self.title == "":
            self.title = title
       
            
    def parse(self):
        """ Deal with directives and turn song into markdown"""
        in_chorus = False
        in_tab = False
        in_block = False
        new_text = ""
        current_instrument = None
        for line in self.text.split("\n"):
            dir = directive(line)
            if dir.type == None:
                if not line.startswith('#'):
                    line = normalize_chord_markup(line)
                    if in_chorus:
                        #">" is Markdown for blockquote
                        new_text += "> "
                        
                    if in_tab:
                        #Four spaces in Markdown means preformatted
                        pass
                    else:
                        #Highlight chords
                        line = line.replace("][","] [").strip()
                        line = re.sub("\[(.*?)\]","**[\\1]**",line)
                        if line.startswith("."):
                            line = re.sub("^\.(.*?) (.*)","<span class='\\1'>\\1 \\2</span>", line)
                    new_text += "%s\n" % line
            else:
               
                if dir.type == directive.comment:
                    if in_block:
                        new_text += "</div>"
                        in_block = False
                    if dir.value.startswith("."):
                        dir.value = dir.value[1:]
                        classs = dir.value.split(" ")[0]
                        if classs:
                            in_block = True
                            new_text += "<div class='%s'>" % classs
                    if in_chorus:
                        #">" is Markdown for blockquote
                        new_text += "\n> **%s**\n" % dir.value
                    else:
                        new_text += "\n**%s**\n" % dir.value
    
                elif dir.type == directive.title:
                    self.title += dir.value
                    
                elif dir.type == directive.subtitle:
                    new_text += "\n**%s**\n" % dir.value
                    
                elif dir.type == directive.key:
                    self.original_key = dir.value
                    self.key = self.transposer.transpose_chord(self.original_key)
                    
                elif dir.type == directive.transpose:
                    trans = dir.value.split(" ")
                    self.standard_transpositions += [int(x) for x in trans]
                    
                elif dir.type in [directive.start_chorus, directive.start_bridge]:
                    #Treat bridge and chorus formatting the same
                    in_chorus = True

                elif dir.type in [directive.end_chorus, directive.end_bridge]:
                    in_chorus = False
                    
                elif dir.type == directive.start_tab and not in_tab:
                    in_tab = True
                    new_text += "```\n"
                    
                elif dir.type == directive.end_tab and in_tab:
                    new_text += "```\n"
                    in_tab = False
                    
                    
                elif dir.type == directive.new_page:
                    if in_block:
                        new_text += "</div>\n"
                        in_block = False
                    new_text +=  "\n<!-- new_page -->\n"
                    self.pages += 1
                    
                elif dir.type == directive.instrument:
                    inst_name = dir.value
                    if self.local_instruments == None:
                        self.local_instruments = Instruments()
                    current_instrument = self.local_instruments.get_instrument_by_name(inst_name)
                    self.local_instrument_names.append(inst_name)
                    if current_instrument == None:
                        current_instrument = Instrument(name = inst_name)
                        current_instrument.chart = ChordChart()
                        self.local_instruments.add_instrument(current_instrument)
                    else:
                        current_instrument.load_chord_chart()
          
                elif dir.type == directive.define:
                    if current_instrument != None:
                        current_instrument.chart.add_grid(line)
                        
                    
                    
            self.text = new_text
            #Add four spaces to mid-stanza line ends to force Markdown to add breaks
            self.text = re.sub("(.)\n(.)", "\\1    \\n\\2", self.text)
  

     
        
    def format(self, transpose=None, instrument_name=None, stand_alone=True):
        """
        Create a markdown version of the song, transposed if necessary,
        does the last-minute formatting on the song incuding transposition
        and fetching chord grids """
        if instrument_name == None:
            instrument_name = self.instrument_name
        local_grids = None
        self.grids = None
        self.transpose = transpose
        
        if instrument_name != None:
            instrument = self.grids = self.instruments.get_instrument_by_name(instrument_name)
            if instrument != None:
                self.grids = instrument.chart
                if self.grids == None:
                    instrument.load_chord_chart()
                    self.grids = instrument.chart
            if  self.local_instruments != None and instrument_name in self.local_instrument_names:
                local_grids = self.local_instruments.get_instrument_by_name(instrument_name).chart
    
        if local_grids == None:
            local_grids = self.grids
            

        
        if transpose and self.original_key:
            self.key = self.transposer.transpose_chord(self.original_key)

        key_string = self.get_key_string()
        title = "%s %s" % (self.title, key_string)
        self.chords_used = []
          
        def format_chord(chord):
            if self.transposer.offset != 0:
                chord = self.transposer.transpose_chord(chord)
    
            if self.grids != None:
                chord_normal = self.grids.normalise_chord_name(chord)
                if not chord_normal in self.chords_used:
                    self.chords_used.append(chord_normal)
        
            return("[%s]" % chord)
                
        song =  self.text
        
        #Chords
        song = re.sub("\[(.*?)\]",lambda m: format_chord(m.group(1)),song)
            
        
        if stand_alone and instrument_name != None:
            title = "%s (%s)" % (title, instrument_name)
            
            
        grid_md = ""
        if self.grids != None:
            grid_md = "<div class='grids'>"
            chords_in_text =  (len(self.chords_used) > 12)
            if chords_in_text:
                song += "\n<!-- new_page -->\n"
            for chord_name in self.chords_used:
                md = local_grids.grid_as_md(chord_name)
                if md == None:         
                    md = self.grids.grid_as_md(chord_name)
                if md != None:
                    if chords_in_text:
                        song += "<figure style='display: inline-block'>%s<figcaption>%s</figcaption></figure>" % (md, chord_name)
                    else:
                        grid_md += "%s<br>%s<br><br>" % (md, chord_name)
            grid_md += "</div>"   
      
        song = "<h1 class='song-title'>%s</h1>\n%s\n<div class='song-page'><div class='song-text'>\n%s\n%s\n\n</div></div>" % ( title, grid_md, self.notes_md, song)
        self.md = song
        self.formatted_title = title

    def save_as_single_sheet(self, instrument_name, trans, out_dir):
        self.format(transpose = trans, instrument_name=instrument_name)
        if self.key != None:
            suffix_string = "_key_%s" % self.key
        else:
            suffix_string = "_" + str(trans) if trans != 0 else ""
            
        if instrument_name != None:
            suffix_string += "_" + instrument_name.lower().replace(" ","_")
        
        temp_file = tempfile.NamedTemporaryFile(suffix=".html")
        html_path = temp_file.name
        with open(html_path, 'w') as html:
            html.write(self.to_stand_alone_html())
        path, filename = os.path.split(self.path)
        pdf_file = "%s%s.pdf" % (filename, suffix_string )
        pdf_dir = os.path.join(path, out_dir)
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = os.path.join(pdf_dir, pdf_file)
        print("Saving to %s" % (pdf_path))
        command = ['wkhtmltopdf', '--enable-javascript', '--print-media-type', html_path, pdf_path]
        subprocess.call(command)
        return pdf_path
        
    def to_html(self):
        #TODO STANDALONE
       
        song = """
<div class='song'>
<div class='page'>

%s

</div>
</div>
</div>
        """ % self.md
        song = song.replace("<!-- new_page -->", "\n</div></div></div><div class='page'><div class='song-page'><div class='song-text'>")
        return pypandoc.convert(song, 'html', format='md')

    def to_stand_alone_html(self):
        return html_book.format(self.to_html(), title = self.title, stand_alone= True)
        
    def get_key_string(self, trans = None):
        if trans:
            self.transpose = trans
        if self.original_key and self.transpose:
            self.transposer = transposer(self.transpose)
            self.key = self.transposer.transpose_chord(self.original_key)
            
        return "(%s)" % self.key if self.key != None else ""

class cp_song_book:
    """Class to hold a set of songs and setlists"""
    transposition_options = ("all","0","1")
    transpose_all, do_not_transpose, transpose_first = transposition_options
    default_title = 'Songbook'
    def __init__(self, keep_order = False, title=None, instruments = None, instrument_name=None, path="."):
        self.path = path
        self.dir, self.filename = os.path.split(self.path)
        self.title = title
        self.songs = [] #songs
        self.default_instrument_names = []
        if instruments == None:
            self.instruments = Instruments()
        else:
            self.instruments = instruments 
        self.instrument_name_passed = instrument_name
        self.text = ""
        self.keep_order = keep_order
        self.sets = [] #Song-like objects to hold rip-out-able set lists
        self.auto_transpose = cp_song_book.do_not_transpose
       
    
    def set_path(self,path):
        self.path = path
        self.dir, self.filename = os.path.split(self.path)
        
    def sort_alpha(self):
        self.songs.sort(key= lambda song: re.sub("(?i)^(the|a|\(.*?\)) ", "", song.title.lower()))
        
    def to_md(self):
        """ Generate Markdown version of a book """
        md = "---\ntitle: %s\n---\n" % self.title
        for song in self.songs:
            md += song.md
        return md

    def __get_file_list(self, files, dir_list):
        """Returns a list of files as speciifed in list of dirs and file-glob passed in files"""
        if dir_list == []:
            dir_list = ['.']
        for dir in dir_list:
            for root, dirnames, filenames in os.walk(os.path.join(self.dir,dir.strip())):
                for filename in fnmatch.filter(filenames, files):
                     if not filename.startswith("."):
                        self.add_song_from_file(open(os.path.join(root, filename)))

    def add_song_from_text(self, text, name, transpose=0):
        song = cp_song(text , path=name, transpose=transpose, instruments = self.instruments, instrument_name=self.instrument_name_passed)
        if self.auto_transpose == cp_song_book.transpose_all:
            transpositions_needed = song.standard_transpositions
        elif self.auto_transpose == cp_song_book.transpose_first and len(song.standard_transpositions) > 1:
            transpositions_needed = [song.standard_transpositions[1]]
        else:
            self.songs.append(song)
            transpositions_needed = []
            
        #Add transposed versions of songs
        for trans in transpositions_needed:
            s = copy.deepcopy(song)
            s.transpose = trans
            self.songs.append(s)
                        
    def add_song_from_file(self, file, transpose=0):
        """ Adds a song from a file to a book and works out how many transposed versions to add """
        with file as f:
           self.add_song_from_text(f.read(), f.name, transpose)
           
        
    def load_from_text(self, text, relative_to="."):
        self.text = text
        dir_list = []
        for line in self.text.split("\n"):
            directiv = directive(line)
            if directiv.type == None:
                if not line.startswith("#") and not line.strip() == "":
                    #Assume this is a path
                    #Look for transpose
                    transpose = 0
                    if "{" in line:
                        line, direct = line.split("{")
                        transpose_dir = directive("{" + direct)
                        if transpose_dir.type == directive.transpose:
                            trans = transpose_dir.value.split(" ")
                            transpositions = []
                            transpositions += [int(x) for x in trans]
                            transpose = transpositions[0]
                    song_path = os.path.join(self.dir, line.strip())
                    self.add_song_from_file(open(song_path), transpose)                    
            else:
                if directiv.type == directive.title and self.title == None:
                    self.title = directiv.value
                elif directiv.type == directive.instrument:
                    self.default_instrument_names.append(directiv.value)
                elif directiv.type == directive.dirs:
                    dir_list.append(directiv.value)
                elif directiv.type == directiv.files:
                    self.__get_file_list(directiv.value, dir_list)
                elif directiv.type == directive.transpose:
                    if directiv.value.lower() in cp_song_book.transposition_options:
                        self.auto_transpose = directiv.value.lower()

                  
                        
                        


    def __songs_to_html(self, instrument_name, args, output_file):
        all_songs = self.sets_md
        if self.title == None:
            self.title = cp_song_book.default_title
        for song  in self.songs:
            song.format(instrument_name = instrument_name, stand_alone=False)
            all_songs += song.to_html()
            
        if instrument_name != None:
            suffix = "_%s" % instrument_name.lower().replace(" ", "_")
            title_suffix = " (for&nbsp;%s)" % instrument_name
        else:
            suffix = ""
            title_suffix = ""
    
        output_file += suffix
        if args['html']:
            html_path = output_file + ".html"
        else:
            temp_file = tempfile.NamedTemporaryFile(suffix=".html")
            html_path = temp_file.name
        if args['pdf']:
            pdf_path = output_file + ".pdf"
        else:
            pdf_path = None
        #print("Outputting html", html_path)
        with open(html_path, 'w') as html:
            html.write( html_book.format(all_songs,
                                        title=self.title + title_suffix,
                                        for_print = args['a4'],
                                        contents=pypandoc.convert(self.contents,
                                                                    "html",
                                                                    format="md")))
        if pdf_path != None:
            print("Outputting PDF:", pdf_path)
            command = ['wkhtmltopdf', '-s','A4', '--enable-javascript', '--print-media-type', '--outline',
                       '--outline-depth', '1','--header-right', "[page]/[toPage]",
                       '--header-line', '--header-left', "%s" % self.title, html_path, pdf_path]
            subprocess.call(command)
            #subprocess.call(["open", pdf_path])

    def to_html_and_pdf(self,args, output_file):
        self.contents = ""
       
        self.sets_md = ""
        
        for set in self.sets:
            set.format()
            self.sets_md += set.to_html()
            
        
        self.reorder(1)
        
        toc = TOC(self, 2)
        
        self.contents = toc.format()
        
        if self.instrument_name_passed == None:
            if self.default_instrument_names != []:
                for instrument_name in [None] + self.default_instrument_names:
                    self.__songs_to_html(instrument_name, args, output_file)
            else:
                self.__songs_to_html(None, args, output_file)
        else:
            self.__songs_to_html(self.instrument_name_passed, args, output_file)
            
            


        
    def save_as_single_sheets(self, out_dir):
        """
        Saves version of a song as PDF files - one for each key/instrument combo
        Returns a list of converted songs [{title, path}]
        """
        converted_songs = []
        for song in self.songs:
            if song.path != None:
                
                for trans in song.standard_transpositions:
                    if self.instrument_name_passed != None:
                        instruments=[self.instrument_name_passed]
                    else:
                         instruments = song.local_instrument_names
                         
                    for instrument_name in instruments:
                        song.save_as_single_sheet(instrument_name, trans, out_dir)
                        
                    path = song.save_as_single_sheet(None, trans, out_dir)
                    converted_songs.append({"title" : song.formatted_title, "path" : path})
        return converted_songs
                        
    def order_by_setlist(self, setlist):
        """
        Use a setlist to order the book. Setlist will already have {title: } and {book: }
        directives removed by this point.

        Setlist uses markdown conventions, with ATX-style headers
        # Set 1

        ## Song name

        Notes on performance go here.

        ## Another song

        # Set 2

        ...
        """
        new_order = []
        current_set = None
        new_set = False
        current_song = None
        for potential_song in setlist.split("\n"):
            if potential_song.strip() != "":
                if potential_song.startswith("{") and potential_song.endswith("}"):
                    dir = directive(potential_song)
                    if dir.type == directive.title:
                        self.title = dir.value
                potential_song = re.sub("\s+", " ", potential_song)        
                if potential_song.startswith("# "):
                    potential_song = potential_song.replace("# ","").strip()
                    # Use songs to represent sets, so each set gets a single page up front of the book
                    # the text of which will scale up nice and big courtesy of the song scaling algorithm
                    if current_song != None and current_set != None:
                        current_song.title = "%s {End of %s}" % (current_song.title, current_set.title)
                    current_set = cp_song("{title: %s}" % potential_song)
                    self.sets.append(current_set)
                    new_set = True

                elif potential_song.startswith("## "): # A song
                    
                    song_name = potential_song.replace("## ", "").strip()
                    song_name, transpositions = extract_transposition(song_name)
                    restring = song_name.replace(" +", ".*?").lower()
                    regex = re.compile(restring)
                    found_song = False
               
                    for song in self.songs:
                        if re.search(regex, song.title.lower()) != None:
                            #Copy the song in case it is in the setlist twice with different treatment, such as keys or notes
                            prev_song = current_song
                            current_song = copy.deepcopy(song)
                            if transpositions == [0]:
                                transpositions = current_song.standard_transpositions
                            if new_set:
                                current_song.title = "%s {Start of %s}" % (song.title, current_set.title)
                                new_set = False
                            if len(transpositions) > 1 and transpositions[1] != 0:
                                current_song.format(transpose = transpositions[1])
                            if current_song.key != None:
                                song_name = "%s (in %s)" % (song_name, current_song.key)
                            new_order.append(current_song)
                            current_set.text +=  "## %s\n" % song_name
                            found_song = True
                            
                    if not found_song:
                        new_order.append(cp_song("{title: %s (not found)}" % song_name))
                        
                elif current_song != None:
                    current_song.notes_md += potential_song + "\n\n"
                    current_set.text +=  potential_song + "\n\n"
        
        self.songs = new_order
       
        
    def reorder(self, start_page, old = None, new_order=[], waiting = []):
        """Reorder songs in the book so two-page songs start on an even page
           Unless this is a set-list in which case insert blanks. Recursive."""
        
        def make_blank():
            new_order.append(cp_song("", title="", blank=True))
            
        if old == None:
            old = self.songs
        
        if old == []:            
            if start_page % 2 == 1 and waiting != []:
                make_blank()
            self.songs = new_order + waiting
            return
        
        if  start_page % 2 == 0:
            #We're on an even page so can output all the two-or-more-page songs
            for s in waiting:
                new_order.append(s)
                start_page += s.pages
            waiting = []
            
            #Also OK to start any other song here so append head of list
            new_order.append(old[0])
            start_page += old[0].pages
            
        elif old[0].pages % 2 == 0:
            # Have a two page spread, so save it
            if self.keep_order:
                make_blank()
                new_order.append(old[0])
                start_page += 1
            else:
                waiting.append(old[0])
        else:
            new_order.append(old[0])
            start_page += old[0].pages
            
        self.reorder(start_page, old[1:], new_order, waiting)    
                    
                
class html_book:
    
    def format(html, contents = "",  title="Untitled", for_print=True, stand_alone=False):
        script = """
function fill_page() {

$("div.page").each(function() {
 var page = $(this);
 var page_width =page.width();
 var song_page = page.children("div.song-page");
 var text = song_page.children("div.song-text");
 var grids = page.children("div.grids");
 
 var heading = page.children("h1.song-title");


 // Fit song title across top of page
 if (heading.length > 0) {
    heading.css('font-size', ("40px" ));
    while (heading.width() > page.width()) {
      heading.css('font-size', (parseInt(heading.css('font-size')) - 1) +"px" );
    }
 }

  //Fit chord grids into page height
 while (grids.height() > page.height()) {
   img_height =  parseInt(page.find("div.grids img").css('height'));
   if (img_height < 10) {break}
   page.find("div.grids img").css('height', img_height - 5);
 }

 
 var heading_height = heading.height();
 var height_remaining = page.height()  - heading_height;

 var i = 0;
 
 if (text.length > 0)
 {
   song_page.height( height_remaining);
   // Make text smaller until it is just right
   i = 0;
   while( height_remaining * %(cols)s < text.height()) {
    
     text.css('font-size', (parseInt(text.css('font-size')) - 1) +"px" );
      i++;

       if (i > 100) {break}
    }
  //Hack - some songs were running off page
  if (grids.height() > 10) {
    text.css('font-size', (parseInt(text.css('font-size')) - 1) +"px" );
  }
 var title = text.children("h1.book-title");
 i = 0;
 
 if (title.length > 0) {
  
   
    while (title.width() < page.width()) {

          i++;
          title.css('font-size', (parseInt(title.css('font-size')) + 1) +"px" );
          if (i > 1000) {break}
    }
   
  
    while (title.height() > page.height() - 200) {
          i++;
         
          title.css('font-size', (parseInt(title.css('font-size')) - 10) + "px" );
          if (i > 2000) {break}
    }
   
 }

 
    //console.log(page.find("h1").html(), "PAGE HEIGHT TO MATCH", height_remaining, "CONTENTS HEIGHT", text.height(), "FONT SIZE", text.css('font-size') );
  }
});


};
$(function() {
  fill_page()
});
"""
        web_template = """
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<title>%s</title>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
<script>
%s

</script>
<style>
.page {
    height: 100%%;
    width: 100%%;  
    font-size: 12pt;
    border-style: solid;
    border-width: 1px;
    overflow: hidden;
    -webkit-column-count: 2;
    border-bottom: thick dotted #ff0000;
    page-break-inside: avoid;
    position: relative;
    
}

.page p {
 -webkit-column-break-inside:avoid;
}

blockquote {
-webkit-column-break-inside:avoid;
margin-left: 0px;
margin-right: 0px;
background-color: #CCFF33;
}


h1 {
    
    -webkit-column-span: all;
     padding: 0px 0px 0px 0px;
     margin: 0px 0px 0px 0px;
     -webkit-margin-before: 0px;
     -webkit-margin-after: 0px;
}
h2 {
     padding: 0px 0px 0px 0px;
     margin: 0px 0px 0px 0px;
     -webkit-margin-before: 0px;
     -webkit-margin-after: 0px;
}

h3 {
     padding: 0px 0px 0px 0px;
     margin: 0px 0px 0px 0px;
     -webkit-margin-before: 0px;
     -webkit-margin-after: 0px;    
}
div {
    padding: 0px 0px 0px 0px;
    margin: 0px 0px 0px 0px;
    border-color: #FFFFFF;
    border-style: solid;
    border-width: 1px;
}
p {
  
     -webkit-margin-after: .5em;
}
@media print  
{
    .page{
        page-break-inside: avoid;
      

    }
}
</style>
</head>
<body>

%s


%s

</body>
</html>
"""
        frontmatter = """
<div class='song'>
<div class='page'>
<div class='song-page'>
<div class='song-text'>
<h1 class="book-title">%s</h1>
</div>
</div>
</div>
</div>

%s


        """


        print_template = """
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<title>%s</title>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
<script>
%s
</script>

<style>
.♂ {color: #0000FF; border-width: 1px; border-style: dashed; border-color: #FFFFFF #FFFFFF #0000FF #0000FF}
.♀ {font-style: italic; color: #FF00FF; border-width: 1px;  border-style: solid; border-color: #FFFFFF  #FFFFFF  #FF00FF  #FF00FF}

.♂ p, .♀ p {
    margin-top: 0;
}


p:last-child {
   margin-bottom: 0;
}
.page {
width: 20cm;
height: 29cm;
padding: 0cm;
margin: 0cm;
border-style: solid;
border-width: 1px;
border-color: #FFFFFF;
page-break-inside: avoid;
position: relative;
}

.grids {
 font-size: 14pt;
 font-weight: bold;
 text-align: center;
 float: right;
}

div.grids img {
 border-style: solid;
 border-width: 1px;
 border-color: white;
 height: 100; 
 width: auto; 
}

div.song-page {
padding: 0cm;
margin: 0cm;
border-style: solid;
border-width: 1px;
overflow: hidden;
border-color: #FFFFF;
page-break-inside: avoid;
font-size: 26px;
}


img {
     padding: 0px 0px 0px 0px;
     margin: 0px 0px 0px 0px;
     -webkit-margin-before: 0px;
     -webkit-margin-after: 0px;
}

h1.book-title {
  white-space: normal;
  text-align: center;
  font-size: 1pt;
  display: inline-block;
}

h1.song-title {
     text-align: center;
     padding: 0px 0px 0px 0px;
     margin: 0px 0px 0px 0px;
     white-space: nowrap;
     display: inline-block;
     -webkit-margin-before: 0px;
     -webkit-margin-after: 0px;
}
div {

    border-style: solid;
    border-width: 1px;
    border-color: #FFFFFF;
}
@media print  
{
    div.page{
        page-break-inside: avoid;
    }
    div.song-page{
        
        page-break-inside: avoid;
    }
}
</style>
</head>
<body>

%s


%s
</body>
</html>
"""
        if for_print:
             web_template = print_template
             cols = "1"
        else:
            cols = "2"
        if stand_alone:
            frontmatter = ""
        else:
            frontmatter = frontmatter % (title, contents)
            
        return web_template % (title, script % {'cols': cols}, frontmatter, html)
        
        

    
output = "markdown"


    
def convert():
    default_output_file = "songbook"
    parser = argparse.ArgumentParser()
    parser.add_argument('files', type=argparse.FileType('r'), nargs="*", default=None, help='List of files')
    parser.add_argument('-a', '--alphabetically', action='store_true', help='Sort songs alphabetically')
    parser.add_argument('-d', '--directory', default='.', help='Directory in which to put the output, relative to the book, setlist or indivudal file. If you want to put files somwhere specific, use a full path starting with "/": defaults to "." ')
    parser.add_argument('-i', '--instrument', default=None, help='Show chord grids for the given instrument. Eg --instrument "Soprano Ukulele"')
    parser.add_argument('--instruments', action='store_true', help='List known instruments and their alises then quit. You use any of the names or aliases listed under AKA with the --instument option')
    parser.add_argument('-k',
                        '--keep-order',
                        action='store_true',
                        help='Preserve song order for playing as a setlist (inserts blank pages to keep multi page songs on facing pages')
    parser.add_argument('--a4', action='store_true', default=True, help='Format for printing (web page output)')
    parser.add_argument('-e', '--epub', action='store_true', help='Output epub book')
    parser.add_argument('-f', '--file-stem', default=default_output_file, help='Base file name, without extension, for output files')
    parser.add_argument( '--html', action='store_true', default=False, help='Output HTML book, defaults to screen-formatting use --a4 option for printing (PDF generation not working unless you chose --a4 for now')
    parser.add_argument('-w', '--word', action='store_true', help='Output .docx format')
    parser.add_argument('-p', '--pdf', action='store_true', help='Output pdf', default=True)
    parser.add_argument('-r', '--reference-docx', default = None, help="Reference docx file to use (eg with Heading 1 having a page-break before)")
    parser.add_argument('-o','--one-doc', action='store_true', help='Output a single document per song: assumes you want A4 PDF')
    parser.add_argument('-b',
                        '--book-file',
                        action='store_true',
                        help ="""First file contains a list of files, each line optionally followed by a transposition (+|-)\d\d?
                                 eg to transpose up one tone:
                                 song-file.cho +2, you can also add a title line: {title: Title of book}""")
    parser.add_argument('-s',
                        '--setlist',
                        default=None,
                        help ="Use a setlist file in markdown format to filter the book, one song per line, and keep facing pages together. Setlist lines can be one or more words from the song title starting with '## ', with '# ' for the names of sets and other markdown as you require in between you can also add a setlist line: {title: Title of setlist}")
    parser.add_argument('--title', default=None, help='Title to use for the book, if there is no title in a book file or setlist file')
    
   

    args = vars(parser.parse_args())
    #Need to be able to pass this into songs now
    instruments = Instruments()
    
    if args["instruments"]:
        instruments.describe()
        exit()
    out_dir = args["directory"]
    output_file =  args["file_stem"]


    
    # Do we want chord grids?
    if args["instrument"] != None:
        instrument = instruments.get_instrument_by_name(args['instrument'])
        if instrument != None:
            instrument.load_chord_chart()
            chart = instrument.chart
            if chart == None:
                print(instrument.error)
        else:
            print("No such instrument on file. Try typing ./chordprobook.py --instruments to get a list")

    #Is there a setlist file?
    if args["setlist"] == None:
        list = None
    else:
       with open(args["setlist"]) as sets_file:
           list = sets_file.read()
       args["keep_order"] = True
       set_dir, set_name = os.path.split(args["setlist"])
       list, bookfile = extract_book_filename(list)
       if bookfile != None and not args["book_file"]:
           #No book file passed so use the one we found in the setlist
           args["files"] = [open(os.path.join(set_dir,bookfile),'r')]
           args["book_file"] = True
           
       
    
    if args["files"] != None:
       book = cp_song_book(keep_order = args['keep_order'], title=args["title"],instruments = instruments, instrument_name=args["instrument"])
       if args["book_file"]:
            book_file = args["files"][0]
            book.set_path(book_file.name)
            book_dir, book_name = os.path.split(book_file.name)
            #base output path on book unless user passed a different name
            if args["file_stem"] == default_output_file:
                output_file, _ = os.path.splitext(book_name)
                output_file = os.path.join(book_dir, out_dir, output_file)
                print ("SETTING OUT ", output_file)
            text = book_file.read()
            book.load_from_text(text)
            
       else:
           output_file = os.path.join(out_dir, output_file)
           for f in args['files']:
                book.add_song_from_file(f)
    else:
        print("ERROR: You need to pass one or more files to process")
  
    # Make all the input files into a book object
   
    
    # If there's a setlist file use it
    if args["setlist"] != None:
       #Let the setlist override titles set elsewere
       book.order_by_setlist(list)
       if args["book_file"] or args["file_stem"] == default_output_file:
            set_dir, set_name = os.path.split(args["setlist"])
            
            output_file = os.path.join(set_dir, out_dir, set_name)

    if args["alphabetically"]:
        book.sort_alpha()

    title = args['title']
     
    #TODO: Make this into separate methods
    if  args['epub']:
        epub_path = output_file + ".epub"
        xtra =[ "--toc-depth=1","--epub-chapter-level=1"] #, "--epub-stylesheet=songbook.css"] 
        pypandoc.convert(book.to_md(), "epub", format="md", outputfile=epub_path, extra_args=xtra)
        #subprocess.call(["open", epub_path])
 
    if  args["word"]:
        word_path = output_file + ".docx"
        xtra = ["--toc", "--data-dir=.", "--toc-depth=1"]
        if args["reference_docx"] != None:
            xtra.append('--reference-docx=%s' % args["reference_docx"])
        pypandoc.convert(book.to_md(), "docx", format="md", outputfile=word_path, extra_args=xtra)
        #subprocess.call(["open", word_path])
        
   
    #PDF is generated from HTML, BTW
    if args['one_doc']: #Assume standalone PDF
        book.save_as_single_sheets(out_dir)
        
        
    elif args['html'] or args['pdf']:
        book.to_html_and_pdf(args, output_file)
        
if __name__ == "__main__":
    convert()
