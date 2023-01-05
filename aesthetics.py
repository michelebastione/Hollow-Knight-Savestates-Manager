import wx

bground_color = (249, 247, 223, 1)

frame_style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
combo_style = wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SORT
error_style = wx.OK | wx.CANCEL | wx.ICON_WARNING
listbox_style = wx.adv.EL_DEFAULT_STYLE | wx.adv.EL_NO_REORDER
dial_style = wx.CAPTION | wx.CLOSE_BOX

title_font = wx.Font()
title_font.SetFaceName("Gabriola")
title_font.Scale(3)
title_font.MakeBold()

small_font = wx.Font()
small_font.SetFaceName("Constantia")
small_font.SetPointSize(12)

list_font = wx.Font()
list_font.SetFaceName("Constantia")
list_font.SetPointSize(13)
list_font.MakeBold().MakeItalic()
