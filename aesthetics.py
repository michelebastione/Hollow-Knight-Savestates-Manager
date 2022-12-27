from wx import Font

bground_color = (249, 247, 223, 1)

title_font = Font()
title_font.SetFaceName("Gabriola")
title_font.Scale(3)
title_font.MakeBold()

small_font = Font()
small_font.SetFaceName("Constantia")
small_font.SetPointSize(12)

list_font = Font()
list_font.SetFaceName("Constantia")
list_font.SetPointSize(13)
list_font.MakeBold().MakeItalic()
