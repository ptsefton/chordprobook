#!usr/bin/env python3
import unittest
import tempfile
import chordprobook.books as books
import chordprobook.chords as chords
import os

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
      for song in b.songs:
          song.format()
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
      self.assertEqual(len(b.songs), 130)

      book_text += slotmachine * 80
      b = books.cp_song_book()
      b.load_from_text(book_text)
      toc = books.TOC(b, 3)
      self.assertEqual(len(toc.pages), 6)
      self.assertEqual(len(b.songs), 210)

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
      b = books.cp_song_book(path=book_path)
      self.assertEqual(len(b.songs), 4)
      self.assertEqual(b.songs[1].key, "C")
      self.assertEqual(b.songs[2].key, "Bb")

      book_path="samples/sample-lazy.book.txt"

      b = books.cp_song_book( path=book_path)
      self.assertEqual(len(b.songs), 8)
      self.assertEqual(b.title, "Sample songs")

      book_path="samples/sample-lazy-uke.book.txt"
      b = books.cp_song_book(path=book_path)

      self.assertEqual(len(b.songs), 4)
      #self.assertEqual(b.songs[3].transpose, -3)
      self.assertEqual(b.songs[3].title, "Universe")
      self.assertEqual(b.title, "Sample songs")
      self.assertEqual(b.default_instrument_names[0],"Ukulele")

  def test_versioned_book(self):
      book_path = "samples/sample.book.txt"
      b = books.cp_song_book(path=book_path)

      self.assertEqual(b.version, None)
      book_path = "samples/sample_versioned.book.txt"
      b = books.cp_song_book(path=book_path)
      self.assertEqual(b.version, "v1.1a")

      book_path = "samples/sample_auto_versioned.book.txt"
      b = books.cp_song_book(path=book_path)
      self.assertEqual(b.version, 'auto')


  def test_setlist(self):

      #This is our setlist
      book_path = "samples/sample.setlist.md"
      b = books.cp_song_book()

      #Now use the setlist to order the book - should find the {book directive}
      b.order_by_setlist(book_path)


      self.assertEqual(len(b.songs), 4)
      self.assertEqual(len(b.sets), 2)

      b.format()

      keys = ["C","A","G","Bb"]
      actual_keys = [s.key for s in b.songs]
      self.assertEqual(keys, actual_keys)

      original_keys = ["C","C","G","C"]
      actual_keys = [s.original_key for s in b.songs]
      self.assertEqual(original_keys, actual_keys)



  def test_versioned_setlist(self):
      book_path = "samples/sample.setlist.md"
      sample_book_text = open(book_path).read()
      # This is cumbersome, but if you want to pass a string to setlist
      # you need to set the path first
      b = books.cp_song_book()
      b.set_path(book_path)
      b.order_by_setlist(sample_book_text)
      self.assertEqual(b.version, None)



      book_path = "samples/sample_versioned.setlist.md"
      b = books.cp_song_book()
      b.order_by_setlist(book_path)
      self.assertEqual(b.version, "32b")


      book_path = "samples/sample_auto_versioned.setlist.md"
      b = books.cp_song_book()
      b.order_by_setlist(book_path)
      self.assertEqual(b.version, 'auto')

  def test_directive(self):
      d = books.directive("{title: This is my title}")
      self.assertEqual(d.type, books.directive.title)

      self.assertEqual(d.value, "This is my title")
      d = books.directive("{st: This: is my: subtitle}")
      self.assertEqual(d.type, books.directive.subtitle)

      d = books.directive("{grids}")
      self.assertEqual(d.type, books.directive.grids)

      # Allow extra space
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

      d = books.directive("{page_image: test.png}")
      self.assertEqual(d.type, books.directive.page_image)

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

  def test_numbered_chords(self):
    # Check that nashville/numbered chords are working
    song = books.cp_song("{title: A Song!}\nSome stuff\n{key: C}\n[C] [F] [G]", nashville=True)
    song.format()
    self.assertTrue("[I]" in song.md)
    self.assertTrue("[IV]" in song.md)
    self.assertTrue("[V]" in song.md)

    # Lowercase for minors
    song = books.cp_song("{title: A Song!}\nSome stuff\n{key: Cm}\n[Cm] [Fm] [G]", nashville=True)
    song.format()
    self.assertTrue("[i]" in song.md)
    self.assertTrue("[iv]" in song.md)
    self.assertTrue("[V]" in song.md)

    # Check that charts are working
    song = books.cp_song("{title: A Song!}\nSome stuff\n{key: Cm}\n[Cm] [Fm] [G]", nashville=True, major_chart=True)
    song.format()
    self.assertTrue("[vi]" in song.md)
    self.assertTrue("[ii]" in song.md)
    self.assertTrue("[III]" in song.md)


    # Check that we can change keys
    song = books.cp_song("{title: A Song!}\nSome stuff\n{key: C}\n[C] [F] [G]\n{key: G}\n [C] [F] [G]", nashville=True)
    song.format()
    self.assertTrue("[I]" in song.md)
    self.assertTrue("[IV]" in song.md)
    self.assertTrue("[V]" in song.md)

    # Should be variants for these cos of the key change
    self.assertTrue("[IV]" in song.md)
    self.assertTrue("[♭VII]" in song.md)
    self.assertTrue("[I]" in song.md)



  def test_page_image_formatting(self):
     import re
     song = books.cp_song("""
          {page_image: test.png}
          """, path="/this/is/my/path/song.cho.txt")


     print("TEST", song.text)
     self.assertTrue(song.text, re.search("<img src='file:///.*?' width='680'>", song.text))


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
    Chorus chorus
    {eoc}

    After the chorus

    """)
    result = """
<blockquote class='chorus'>

**Chorus**    
This is the chorus    
Chorus chorus    
</blockquote>

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
    #normalise space at end of line as that's not what we're testing here
    import re
    txt = re.sub(" ","", song.text)
    result = re.sub(" ","", result)
    self.assertEqual(txt, result)

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
<blockquote class='chorus'>

**Chorus**
Where someone forgot to close the tab
</blockquote>
"""
    txt = re.sub(" ","", song.text)
    result = re.sub(" ","", result)
 
    self.assertEqual(txt, result)


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





if __name__ == '__main__':
    unittest.main()
