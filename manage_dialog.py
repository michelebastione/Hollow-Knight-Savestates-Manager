import os
import json
import wx
from wx.adv import EditableListBox
from aesthetics import bground_color


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
            new.Bind(wx.EVT_BUTTON, self.on_new)
        edit.Bind(wx.EVT_BUTTON, self.on_start_edit)
        delete.Bind(wx.EVT_BUTTON, self.on_delete)

        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.on_end_edit)

    def SetStrings(self, strings):
        self.control.DeleteAllItems()
        for s in strings:
            self.control.Append([s])

    def on_new(self, evt):
        self.IsMakingNew = True
        self.control.Append(["New Category"])
        newest = self.control.GetItemCount()-1
        self.control.EditLabel(newest)

    def on_start_edit(self, evt):
        to_edit = self.control.GetFirstSelected()
        self.control.EditLabel(to_edit)

    def on_end_edit(self, evt):
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

    def on_delete(self, evt):
        to_delete = self.control.GetFirstSelected()
        base_message = "Are you sure you want to delete this entry?\n"
        if self.label == "Categories":
            message = "All savestates within this category will be eliminated!\nThis action is irreversible!"
        else:
            message = "This action is irreversible!"
        confirm = wx.MessageDialog(self, f"{base_message}{message}", "Warning!", wx.ICON_WARNING | wx.OK | wx.CANCEL)

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
        small_panel.SetBackgroundColour(bground_color)

        style_1 = wx.adv.EL_DEFAULT_STYLE | wx.adv.EL_NO_REORDER
        style_2 = wx.adv.EL_ALLOW_EDIT | wx.adv.EL_ALLOW_DELETE | wx.adv.EL_NO_REORDER
        self.category_list = ELB(small_panel, "Categories", (10, 10), (150, 170), style_1)
        self.category_list.SetStrings(parent.current_categories)
        self.category_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_category_select)
        self.category_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_category_deselect)

        self.scenes_list = ELB(small_panel, "Scenes", (180, 10), (220, 400), style_2)
        self.scenes_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_scene_select)

    def on_category_select(self, evt):
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

    def on_category_deselect(self, evt):
        self.scenes_list.control.DeleteAllItems()
        self.scenes_list.GetDelButton().Disable()
        self.scenes_list.GetEditButton().Disable()

    def on_scene_select(self, evt):
        self.scenes_list.GetDelButton().Enable()
        self.scenes_list.GetEditButton().Enable()
