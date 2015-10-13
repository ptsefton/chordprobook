# chordprobook

## What does this do? Formats song charts


This is a Python 3 script to convert collections of
[chordpro](http://blossomassociates.net/Music/chopro.html) formatted
song charts to PDF, HTML, and word processing doc formats. You can
convert a direcotry full of files to a single book, or a set of
song-sheets.


NOTE: Unlike most chordpro software this does not display chords above the text (not yet anyway). Displaying chords inline is more compact and it's good enough for Rob Weule and his [Ukulele Club Songbook](http://katoombamusic.com.au/product/ukulele-club-songbook/) and for [Richard G](http://www.scorpexuke.com/ukulele-songs.html) it's good enough for me.

## TODO

When I get time I'll convert these TODOs into github milestones.

* Chord charts for various intruments
* Better doco
* Maybe a GUI? Probably not
* Display chords above text? Probably not


## Audience

This is for people running a unix-like operating system who know how
to install packaged software scripts and python modules.


Status: Alpha / mostly works for me  on OS X 10.10.5.


## Installation on OS X (you're on your own on other platforms)

Requires pandoc 1.15.0.6 or later  and wkhtmltopdf installed on on your path.

* Install Pandoc HEAD using [brew](http://brew.sh/):

    ```brew install pandoc --HEAD```
* Download and install [wkhtmltopdf](http://wkhtmltopdf.org/downloads.html)
* Install dependencies using pip3:

    ```pip3 install pypandoc```

```
./chordprobook.py -h

## usage

chordprobook.py [-h] [-a] [-k] [--a4] [-e] [-f FILE_STEM] [--html] [-w]
                       [-p] [-r REFERENCE_DOCX] [-o] [-b] [-s SETLIST]
                       [--title TITLE]
                       [files [files ...]]

positional arguments:
  files                 List of files

optional arguments:
  -h, --help            show this help message and exit
  -a, --alphabetically  Sort songs alphabetically
  -k, --keep_order      Preserve song order for playing as a setlist (inserts
                        blank pages to keep multi page songs on facing pages
  --a4                  Format for printing (web page output)
  -e, --epub            Output epub book
  -f FILE_STEM, --file-stem FILE_STEM
                        Base file name, without extension, for output files
  --html                Output HTML book, defaults to screen-formatting use
                        --a4 option for printing (PDF generation not working
                        unless you chose --a4 for now
  -w, --word            Output .docx format
  -p, --pdf             Output pdf
  -r REFERENCE_DOCX, --reference-docx REFERENCE_DOCX
                        Reference docx file to use (eg with Heading 1 having a
                        page-break before)
  -o, --one-doc         Output a single document per song: assumes you want A4
                        PDF
  -b, --book-file       First file contains a list of files, each line
                        optionally followed by a transposition (+|-)\d\d? eg
                        to transpose up one tone: song-file.cho +2
  -s SETLIST, --setlist SETLIST
                        Use a setlist file to filter the book, one song per
                        line and keep facing pages together. Setlist lines can
                        be one or more words from the song title
  --title TITLE         Title to use for the book


```

# Examples

Create a PDF book from all the files in a directory. 

* To make a PDF book (defaults to songbook.pdf) from a set of chordpro
  files:

   ```./chordprobook samples/*.cho```

    Which is equivalent to:

    ```./chordprobook --pdf --a4  --title="My book" samples/*.cho```

*  To add a file name and a title to the book.
 
    ```./chordprobook --file-stem=my_book --title="My book"  samples/*.cho```

*  If you'd like it sorted alphabetically by title:

    ```./chordprobook -a --file-stem=my_book --title="My book"  samples/*.cho```

* To build a book from a list of files use a book file and the -b
   flag. This will preserve the order you entered the songs except
   that it will make sure that two-page songs appear on facing pages.
  
    ```./chordprobook.py -b samples/sample-book.txt```

* To make sure the order of songs is preserved exactly, for example to
  use as a setlist, use -k or --keep-order. This will insert blank
  pages if necessary.

    ```./chordprobook.py -k -b samples/sample-book.txt```

*  To sort songs alphabetically add the -a or --alphabetical flag:

    ```./chordprobook.py -a -b samples/sample-book.txt```
    
* To choose a subset of the songs in a book in a particular order use
  a setlist file.  The setlist consists of an optional {title: }
  directive, and optional {book: <path>} directive followed by a list
  of songs, one per line. Identify songs by entering one or more words
  from the title, in order. So "Amazing" will match "Amazing Grace"
  and "Slot Baby" would match "Slot Machine Baby".

* To choose a subset of the songs in a book in a particular order use a setlist file. 
  The setlist consists of an optional {title: } directive, and optional {book: <path>} directive followed by a list of songs, one per line. Identify songs by entering one or more words from the title, in order. So "Amazing" will match "Amazing Grace" and "Slot Baby" would match "Slot Machine Baby".
>>>>>>> a5e4b075ffd87e5e2d172b2af9caaedeff29da88

   Use this to filter all the songs in a directory using a setlist:

    ```./chordprobook.py -s samples/setlist.txt samples/*.cho```
    
*  Or use a book file:

   Use this to filter all the songs in a directory using a setlist:

    ```./chordprobook.py -s samples/setlist.txt -b samples/sample-book.txt```
