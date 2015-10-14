from PIL import Image, ImageFont, ImageDraw
class Dot:
    """ Class to represent a single dot in the diagram ie a finger on a fret"""
    def __init__(self, fret, finger = None):
        self.fret = fret
        self.finger = finger
        
class String:
    """Class to represent all the dots to show on a string, pass in an array of dots,
       or dont_play = True for stings that should be marked 'x' """
    def __init__(self, dots, dont_play = False):
        self.dots = dots if not dont_play else []
        self.dont_play  = dont_play

class Fret:
    """Placeholder for a fret class to hold x,y coordinates"""
    def __init__(self, left_x, y, right_x):
        self.left_x = left_x
        self.y = y
        self.right_x = right_x
        
class ChordDiagram:
    box_width =  80
    box_height = 100
    top_margin = 5 # Between chord name and zero fret
    bottom_margin = 5 #between last fret and bottom of diagram
    box_size = (box_width, box_height)
    bgcolor = (255,255,255)
    dot_text_color = (256,256,256)
    dot_color = (256,0,256)
    
    def __init__(self, name="C7", strings=[String([Dot(0)]),String([Dot(0)]),String([Dot(0)]),String([Dot(1, 1)])]):
        """ Defaults to a diagram for a sprano uke C7 chord """
        self.name = name
        self.strings = strings
        self.img = Image.new("RGB", ChordDiagram.box_size, ChordDiagram.bgcolor)
        self.frets = [] #Will contain fret objects

    def draw(self):
        """
        Render the chord - have exposed a lot of the internal maths to help with testing, hard to test the diagrams but
        we can at least check that frets are not on top of each other, and so on.
        """
        draw = ImageDraw.Draw(self.img)
        #Write my own name
        w, h = draw.textsize(self.name)
        draw.text(((ChordDiagram.box_width - w) / 2, 0),self.name, (0,0,0))
        
        # Draw plenty of strings evenly placed across the diagram
        self.string_top = h + ChordDiagram.top_margin
        self.string_bottom = ChordDiagram.box_height - ChordDiagram.bottom_margin
        self.num_strings = len(self.strings)
        self.string_spacing = ChordDiagram.box_width / (self.num_strings + 1)
        for i  in range(0, len(self.strings)):
            string = self.strings[i]
            string.string_x = self.string_spacing * (i + 1)
            coords = (string.string_x, self.string_top, string.string_x, self.string_bottom)
            draw.line(coords, fill=128)

        # Draw enough frets
        self.num_frets = 5 # TODO - work out if we actually need more for a particular chord
        self.fret_spacing = (self.string_bottom - self.string_top) / self.num_frets
        
        for i in range(0, self.num_frets + 1):
            fret = Fret(self.string_spacing, self.string_top +  i * self.fret_spacing, self.string_spacing * self.num_strings )
            self.frets.append(fret)
            draw.line(( fret.left_x, fret.y, fret.right_x, fret.y ), fill=128)
            
        # Draw the dots
        for i in range(0, len(self.strings)):
            string = self.strings[i]
            # TODO deal with dont_play
            for dot in string.dots:
                f = dot.fret
                x = (i + 1) * self.string_spacing
                y = self.string_top + f * self.fret_spacing
                w, h = draw.textsize("8")
                r = w 
                if dot.fret != 0:
                    draw.ellipse((x-r, y-r, x+r, y+r), ChordDiagram.dot_color)
                    if dot.finger != None:
                        draw.text((x - r /3.1415 ,y - r ),str(dot.finger), ChordDiagram.dot_text_color)
                    
    def show(self):
        self.draw()
        self.img.show()


        
    


      	  
