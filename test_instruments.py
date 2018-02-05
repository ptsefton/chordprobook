import unittest
import chordprobook
import chordprobook.instruments as inst

class TestIntruments(unittest.TestCase):
  """
  Check that we can recognize tunings from instrument names
  """
  def test_instruments(self):
    instruments = inst.Instruments()
    ukes = instruments.get_instruments_by_tuning("GCEA")
    self.assertEqual(len(ukes), 2)
    instruments.describe()
    self.assertEqual(instruments.get_tuning_by_name("Uke"), "GCEA")
    self.assertEqual(instruments.get_instrument_by_name("0 String Banjo"), None)
    uke = instruments.get_instrument_by_name("Uke")
    uke.load_chord_chart()
    chord = uke.chart.get_default("C7")
    self.assertEqual(chord.to_chordpro(),"{define: C7 frets 0 0 0 1}") #TODO FIX THIS TO INCLUDE FINGERINGS ETC

    p = instruments.get_instrument_by_name("Plucky")
    p.load_chord_chart()
    chord = p.chart.get_default("C7")
    self.assertEqual(chord.to_chordpro(),"{define: C7 frets 3 0 0 0}")

  def test_lefty(self):
    instruments = inst.Instruments()
    uke = instruments.get_instrument_by_name("Uke")
    uke.load_chord_chart(lefty=True)
    chord = uke.chart.get_default("C7")
    self.assertEqual(chord.to_chordpro(),"{define: C7 frets 1 0 0 0}") 

      
if __name__ == '__main__':
    print (dir(inst))
    unittest.main()
