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


### Word output (.docx / .odt)

* Gives you a start on creating a Word or OpenOffice document (via pandoc) from a set of chordpro files. Each song begins with a Heading 1 on a new page.
* You can change the styles in the included ```reference.docx``` to your taste. At the moment it does not auto-scale the text to fit the page

### HTML output

The HTML output is currently set up to create an A4 page per song (with optional multi-page songs using {new_page}). This HTML is used to generate a PDF, but it may be useful on its own.


### Probably won't do
* Make a GUI, but see the comment below about auto-creating PDF

* Display chord names above text.

## Audience

This is for people running a unix-like operating system who know how
to install packaged software scripts and python modules.
 
Status: Alpha / mostly works for me  on OS X 10.10.5.


## Installation on OS X 

Requires pandoc 1.15.0.6 or later  and wkhtmltopdf installed on on
your path.

NOTE: It is recommended that you use a Python 3 virtual
environment.

*  To create one, first get the brew version of Python 3

   ```brew install python3```

* Create a virtual environment

	```mkdir ~/virtualenvs```
	```pyvenv ~/virtualenvs/chorprobook```

* Activate the virtual env

    ```. ~/virtualenvs/chordprobook/bin/activate```

* Install Pandoc HEAD using [brew](http://brew.sh/):

    ```brew install pandoc --HEAD```

* Download and install [wkhtmltopdf](http://wkhtmltopdf.org/downloads.html)

* Download from Github:

    ```git clone https://github.com/ptsefton/chordprobook.git```

* Activate your virutal environment:

    ```.  ~/virtualenvs/chordprobook/bin/activate```

* Install

    ```cd chordprobook```
    ```pip3 install .```

* To check that you have a commandline client now, type ```mksong --help```


## Installation on other *nix platforms

Some installation notes courtesy of [lpinner](https://github.com/lpinner):
>Just sharing some installation instructions that worked for me on Linux (and would possibly work on Win/MacOS as well)
>
> *  Install conda (miniconda will do).
> *  Create a conda environment, activate it and pip install chordprobook from github:
>
>```conda create -c conda-forge -n chordprobook python=3 pypandoc wkhtmltopdf pillow pyaml```
> ```source activate chordprobook```
> ```pip install git+https://github.com/ptsefton/chordprobook.git```
>
> Note: conda-forge channel is needed for wkhtmltopdf


## The local dialect of Chordpro format

The Chordpro format is defined on https://www.chordpro.org/chordpro/ChordPro-Directives.html.
This implementation is designed to be relaxed and pragmatic about what it accepts.

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
{transpose: +1 +2 -2} | A space seperated list of semitone deltas.  | In a song file, when called in single-song mode the software will automatically produce extra versions transposed as per the directive. In this case if the song is in C it would be transposed to C#, D and Bb. Can be used in a book file or a setlist file at the end of a line after a file-path or the title of the song, respectively.
{transpose: 0} | In a book file, don't transpose the songs at all | no change
{transpose: 1} | In a book file, for each song use the first transposition specified using {transpose: } | Song is transposed
{transpose: all} | In a book file, add a song for the original key, and for each transposition specified using {transpose: } in the song| Multiple songs in the book, in different keys, where they are specified
{C: Some comment} {Comment: Some comment} | Notes on the song  | A third level heading
{instrument: } | Name of an instrument you'd like to display chord grids for. Can occur multiple times in song or book files (not yet in setlists) | A set of chord grids across the top of the song's first page, if the instrument is know to the software. chordpro.py --instruments will list the instruments known 
{define: } | In the context of an {instrument: } directove above will define fingering for a chord for that instrument. Uses the same conventions as over at [uke-geeks](http://blog.ukegeeks.com/users-guide/how-do-i-define-my-own-chords/) except that here chords have to start with [A-G] | Causes a chord grid (if chords are being rendered) to appear at the top of the song 
{new+page}<br>{np} | New page | A page break. When generating HTML and PDF the software will attempt to fill each page to the screen or paper size respectively as best it can.
{start_of_chorus} {soc} | Start of chorus. Could be followed by some variant of {c: Chorus} | Chorus is rendendered as an indendented block. TODO: make this configurable via stylesheets. In .docx format the chorus is rendered using ```Block Text``` style.
{start_of_bridge} {sob} | Start of bridge. Usually followed by some variant of {c: Bridge} | Same behaviour as chorus
{eoc} {end_of_chorus} | End of chorus | Everything between the {soc} and {eoc} is in an indented block 
{eob} {end_of_bridge} | End of bridge | Same behviour as chorus
{sot} {start_of_tab} | Start of tab (tablature) | Rendered in a fixed width (monospace) font, as per the HTML \<pre> element. NOTE: Tabs that are acutal text-formatted representations of the fingerboard will not be transposed, although chords in square brackets will, so you can use tab-blocks to format intros or breaks where chords line up under each other 
{eot} {end_of_tab} | End of tab | Finishes the fixed-width formatting
{book: path_to_book} | For use in setlist files, a path to a book file relative to the setlist file or an absolute path | 
{files: } & {dirs: }| A file-glob pattern to match, eg {files: *.cho} in a space separated list of directories| For use in book files only, does a recursive search in the directories for files matching the pattern. If the song has a {transpose: } directive it will generate multiple pages, one for each transposition.
{version: } | In book files. Put a version such as {version: v2.1}, and it will add v2.1 to the title and output filename. Or use {version: auto} for a time-stamped (to the millisecond!) version | A suffix in the title and output file name |


### Implementation

This implementation will:

* Look for one directive per line (Except in setlists, where you can add {transpose: } to the end of a line)
* Accept leading and trailing space before and after directives.

I am still undecided about:
* How to handle extra text before or after a declaration
* How to handle two directives on one line

### Book files
A book file is a text file with a list of paths with and optional title (see [samples/sample.book.txt](samples/sample.book.txt)).

To transpose the song, add a positive or negative integer at after the (partial) song name, separated by a space. eg:
```./songs/my-song.cho {transpose: +2}```

A book file may also have 'lazy' loading via directives on how to find song files.

*  To specifiy one or more directories in which to look use one or more dir directives ```{dir: ./some-path}``

*  To speficy a set of files use a file-glob expression, eg this matches all files that end in .cho ```{files: *.cho}``

### Setlist files

The setlist consists of an optional {title: } directive, and optional {book: <path>} directive followed by a list of songs, one per line.   (see [samples/sample.setlist.md](samples/sample.setlist.md)).

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
mksong --help
```
And you'll see this:

```


```



## Examples

* To make a PDF book (defaults to songbook.pdf) from a set of chordpro
  files:

   ```mksong samples/*.cho.txt```

    Which is equivalent to:

    ```mksong --pdf  samples/*.cho.txt```

*  To add a file name and a title to the book.
 
    ```mksong --file-stem=my_book --title="My book"  samples/*.cho.txt```

*  If you'd like it sorted alphabetically by title:

    ```mksong -a --file-stem=my_book --title="My book"  samples/*.cho.txt```

* To add chord grids for soprano ukulele:
	```mksong -a --file-stem=my_book --title="My book"	--instrument Uke samples/*.cho.txt```
  
* To add chord grids for left-handed soprano ukulele:
	```mksong -a -l --file-stem=my_book --title="My book" --instrument Uke samples/*.cho.txt```

* To find out what instruments are supported:
	```mksong.py --instruments```

* To use an instrument name with space, quote it:
	```mksong -a --file-stem=my_book --title="My book"	--instrument "5 String Banjo" samples/*.cho.txt```

* To build a book from a list of files use a book file, containing a
   list of files, one per line and the -b
   flag. This will preserve the order you entered the songs except
   that it will make sure that two-page songs appear on facing pages.
  
    ```mksong -b samples/sample.book.txt```

* To build a book in a lazier way, use a directive such as ```{files:
  *.cho.txt}``` and specify a space separated directory of file names, like ```{dirs:
  *./covers .originals}```
  
  ```mksong -b samples/sample-book-lazy.txt ```

* To automatically include chord grids, add {instrument: } directives to a bookfile, eg:

  ```mksong -b samples/sample-lazy.txt ```

* To make sure the order of songs is preserved exactly, for example to
  use as a setlist, use -k or --keep-order. This will insert blank
  pages if necessary.

    ```mksong -k -b samples/sample.book.txt```

*  To sort songs alphabetically add the -a or --alphabetical flag:

    ```mksong -a -b samples/sample.book.txt```
    
* To choose a subset of the songs in a book in a particular order use
  a setlist file. 

   Use this to filter all the songs in a directory using a setlist:

    ```mksong -s samples/sample.setlist.md samples/*.cho.txt```
    
*  Or use a book file and filter that:

    ```mksong -s samples/sample.setlist.md -b samples/sample.book.txt```

* To version control a book, use the {version: } directive. Either
  with a version number like {version: 12.1beta} or to get a
  timestamp, use {version: auto}. See these samples:

    ```mksong -b samples/sample_versioned. book.txt ```
	```mksong -b samples/sample_auto_versioned. book.txt ```
