#!usr/bin/env python3
import unittest
import chorddiagram as cd
from chorddiagram import String, Dot


class TestChorddiagram(unittest.TestCase):

  def test_init(self):
    """
    Struggling to write good tests here 

    """
    d = cd.ChordDiagram()
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

   
      
    d= cd.ChordDiagram( name="D", strings=[String([Dot(2,1)]),String([Dot(2,1)]),String([Dot(2,1)]),String([Dot(5, 3),Dot(2,1)])])
    #d.show()

    
    d= cd.ChordDiagram( name="G", strings=[String([Dot(0)]),String([Dot(2,1)]),String([Dot(3,3)]),String([Dot(2, 2)])])
    #d.show()

    #Guitar G chord
    d= cd.ChordDiagram( name="G", strings=[String([Dot(3,2)]),String([Dot(2,1)]),String([Dot(0)]),String([Dot(0)]),String([Dot(0)]), String([Dot(3,3)])])
    #Check strings are not on top of each other
   
    
    d.show()
    self.assertEqual(d.num_strings, 6)
    string_x = 0
    for s in d.strings:
      self.assertTrue(s.string_x > string_x)
      string_x = s.string_x
      self.assertTrue(string_x < cd.ChordDiagram.box_width)

if __name__ == '__main__':
    unittest.main()
