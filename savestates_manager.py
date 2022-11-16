import json, os, wx, sys

username = os.environ.get("USERNAME")
with open("game_data_folder.txt") as file:
    full_path = file.read().format(username)
all_categories = os.listdir("savestates")


class Frame(wx.Frame):
    custom_style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
    font = wx.Font(); font.SetPointSize(10)
    font2 = wx.Font(); font2.SetPointSize(12); font2.MakeBold().MakeItalic()

    def __init__(self, parent=None, title="Hollow Knight Savestates Manager", size=(750, 480)):
        super(Frame, self).__init__(parent, title=title, size=size, style=self.custom_style)
        self.Center()
        self.panel = wx.Panel(self); self.panel.SetBackgroundColour('white')
        self.SetIcon(wx.Icon(wx.Bitmap("icon.png")))
        self.cat_boxes = []
        self.saves_boxes = []
        self.buttons = []
        self.temporary_scenes = dict()
        wx.StaticText(self.panel, label="Category", pos=(122, 35)).SetFont(self.font.MakeBold())
        wx.StaticText(self.panel, label="Scene", pos=(272, 35)).SetFont(self.font.MakeBold())

        for ss in range(6):
            wx.StaticText(self.panel, label=f"Savestate {ss}:", pos=(15, 8+50*(ss+1))).SetFont(self.font2)
            category_box = wx.ComboBox(self.panel, pos=(120, 5+50*(ss+1)), size=(130, 35),
                                       style=wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SORT)

            savestate_box = wx.ComboBox(self.panel, pos=(270, 5+50*(ss+1)), size=(300, 65),
                                        style=wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SORT)

            button = wx.Button(self.panel, label=f"Add savestate as", pos=(585, 50*(ss+1)), size=(130, 35))

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

        self.apply_changes = wx.Button(self.panel, label=f"Apply savestates", pos=(270, 360))
        self.cancel = wx.Button(self.panel, label=f"Cancel", pos=(390, 360))
        self.apply_changes.Bind(wx.EVT_BUTTON, self.overwrite); self.cancel.Bind(wx.EVT_BUTTON, self.revert)
        self.apply_changes.Disable(); self.cancel.Disable()

        self.Bind(wx.EVT_CLOSE, self.quit)
        self.Show()

    def load(self):
        self.Freeze()
        for box in range(6):
            savestate = os.path.join(full_path, f"savestate{box}.json")
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

            if category in all_categories:
                cat_choices = all_categories
                saves_choices = [*map(lambda x: x[:-5], os.listdir(f"savestates\\{category}"))]

            else:
                cat_choices = [category, *all_categories]
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
            raw_list = os.listdir(f"savestates\\{text}")
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
        scene_path = f"savestates\\{corresponding_cat}\\{choice.Value}.json"
        self.temporary_scenes[choice_id] = scene_path
        self.apply_changes.Enable(); self.cancel.Enable(); self.buttons[choice_id].Enable()

    def overwrite(self, evt):
        for choice_id, scene_path in self.temporary_scenes.items():
            with open(scene_path) as file:
                current_ss = json.load(file)
            with open(f"{full_path}\\savestate{choice_id}.json", "w") as file:
                json.dump(current_ss, file, indent=4)
        self.apply_changes.Disable(); self.cancel.Disable()

    def revert(self, evt):
        self.load()
        self.apply_changes.Disable(); self.cancel.Disable()

    def button_handler(self, evt):
        button_id = evt.GetEventObject().button_id
        dialog = Dialog(self, button_id)
        dialog.ShowModal()

    def path_error(self):
        error = wx.MessageDialog(self, caption="Error!", style=wx.OK | wx.CANCEL | wx.ICON_WARNING,
                                 message="The folder containing the Hollow Knight savestates couldn't be found! \nPlease select it manually!")
        if error.ShowModal() == wx.ID_OK:
            new_path = self.select_folder()
            if new_path:
                with open("game_data_folder.txt", 'w') as path:
                    path.write(new_path)
                global full_path
                full_path = new_path
                self.load()


    def select_folder(self):
        dialog = wx.DirDialog(self, 'Select the Hollow Knight save data folder', style=wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            return dialog.GetPath()

    def quit(self, evt):
        sys.exit()


class Dialog(wx.Dialog):
    def __init__(self, parent, ss_id, title="Add savestate as", size=(400, 200)):
        super(Dialog, self).__init__(parent, title=title, size=size, style=wx.CAPTION | wx.CLOSE_BOX)
        self.Centre()
        self.ss_id = ss_id
        small_panel = wx.Panel(self); small_panel.SetBackgroundColour('white')

        wx.StaticText(small_panel, label="Select category:", pos=(10, 35)).SetFont(Frame.font)
        wx.StaticText(small_panel, label="Enter scene name:", pos=(10, 75)).SetFont(Frame.font)
        self.category_choice = wx.ComboBox(small_panel, pos=(150, 35), size=(200, 100),
                                           style=wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SORT)
        self.category_choice.AppendItems(all_categories)
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

            with open(f"{full_path}\\savestate{self.ss_id}.json") as file:
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


if __name__ == "__main__":
    app = wx.App()
    frame = Frame()
    if os.path.exists(full_path):
        frame.load()
    else:
        frame.path_error()
    app.MainLoop()