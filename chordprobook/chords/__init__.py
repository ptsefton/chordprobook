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
import chordprobook
import chordprobook.instruments

class transposer:
    """ This should have been a static method with two parameters transpose(chord_or_note, offset)
    NOTE: This was a very bad idea - it's too complicated. TODO get rid of this class and move functionality to note

    """

    __note_indicies = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "D#": 3,
                     "E" : 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "Ab": 8,
                     "G#": 8, "A" : 9, "Bb": 10, "A#": 10, "B": 11}

    __notes = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]

    __numbers = ["1", "♭2", "2", "♭3", "3", "4", "♭5", "5", "♭6", "6", "♭7", "7"]

    __numbers_minor = ["1", "♭2", "2", "3", "♯3", "4", "♭5", "5", "♭6", "6", "7", "♯7"]

    __romans = ["I", "♭II", "II", "♭III", "III", "IV", "♭V", "V", "♭VI", "VI", "♭VII", "VII"]

    __romans_minor = ["I", "♭II", "II", "III", "♯III", "IV", "♭V", "V", "♭VI", "VI", "VII", "♯VII"]

    __superscripts = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

    def __init__(self, offset = 0, key = None, major_chart = False):
        self.minor = False
        if key:
            if key.endswith("m"):
                key = key.replace("m","")
                self.minor = True
            self.offset = self.__note_indicies[key]
            if self.minor and major_chart:
                self.offset = (self.offset + 3) % 12
                self.minor = False
        else:
            self.offset = offset

    def transpose_chord(self, chord_string, offset=None):
        if offset:
            self.offset = offset
        return re.sub("([A-G](\#|b)?)",(lambda x: self.transpose_note(x.group())), chord_string)

    def transpose_chord_nashville(self, chord_string, offset=None):
        if offset:
            self.offset = offset
        parts = chord_string.split("/")
        chord_name =  re.sub("^([A-G](\#|b)?)",(lambda x: self.transpose_note_to_roman(x.group())), parts[0])

        chord_name = chord_name.translate(self.__superscripts)
        if len(parts) > 1:
            chord_name += "/" + re.sub("([A-G](\#|b)?)",(lambda x: self.transpose_note_to_num(x.group())), parts[1])
        return chord_name

    def get_note_index(self, note):
        return self.__note_indicies[note] if note in self.__note_indicies else none

    def get_note(self, index):
        return transposer.__notes[index]

    def transpose_note(self, note):
        note_index = self.get_note_index(note)
        new_note = (note_index + self.offset ) % 12
        return self.__notes[new_note]

    def transpose_note_to_roman(self, note):
        note_index = self.get_note_index(note)
        new_note = (note_index - self.offset ) % 12
        roman = self.__romans_minor[new_note] if self.minor  else self.__romans[new_note]
        return roman

    def transpose_note_to_num(self, note):
        note_index = self.get_note_index(note)
        new_note = (note_index - self.offset ) % 12
        num = self.__numbers_minor[new_note] if self.minor else self.__numbers[new_note]
        return num  # if  note_index != None else note

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




class ChordChart(object):
    """ A set of ChordDiagrams, multiple fingerings per chord """

    def __init__(self, transpose = 0,file = None, lefty=False):
        """Container for a set of ChordDiagrams"""
        self.grids = {}
        self.tuning = None
        self.transposer = transposer(transpose)
        self.error = None
        self.lefty = lefty
        if file != None:
            self.load_file(open(file))
        


    def load_tuning_by_name(self, instrument_name):
        """
        Load given an instrument name

        TODO:
        If it can't find the file will try to find a chord chart with the same
        relative tuning eg DGBE should find GCEA

        """
        instruments = chordprobook.instruments.Instruments()
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
        grid = ChordDiagram(lefty=self.lefty)
        grid.parse_definition(definition)
        grid.name = self.normalise_chord_name(grid.name)
        if grid.name not in self.grids:
            self.grids[grid.name] = ChordVoicings(grid)
        else:
            self.grids[grid.name].push_to_front(grid)

    def add_from_diagram(self, grid):
        grid.name = self.normalise_chord_name(grid.name)
        if grid.name not in self.grids:
            self.grids[grid.name] = ChordVoicings(grid)
        else:
            self.grids[grid.name].push_to_front(grid)

    def load(self, f):
        self.load_file(f.split("\n"))

    def load_file(self, f):
        
        self.transposer.offset = 12 - self.transposer.offset
        for line in f:
            if line.startswith("{define:"):
                grid = ChordDiagram(lefty=self.lefty)
                grid.parse_definition(line)
                grid.name = self.normalise_chord_name(grid.name)
                if self.transposer.offset > 0:
                    grid.name = self.transposer.transpose_chord(grid.name)
                if grid.name not in self.grids:
                    self.grids[grid.name] = ChordVoicings(grid)
                else:
                    self.grids[grid.name].append(grid)

    def clean_chord_name(self, chord_name):
        """ Remove characters from a chord name that are to do with timing: ! and /. """
         # Allow ! for stacatto chord
        chord_name = re.sub("\!$","", chord_name)

        # Allow / / / ,, - inside chords for strumming
        chord_name = re.sub("([/,-]* *)*$","", chord_name)
        return chord_name

    def normalise_chord_name(self, chord_name):
        """ Transform chord name as used to a canonical name, means we only have to store a limited set of chords
        chord_name: a string representation of a chord
        """
        chord_name = self.clean_chord_name(chord_name)
        # Normalise "add" for ninths, elevenths etc - TODO sharps as well
        #chord_name = re.sub("[aA]dd(\d+)","\\1", chord_name)

        #Get rid of maj and Maj except when its maj7
        chord_name = re.sub("maj","Maj", chord_name)
        chord_name = re.sub("Maj7","maj7", chord_name)
        chord_name = re.sub("M7","maj7", chord_name)
        chord_name = re.sub("Maj","", chord_name)

        #Min -> m
        chord_name = re.sub("[mM]in","m", chord_name)

        # + -> aug
        chord_name = re.sub("\+","aug", chord_name)
        tr = transposer(0)
        chord_name = tr.transpose_chord(chord_name)
        return chord_name

    def nashvillize(self, chord_name, key, major_chart = False):
        """ Transform a chord name into a numeric name (given the key), Nashville Numbering style

        TODO - handle "/"
        """

        tr = transposer(key=key, major_chart=major_chart)
        chord_name= self.normalise_chord_name(chord_name)


        #Min -> m
        chord_name = re.sub("maj7","Δ", chord_name)
        chord_name = re.sub("dim","°", chord_name)
        chord_name = re.sub("aug", "⁺", chord_name)

        # + -> aug
        chord_name = re.sub("\+","aug", chord_name)
        chord_name = tr.transpose_chord_nashville(chord_name)
        chord_name = re.sub("(((I|V)+)m)",lambda x: x.group(2).lower(), chord_name)
        return chord_name


    def grid_as_md(self, chord_name, display_name=False):
        # TODO: add tests
        chord_name_norm = self.normalise_chord_name(chord_name)
        if display_name:
            display_name = chord_name
        chord = self.get_default(chord_name_norm)
        if chord != None:
            return chord.to_md(display_name=display_name)
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
        """ Output chordpro definitions for all know variants of a chord"""
        if chord_name in self.grids:
            chordpro = ""
            for grid in self.grids[chord_name].voicings:
                chordpro += "%s\n" % grid.to_chordpro()
            return chordpro

    def all_to_chordpro(self):
       """ Output all voicings of all chords"""
       chordpro = ""
       for chord_name in sorted(self.grids.keys()):
            chordpro += "%s\n" % self.to_chordpro(chord_name)
       return chordpro

class ChordDiagram(object):
    box_width =  80
    box_height = 100
    top_margin = 10 # Between chord name and zero fret
    default_frets = 5
    default_strings = 4
    bottom_margin = 8 #between last fret and bottom of diagram
    bgcolor = (255,255,255) #whitish
    dot_text_color = (256,256,256) #white
    dot_color = (0,0,0) #black

    def __init__(self, name="", strings=[], draw_name=False, offsets = None, lefty= False):
        """ Empty diagram. No strings, no frets, no nothin' """
        self.name = name
        self.strings = strings
        self.lefty = lefty
        if offsets:
            self.strings = []
            for offset in offsets:
                if offset == -1:
                    offset = None
                self.strings.append(String([Dot(offset)]))

        self.draw_name = False
        self.frets = [] #Will contain fret objects
        self.base_fret = 0
        self.chord = Chord(name)
        self.setup()

    def to_data_URI(self, display_name=None):
        """Convert pic binary data to a data URI for use in web pages"""
        self.draw(display_name=display_name)
        output = BytesIO()
        self.img.save(output, format='PNG')
        im_data = output.getvalue()
        return('data:image/png;base64,' + base64.b64encode(im_data).decode())
        

    def to_md(self, display_name=None):
        """ Markdown version of chord (actually it's HTML anyway) """
        return("<img width='%s' height='%s' alt='%s' src='%s' />" % 
                                            (self.box_width, self.box_height, 
                                             self.name, self.to_data_URI(display_name)))

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

        # Count fingers starting with the min-fret which we only count once as we assume it can be barred
        self.fingers = 0 if self.min_fret < 100 else 0
        for string in self.strings:
            for dot in string.dots:
                if dot.fret and dot.fret > self.min_fret:
                    self.fingers += 1

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
        self.playability = self.open_strings * 50  - self.max_fret * 29 - (self.max_fret - self.min_fret) * 7 - self.fingers * 8


    def draw(self, display_name=None):
        """
        Render the chord.
        """
        # Commence scribbling
        self.img = Image.new("RGB", (self.box_width, self.box_height), ChordDiagram.bgcolor)
        draw = ImageDraw.Draw(self.img)

        w, h = draw.textsize(self.name)
        top_margin = ChordDiagram.top_margin
       
        # Look, I can write my own name
        if display_name or self.draw_name:
            name = display_name if display_name else self.name
            draw.text(((self.box_width - w) / 2, 0), name, (0,0,0))
        else:
            (w, h) = (0, 0)

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
        """Unpack a chordpro chord definition, trying to be as permissive as possible """
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
            # Don't use fingerings if we're doing left handed chords
            if not self.lefty and fingers_search != None:
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
            if self.lefty:
                self.strings.reverse()

        self.setup()





class Note:
    """ Class for representing a note
    Todo - move some of the transpose functionality into here

    """
    __note_indicies = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "D#": 3,
                     "E" : 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "Ab": 8,
                     "G#": 8, "A" : 9, "Bb": 10, "A#": 10, "B": 11}

    __note_names = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


    def __init__(self, note):
        """ Get a new note object """
        if type(note) == int:
            self.name = Note.__note_names[note]
            self.num = note
        elif note in Note.__note_indicies:
            self.num = Note.__note_indicies[note]
            self.name = note
        else:
            return None

    def get_note_index(self, note):
        return Note.__note_indicies[note] if note in Note.__note_indicies else None


    def transpose(self, offset):
        new_note_num = (self.num + offset ) % 12
        self.num = new_note_num
        self.name = Note.__note_names[new_note_num]





class Chord:
    """ Class for representing chords as a set of notes, to be used for generating chord charts automatically.
    Will add some new code here that (TODO) can later be used in the rest of the library."""
    def __init__(self, chord_name, lefty = False):
        """Initialise chord by name
        Parameters:
        name: name of the chord; eg C#m
        Return:
        Array of notes eg ['C#','E','Ab']
        or None if the chord type is not known
        """
        self.lefty=lefty

        chart = ChordChart(lefty=lefty)
        # Work out what type of chord this is
        self.name = chart.normalise_chord_name(chord_name)
        self.flavour = re.sub("([A-G](\#|b)?)", "", chord_name)
        self.root = Note(re.sub("([A-G](\#|b)?).*", "\\1", chord_name))


    def spell(self):
        #Lookup table of chord offsets
        spellings = {
        "" :  [Note("C"), Note("E"), Note("G")],
        "m" : [Note("C"), Note("Eb"), Note("G")],
        "7" : [Note("C"), Note("E"), Note("G"), Note("Bb")],
        "6" : [Note("C"), Note("E"), Note("G"), Note("A")],
        "m7" : [Note("C"), Note("Eb"), Note("G"), Note("Bb")],
        "9":  [Note("C"), Note("E"), Note("G"), Note("B"), Note("D")],
        "add9":  [Note("C"), Note("E"), Note("G"), Note("D")],
        "maj7":  [Note("C"), Note("E"), Note("G"), Note("B")],
        "aug": [Note("C"), Note("E"), Note("G#")],
        "dim": [Note("C"), Note("Eb"), Note("Gb")],
        "sus4":  [Note("C"), Note("E"), Note("F"), Note("G")]
        }
        self.notes = None
        self.nums = None
        if self.flavour in spellings:
           self.notes = []
           self.nums = []
           for note in spellings[self.flavour]:
               note.transpose(self.root.num)
               self.nums.append(note.num)
               self.notes.append(note)

        return self.nums

    def find_fingerings(self, instrument, reach = 4, fingers = 4, unplayed = 0):
        """Work out ways of playing a chord on the given instrument
        instrument: an instrument object
      """
        self.spell()
        self._fingering_array = Fingerings(self, instrument, reach, fingers, unplayed).fingerings


    def to_chordpro(self):
        """ Generate a chord chart just for this chord and return in chordpro format """
        self.chart = ChordChart(lefty=self.lefty)
        self.add_to_chordchart(self.chart)
        return (self.chart.to_chordpro(self.name))


    def add_to_chordchart(self, chart):
        """ Add the chords found by find_fingerings to a chord chart object)"""
        for fingering in self._fingering_array:
            diagram = ChordDiagram(offsets = fingering, name=self.name, lefty=self.lefty)
            chart.add_from_diagram(diagram)
        chart.sort_by_playability(self.name)

class Fingerings:
    """ Class for holding and finding different ways of playinc a chord """

    def __init__(self, chord, instrument, reach=4, fingers=4, max_unplayed_strings = 1):
        """ Set up a fingerings object
        chord = A and instance of chordprobook.chords.Chord
        instrument = An instance of chordprobook.instruments.Instrument
        """
        self.chord = chord
        notes_yet_to_find = [x.num for x in chord.notes]
         # TODO make this a chord

        self.max_reach = reach
        self.max_fingers = fingers
        self.instrument = instrument
        self.max_unplayed_strings = max_unplayed_strings
        self.fingerings = [] # Array of working chords
        #Start recursive search from leftmost string, initialise with no strings played
        frets_found = [-1] * len(instrument.notes)
        self.find_note(list(frets_found), list(notes_yet_to_find), 0,0)


    def find_note(self, frets_found, notes_yet_to_find, search_string, search_fret):
        """ Recursive search for chord fingerings, uses integer arrays for now. TODO, integrate this code with ChordDiagram
        frets_found = array with one element per string, playable notes with be added as fret numbers eg [0,0,0,3] is a uke C
        TODO: Finger counting, unplayed strings, barre chords
         """
        def chord_stats(frets_found):
            """calculate some details about the chord
            Returns:
            max_fret: Highest fret position
            min_fret: Lowest non-zero played string fret position
            fingers: Number of fingers needed to play
            """
            max_fret = 0
            min_fret = 1
            fingers = 0
            played_notes = [x for x in frets_found if x > 0]
            if played_notes != []:
                max_fret = max(played_notes)
                min_fret = min(played_notes)
                fingers = len(played_notes)
                # Allow for barre by assuming one finger can play the min_fret position
                if frets_found.count(0) == 0:
                    fingers = fingers - frets_found.count(min_fret) + 1
            return (max_fret, min_fret, fingers)

        # Terminate recursion when we've gone past the 11th fret, or run out of strings
        if search_fret > 11 or search_string > len(self.instrument.notes) - 1:
            return None

        self.find_note(list(frets_found), list(notes_yet_to_find), search_string, search_fret + 1)
        # Left-most strings may be left uplayed so if the one to the left is, and we have enough strings left then search
        if  search_string < self.max_unplayed_strings and  (search_string  == 0 or frets_found[search_string - 1] == -1) and search_fret == 0 and len(frets_found) - search_string > len(notes_yet_to_find):
            self.find_note(list(frets_found), list(notes_yet_to_find), search_string + 1, 0 )

        current_note = Note(self.instrument.notes[search_string].name)

        current_note.transpose(search_fret)
        #print("string ", search_string, "fret", search_fret, "Is note", current_note.name, "so far", frets_found, "To find", [Note(x).name for x in notes_yet_to_find], "max", max_fret, "min", min_fret)

        if current_note.num in self.chord.nums:
            frets_found[search_string] = search_fret

             #If chord not playable bail out
            max_fret, min_fret, fingers = chord_stats(frets_found)
            if fingers > self.max_fingers or max_fret - min_fret >= self.max_reach: # or (search_string == 0 and max_fret  > self.max_reach):
                return

            if current_note.num in notes_yet_to_find: #Note index already found?
                notes_yet_to_find.remove(current_note.num)
                #print("Got a match:", self.chord.name, frets_found, [Note(x).name  for x in notes_yet_to_find], search_string == len(self.instrument.notes))
            elif self.chord.nums.index(current_note.num) > 3:
                    # This is a chord mod that's not core so don't put in more than one
                    return
            if len(notes_yet_to_find) == 0 and search_string == len(self.instrument.notes) - 1:
                self.fingerings.append(frets_found)


            self.find_note(list(frets_found), list(notes_yet_to_find), search_string + 1, 0)
