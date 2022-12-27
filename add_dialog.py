import os
import json
import wx
from aesthetics import bground_color, small_font


class AddDialog(wx.Dialog):
    def __init__(self, parent, ss_id, title="Add new savestate", size=(400, 200)):
        super().__init__(parent, title=title, size=size, style=wx.CAPTION | wx.CLOSE_BOX)
        self.Centre()
        self.parent = parent
        self.ss_id = ss_id
        self.parent = parent

        small_panel = wx.Panel(self, style=wx.SUNKEN_BORDER)
        small_panel.SetBackgroundColour(bground_color)
        wx.StaticText(small_panel, label="Select category:", pos=(30, 35)).SetFont(small_font)
        wx.StaticText(small_panel, label="Enter scene name:", pos=(15, 75)).SetFont(small_font)

        style = wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SORT
        self.category_choice = wx.ComboBox(small_panel, pos=(155, 35), size=(200, 100), style=style)
        self.category_choice.AppendItems(self.parent.current_categories)
        self.new_name = wx.TextCtrl(small_panel, pos=(155, 75), size=(200, 25))
        self.ok_button = wx.Button(small_panel, label="Ok", pos=(130, 120), name="ok")
        self.cancel_button = wx.Button(small_panel, label="Cancel", pos=(220, 120), name="cancel")

        self.ok_button.Bind(wx.EVT_BUTTON, self.on_button_press)
        self.ok_button.Disable()
        self.cancel_button.Bind(wx.EVT_BUTTON, self.on_button_press)
        self.category_choice.Bind(wx.EVT_COMBOBOX, self.on_modify)
        self.new_name.Bind(wx.EVT_TEXT, self.on_modify)

    def on_modify(self, evt):
        if self.new_name.GetValue() and self.category_choice.GetValue():
            self.ok_button.Enable()
        else:
            self.ok_button.Disable()

    def on_button_press(self, evt):
        if evt.GetEventObject().GetName() == "ok":
            new_scene = self.new_name.GetValue()
            new_cat = self.category_choice.GetValue()
            new_path = f"savestates\\{self.parent.patch}\\{new_cat}\\{new_scene}.json"

            if os.path.exists(new_path):
                message = "Do you want to overwrite the savestate with the same name?"
                style = wx.YES_NO | wx.ICON_WARNING
                dialog = wx.MessageDialog(self, caption="This savestate already exists!", message=message, style=style)
                if dialog.ShowModal() == wx.ID_NO:
                    return

            with open(f"{self.parent.current_path}\\savestate{self.ss_id}.json") as file:
                temp = json.load(file)
                temp["category"] = new_cat
                temp["saveStateIdentifier"] = new_scene

            with open(f"{self.parent.current_path}\\savestate{self.ss_id}.json", "w") as file:
                json.dump(temp, file, indent=4)
            with open(new_path, "w") as file:
                json.dump(temp, file, indent=4)

            self.parent.load()

        self.Destroy()
