# chordprobook

## What does this do? Formats song charts


This is a Python 3 script to convert collections of
[chordpro](http://blossomassociates.net/Music/chopro.html) formatted
song charts to PDF, HTML, epub, and word processing doc formats. You can
convert a directory full of files to a single book, or a set of
song-sheets. Uses Pandoc and wkhtmltopdf to do all the hard work.

NOTE: Unlike most chordpro software this does not display chords above
the text (not yet anyway). Displaying chords inline is more compact. If it's good enough for Rob Weule and his
[Ukulele Club Songbook](http://katoombamusic.com.au/product/ukulele-club-songbook/)
and for [Richard G](http://www.scorpexuke.com/ukulele-songs.html) it's
good enough for me.

## Status

This is alpha code, until there are other people using it will
continue to develop without branches and may make breaking
changes. Let me know if you want a more stable release.

There are some (patchy) unit tests, I have been improving this with most of the changes I make.

## Features

* Generate books from files passed on the command line

* Generate books from a book file, which is a list of files, or a pattern to match (eg *.cho)

* Reorder songs using a setlist file using either of the above ways of
selecting files, for using in performance

* Show chord grids at the top of the page for a range of instruments
  (I could use some help getting better chord definition

*  Transpose songs

If you play with a group you can maintain a songbook for the
group to play from, then create setlists which are ordered subsets of that book by typing abbreviated titles
into a text file in markdown format, and generating a book from that. The setlists are added as pages you can 
put on the floor, like a real rock n roll band.

### PDF

* **Formats songs to fit the page** as best it can making the text as big as possible (good for ageing eyes
   and working in the dark). This feat is accompished by creating an HTML document, via Pandoc, with CSS to render the pages at A4 size then using wkhtmltopdf to create a PDF.

* **Generates individual song-sheets in multiple keys and for multiple instruments** transposed from the original.

* **Produces a PDF table of contents** which works well on tablets for navigation.


### Word output (.docx)

* Gives you a start on creating a word document (via pandoc) from a set of chordpro files. Each song begins on a new page.
* You can change the styles in the included ```reference.docx``` to your taste. At the moment it does not auto-scale the text to fit the page

### HTML output

This is still experimental, but the idea is to produce HTML that fills the screen for use on tablets, phones, etc with swipe navigation.



### Probably won't do
* Make a GUI, but see the comment below about auto-creating PDF

* Display chord names above text.

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

## The local dialect of Chordpro format

Chordpro format has no formal definition, and many different
implementations. This implementation is designed to be relaxed and
pragmatic about what it accepts.

Chordpro files are plain-text files with chords
inline in square brackets, eg [C]. It uses formatting 'directives'.

### Chords
Chords are anything in square brackets that starts with a capital
C..G, followed by any mixture of lower case, slashes, and numbers. Eg:

```[C] [Csus4] [C/B] [Cmaj7]```

Note that when transposing, any capital A...G inside a chord will get transposed so
don't write [CAug] use [Caug].

Some charts use ! and / inside chords to indicate a staccato chord or
rhythm respectively. This works, and will be recognised for the
purposes of transposing the song:

``` [C / / / ] [F / /] [C!]```


### Other formatting

Directives are lines beginning and ending with { and }, whitespae before and after the braces is ignored, but if there is text outside of them then the line is not treated as a directive.

None of the directives are case sensitive and they are all optional. Title, subtitle, key and transpose can be placed anywhere, but by convention are put at the top of the file.

Formatting / Directive         |      Description  | Rendered as
------------------------------ | ----------------- | -----------
{Title: \<Song title>} {t: \<Song title>}  | Song title | A top-level heading
{Subtitle: \<Artist / songwriter name>} | Subtitle, by convention this is the composer or artist | An second-level heading
{key: \<A...G>} | The key of the song     | Will be added to the title in brackets like ```(Key of G)``` if present.
{transpose: +1 +2 -2} | A space separted list of semitone deltas.  | In a song file, when called in single-song mode the software will automatically produce extra versions transposed as per the directive. In this case if the song is in C it would be transposed to C#, D and Bb. Can be used in a book file or a setlist file at the end of a line after a file-path or the title of the song, respectively.
{C: Some comment} {Comment: Some comment} | Notes on the song  | A third level heading
{instrument: } | Name of an instrument you'd like to display chord grids for. Can occur multiple times in song or book files (not yet in setlists) | A set of chord grids across the top of the song's first page, if the instrument is know to the software. chordpro.py --instruments will list the instruments known 
{define: } | In the context of an {instrument: } directove above will define fingering for a chord for that instrument. Uses the same conventions as over at [uke-geeks](http://blog.ukegeeks.com/users-guide/how-do-i-define-my-own-chords/) except that here chords have to start with [A-G] | Causes a chord grid (if chords are being rendered) to appear at the top of the song 
{new+page} {np} | New page | A page break. When generating HTML and PDF the software will attempt to fill each page to the screen or paper size respectively as best it can.
{start_of_chorus} {soc} | Start of chorus. Usually followed by some variant of {c: Chorus} | Chorus is rendendered as an indendented block. TODO: make this configurable via stylesheets. In .docx format the chorus is rendered using ```Block Text``` style.
{start_of_bridge} {sob} | Start of bridge. Usually followed by some variant of {c: Bridge} | Same behaviour as chorus
{eoc} {end_of_chorus} | End of chorus | Everything between the {soc} and {eoc} is in an indented block 
{eob} {end_of_bridge} | End of bridge | Same behviour as chorus
{sot} {start_of_tab} | Start of tab (tablature) | Rendered in a fixed width (monospace) font, as per the HTML \<pre> element. NOTE: Tabs that are acutal text-formatted representations of the fingerboard will not be transposed, although chords in square brackets will, so you can use tab-blocks to format intros or breaks where chords line up under each other 
{eot} {end_of_tab} | End of tab | Finishes the fixed-width formatting
{book: path_to_book} | For use in setlist files, a path to a book file relative to the setlist file or an absolute path | 
{files: } & {dirs: }| A file-glob pattern to match, eg {files: *.cho} in a space separated list of directories| For use in book files only, does a recursive search in the directories for files matching the pattern. If the song has a {transpose: } directive it will generate multiple pages, one for each transposition.

### Implementation

This implementation will:

* Look for one-directive per line.
* Accept leading and trailing space before and after directives.

I am still undecided about:
* How to handle extra text before or after a declaration
* How to handle two directives on one line

### Book files
A book file is a text file with a list of paths with and optional title (see [samples/sample-book.txt](samples/sample-book.txt)).

To transpose the song, add a positive or negative integer at after the (partial) song name, separated by a space. eg:
```./songs/my-song.cho {transpose: +2}```

A book file may also have 'lazy' loading via directives on how to find song files.

*  To specifiy one or more directories in which to look use one or more dir directives ```{dir: ./some-path}``

*  To speficy a set of files use a file-glob expression, eg this matches all files that end in .cho ```{files: *.cho}``

### Setlist files

The setlist consists of an optional {title: } directive, and optional {book: <path>} directive followed by a list of songs, one per line.   (see [samples/sample-book.txt](samples/setlist.txt)).

If there is no {book: } directive then the setlist will be selected
from the song files passed in as arguments:  see the examples below.

Unlike book and song files, the setlist uses markdown format. Songs
are second level headings starting with "##" and sets are first level
headings. You can include any other (Pandoc) markdown markup you like.
Identify songs by entering one or more words from the title, in
order. So "## Amazing" will match "Amazing Grace" and "## Slot Baby"
would match "Slot Machine Baby".

To transpose the song, add a positive or negative integer at after the path, separated by a space. eg:
```#My Song  {transpose: +2}```

## usage

To see  usage info, type:
```
chordprobook.py --help

usage: chordprobook.py [-h] [-a] [-i INSTRUMENT] [--instruments] [-k] [--a4]
                       [-e] [-f FILE_STEM] [--html] [-w] [-p]
                       [-r REFERENCE_DOCX] [-o] [-b] [-s SETLIST]
                       [--title TITLE]
                       [files [files ...]]

positional arguments:
  files                 List of files

optional arguments:
  -h, --help            show this help message and exit
  -a, --alphabetically  Sort songs alphabetically
  -i INSTRUMENT, --instrument INSTRUMENT
                        Show chord grids for the given instrument. Eg
                        --instrument "Soprano Ukulele"
  --instruments         chord grids for the given instrument, then quit use
                        any of the names or aliases listed under AKA
  -k, --keep-order      Preserve song order for playing as a setlist (inserts
                        blank pages to keep multi page songs on facing pages
  --a4                  Format for printing (web page output)
  -e, --epub            Output epub book
  -f FILE_STEM, --file-stem FILE_STEM
                        Base file name, without extension, for output files
  --html                Output HTML book, defaults to screen-formatting use
                        --a4 option for printing 
  -w, --word            Output .docx format
  -p, --pdf             Output pdf
  -r REFERENCE_DOCX, --reference-docx REFERENCE_DOCX
                        Reference docx file to use (eg with Heading 1 having a
                        page-break before)
  -o, --one-doc         Output a single document per song: assumes you want A4
                        PDF
  -b, --book-file       First file contains a list of files, each line
                        optionally followed by a transposition (+|-)\d\d? eg
                        to transpose up one tone: song-file.cho +2, you can
                        also add a title line: {title: Title of book}
  -s SETLIST, --setlist SETLIST
                        Use a setlist file in markdown format to filter the
                        book, one song per line, and keep facing pages
                        together. Setlist lines can be one or more words from
                        the song title starting with '## ', with '# ' for the
                        names of sets and other markdown as you require in
                        between you can also add a setlist line: {title: Title
                        of setlist}
  --title TITLE         Title to use for the book, if there is no title in a
                        book file or setlist file

```



## Examples

* To make a PDF book (defaults to songbook.pdf) from a set of chordpro
  files:

   ```./chordprobook samples/*.cho```

    Which is equivalent to:

    ```./chordprobook --pdf --a4  samples/*.cho```

*  To add a file name and a title to the book.
 
    ```./chordprobook --file-stem=my_book --title="My book"  samples/*.cho```

*  If you'd like it sorted alphabetically by title:

    ```./chordprobook -a --file-stem=my_book --title="My book"  samples/*.cho```

* To add chord grids for soprano ukulele:
	```./chordprobook -a --file-stem=my_book --title="My book"	--instrument Uke samples/*.cho```

* To find out what instruments are supported:
	```./chordprobook.py --instruments```

* To use an instrument name with space, quote it:
	```./chordprobook -a --file-stem=my_book --title="My book"	--instrument "5 String Banjo" samples/*.cho```

* To build a book from a list of files use a book file, containing a
   list of files, one per line and the -b
   flag. This will preserve the order you entered the songs except
   that it will make sure that two-page songs appear on facing pages.
  
    ```./chordprobook.py -b samples/sample-book.txt```

* To build a book in a lazier way, use a directive such as ``{files:
  *.cho}`` and specify a space separated directory of file names, like ``{dirs:
  *./covers .originals}```
  
  ```./chordprobook.py -b samples/sample-book-lazy.txt ```

* To automatically include chord grids, add {instrument: } directives to a bookfile, eg:

  ```./chordprobook.py -b samples/sample-book-lazy.txt ```

* To make sure the order of songs is preserved exactly, for example to
  use as a setlist, use -k or --keep-order. This will insert blank
  pages if necessary.

    ```./chordprobook.py -k -b samples/sample-book.txt```

*  To sort songs alphabetically add the -a or --alphabetical flag:

    ```./chordprobook.py -a -b samples/sample-book.txt```
    
* To choose a subset of the songs in a book in a particular order use
  a setlist file. 

   Use this to filter all the songs in a directory using a setlist:

    ```./chordprobook.py -s samples/setlist.txt samples/*.cho```
    
*  Or use a book file and filter that:

    ```./chordprobook.py -s samples/setlist.txt -b samples/sample-book.txt```


