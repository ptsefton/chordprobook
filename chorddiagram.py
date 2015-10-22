from PIL import Image, ImageFont, ImageDraw
import re
from io import BytesIO
import base64
import os.path


class Dot:
    """ Class to represent a single dot in the diagram ie a finger on a fret use None to say 'don't play'"""
    def __init__(self, fret, finger = None):
        self.fret = fret 
        self.finger = finger if self.fret != None else 0
        
        
class String:
    """Class to represent all the dots to show on a string, pass in an array of dot """
    def __init__(self, dots):
        self.dots = dots

        
class Fret:
    """Placeholder for a fret class to hold x,y coordinates"""
    def __init__(self, left_x, y, right_x):
        self.left_x = left_x
        self.y = y
        self.right_x = right_x
        
class ChordChart:
    def __init__(self):
        """Container for a set of chord-grids"""
        self.grids = {}
        self.tuning = None
        
    def load_tuning(self, strings):
        """
        Takes a string representation of an instrument tuning, eg:
        EADGBE (guitar) or
        GCEA (soprano uke)
        """
        
        self.tuning = strings.upper()
        path, file = os.path.split(os.path.realpath(__file__))
        
        f = open(os.path.join(path, "%s_chords.cho" %  self.tuning))
        self.load_file(f)
    
        
    def load_file(self, f):
        for line in f:
            if line.startswith("{define:"):
                grid = ChordDiagram()
                grid.parse_definition(line)
                self.grids[grid.name] = grid

    def normalise_chord_name(self, chord_name):
        """ Transform chord name as used to a canonical name, means we only have to store a limited set of chords """
        # Allow ! for stacatto chord
        chord_name = re.sub("\!$","", chord_name)
        
        # Allow / / / inside chord diagrams for strumming
        
        chord_name = re.sub("(/* *)*$","", chord_name)
        
        # Normalise "add" for ninths, elevenths etc - TODO sharps as well
        chord_name = re.sub("add(\d+)","\\1", chord_name)
        return chord_name
                
    def grid_as_md(self, chord_name):
        # TODO: add tests
        chord_name = self.normalise_chord_name(chord_name)
        if chord_name in self.grids:
            return self.grids[chord_name].to_md()
        else:
            return("[%s]" % chord_name)
    
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
    
    def __init__(self, name="", strings=[]):
        """ Empty diagram. No strings, no frets, no nothin' """
        self.name = name
        self.strings = strings
        
        self.frets = [] #Will contain fret objects
        self.base_fret = 0
        
    def to_data_URI(self):
        self.draw()
        output = BytesIO()
        self.img.save(output, format='PNG')
        im_data = output.getvalue()
        return('data:image/png;base64,' + base64.b64encode(im_data).decode())
    
    def to_md(self):
        return("<img width='%s' height='%s' alt='%s' src='%s' />" % (self.box_width, self.box_height, self.name, self.to_data_URI()))

    def draw(self):
        """
        Render the chord - have exposed a lot of the internal maths to help with testing, hard to test the diagrams but
        we can at least check that frets are not on top of each other, and so on.
        """
       
        #work out min non-0 and max fretted (rather than open) positions
        #if self.base_fret == 0:
        max_fret = 0
        min_fret = 100
        for string in self.strings:
            for dot in string.dots:
                if dot.fret != None and dot.fret != 0:
                    dot.fret = dot.fret + self.base_fret
                    max_fret = max(dot.fret,max_fret)
                    min_fret = min(dot.fret, min_fret)

        # Recalculate base_fret
        if max_fret > ChordDiagram.default_frets and 100 > min_fret > 1:
            self.base_fret = min_fret - 1
            for string in self.strings:
                for dot in string.dots:
                    if dot.fret != None and dot.fret != 0:
                        dot.fret = dot.fret - self.base_fret

        #Work out how many frets to draw.
        #This program is not your music teacher! if you put in stupid chords it will
        # draw them
        fret_range = max_fret - self.base_fret
        if fret_range > ChordDiagram.default_frets:
            self.num_frets = fret_range
        else:
            self.num_frets = ChordDiagram.default_frets

        #Scale up if there are lots of strings or frets
        self.num_strings = len(self.strings)
        self.box_height = ChordDiagram.box_height
        self.box_width = ChordDiagram.box_width
        
        #TODO: get rid of these contstants
        if self.num_strings > ChordDiagram.default_strings:
            self.box_width = int((self.box_width / ChordDiagram.default_strings) * self.num_strings)

        if self.num_frets> ChordDiagram.default_frets:
            self.box_height = int((self.box_height / ChordDiagram.default_frets) * self.num_frets)

        # Commence scribbling
        self.img = Image.new("RGB", (self.box_width, self.box_height), ChordDiagram.bgcolor)
        draw = ImageDraw.Draw(self.img)

        # Look, I can write my own name
        # TODO, bigger, nicer font
        w, h = draw.textsize(self.name)
        draw.text(((ChordDiagram.box_width - w) / 2, 0),self.name, (0,0,0))
        
        # Draw plenty of strings evenly placed across the diagram, instrument agnostic,
        self.string_top = h + ChordDiagram.top_margin
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
                if dot.finger != None:
                    w, h = draw.textsize(str(dot.finger))
                else:
                    w, h = draw.textsize("8")
                r = w
                
                if dot.fret == None:
                    draw.text((x - w/2, self.string_top - h), "x", self.dot_color)
                elif dot.fret != 0:
                    y = self.string_top + f * self.fret_spacing
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
            #Could add this to main regex but this was simpler in initial coding
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
                 
        


        
    


      	  
