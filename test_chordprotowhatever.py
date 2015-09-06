import unittest
import chordprotowhatever as cm


class TestStringMethods(unittest.TestCase):

  def test_reorder(self):
    one1 = cm.cp_song("{title: 1 page}")
    one2 = cm.cp_song("{title: 1 page}")
    two1 = cm.cp_song("{title: 2 page}")
    two1.pages = 2
    two2 = cm.cp_song("{title: 2 page}")
    two2.pages = 2
    book = cm.cp_song_book([one1,two1, one2, two2])
    page = 3
    print(book.songs)
    book.reorder(page)
    print(book.songs)
    for song in book.songs:
      #Check that two or four page spreads start on an even page
      print(page, song.pages)
      if song.pages % 2 == 0:
        self.assertEqual(page % 2, 0)
      page += song.pages
    
  def test_parse(self):
    song = cm.cp_song("{title: A Song!}\nSome stuff\n{key: C#}\n")
    self.assertEqual(song.key, "C#")
    self.assertEqual(song.title, "A Song!")
    song = cm.cp_song("{title: A Song!}\nSome stuff\n{key: C#}\n#A comment\n#or two", transpose=3)
    self.assertEqual(song.key, "E")
    #self.assertEqual(song.text, "# A Song! (Key of E)\n    \nSome stuff    \n    \n")

    self.assertEqual(song.to_html(), '<div class="song">\n<div class="page">\n<h1 id="a-song-key-of-e">A Song! (Key of E)</h1>\n<p>Some stuff</p>\n</div>\n</div>\n')
    
    
  def test_transpose(self):
    c = cm.transposer(2)
    self.assertEqual(c.transpose_note("C"), "D")
    c = cm.transposer(1)
    self.assertEqual(c.transpose_note("B"), "C")
    c = cm.transposer(2)
    self.assertEqual(c.transpose_chord("C"), "D")
    c = cm.transposer(1)
    self.assertEqual(c.transpose_chord("C7"), "C#7")
    c = cm.transposer(1)
    self.assertEqual(c.transpose_chord("Asus4"), "Bbsus4")
    c = cm.transposer(-1)
    self.assertEqual(c.transpose_chord("C#7"), "C7")
    self.assertEqual(c.transpose_chord("Cm"), "Bm")
    self.assertEqual(c.transpose_chord("G#m/B"), "Gm/Bb")
if __name__ == '__main__':
    unittest.main()
