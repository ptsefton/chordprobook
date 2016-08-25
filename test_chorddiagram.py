#!usr/bin/env python3
import unittest
import chords
import instruments as inst

class TestChorddiagram(unittest.TestCase):

  
  def test_init(self):
    """
    Struggling to write good tests here 

    """
    d = chords.ChordDiagram( name="D", strings=[chords.String([chords.Dot(2,1)]),chords.String([chords.Dot(2,1)]),chords.String([chords.Dot(2,1)]),chords.String([chords.Dot(5, 3),chords.Dot(2,1)])])
    #d.show()


    d.draw()
    self.assertTrue(d.string_top < d.string_bottom)

    #Check frets are not on top of each other
    fret_y = 0
    for f in d.frets:
      self.assertTrue(f.y > fret_y)
      fret_y = f.y
      
    #'Normal' chord, diagram should have 5 frets
    self.assertEqual(d.num_frets, 5)

   
      
   
    #d.show()

    
    d= chords.ChordDiagram( name="G", strings=[chords.String([chords.Dot(0)]),chords.String([chords.Dot(2,1)]),chords.String([chords.Dot(3,3)]),chords.String([chords.Dot(2, 2)])])
    d.draw()

    #Guitar G chord
    d= chords.ChordDiagram( name="G", strings=[chords.String([chords.Dot(3,2)]),chords.String([chords.Dot(2,1)]),chords.String([chords.Dot(0)]),chords.String([chords.Dot(0)]),chords.String([chords.Dot(0)]), chords.String([chords.Dot(3,3)])])
    #Check strings are not on top of each other
    d.draw()
    self.assertEqual(d.num_strings, 6)
    string_x = 0
    for s in d.strings:
      self.assertTrue(s.string_x > string_x)
      string_x = s.string_x
      self.assertTrue(string_x < d.box_width)

  def test_parse(self):
        #Simple chord
        achord = "{define: A frets 2 1 0 0}"
        d = chords.ChordDiagram()
        d.parse_definition(achord)
        d.draw()
        self.assertEqual(d.num_strings, 4)
        self.assertEqual(d.strings[0].dots[0].fret, 2)
        self.assertEqual(d.strings[0].dots[0].finger, None)
        self.assertEqual(d.strings[1].dots[0].fret, 1)
        self.assertEqual(d.strings[1].dots[0].finger, None)
        self.assertEqual(d.strings[2].dots[0].fret, 0)
        self.assertEqual(d.strings[2].dots[0].finger, None)
        self.assertEqual(d.strings[3].dots[0].fret, 0)
        self.assertEqual(d.strings[3].dots[0].finger, None)
        
        # Simple chord without "frets"
        achord = "{define: A 2 1 0 0}"
        d = chords.ChordDiagram()
        d.parse_definition(achord)
        d.draw()
        self.assertEqual(d.num_strings, 4)
        self.assertEqual(d.strings[0].dots[0].fret, 2)
        self.assertEqual(d.strings[0].dots[0].finger, None)
        self.assertEqual(d.strings[1].dots[0].fret, 1)
        self.assertEqual(d.strings[1].dots[0].finger, None)
        self.assertEqual(d.strings[2].dots[0].fret, 0)
        self.assertEqual(d.strings[2].dots[0].finger, None)
        self.assertEqual(d.strings[3].dots[0].fret, 0)
        self.assertEqual(d.strings[3].dots[0].finger, None)
        
        # Chord with fingering
        achord = "{define: A frets 2 1 0 0 fingers 2 1 0 0}"
        d = chords.ChordDiagram()
        d.parse_definition(achord)
        d.draw()
        self.assertEqual(d.num_strings, 4)
        self.assertEqual(d.strings[0].dots[0].fret, 2)
        self.assertEqual(d.strings[1].dots[0].fret, 1)
        self.assertEqual(d.strings[2].dots[0].fret, 0)
        self.assertEqual(d.strings[3].dots[0].fret, 0)

        
        # Chord with added fingering
        aaugchord = "{define: Aaug frets 2 1 1 4 fingers 2 1 1 4 add: string 1 fret 1 finger 1 add: string 4 fret 1 finger 1}"
        d = chords.ChordDiagram()
        d.parse_definition(aaugchord)
        d.draw()
        self.assertEqual(d.num_strings, 4)
        # TODO - check serialisation of this chord with fingers and all
        
        # Chord with non-played strings
        dchord = "{define: D x 0 0 2 3 2}"
        d = chords.ChordDiagram()
        d.parse_definition(dchord)
        d.draw()
        self.assertEqual(d.num_strings, 6)
        self.assertEqual(d.strings[0].dots[0].fret, None)
        self.assertEqual(d.strings[1].dots[0].fret, 0)
        self.assertEqual(d.strings[2].dots[0].fret, 0)
        self.assertEqual(d.strings[3].dots[0].fret, 2)
        self.assertEqual(d.strings[4].dots[0].fret, 3)
        self.assertEqual(d.strings[5].dots[0].fret, 2)
      
        # Chord starting on a higher fret
        e5chord = "{define: E5 base-fret 7 frets 0 1 3 3 x x}"
        d = chords.ChordDiagram()
        d.parse_definition(e5chord)
        d.draw()
        self.assertEqual(d.num_strings, 6)
        self.assertEqual(d.strings[0].dots[0].fret, 0)
        self.assertEqual(d.strings[1].dots[0].fret, 1)
        self.assertEqual(d.strings[2].dots[0].fret, 3)
        self.assertEqual(d.strings[3].dots[0].fret, 3)
        self.assertEqual(d.strings[4].dots[0].fret, None)
        self.assertEqual(d.strings[5].dots[0].fret, None)
       

        # Same E5 chord starting on a higher fret
        e5chord = "{define: E5 frets 0 8 10 10 x x}"
        d = chords.ChordDiagram()
        d.parse_definition(e5chord)
        d.draw()
        self.assertEqual(d.num_strings, 6)
        self.assertEqual(d.strings[0].dots[0].fret, 0)
        self.assertEqual(d.strings[1].dots[0].fret, 1)
        self.assertEqual(d.strings[2].dots[0].fret, 3)
        self.assertEqual(d.strings[3].dots[0].fret, 3)
        self.assertEqual(d.strings[4].dots[0].fret, None)
        self.assertEqual(d.strings[5].dots[0].fret, None)
        self.assertEqual(d.open_strings, 1)
        self.assertEqual(d.non_played_strings, 2)
        self.assertEqual(d.to_chordpro(), "{define: E5 base-fret 7 frets 0 1 3 3 x x}")
        

        
        dchord = "{define: D base-fret 1 frets  1 1 1 4}"
        d = chords.ChordDiagram()
        d.parse_definition(dchord)
        d.draw()
        self.assertEqual(d.num_strings, 4)
        self.assertEqual(d.strings[0].dots[0].fret, 2)
        self.assertEqual(d.strings[1].dots[0].fret, 2)
        self.assertEqual(d.strings[2].dots[0].fret, 2)
        self.assertEqual(d.strings[3].dots[0].fret, 5)
       

        # Stupid chord requiring 7 fingers and 8 strings
        stupid = "{define: F#stupid base-fret 22 frets 1 2 3 x 4 5 6 7 8 9 10 11 fingers 11 10 9 8 0 7 6 5 4 3 2 1}"
        d = chords.ChordDiagram()
        d.parse_definition(stupid)        
        d.draw()
        self.assertEqual(d.non_played_strings, 1)
        
    
       
        
        

  def test_grid(self):
        chart = chords.ChordChart()
        chart.load_tuning_by_name("Soprano Uke")
        self.assertEqual(chart.grid_as_md("F#7"), chart.grid_as_md("F#7!"))
        #chart.get_default("F#7").show()

        #Check that normalisation code
        self.assertEqual(chart.grid_as_md("F#7///"), chart.grid_as_md("F#7"))
        self.assertEqual(chart.normalise_chord_name("Fadd9"), "F9")
        self.assertEqual(chart.normalise_chord_name("Am7-5"), "Am7-5")
        self.assertEqual(chart.normalise_chord_name("Cmaj"), "C")
        self.assertEqual(chart.normalise_chord_name("Cmaj7"), "Cmaj7")
        self.assertEqual(chart.normalise_chord_name("C+"), "Caug")

        self.assertEqual(chart.get_default("Gbm7").to_chordpro(), chart.get_default("F#m7").to_chordpro())

        F_sharp_chord_def = "{define: F#m7 base-fret 7 frets 2 1 2 0}"
        Gb_chord_def = "{define: Gbm7 base-fret 7 frets 2 1 2 0}"
        c = chords.ChordChart()
        c.add_grid(Gb_chord_def)
        self.assertEqual(c.get_default("Gbm7").to_chordpro(), F_sharp_chord_def)


        c = chords.ChordChart()
        c.add_grid(Gb_chord_def)
        self.assertEqual(c.get_default("F#m7").to_chordpro(), F_sharp_chord_def)
        self.assertEqual(c.get_default("F#m7//").to_chordpro(), F_sharp_chord_def)
        self.assertEqual(c.get_default("F#m7!").to_chordpro(), F_sharp_chord_def)
        
if __name__ == '__main__':
    unittest.main()
