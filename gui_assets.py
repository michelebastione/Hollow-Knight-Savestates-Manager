import json, os, wx, sys


class Frame(wx.Frame):
    custom_style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
    font = wx.Font(); font.SetPointSize(10)
    font1 = wx.Font(); font1.SetPointSize(10); font1.Scale(2)
    font2 = wx.Font(); font2.SetPointSize(12); font2.MakeBold().MakeItalic()
    beige = (249, 247, 223, 1)

    def __init__(self, preferences, parent=None, title="Hollow Knight Savestates Manager", size=(760, 600)):
        super(Frame, self).__init__(parent, title=title, size=size, style=self.custom_style)
        self.Center()
        self.panel = wx.Panel(self, style=wx.SUNKEN_BORDER)
        self.panel.SetBackgroundColour(self.beige)

        self.SetIcon(wx.Icon(wx.Bitmap("icon.png")))
        self.preferences = preferences
        self.patch = preferences["patch"]

        self.cat_boxes = []
        self.saves_boxes = []
        self.buttons = []
        self.temporary_scenes = {}

        file_menu = wx.Menu()
        changeGameFolder_button = file_menu.Append(wx.ID_ANY, "Change game data folder")
        # TODO: addCategory_button = file_menu.Append(wx.ID_ANY, "Add new category")

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

        file_menu.AppendSeparator()
        exit_button = file_menu.Append(wx.ID_EXIT, 'Exit')
        self.Bind(wx.EVT_MENU, self.quit, exit_button)
        self.Bind(wx.EVT_MENU, self.switch_1221, self.patch_1221_button)
        self.Bind(wx.EVT_MENU, self.switch_cp, self.patch_cp_button)
        self.Bind(wx.EVT_MENU, self.select_folder, changeGameFolder_button)

        self.menu = wx.MenuBar()
        self.menu.Append(file_menu, "&Settings")
        self.SetMenuBar(self.menu)

        self.text1221 = wx.StaticText(self.panel, label="Savestates for Patch 1.2.2.1")
        self.text1221.SetFont(self.font1); self.text1221.Centre(wx.HORIZONTAL); self.text1221.Hide()
        self.textCP = wx.StaticText(self.panel, label="Savestates for Current Patch")
        self.textCP.SetFont(self.font1); self.textCP.Centre(wx.HORIZONTAL); self.textCP.Hide()

        self.page_box = wx.ComboBox(self.panel, size=(100, 30), pos=(10, 45), style=wx.CB_READONLY)
        self.page_box.Bind(wx.EVT_COMBOBOX, self.onPageSelect)
        self.page_box.AppendItems([f"Page {n}" for n in range(10)]); self.page_box.SetSelection(0)

        wx.StaticText(self.panel, label="Category", pos=(155, 50)).SetFont(self.font.MakeBold())
        wx.StaticText(self.panel, label="Scene", pos=(390, 50)).SetFont(self.font)

        if self.patch == "1221":
            self.ss_path = "savestates\\1221"
            self.current_categories = os.listdir(self.ss_path)
            self.current_path = f"{preferences['path']}\\Savestates-1221\\0"
            self.text1221.Show()
            self.textCP.Hide()
        else:
            self.ss_path = "savestates\\CP"
            self.current_categories = os.listdir(self.ss_path)
            self.current_path = f"{preferences['path']}\\DebugModData\\Savestates Current Patch\\0"
            self.text1221.Hide()
            self.textCP.Show()

        for ss in range(10):
            text = wx.StaticText(self.panel, label=f"Savestate {ss}:", pos=(10, 70+43*ss))
            text.SetFont(self.font2)
            category_box = wx.ComboBox(self.panel, size=(130, 30), pos=(120, 70+43*ss),
                                       style=wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SORT)
            savestate_box = wx.ComboBox(self.panel, size=(300, 30), pos=(275, 70+43*ss),
                                        style=wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SORT)
            button = wx.Button(self.panel, label=f"Add savestate as", size=(130, 35), pos=(600, 65+43*ss))

            category_box.Disable()
            savestate_box.Disable()
            category_box.box_id = savestate_box.box_id = ss
            category_box.Bind(wx.EVT_COMBOBOX, self.onCategorySelect)
            savestate_box.Bind(wx.EVT_COMBOBOX, self.onSceneSelect)
            self.cat_boxes.append(category_box)
            self.saves_boxes.append(savestate_box)

            button.button_id = ss
            button.Bind(wx.EVT_BUTTON, self.button_handler)
            button.Disable()
            self.buttons.append(button)

        self.apply_changes = wx.Button(self.panel, label=f"Apply savestates", pos=(280, 500))
        self.cancel = wx.Button(self.panel, label=f"Cancel", pos=(400, 500))
        self.apply_changes.Bind(wx.EVT_BUTTON, self.overwrite); self.cancel.Bind(wx.EVT_BUTTON, self.revert)
        self.apply_changes.Disable(); self.cancel.Disable()

        self.Bind(wx.EVT_CLOSE, self.quit)
        self.Show()

    def load(self):
        self.Freeze()
        for box in range(10):
            savestate = os.path.join(self.current_path, f"savestate{box}.json")
            if os.path.exists(savestate):
                with open(savestate) as file:
                    temp = json.load(file)
                    if "category" in temp:
                        category = temp["category"]
                    else:
                        category = "Unknown"
                    scene = temp["saveStateIdentifier"]
                self.buttons[box].Enable()
            else:
                category = "Unknown"
                scene = ""
                self.buttons[box].Disable()

            if category in self.current_categories:
                cat_choices = self.current_categories
                saves_choices = [*map(lambda x: x[:-5], os.listdir(f"savestates\\{category}"))]

            else:
                cat_choices = [category, *self.current_categories]
                saves_choices = [scene]

            cat_box = self.cat_boxes[box]
            save_box = self.saves_boxes[box]
            cat_box.Clear(); cat_box.Enable()
            cat_box.AppendItems(cat_choices); cat_box.SetValue(category)
            save_box.Clear(); save_box.Enable()
            save_box.AppendItems(saves_choices); save_box.SetValue(scene)
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

    def onCategorySelect(self, evt):
        choice = evt.GetEventObject()
        self.update_box(choice.box_id, choice.Value)

    def onSceneSelect(self, evt):
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
        dialog = Dialog(self, button_id, self.current_categories)
        dialog.ShowModal()

    def path_error(self):
        error = wx.MessageDialog(self, caption="Error!", style=wx.OK | wx.CANCEL | wx.ICON_WARNING,
                                 message="The Hollow Knight save data folder couldn't be found! \nPlease select it manually!")
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
                self.preferences['path'] = new_path
                self.current_path = new_path
                with open("game_data.json", 'w') as file:
                    json.dump(self.preferences, file)
                self.load()

    def switch_1221(self, evt):
        self.preferences["patch"] = "1221"
        self.ss_path = "savestates\\1221"
        self.current_categories = os.listdir(self.ss_path)
        self.current_path = f"{self.preferences['path']}\\Savestates-1221\\0"
        self.page_box.SetSelection(0)
        self.patch_1221_button.Enable(False)
        self.patch_cp_button.Enable()
        self.text1221.Show()
        self.textCP.Hide()
        self.load()

    def switch_cp(self, evt):
        self.preferences["patch"] = "CP"
        self.ss_path = "savestates\\CP"
        self.current_categories = os.listdir(self.ss_path)
        self.current_path = f"{self.preferences['path']}\\DebugModData\\Savestates Current Patch\\0"
        self.page_box.SetSelection(0)
        self.patch_1221_button.Enable()
        self.patch_cp_button.Enable(False)
        self.text1221.Hide()
        self.textCP.Show()
        self.load()

    def onPageSelect(self, evt):
        page = evt.GetEventObject().GetCurrentSelection()
        self.current_path = f"{self.current_path[:-1]}{page}"
        self.revert()

    def quit(self, evt):
        with open("game_data.json", 'w') as file:
            json.dump(self.preferences, file)
        self.Destroy()
        sys.exit()


class Dialog(wx.Dialog):
    def __init__(self, parent, ss_id, categories, title="Add savestate as", size=(400, 200)):
        super(Dialog, self).__init__(parent, title=title, size=size, style=wx.CAPTION | wx.CLOSE_BOX)
        self.Centre()
        self.ss_id = ss_id
        self.parent = parent
        small_panel = wx.Panel(self); small_panel.SetBackgroundColour('white')

        wx.StaticText(small_panel, label="Select category:", pos=(10, 35)).SetFont(Frame.font)
        wx.StaticText(small_panel, label="Enter scene name:", pos=(10, 75)).SetFont(Frame.font)
        self.category_choice = wx.ComboBox(small_panel, pos=(150, 35), size=(200, 100),
                                           style=wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SORT)
        self.category_choice.AppendItems(categories)
        self.new_name = wx.TextCtrl(small_panel, pos=(150, 75), size=(200, 25))
        self.ok_button = wx.Button(small_panel, label="Ok", pos=(130, 120), name="ok")
        self.cancel_button = wx.Button(small_panel, label="Cancel", pos=(220, 120), name="cancel")

        self.ok_button.Bind(wx.EVT_BUTTON, self.onButton); self.ok_button.Disable()
        self.cancel_button.Bind(wx.EVT_BUTTON, self.onButton)
        self.category_choice.Bind(wx.EVT_COMBOBOX, self.onModify)
        self.new_name.Bind(wx.EVT_TEXT, self.onModify)

    def onModify(self, evt):
        if self.new_name.GetValue() and self.category_choice.GetValue():
            self.ok_button.Enable()
        else:
            self.ok_button.Disable()

    def onButton(self, evt):
        if evt.GetEventObject().GetName() == "ok":
            new_cat = self.category_choice.GetValue(); new_scene = self.new_name.GetValue()
            new_path = f"savestates\\{new_cat}\\{new_scene}.json"
            if os.path.exists(new_path):
                if wx.MessageDialog(self, caption="This savestate already exists!",
                                    message="Do you want to overwrite the savestate with the same name?",
                                    style=wx.YES_NO | wx.ICON_WARNING).ShowModal() == wx.ID_NO: return

            with open(f"{self.parent.current_path}\\savestate{self.ss_id}.json") as file:
                temp = json.load(file)
                temp["saveStateIdentifier"] = new_scene
            with open(new_path, "w") as file:
                json.dump(temp, file, indent=4)

            par = self.GetParent()
            par.load()
            par.cat_boxes[self.ss_id].SetValue(new_cat)
            par.update_box(self.ss_id, new_cat)
            par.saves_boxes[self.ss_id].SetValue(new_scene)
        self.Destroy()
