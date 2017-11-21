from distutils.core import setup
setup(
    packages=['chordprobook', 'chordprobook.books', 'chordprobook.instruments', 'chordprobook.chords'],
    #py_modules =[ 'chordprobook', 'chordprobook.books', 'chordprobook.instruments', 'chordprobook.chords'],
    package_data={   
    'chordprobook.instruments': ['instruments.yaml'],
    'chordprobook.chords' : ['chord_data/*.cho']
     },
    data_files = [ ('data', ['data/reference.odt']),
                   ('data', ['data/reference.docx'])],
    version = "0.1",
    description = "Chordpro songsheet and book generator",
    author = "Peter Sefton",
    author_email = "pt@ptsefton.com",
    url = "https://github.com/ptsefton/chordprobook",
    download_url = "https://github.com/ptsefton/chordprobook",
    keywords = ["chordpro", "pdf", "song"],
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 1 - Alpha",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GPL",
        "Operating System :: OS Independent",
    
        ],
        install_requires = ['pypandoc', 'pillow', 'pyaml'],
        scripts=['mksong'],
    long_description = """\
This is a Python 3 script to convert collections of chordpro formatted song charts to 
PDF, HTML, epub, and word processing doc formats including chord diagrams.

Can convert a directory full of files to a single book, or a set of song-sheets, also handles setlists. 

Uses Pandoc and wkhtmltopdf to do all the hard work.
"""
)
