#!usr/bin/env python3
import unittest
import chordprobook as cpb


class TestStuff(unittest.TestCase):

  def test_TOC(self):
      book_text = ""
      slotmachine = "./samples/slot_machine_baby.cho\n"
      book_text += slotmachine * 30
      b = cpb.cp_song_book()
      b.load_from_text(book_text)
      toc = cpb.TOC(b, 3)

      
      self.assertEqual(len(toc.pages), 1)
      book_text += slotmachine * 60
      b = cpb.cp_song_book()
      b.load_from_text(book_text)
      toc = cpb.TOC(b, 3)
      self.assertEqual(len(toc.pages), 3)
      
      book_text += slotmachine * 100
      b = cpb.cp_song_book()
      b.load_from_text(book_text)
      toc = cpb.TOC(b, 3)
      self.assertEqual(len(toc.pages), 5)
      
  def test_book(self):
      book_path = "samples/sample-book.txt"
      sample_book_text = open(book_path).read()
      b = cpb.cp_song_book(path=book_path)
      b.load_from_text(sample_book_text)
      self.assertEqual(len(b.songs), 4)
      self.assertEqual(b.songs[1].key, "C")
      self.assertEqual(b.songs[2].key, "Bb")
      
      book_path="samples/sample-book-lazy.txt"
      sample_book_text = open(book_path).read()
      b = cpb.cp_song_book( path=book_path)
      b.load_from_text(sample_book_text)
      self.assertEqual(len(b.songs), 4)
      self.assertEqual(b.title, "Sample songs")
     
      book_path="samples/sample-book-lazy-uke.txt"
      sample_book_text = open(book_path).read()
      b = cpb.cp_song_book(path=book_path)
      b.load_from_text(sample_book_text)
      self.assertEqual(len(b.songs), 4)
      self.assertEqual(b.title, "Sample songs")
      self.assertEqual(b.default_instrument_names[0],"Ukulele")

  def test_directive(self):
      d = cpb.directive("{title: This is my title}")
      self.assertEqual(d.type, cpb.directive.title)
      
      self.assertEqual(d.value, "This is my title")
      d = cpb.directive("{st: This: is my: subtitle}")
      self.assertEqual(d.type, cpb.directive.subtitle)
      
      d = cpb.directive("{grids}")
      self.assertEqual(d.type, cpb.directive.grids)
      
      #Allow extra space
      d = cpb.directive(" {grids}   ")
      self.assertEqual(d.type, cpb.directive.grids)
      
      #Allow things to have values, or not
      d = cpb.directive(" {grids: C#7}   ")
      self.assertEqual(d.type, cpb.directive.grids)
      self.assertEqual(d.value, "C#7")
      d = cpb.directive(" {grids: C#7 Bbsus4   }   ")
      self.assertEqual(d.type, cpb.directive.grids)
      self.assertEqual(d.value, "C#7 Bbsus4")

      #This is a directive, for now, but the value is bad
      d = cpb.directive(" {grids: C#7 Bbsus4   } {title: ASDASD}   ")
      self.assertEqual(d.value, "C#7 Bbsus4   } {title: ASDASD")

      
      # These are not directives
      d = cpb.directive("{title: This is my title ")
      self.assertEqual(d.type, None)
      d = cpb.directive("{{title: This is my title} ")
      self.assertEqual(d.type, None)
      
    

  def test_reorder(self):
    one1 = cpb.cp_song("{title: 1 page}")
    one2 = cpb.cp_song("{title: 1 page}")
    two1 = cpb.cp_song("{title: 2 page}")
    two1.pages = 2
    two2 = cpb.cp_song("{title: 2 page}")
    two2.pages = 2
    book = cpb.cp_song_book([one1,two1, one2, two2])
    page = 3
    book.reorder(page)
    for song in book.songs:
      #Check that two or four page spreads start on an even page
      if song.pages % 2 == 0:
        self.assertEqual(page % 2, 0)
      page += song.pages

  def test_auto_transpose(self):
      song1 =  cpb.cp_song("{title: 1 page}\n{key: C}\n{transpose: +2 -3}")
      self.assertEqual(song1.standard_transpositions, [0, 2, -3])

      
  def test_parse(self):
    song = cpb.cp_song("{title: A Song!}\nSome stuff\n{key: C#}\n")
    self.assertEqual(song.key, "C#")
    self.assertEqual(song.title, "A Song!")
    song = cpb.cp_song("{title: A Song!}\nSome stuff\n{key: C#}\n#A comment\n#or two", transpose=3)
    self.assertEqual(song.key, "E")
    self.assertEqual(song.to_html(), '<div class="song">\n<div class="page">\n<h1 id="a-song-e">A Song! (E)</h1>\n<div class="song-page">\n<div class="song-text">\n<p>Some stuff</p>\n</div>\n</div>\n</div>\n</div>\n</div>\n')

    song = cpb.cp_song("""
    {title: Test}
    {soc}
    {c: Chorus}
    This is the chorus
    CHorus chorus
    {eoc}
    
    After the chorus

    """)
    result = """

> **Chorus**    
> This is the chorus    
> CHorus chorus

After the chorus


"""
    self.assertEqual(song.text, result)
    song = cpb.cp_song("""
{title: Test}
{sot}
This is where some
    Preformatted
    Tab goes
    --5---5----5
    1---2--2--2-
    3-3-3-3-3-3-
    --9--9--9-9-
{eot}
After the tab

    """)
    result = """
```    
This is where some    
    Preformatted    
    Tab goes    
    --5---5----5    
    1---2--2--2-    
    3-3-3-3-3-3-    
    --9--9--9-9-    
```    
After the tab


"""

    self.assertEqual(song.text, result)

    song = cpb.cp_song("""
{title: Test}
{sot}
This is where some
    Preformatted
    Tab goes
    --5---5----5
    1---2--2--2-
    3-3-3-3-3-3-
    --9--9--9-9-
{soc}
{c: Chorus}
Where someone forgot to close the tab
{eoc}""")
    result = """
```    
This is where some    
    Preformatted    
    Tab goes    
    --5---5----5    
    1---2--2--2-    
    3-3-3-3-3-3-    
    --9--9--9-9-

> **Chorus**    
> Where someone forgot to close the tab
"""
    print(song.text)
    self.assertEqual(song.text, result)


    song = cpb.cp_song("""
{title: Test}
{start_of_chorus}
{c: Here's a chorus with tab in it}
{sot}
This is where some
    Preformatted
    Tab goes
    --5---5----5
    1---2--2--2-
    3-3-3-3-3-3-
    --9--9--9-9-
{eot}
Still in the chorus
{eoc}
After the chorus

    """)
    result = """

> **Here's a chorus with tab in it**    
>     This is where some    
>         Preformatted    
>         Tab goes    
>         --5---5----5    
>         1---2--2--2-    
>         3-3-3-3-3-3-    
>         --9--9--9-9-    
> Still in the chorus    
After the chorus


"""
    # TODO TEST IS MISSING!

    
    song = cpb.cp_song("{instrument: Thongaphone}") 
    self.assertEqual( "Thongaphone", song.local_instruments.get_instrument_by_name("Thongaphone").name)
    self.assertEqual( "Thongaphone", song.local_instruments.get_instrument_by_name("Thongaphone").name)

    song = cpb.cp_song("{instrument: Thongaphone}\n{define: C#7 frets 0 1 0 1 0 1 0 1}\n{define: C#7-5 frets 0 1 0 1 0 1 0 1}")
    #song.instruments.get_instrument_by_name("Thongaphone").chart.get_default("C#7-5").show()
    self.assertEqual("{define: C#7-5 frets 0 1 0 1 0 1 0 1}", song.local_instruments.get_instrument_by_name("Thongaphone").chart.get_default("C#7-5").to_chordpro())
   
    song = cpb.cp_song("{instrument: Uke}\n{define: C frets 12 12 12 15}")
    #song.instruments.get_instrument_by_name("Soprano Ukulele").chart.get_default("C").show()
    song.format(instrument_name = "Nope!")
    
    self.assertEqual("{define: C base-fret 11 frets 1 1 1 4}", song.local_instruments.get_instrument_by_name("Soprano Ukulele").chart.get_default("C").to_chordpro())


    
  def test_transpose(self):
    c = cpb.transposer(2)
    self.assertEqual(c.transpose_note("C"), "D")
    c = cpb.transposer(1)
    self.assertEqual(c.transpose_note("B"), "C")
    c = cpb.transposer(2)
    self.assertEqual(c.transpose_chord("C"), "D")
    c = cpb.transposer(1)
    self.assertEqual(c.transpose_chord("C7"), "C#7")
    c = cpb.transposer(1)
    self.assertEqual(c.transpose_chord("Asus4"), "Bbsus4")
    c = cpb.transposer(-1)
    self.assertEqual(c.transpose_chord("C#7"), "C7")
    self.assertEqual(c.transpose_chord("Cm"), "Bm")
    self.assertEqual(c.transpose_chord("G#m/B"), "Gm/Bb")
if __name__ == '__main__':
    unittest.main()
