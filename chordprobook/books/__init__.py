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
import chordprobook.chords as chords
import chordprobook.instruments



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
            self.instruments = chordprobook.instruments.Instruments()
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
        self.transposer = chords.transposer(transpose)
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
                        self.local_instruments = chordprobook.instruments.Instruments()
                    current_instrument = self.local_instruments.get_instrument_by_name(inst_name)
                    self.local_instrument_names.append(inst_name)
                    if current_instrument == None:
                        current_instrument = chordprobook.instruments.Instrument(name = inst_name)
                        current_instrument.chart = chords.ChordChart()
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
            self.transposer = chords.transposer(self.transpose)
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
            self.instruments = chordprobook.instruments.Instruments()
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
     -webkit-margin-before: 0em;
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

p, blockquote {
     -webkit-margin-before: 0em;
     -webkit-margin-after: .6em;
}

blockquote {
  border-left: 5px solid #c00;
  padding-left: 5px;
  margin-left: 0em;
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
        
   
