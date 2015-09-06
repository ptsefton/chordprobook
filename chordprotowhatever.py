import glob
import re
import argparse
import os
import subprocess
import pypandoc

class transposer:
   
    __note_indicies = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "D#": 3,
                     "E" : 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "Ab": 8,
                     "G#": 8, "A" : 9, "Bb": 10, "A#": 10, "B": 11}
        
    __notes = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
    
    def __init__(self, offset = 0):
        self.offset = offset
    
    def transpose_chord(self, chord_string):
        return re.sub("([A-G](\#|b)?)",(lambda x: self.transpose_note(x.group())), chord_string)
               
    def __getNoteIndex(self, note):
        return self.__note_indicies[note] if note in self.__note_indicies else none
    
   
    def transpose_note(self, note):   
        note_index = self.__getNoteIndex(note)
        new_note = (note_index + self.offset ) % 12
        return self.__notes[new_note] if  note_index != None else note
    
class cp_song:
    def __init__(self, song, title="Song", transpose=0, blank = False):
        self.blank = blank
        self.text = re.sub("(.)\n(.)", "\\1    \\n\\2", song)
        self.key = None
        self.pages = 1
        self.title = title
        self.transposer = transposer(transpose)
        self.__find_title()
        if self.title == None:
            self.title = title
        self.__find_key()
        self.__format_tab()
        self.format()    

        self.__format_chorus()

    def __find_title(self):
        self.title = None
        title_re = "{(ti:|title:) *(.*?)}"
        title_search = re.search(title_re, self.text)
        if title_search != None:
            self.title = title_search.group(2)
            self.text = re.sub(title_re, "", self.text)
        
    def __find_key(self):
        key_re = re.compile("{key: *(.*)}")
        key_search = re.search(key_re, self.text)
        if key_search != None:
            self.key = key_search.group(1)
            self.key = self.transposer.transpose_chord(self.key)
            self.text = re.sub(key_re, "", self.text)

    def __format_chorus(self):
        in_chorus = False
        new_text = ""
        for line in self.text.split("\n"):
            if re.match("{(soc|start_of_chorus)}", line):
                in_chorus = True
            elif re.match("{(eoc|end_of_chorus)}", line):
                in_chorus = False
            else:
                if in_chorus:
                    new_text += ">"
                new_text += line + "\n"
        if in_chorus:
            new_text +=  "\n\n"
        self.text = new_text
        
    def __format_tab(self):
        in_tab = False
        new_text = ""
        for line in self.text.split("\n"):
            if re.match("{(sot|start_of_tab)}", line):
                in_tab = True
                new_text += "\n\n```\n"
            elif re.match("{(eot|end_of_tab)}", line):
                in_tab = False
                new_text += "```\n"
            else:
                if not in_tab:
                    line = line.replace("][","] [")
                    line = re.sub("\[(.*?)\]","**[\\1]**",line)
                new_text += line + "\n"
        if in_tab:
            new_text +=  "```"
        self.text = new_text
     
        
    def format(self):
        def format_chord(chord):
            return ("%s" % (self.transposer.transpose_chord(chord)))
        song =  self.text
        
        
        #TAB
        #song = re.sub("{(sot|eot|start_of_tab|end_of_tab)}","```", song)
        # Subtitle
        # Remove comments (as in remarks, not {c: })
        song = re.sub("\n#.*","", song)
        
        song = re.sub("{(st:|subtitle:) *(.*)}","\n*\\2*", song)
        
        #Comments / headings
        song = re.sub("{(c:|comment:) *(.*)}","*\\2*", song)
        
        #Chords
        song = re.sub("\[(.*?)\]",lambda m: format_chord(m.group()),song)
        key_string = self.get_key_string()

        
        title = "%s %s" % (self.title, key_string)
        song = "<div>\n# %s\n%s\n</div>" % (title, song)
        #song = "\n<div>\n%s\n</div>\n" % (song)
        song, pages = re.subn("{(new_page|np)}", "<!-- new_page -->", song)
        if pages > 0:
            self.pages = pages + 1
        self.md = song
        
    def to_html(self):
        self.format()
        song = """
<div class='song'>
<div class='page'>

%s

</div>
</div>
        """ % self.md
        song = song.replace("<!-- new_page -->", "\n</div></div><div class='page'><div>")
        return pypandoc.convert(song, 'html', format='md')
        
    def get_key_string(self):
        return "(Key of %s)" % self.key if self.key != None else ""

class cp_song_book:
    def __init__(self, songs = [], keep_order = False):
        self.songs = songs
        self.keep_order = keep_order
        
    def order_by_setlist(self, setlist):
        new_order = []
        for potential_song in setlist.split("\n"):
            if potential_song.strip() != "":
                restring = potential_song.replace(" ", ".*?").lower()
                print (restring)
                regex = re.compile(restring)
                print (self.songs)
                found_song = False
                for song in self.songs:
                    if re.search(regex, song.title.lower()):
                        new_order.append(song)
                        found_song = True
                if not found_song:
                    new_order.append(cp_song("{title: %s (not found)}" % potential_song))
        self.songs = new_order
        
    def reorder(self, start_page, old = None, new_order=[], waiting = []):
        def make_blank():
            new_order.append(cp_song("{title:This page intentionally left blank}", blank=True))
        if old == None:
            old = self.songs
        """Reorder songs in the book so two-page songs start on an even page)
           Unless this is a set-list in which case insert blanks"""
        if old == []:
            #TODO insert a blank page if needed or look back
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
            
            #Also OK to start any song here so append head of list
            new_order.append(old[0])
            start_page += old[0].pages
        elif old[0].pages % 2 == 0:
            # Have a two page spread, so save it
            if self.keep_order:
                make_blank()
                new_order.append(old[0])
            else:
                waiting.append(old[0])
        else:
            new_order.append(old[0])
            start_page += old[0].pages
        self.reorder(start_page, old[1:], new_order, waiting)    
                    
                
class html_book:
    
    def format(html, contents = "",  title="Untitled", for_print= False):
        script = """
$(function() {

$("div.page").each(function() {
 var div = $(this).children("div");
 var i = 0;
 console.log("Looping");
 if (div.length > 0)
 {
   // Make text bigger until it is too big
   while( $(this).height() * %(cols)s > div.height()) {
    div.css('font-size', (parseInt(div.css('font-size')) + 1) +"px" );
    i++;
    if (i > 50) {break}
    }
   // Make text small until it is just right
   while( $(this).height() * %(cols)s < div.height() ) {
    div.css('font-size', (parseInt(div.css('font-size')) - 1) +"px" );
      i++;
    if (i > 100) {break}
    }
    console.log($(this).find("h1").html(), $(this).width(), div.width(), div.css('font-size') );
    
  }
});

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
  -webkit-margin-before: .5em;
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

<div class='song'>
<div class='page'>

<div>
<h1>%s</h1>
</div>
</div>
</div>

<div class='song'>
<div class='page'>

</div>
</div>

<div class='song'>
<div class='page'>
<div>
%s
</div>
</div>
</div>

%s

</body>
</html>
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
.page {
width: 21cm;
height: 29cm;
padding: .2cm;
margin: .2cm;
border-style: solid;
border-width: 1px;
overflow: hidden;
border-color: #FFFFFF;


}
h1 {
   padding: 0px 0px 0px 0px;
     margin: 0px 0px 0px 0px;
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
}
</style>
</head>
<body>

<div class='song'>
<div class='page'>
<div>
<h1>%s</h1>
</div>
</div>
</div>

<div class='song'>
<div class='page'>
<div>

</div>
</div>
</div>

<div class='song'>
<div class='page'>

%s

</div>
</div>

%s
</body>
</html>
"""
        if for_print:
             web_template = print_template
             cols = "1"
        else:
            cols = "2"
        return web_template % (title, script % {'cols': cols}, title, contents, html)
        
        
def to_markdown(f, out_dir, transpose = 0):
    song = f.read()
    s = ""
    outname = os.path.split(f.name)[1]
    if transpose != 0:
        outname = outname + str(transpose)
    out_path = os.path.join(out_dir,"%s.md" % outname)
    
    
output = "markdown"

def process_list(files, out_dir):
    #TODO: get title and rememeber
    songs = []
    for f in files:
        songs.append(to_markdown(f, out_dir))
    return songs
    
def convert():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', type=argparse.FileType('r'), nargs="*", default=None, help='List of files')
    parser.add_argument('-d', '--directory', default=".", help='Directory to process')
    parser.add_argument('-a', '--alphabetically', action='store_true', help='Preserve song order for playing as a setlist (inserts blank pages to keep multi page songs on facing pages')
    parser.add_argument('-k', '--keep_order', action='store_true', help='Sort songs alphabetically')
    parser.add_argument('--a4', action='store_true', help='Format for printing (web page output)')
    parser.add_argument('-e', '--epub-file', default=None, help='Output epub book')
    parser.add_argument('-m', '--html-file', default=None, help='Output HTML book, defaults to screen-formatting use --a4 option for printing')
    parser.add_argument('-w', '--word-file', default=None, help='Output word book')
    parser.add_argument('-p', '--pdf-file', default=None, help='Output pdf book')
    parser.add_argument('-i', '--odp-file', default=None, help='Output impress (.odp)')
    parser.add_argument("-t", '--odp-template', default='songbook-template.odp', help='Impress (.odp) template to use')
    parser.add_argument('-b', '--input-is-book', action='store_true', help ='First file contains a list of files, each line optionally followed by a transposition (+|-)\d\d?')
    parser.add_argument('-s', '--setlist', default=None,
                        help ='Use a setlist file to filter the book, one song per line. Setlist lines can be one or more words from the song title')
    parser.add_argument('--title', default='Songs', help='Title to use for the book')
    


   

    args = vars(parser.parse_args())
    print (args["setlist"])
    
    out_dir = "."
    os.makedirs(out_dir, exist_ok=True)
   
    if args["files"] != None:
       if args["input_is_book"]:
            songs = []
            book_file = args["files"][0]
            book_dir, _ = os.path.split(book_file.name)
            for line in book_file:
                trans = re.search("((\+|-)?\d+)$", line)
                t = 0
                if trans != None:
                    print(trans.group(0))
                    t = int(trans.group(0))
                    print(t)
                    line = re.sub("((\+|-)?\d+)$", "", line)
                line = line.strip()
                if line != "":
                    songs.append(cp_song(open(os.path.join(book_dir, line.strip())).read(), transpose=t))
       else:
           songs = process_list(args["files"], out_dir)
    else:
        in_dir = args["directory"]
        out_dir = in_dir if out_dir == "." else outdir
        songs = process_list(glob.glob(os.path.join(in_dir,"*.cho")), out_dir)
        
    book_name =  args["epub_file"]
    word_name = args["word_file"]
    pdf_name = args["pdf_file"]
    odp_name = args["odp_file"]
    html_name = args["html_file"]

    
    output_files = []
    
    book = cp_song_book(songs, keep_order = args['keep_order'])

    if args["setlist"] != None:
       list = open(args["setlist"]).read()
       book.order_by_setlist(list)

       
    if args["alphabetically"]:
        songs.sort(key= lambda song: re.sub("^(the|a|\(.*?\)) ", "", song.title.lower()))
    
   
    # TODO FIX IT 
    if  book_name != None:
        command = ["pandoc", "--toc-depth", "1", "-t", "epub", "-f", "markdown+hard_line_breaks", "-o", book_name, "--epub-chapter-level=1", "--epub-stylesheet", "songbook.css"] +  output_files
        subprocess.call(command)
        subprocess.call(["open", book_name])
    # TODO FIX IT  
    if word_name != None:
        command = ["pandoc", "--toc", "--data-dir", ".", "--toc-depth", "1", "-t", "docx", "-f", "markdown+hard_line_breaks", "-o", word_name, "--epub-chapter-level=1",] +  output_files
        subprocess.call(command)
        
        subprocess.call(["open", word_name])
        
    if pdf_name != None:
        command = ["pandoc", '-s', '-V', '--document-class=memoir', "--toc", "--template", "onepage.latex", "--toc-depth", "1", "-t", "latex", "-f", "markdown+hard_line_breaks", "-o", pdf_name, "--epub-chapter-level=1",] +  output_files
        subprocess.call(command)
        
        subprocess.call(["open", pdf_name])
    title = args['title']
    
    if odp_name != None:
        odp_template = args["odp_template"]
        omnibus_md = odp_name + "temp.md"
        contents = "# Contents\n"
        #TODO Depends on template so should be passed as an option
        start_page = 4
        book.reorder(start_page)
        all_songs = ""
        page_count = start_page
        for song  in book.songs:
            if not song.blank:
                contents += song.title +  " - " + str(page_count) + "    \n"
                song.title = "%s" % (str(page_count), song.title)
                song.format()
            page_count += song.pages
            all_songs += song.md
        
        open(omnibus_md, 'w').write(contents + all_songs)
       
        command = ["python", "odpdown/odpdown.py", "--break-master=song", "--content-master=toc",  omnibus_md, odp_template, odp_name]
       
        subprocess.call(command)
        subprocess.call(["open", odp_name])

    
    if html_name != None:
        pdf_path = re.sub(".html$",".pdf", html_name)
        contents = "# Contents\n<table width='100%'>\n"
        #TODO Depends on template so should be passed as an option
        start_page = 4
        book.reorder(start_page)
        all_songs = ""
        page_count = start_page
        for song  in book.songs:
            if not song.blank:
                contents += "<tr><td>%s</td><td>%s</td></tr>" % (song.title, str(page_count)) 
                song.format()
                
            page_count += song.pages
            
            all_songs += song.to_html()
        contents += "</table>"
            
            #all_songs += "<table style="align:><tr><td>prev</td><td>%s</td><td>next</td></tr></table>" %  str(page_count)
        #TODO FRONTMATTER / CONTENTS!
        open(html_name, 'w').write( html_book.format(all_songs,
                                                      title=title,
                                                      for_print = args['a4'],
                                                      contents=pypandoc.convert(contents,
                                                                                "html",
                                                                                format="md")))
        
        if args['a4']:
            command = ['wkhtmltopdf', '--enable-javascript', '--print-media-type', '--outline', '--outline-depth', '1', '--default-header', html_name, pdf_path]
            subprocess.call(command)
            subprocess.call(["open", pdf_path])
        
if __name__ == "__main__":
    convert()
