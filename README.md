# chordprobook

Status: Alpha / mostly works for me  on OS X 10.10.5.

Python 3 script to convert collections  of
[chordpro](http://blossomassociates.net/Music/chopro.html). Ch
formatted song charts to PDF,
HTML, and word processing doc formats.

Requires pandoc 1.15.0.6 or later  and wkhtmltopdf installed on on your path.

On OS X install Pandoc HEAD using [brew](http://brew.sh/):
    brew install pandoc --HEAD
    

```
./chordprobook.py -h

usage: chordprobook.py [-h] [-a] [-k] [--a4] [-e] [-f FILE_STEM] [--html] [-w]
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

Create a PDF book from all the files in a directory. Note that PDF
files without the A4 flag don't actually work ATM.

```./chordprobook --pdf --a4 --file-stem=my_book --title="My book"  my-songs/*.cho```

If you'd like it sorted 
