#! /usr/bin/env python3

"""
Quick and dirty script to generate a set of chordpro definitions for a given instrument tuning
Attempts to sort by playability, but the idea is to create a set of shapes that can then be tweaked by hand.

Calls a hacked version of "Simple minded guitar chords" by Erich Rickheit

usage:

generate_chord_defs <tuning>

where tuning is a space list of strings (in quotes) eg

"GCEA"

"""

import argparse
import re
import subprocess
from chordprobook  import chords
    
def generate_grids(chord, tuning):
    command = ["./chord/ch", "-f", "4", "-p", "4",  "-r", "3", "-i", "0",  "-t"]
    for string in tuning:
        command.append(string)
    command += [".", chord]
    print(" ".join(command))
    out = subprocess.check_output(command)
    print(out)
    return str(out.decode())

def generate_defs():
    transposer = chords.transposer()
    parser = argparse.ArgumentParser()
    parser.add_argument('tuning',  default=None, help='tuning')
    args = vars(parser.parse_args())
    tuning = args["tuning"]
    chordpro_definitions = "";
    for note_index  in range(0,12):
        for variant in ["", "7","6","sus4","m" ,"maj7" ,"m7","Add9","dim"]:
            chord_name = transposer.get_note(note_index) + variant
            defs = generate_grids(chord_name, tuning)
            grids = chords.ChordChart()
            grids.load(defs)
            norm_chord_name = grids.normalise_chord_name(chord_name)
            grids.sort_by_playability(norm_chord_name)
            chordpro_definitions += "{c: %s}\n%s\n" % (norm_chord_name,  str(grids.to_chordpro(norm_chord_name)))
            
    open("%s_chords.cho" % tuning.replace(" ",""), 'w').write(chordpro_definitions)  
    

if __name__ == "__main__":
    generate_defs()
