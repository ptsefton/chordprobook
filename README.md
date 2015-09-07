# chordprobook

Python 3 script to convert collections  of chordpro format song charts to PDF,
HTML, and word processing doc formats.

Requires pandoc 1.15.0.6  and wkhtmltopdf installed on on your path.


```
usage: chordprobook.py [-h] [-a] [-k] [--a4] [-e] [-f FILE_STEM] [--html HTML]
                       [-w] [-p] [-b] [-s SETLIST] [--title TITLE]
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
  --html HTML           Output HTML book, defaults to screen-formatting use
                        --a4 option for printing
  -w, --word            Output word
  -p, --pdf             Output pdf
  -b, --book-file       First file contains a list of files, each line
                        optionally followed by a transposition (+|-)\d\d? eg
                        to transpose up one tone: song-file.cho +2
  -s SETLIST, --setlist SETLIST
                        Use a setlist file to filter the book, one song per
                        line and keep facing pages together. Setlist lines can
                        be one or more words from the song title
  --title TITLE         Title to use for the book

```


