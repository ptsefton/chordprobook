#!usr/bin/env python3
import unittest
import tempfile
import chordprobook.books as books
import chordprobook.chords as chords

class TestStuff(unittest.TestCase):
  def test_chord_markup_normaliser(self):
     self.assertEqual(books.normalize_chord_markup("xxxxxxx[A] yyyy"), "xxxxxxx [A] yyyy")
     self.assertEqual(books.normalize_chord_markup("[A]yyyy"), "[A] yyyy")
     self.assertEqual(books.normalize_chord_markup("xxxxxxx[A]"), "xxxxxxx [A]")
     self.assertEqual(books.normalize_chord_markup("xxxxxxx [A]yyyy"), "xxxxxxx [A] yyyy")
     self.assertEqual(books.normalize_chord_markup("[A7]xxxxxxx[A]yyyy[A9]"), "[A7] xxxxxxx[A]yyyy [A9]")
     self.assertEqual(books.normalize_chord_markup("When he chucked me off the[D] pier at Woolloomoo[G]loo [C] [G]"), "When he chucked me off the [D] pier at Woolloomoo[G]loo [C] [G]")

      
  def test_TOC(self):
      #Check that we can build a table of contents and split it across multiple pages when necessary
      book_text = ""
      slotmachine = "samples/slot_machine_baby.cho.txt\n"
      book_text += slotmachine * 30
      b = books.cp_song_book()
      b.load_from_text(book_text)
      toc = books.TOC(b, 3)
      self.assertEqual(len(toc.pages), 1)
      self.assertEqual(len(b.songs),30)
      
      
      book_text += slotmachine * 60
      b = books.cp_song_book()
      b.load_from_text(book_text)
      toc = books.TOC(b, 3)
      self.assertEqual(len(toc.pages), 3)
      self.assertEqual(len(b.songs), 90)

      book_text += slotmachine * 40
      b = books.cp_song_book()
      b.load_from_text(book_text)
      toc = books.TOC(b, 3)
      self.assertEqual(len(toc.pages), 4)
      self.assertEqual(len(b.songs), 131)
      
      book_text += slotmachine * 80
      b = books.cp_song_book()
      b.load_from_text(book_text)
      toc = books.TOC(b, 3)
      self.assertEqual(len(toc.pages), 6)
      self.assertEqual(len(b.songs), 211)

  def test_single_song_multitple_pdf(self):
      b = books.cp_song_book()
      b.add_song_from_text("{title: This is a song!}\n{key: Db}", "test1")
      with tempfile.TemporaryDirectory() as tmp:
          result = b.save_as_single_sheets(tmp)
      self.assertEqual(len(result), 1)
      b = books.cp_song_book()
      self.assertEqual(result[0]["title"], "This is a song! (C#)")
      b.add_song_from_text("{title: This is a second song!}\n{key: Db}\n{tr: +1 +2}", "test1")
      with tempfile.TemporaryDirectory() as tmp:
          result = b.save_as_single_sheets(tmp)
      self.assertEqual(len(result), 3)
      self.assertEqual(result[1]["title"], "This is a second song! (D)")
      
      
  def test_book(self):
      book_path = "samples/sample.book.txt"
      sample_book_text = open(book_path).read()
      b = books.cp_song_book(path=book_path)
      b.load_from_text(sample_book_text)
      self.assertEqual(len(b.songs), 4)
      self.assertEqual(b.songs[1].key, "C")
      self.assertEqual(b.songs[2].key, "Bb")
      
      book_path="samples/sample-lazy.book.txt"
      """This one has auto-transpose turned on"""
      sample_book_text = open(book_path).read()
      b = books.cp_song_book( path=book_path)
      b.load_from_text(sample_book_text)
      self.assertEqual(len(b.songs), 8)
      self.assertEqual(b.title, "Sample songs")
     
      book_path="samples/sample-lazy-uke.book.txt"
      sample_book_text = open(book_path).read()
      b = books.cp_song_book(path=book_path)
      b.load_from_text(sample_book_text)
     
      self.assertEqual(len(b.songs), 4)
      #self.assertEqual(b.songs[3].transpose, -3)
      self.assertEqual(b.songs[3].title, "Universe")
      self.assertEqual(b.title, "Sample songs")
      self.assertEqual(b.default_instrument_names[0],"Ukulele")
      
  def test_versioned_book(self):
      book_path = "samples/sample.book.txt"
      sample_book_text = open(book_path).read()
      b = books.cp_song_book(path=book_path)
      b.load_from_text(sample_book_text)

      self.assertEqual(b.version, None)
      
      book_path = "samples/sample_versioned.book.txt"
      sample_book_text = open(book_path).read()
         

      b = books.cp_song_book(path=book_path)
      b.load_from_text(sample_book_text)
      self.assertEqual(b.version, "v1.1a")

      book_path = "samples/sample_auto_versioned.book.txt"
      sample_book_text = open(book_path).read()
      b = books.cp_song_book(path=book_path)
      b.load_from_text(sample_book_text)
      self.assertEqual(b.version, 'auto')


def test_setlist(self):
      book_path = "samples/sample.setlist.md"

      
      sample_book_text = open(book_path).read()
      b = books.cp_song_book(path=book_path)
      b.load_from_text(sample_book_text)

      self.assertEqual(b.version, None)
      
      book_path = "samples/sample_versioned.book.txt"
      sample_book_text = open(book_path).read()
         

      b = books.cp_song_book(path=book_path)
      b.load_from_text(sample_book_text)
      self.assertEqual(b.version, "v1.1a")

      book_path = "samples/sample_auto_versioned.book.txt"
      sample_book_text = open(book_path).read()
      b = books.cp_song_book(path=book_path)
      b.load_from_text(sample_book_text)
      self.assertEqual(b.version, 'auto')
      
  def test_directive(self):
      d = books.directive("{title: This is my title}")
      self.assertEqual(d.type, books.directive.title)
      
      self.assertEqual(d.value, "This is my title")
      d = books.directive("{st: This: is my: subtitle}")
      self.assertEqual(d.type, books.directive.subtitle)
      
      d = books.directive("{grids}")
      self.assertEqual(d.type, books.directive.grids)
      
      #Allow extra space
      d = books.directive(" {grids}   ")
      self.assertEqual(d.type, books.directive.grids)
      
      #Allow things to have values, or not
      d = books.directive(" {grids: C#7}   ")
      self.assertEqual(d.type, books.directive.grids)
      self.assertEqual(d.value, "C#7")
      d = books.directive(" {grids: C#7 Bbsus4   }   ")
      self.assertEqual(d.type, books.directive.grids)
      self.assertEqual(d.value, "C#7 Bbsus4")

      #This is a directive, for now, but the value is bad
      d = books.directive(" {grids: C#7 Bbsus4   } {title: ASDASD}   ")
      self.assertEqual(d.value, "C#7 Bbsus4   } {title: ASDASD")

      
      # These are not directives
      d = books.directive("{title: This is my title ")
      self.assertEqual(d.type, None)
      d = books.directive("{{title: This is my title} ")
      self.assertEqual(d.type, None)
      
    

  def test_reorder(self):
    one1 = "{title: 1 page}"
    one2 = "{title: 1 page}"
    two1 = "{title: 2 page}\n{new_page}\nxxx"
    two2 = "{title: 2 page}\n{new_page}\yxxx"
  
    book = books.cp_song_book()
    book.add_song_from_text(one1, "1")
    book.add_song_from_text(one2, "2")
    book.add_song_from_text(two1, "3")
    book.add_song_from_text(two2, "4")
    page = 3
    book.reorder(page)
    for song in book.songs:
      #Check that two or four page spreads start on an even page
      if song.pages % 2 == 0:
        self.assertEqual(page % 2, 0)
      page += song.pages

  def test_auto_transpose(self):
      song1 =  books.cp_song("{title: 1 page}\n{key: C}\n{transpose: +2 -3}")
      self.assertEqual(song1.standard_transpositions, [0, 2, -3])

      
  def test_parse(self):
    song = books.cp_song("{title: A Song!}\nSome stuff\n{key: C#}\n")
    self.assertEqual(song.key, "C#")
    self.assertEqual(song.title, "A Song!")
    song = books.cp_song("{title: A Song!}\nSome stuff\n{key: C#}\n#A comment\n#or two", transpose=3)
    self.assertEqual(song.key, "E")
    song.format()
    self.assertEqual(song.to_html().replace("\n",''), '<div class="song"><div class="page"><h1 class="song-title">A Song! (E)</h1><div class="grids"></div><div class="song-page"><div class="song-text"><p>Some stuff</p></div></div></div></div>')


    # Test auto-apply of classes to lines beginning with a .
    song = books.cp_song("{title: A Song!}\nSome stuff\n{key: C#}\n.♂ Mark this up as class ♂ \n")
    self.assertEqual(song.key, "C#")
    self.assertEqual(song.title, "A Song!")
    self.assertEqual(song.text, "Some stuff    \n<span class='♂'>♂ Mark this up as class ♂</span>\n\n")



    # Test that chords with rhythm don't get counted as separate chords
    song = books.cp_song("""
    {title: Test}
    {soc}
    {c: Chorus}
    {instrument: Uke}
    This [C] is the [C!] chorus [Db7 / / / /] [C!] [Db7!]
    CHorus chorus
    {eoc}
    
    After the chorus

    """)
    song.format( instrument_name="Uke")
    # Should only be two chords in the above
    self.assertEqual(len(song.chords_used),2)


    # Test that chords with different names for the same thing are all counted
    song = books.cp_song("""
    {title: Test}
    {soc}
    {c: Chorus}
    {instrument: Uke}
    This [BbM7] is the [Bbmaj7] chorus  [A#M7] is the [A#maj7] chorus
    CHorus chorus
    {eoc}
    
    After the chorus

    """)
    song.format( instrument_name="Uke")
    # Should be four chords in the above, all the same, but not up to us to change what the author wrote
    self.assertEqual(len(song.chords_used),4)
    
    song = books.cp_song("""
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
    song = books.cp_song("""
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

    song = books.cp_song("""
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
    self.assertEqual(song.text, result)


    song = books.cp_song("""
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
    song = books.cp_song("{instrument: Thongaphone}") 
    self.assertEqual( "Thongaphone", song.local_instruments.get_instrument_by_name("Thongaphone").name)
    self.assertEqual( "Thongaphone", song.local_instruments.get_instrument_by_name("Thongaphone").name)

    song = books.cp_song("{instrument: Thongaphone}\n{define: C#7 frets 0 1 0 1 0 1 0 1}\n{define: C#7-5 frets 0 1 0 1 0 1 0 1}")
    #song.instruments.get_instrument_by_name("Thongaphone").chart.get_default("C#7-5").show()
    self.assertEqual("{define: C#7-5 frets 0 1 0 1 0 1 0 1}", song.local_instruments.get_instrument_by_name("Thongaphone").chart.get_default("C#7-5").to_chordpro())
   
    song = books.cp_song("{instrument: Uke}\n{define: C frets 12 12 12 15}")
    #song.instruments.get_instrument_by_name("Soprano Ukulele").chart.get_default("C").show()
    song.format(instrument_name = "Nope!")
    
    self.assertEqual("{define: C base-fret 11 frets 1 1 1 4}", song.local_instruments.get_instrument_by_name("Soprano Ukulele").chart.get_default("C").to_chordpro())


    
  def test_transpose(self):
    c = chords.transposer(2)
    self.assertEqual(c.transpose_note("C"), "D")
    c = chords.transposer(1)
    self.assertEqual(c.transpose_note("B"), "C")
    c = chords.transposer(2)
    self.assertEqual(c.transpose_chord("C"), "D")
    c = chords.transposer(1)
    self.assertEqual(c.transpose_chord("C7"), "C#7")
    c = chords.transposer(1)
    self.assertEqual(c.transpose_chord("Asus4"), "Bbsus4")
    c = chords.transposer(-1)
    self.assertEqual(c.transpose_chord("C#7"), "C7")
    self.assertEqual(c.transpose_chord("Cm"), "Bm")
    self.assertEqual(c.transpose_chord("G#m/B"), "Gm/Bb")
if __name__ == '__main__':
    unittest.main()
