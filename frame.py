import os
import sys
import json
import wx
from manage_dialog import ManageDialog
from add_dialog import AddDialog
from aesthetics import *


class Frame(wx.Frame):
    custom_style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)

    def __init__(self, settings, parent=None, title="Hollow Knight Savestates Manager", size=(760, 650)):
        super().__init__(parent, title=title, size=size, style=self.custom_style)
        self.Center()
        self.panel = wx.Panel(self, style=wx.SUNKEN_BORDER)
        self.panel.SetBackgroundColour(bground_color)

        self.SetIcon(wx.Icon(wx.Bitmap("quill.png")))
        self.settings = settings
        self.patch = settings["patch"]

        self.cat_boxes = []
        self.saves_boxes = []
        self.buttons = []
        self.temporary_scenes = {}

        file_menu = wx.Menu()
        patch_menu = wx.Menu()

        self.patch_1221_button = patch_menu.Append(wx.ID_ANY, "Patch 1.2.2.1 Savestates")
        self.patch_cp_button = patch_menu.Append(wx.ID_ANY, "Current Patch Savestates")
        if self.patch == "1221":
            self.patch_1221_button.Enable(False)
            self.patch_cp_button.Enable()
        else:
            self.patch_1221_button.Enable()
            self.patch_cp_button.Enable(False)

        file_menu.AppendSubMenu(patch_menu, "Switch Patches")
        edit_button = file_menu.Append(wx.ID_ANY, "Edit savestates")
        change_game_folder = file_menu.Append(wx.ID_ANY, "Change game data folder")
        file_menu.AppendSeparator()
        exit_button = file_menu.Append(wx.ID_EXIT, 'Exit')

        self.Bind(wx.EVT_MENU, self.quit, exit_button)
        self.Bind(wx.EVT_MENU, self.switch_1221, self.patch_1221_button)
        self.Bind(wx.EVT_MENU, self.switch_cp, self.patch_cp_button)
        self.Bind(wx.EVT_MENU, self.select_folder, change_game_folder)
        self.Bind(wx.EVT_MENU, self.manage, edit_button)

        self.menu = wx.MenuBar()
        self.menu.Append(file_menu, "&Settings")
        self.SetMenuBar(self.menu)

        self.text1221 = wx.StaticText(self.panel, label="Savestates for Patch 1.2.2.1")
        self.text1221.SetFont(title_font)
        if self.text1221.GetFont().GetFaceName() == "Gabriola":
            self.text1221.SetPosition((0, -10))
        self.text1221.Centre(wx.HORIZONTAL)
        self.text1221.Hide()

        self.textCP = wx.StaticText(self.panel, label="Savestates for Current Patch")
        self.textCP.SetFont(title_font)
        if self.textCP.GetFont().GetFaceName() == "Gabriola":
            self.textCP.SetPosition((0, -10))
        self.textCP.Centre(wx.HORIZONTAL)
        self.textCP.Hide()

        self.page_box = wx.ComboBox(self.panel, size=(100, 30), pos=(10, 70), style=wx.CB_READONLY)
        self.page_box.Bind(wx.EVT_COMBOBOX, self.on_page_select)
        self.page_box.AppendItems([f"Page {n}" for n in range(10)])
        self.page_box.SetSelection(0)

        wx.StaticText(self.panel, label="Category", pos=(150, 75)).SetFont(small_font)
        wx.StaticText(self.panel, label="Scene", pos=(390, 75)).SetFont(small_font)

        if self.patch == "1221":
            self.ss_path = "savestates\\1221"
            self.current_categories = os.listdir(self.ss_path)
            self.current_path = f"{settings['path']}\\Savestates-1221\\0"
            self.text1221.Show()
            self.textCP.Hide()
        else:
            self.ss_path = "savestates\\CP"
            self.current_categories = os.listdir(self.ss_path)
            self.current_path = f"{settings['path']}\\DebugModData\\Savestates Current Patch\\0"
            self.text1221.Hide()
            self.textCP.Show()

        style = wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SORT
        for ss in range(10):
            text = wx.StaticText(self.panel, label=f"Savestate {ss}:", pos=(10, 100+43*ss))
            text.SetFont(list_font)
            category_box = wx.ComboBox(self.panel, size=(130, 30), pos=(120, 100+43*ss), style=style)
            savestate_box = wx.ComboBox(self.panel, size=(300, 30), pos=(275, 100+43*ss), style=style)
            button = wx.Button(self.panel, label=f"Add as new savestate", size=(130, 35), pos=(600, 95+43*ss))

            category_box.Disable()
            savestate_box.Disable()
            category_box.box_id = savestate_box.box_id = ss
            category_box.Bind(wx.EVT_COMBOBOX, self.on_category_select)
            savestate_box.Bind(wx.EVT_COMBOBOX, self.on_scene_select)
            self.cat_boxes.append(category_box)
            self.saves_boxes.append(savestate_box)

            button.button_id = ss
            button.Bind(wx.EVT_BUTTON, self.button_handler)
            button.Disable()
            self.buttons.append(button)

        self.apply_changes = wx.Button(self.panel, label=f"Apply savestates", pos=(280, 550))
        self.cancel = wx.Button(self.panel, label=f"Cancel", pos=(400, 550))
        self.apply_changes.Bind(wx.EVT_BUTTON, self.overwrite)
        self.cancel.Bind(wx.EVT_BUTTON, self.revert)
        self.apply_changes.Disable()
        self.cancel.Disable()

        self.Bind(wx.EVT_CLOSE, self.quit)
        self.Show()

    def load(self):
        self.Freeze()

        for box in range(10):
            savestate = f"{self.current_path}\\savestate{box}.json"
            scene = ""
            category = "Unknown"

            self.saves_boxes[box].Disable()
            self.buttons[box].Disable()

            cat_box = self.cat_boxes[box]
            cat_box.Clear()
            cat_box.Enable()

            save_box = self.saves_boxes[box]
            save_box.Clear()

            cat_choices = self.current_categories
            saves_choices = [""]
            if os.path.exists(savestate):
                with open(savestate) as file:
                    temp = json.load(file)
                    if "category" in temp:
                        category = temp["category"]
                    scene = temp["saveStateIdentifier"]
                self.buttons[box].Enable()

                if category in self.current_categories:
                    category_path = os.listdir(f"{self.ss_path}\\{category}")
                    if f"{scene}.json" in category_path:
                        saves_choices = [*map(lambda name: name[:-5], category_path)]
                    else:
                        category = "Unknown"
                        cat_choices = ["Unknown", *self.current_categories]
                        saves_choices = [scene]
                else:
                    category = "Unknown"
                    cat_choices = ["Unknown", *self.current_categories]
                    saves_choices = [scene]

            cat_box.AppendItems(cat_choices)
            cat_box.SetValue(category)

            if category != "Unknown":
                save_box.Enable()
            save_box.AppendItems(saves_choices)
            save_box.SetValue(scene)

        self.Thaw()

    def update_box(self, box_id, text):
        self.buttons[box_id].Disable()
        scene = self.saves_boxes[box_id]
        scene.Clear()
        scene.Enable()

        if text:
            raw_list = os.listdir(f"{self.ss_path}\\{text}")
            pretty_list = [*map(lambda x: x[:-5], raw_list)]
            scene.Enable()
            scene.AppendItems(pretty_list)
        else:
            scene.Disable()

    def on_category_select(self, evt):
        choice = evt.GetEventObject()
        box_id = choice.box_id
        value = choice.Value
        cat = self.cat_boxes[box_id]
        if "Unknown" in cat.GetStrings():
            if value == "Unknown":
                return
            cat.Clear()
            cat.AppendItems(self.current_categories)
            cat.SetValue(value)
        self.cancel.Enable()
        self.update_box(box_id, value)

    def on_scene_select(self, evt):
        choice = evt.GetEventObject()
        choice_id = choice.box_id
        corresponding_cat = self.cat_boxes[choice_id].Value
        scene_path = f"{self.ss_path}\\{corresponding_cat}\\{choice.Value}.json"
        self.temporary_scenes[choice_id] = scene_path
        self.apply_changes.Enable()
        self.cancel.Enable()
        self.buttons[choice_id].Enable()

    def overwrite(self, evt):
        for choice_id, scene_path in self.temporary_scenes.items():
            with open(scene_path) as file:
                current_ss = json.load(file)
            with open(f"{self.current_path}\\savestate{choice_id}.json", "w") as file:
                json.dump(current_ss, file, indent=4)
        self.apply_changes.Disable()
        self.cancel.Disable()
        self.temporary_scenes = {}

    def revert(self, evt=None):
        self.load()
        self.apply_changes.Disable()
        self.cancel.Disable()
        self.temporary_scenes = {}

    def button_handler(self, evt):
        button_id = evt.GetEventObject().button_id
        dialog = AddDialog(self, button_id)
        dialog.ShowModal()

    def path_error(self):
        message = "The Hollow Knight save data folder couldn't be found! \nPlease select it manually!"
        error = wx.MessageDialog(self, caption="Error!", style=wx.OK | wx.CANCEL | wx.ICON_WARNING, message=message)
        if error.ShowModal() == wx.ID_OK:
            self.select_folder()
            self.load()

    def select_folder(self, evt=None):
        dialog = wx.DirDialog(self, 'Select the Hollow Knight save data folder', style=wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            new_path = dialog.GetPath()
            if new_path:
                if "0" in os.listdir(new_path):
                    new_path += "\\0"
                self.settings['path'] = new_path
                self.current_path = new_path
                with open("game_data.json", 'w') as file:
                    json.dump(self.settings, file)
                self.load()

    def switch_1221(self, evt):
        self.settings["patch"] = "1221"
        self.ss_path = "savestates\\1221"
        self.current_categories = os.listdir(self.ss_path)
        self.current_path = f"{self.settings['path']}\\Savestates-1221\\0"
        self.page_box.SetSelection(0)
        self.patch_1221_button.Enable(False)
        self.patch_cp_button.Enable()
        self.text1221.Show()
        self.textCP.Hide()
        self.load()

    def switch_cp(self, evt):
        self.settings["patch"] = "CP"
        self.ss_path = "savestates\\CP"
        self.current_categories = os.listdir(self.ss_path)
        self.current_path = f"{self.settings['path']}\\DebugModData\\Savestates Current Patch\\0"
        self.page_box.SetSelection(0)
        self.patch_1221_button.Enable()
        self.patch_cp_button.Enable(False)
        self.text1221.Hide()
        self.textCP.Show()
        self.load()

    def on_page_select(self, evt):
        page = evt.GetEventObject().GetCurrentSelection()
        self.current_path = f"{self.current_path[:-1]}{page}"
        self.revert()

    def manage(self, evt):
        dialog = ManageDialog(self)
        dialog.ShowModal()
        self.current_categories = os.listdir(self.ss_path)
        self.load()

    def quit(self, evt):
        with open("game_data.json", 'w') as file:
            json.dump(self.settings, file)
        self.Destroy()
        sys.exit()
