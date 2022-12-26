from wx.adv import EditableListBox
import os, sys, json, wx


class Frame(wx.Frame):
    custom_style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
    font = wx.Font(); font.SetFaceName("Constantia"); font.SetPointSize(12)
    font1 = wx.Font(); font1.SetFaceName("Gabriola"); font1.Scale(3); font1.MakeBold()
    font2 = wx.Font(); font2.SetFaceName("Constantia"); font2.SetPointSize(13); font2.MakeBold().MakeItalic()
    beige = (249, 247, 223, 1)

    def __init__(self, settings, parent=None, title="Hollow Knight Savestates Manager", size=(760, 650)):
        super().__init__(parent, title=title, size=size, style=self.custom_style)
        self.Center()
        self.panel = wx.Panel(self, style=wx.SUNKEN_BORDER)
        self.panel.SetBackgroundColour(self.beige)

        self.SetIcon(wx.Icon(wx.Bitmap("icon.png")))
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
        self.text1221.SetFont(self.font1)
        if self.text1221.GetFont().GetFaceName() == "Gabriola":
            self.text1221.SetPosition((0, -10))
        self.text1221.Centre(wx.HORIZONTAL)
        self.text1221.Hide()

        self.textCP = wx.StaticText(self.panel, label="Savestates for Current Patch")
        self.textCP.SetFont(self.font1)
        if self.textCP.GetFont().GetFaceName() == "Gabriola":
            self.textCP.SetPosition((0, -10))
        self.textCP.Centre(wx.HORIZONTAL)
        self.textCP.Hide()

        self.page_box = wx.ComboBox(self.panel, size=(100, 30), pos=(10, 70), style=wx.CB_READONLY)
        self.page_box.Bind(wx.EVT_COMBOBOX, self.onPageSelect)
        self.page_box.AppendItems([f"Page {n}" for n in range(10)])
        self.page_box.SetSelection(0)

        wx.StaticText(self.panel, label="Category", pos=(150, 75)).SetFont(self.font)
        wx.StaticText(self.panel, label="Scene", pos=(390, 75)).SetFont(self.font)

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
            text.SetFont(self.font2)
            category_box = wx.ComboBox(self.panel, size=(130, 30), pos=(120, 100+43*ss), style=style)
            savestate_box = wx.ComboBox(self.panel, size=(300, 30), pos=(275, 100+43*ss), style=style)
            button = wx.Button(self.panel, label=f"Add as new savestate", size=(130, 35), pos=(600, 95+43*ss))

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

    def onCategorySelect(self, evt):
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

    def onPageSelect(self, evt):
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


class ELB(EditableListBox):
    def __init__(self, parent, label, pos, size, style):
        super().__init__(parent, label=label, pos=pos, size=size, style=style)
        self.grandparent = parent.GetParent()
        self.control = self.GetListCtrl()
        self.label = label
        self.control.DeleteItem(0)

        new = self.GetNewButton()
        edit = self.GetEditButton()
        delete = self.GetDelButton()
        self.IsMakingNew = False

        if new is not None:
            temp = new.Position
            new.SetPosition(edit.Position)
            edit.SetPosition(temp)
            new.Bind(wx.EVT_BUTTON, self.onNew)
        edit.Bind(wx.EVT_BUTTON, self.onEdit)
        delete.Bind(wx.EVT_BUTTON, self.onDelete)

        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.endEdit)

    def SetStrings(self, strings):
        self.control.DeleteAllItems()
        for s in strings:
            self.control.Append([s])

    def onNew(self, evt):
        self.IsMakingNew = True
        self.control.Append(["New Category"])
        newest = self.control.GetItemCount()-1
        self.control.EditLabel(newest)

    def onEdit(self, evt):
        to_edit = self.control.GetFirstSelected()
        self.control.EditLabel(to_edit)

    def endEdit(self, evt):
        box = evt.GetEventObject()
        current_item = box.GetFirstSelected()
        previous_name = box.GetItemText(current_item)
        new_name = box.GetEditControl().GetValue()
        found = box.FindItem(-1, new_name)
        main_path = self.grandparent.main_path
        category_path = self.grandparent.current_category

        if not new_name or (found != wx.NOT_FOUND and found != current_item):
            evt.Veto()
            if new_name:
                message = "The entry cannot be given this name as it is already present in the list!"
                if new_name == "New Category":
                    adjust = sum("New Category" in s for s in self.GetStrings())
                    adjusted_name = f"New Category ({adjust})"
                    box.SetItemText(current_item, adjusted_name)
                    os.mkdir(f"{main_path}\\{adjusted_name}")
                    self.IsMakingNew = False
                    return
            else:
                message = "The entry cannot be given an empty name!"
            wx.MessageDialog(self, message, "Error!", wx.OK).ShowModal()

        elif self.IsMakingNew:
            os.mkdir(f"{main_path}\\{new_name}")
            self.IsMakingNew = False

        elif self.label == "Categories":
            if previous_name == new_name:
                return
            new_path = f"{main_path}\\{new_name}"
            os.rename(category_path, new_path)
            progress = wx.ProgressDialog("Updating...", "Please wait until the process is finished")
            for scene in os.listdir(new_path):
                progress.Pulse()
                with open(f"{new_path}\\{scene}")as file:
                    temp = json.load(file)
                    temp["category"] = new_name
                with open(f"{new_path}\\{scene}", "w")as file:
                    json.dump(temp, file, indent=4)
            self.grandparent.current_category = new_path
            self.grandparent.Raise()

        else:
            new_path = f"{category_path}\\{new_name}.json"
            os.rename(f"{category_path}\\{previous_name}.json", new_path)
            with open(new_path) as file:
                temp = json.load(file)
                temp["saveStateIdentifier"] = new_name
            with open(new_path, "w") as file:
                json.dump(temp, file, indent=4)

    def onDelete(self, evt):
        to_delete = self.control.GetFirstSelected()
        if self.label == "Categories":
            message = "Are you sure you want to delete this entry?\nAll savestates within this category will be eliminated!\nThis action is irreversible!"
        else:
            message = "Are you sure you want to delete this entry?\nThis action is irreversible!"
        confirm = wx.MessageDialog(self, message, "Warning!", wx.ICON_WARNING | wx.OK | wx.CANCEL)

        if confirm.ShowModal() == wx.ID_OK:
            category_path = self.grandparent.current_category
            if self.label == "Categories":
                for file in os.listdir(category_path):
                    os.remove(f"{category_path}\\{file}")
                os.rmdir(category_path)
            else:
                scene = self.control.GetItemText(to_delete)
                os.remove(f"{category_path}\\{scene}.json")

            self.control.DeleteItem(to_delete)
            self.control.Select(0)


class ManageDialog(wx.Dialog):
    def __init__(self, parent, title="Edit savestates", size=(430, 480)):
        super().__init__(parent, title=title, size=size, style=wx.CAPTION | wx.CLOSE_BOX)
        self.Centre()

        self.main_path = parent.ss_path
        self.current_category = None
        small_panel = wx.Panel(self, style=wx.SUNKEN_BORDER)
        small_panel.SetBackgroundColour(Frame.beige)

        style_1 = wx.adv.EL_DEFAULT_STYLE | wx.adv.EL_NO_REORDER
        style_2 = wx.adv.EL_ALLOW_EDIT | wx.adv.EL_ALLOW_DELETE | wx.adv.EL_NO_REORDER
        self.category_list = ELB(small_panel, "Categories", (10, 10), (150, 170), style_1)
        self.category_list.SetStrings(parent.current_categories)
        self.category_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onCategorySelect)
        self.category_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onCategoryDeselect)

        self.scenes_list = ELB(small_panel, "Scenes", (180, 10), (220, 400), style_2)
        self.scenes_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSceneselect)

    def onCategorySelect(self, evt):
        control = evt.GetEventObject()
        selected_index = control.GetFirstSelected()
        selection = control.GetItemText(selected_index)
        self.category_list.GetDelButton().Enable()
        self.category_list.GetEditButton().Enable()
        selection_path = f"{self.main_path}\\{selection}"
        if os.path.exists(selection_path):
            self.current_category = selection_path
            current_scenes = [*map(lambda x: x[:-5], os.listdir(self.current_category))]
        else:
            current_scenes = []
        self.scenes_list.SetStrings(current_scenes)
        self.scenes_list.GetDelButton().Disable()
        self.scenes_list.GetEditButton().Disable()

    def onCategoryDeselect(self, evt):
        self.scenes_list.control.DeleteAllItems()
        self.scenes_list.GetDelButton().Disable()
        self.scenes_list.GetEditButton().Disable()

    def onSceneselect(self, evt):
        self.scenes_list.GetDelButton().Enable()
        self.scenes_list.GetEditButton().Enable()


class AddDialog(wx.Dialog):
    def __init__(self, parent, ss_id, title="Add new savestate", size=(400, 200)):
        super().__init__(parent, title=title, size=size, style=wx.CAPTION | wx.CLOSE_BOX)
        self.Centre()
        self.parent = parent
        self.ss_id = ss_id
        self.parent = parent

        small_panel = wx.Panel(self, style=wx.SUNKEN_BORDER)
        small_panel.SetBackgroundColour(Frame.beige)
        wx.StaticText(small_panel, label="Select category:", pos=(30, 35)).SetFont(Frame.font)
        wx.StaticText(small_panel, label="Enter scene name:", pos=(15, 75)).SetFont(Frame.font)

        style = wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SORT
        self.category_choice = wx.ComboBox(small_panel, pos=(155, 35), size=(200, 100), style=style)
        self.category_choice.AppendItems(self.parent.current_categories)
        self.new_name = wx.TextCtrl(small_panel, pos=(155, 75), size=(200, 25))
        self.ok_button = wx.Button(small_panel, label="Ok", pos=(130, 120), name="ok")
        self.cancel_button = wx.Button(small_panel, label="Cancel", pos=(220, 120), name="cancel")

        self.ok_button.Bind(wx.EVT_BUTTON, self.onButton)
        self.ok_button.Disable()
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
