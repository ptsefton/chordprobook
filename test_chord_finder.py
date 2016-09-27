#!usr/bin/env python3
import unittest
import copy
import chordprobook.chords
import chordprobook.chords as chords
import chordprobook.instruments

class TestChorddiagram(unittest.TestCase):
        
  def test_notes(self):
      N = chordprobook.chords.Note
      self.assertEqual(N("C#").num, N("Db").num)
      self.assertEqual(N(0).name, "C")
      self.assertEqual(N(0).num, 0)
      self.assertEqual(N('C').name, 'C')
      D = N('C')
      D.transpose(2)
      self.assertEqual(D.num, 2)
      

  def test_chord(self):
       N = chordprobook.chords.Note
       c_chord = chordprobook.chords.Chord('C')
       self.assertEqual(c_chord.flavour, "")
       self.assertEqual(c_chord.root.num, N("C").num)
       #self.assertEqual(c_chord.spell(), [note('C'),'E','G'])
       
       c_chord = chordprobook.chords.Chord('Cm')
       self.assertEqual(c_chord.flavour, "m")
       self.assertEqual(c_chord.root.num, N("C").num)
       print(str(c_chord.spell()))
       self.assertEqual(c_chord.spell(), [N('C').num, N('Eb').num, N('G').num])

  def test_chord_finder(self):
     C = chordprobook.chords.Chord('C')
     instruments = chordprobook.instruments.Instruments()
     plucky = instruments.get_instrument_by_name("Plucky")
         
     C.find_fingerings(plucky)
     self.assertTrue([0,0,0,0] in C._fingering_array)


     C_sharp = chordprobook.chords.Chord('C#')
     C_sharp.find_fingerings(plucky)
     self.assertTrue([1, 1, 1, 1] in C_sharp._fingering_array)

     
     c7 = chordprobook.chords.Chord('C7')
     c7.find_fingerings(plucky)
     self.assertTrue([0,0,0,3] in c7._fingering_array)
     self.assertTrue([3,0,0,0] in c7._fingering_array)


     F = chordprobook.chords.Chord('F')
     F.find_fingerings(plucky)
     d = chords.ChordDiagram(offsets = F._fingering_array[0])
     #d.draw()
     #d.show()


     
     D = chordprobook.chords.Chord('D')
     D.find_fingerings(plucky)
     print("D", D._fingering_array)

     D = chordprobook.chords.Chord('D6')
     D.find_fingerings(plucky)
     print("D6", D._fingering_array)

     #Try to find chords in impossible situations
     #These should all NOT work
     c_instrument = chordprobook.instruments.Instrument(data = {"name": "c", "tuning" : "CCCCCCC"})
     D.find_fingerings(c_instrument)
     self.assertEqual(D._fingering_array, [])

     print(c7.to_chordpro())

     

if __name__ == '__main__':
    unittest.main()
