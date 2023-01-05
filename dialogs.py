import os
import json
import wx
from wx.adv import EditableListBox
from aesthetics import *


class ELB(EditableListBox):
    """
    This piece of trash was supposed to be a shortcut compared to making a custom ListBox object with "new", "edit" and
    "delete" buttons bound to the correct functionalities. Well it turns out that would have been a far better way
    because this class uses ListCtrl on the inside which is absolute garbage. I had to override everything to make it
    work properly, and now it's a complete garbled up mess. Screw this thing, do not ever use it for your projects.
    """
    def __init__(self, parent, label, pos, size, style):
        super().__init__(parent, label=label, pos=pos, size=size, style=style)
        self.grandparent = parent.GetParent()
        self.control = self.GetListCtrl()
        self.label = label
        self.control.DeleteItem(0)  # The first element has to be deleted or the whole thing breaks

        self.new = self.GetNewButton()
        if self.label == "Scenes":
            self.new.Disable()
        self.edit = self.GetEditButton()
        self.delete = self.GetDelButton()
        self.IsMakingNew = False  # We use this variable as a flag to know when a category is being edited

        # Repositioning and rebinding the buttons
        if self.new is not None:
            temp = self.new.Position
            self.new.SetPosition(self.edit.Position)
            self.edit.SetPosition(temp)
            self.new.Bind(wx.EVT_BUTTON, self.on_new)
        self.edit.Bind(wx.EVT_BUTTON, self.on_start_edit)
        self.delete.Bind(wx.EVT_BUTTON, self.on_delete)

        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.on_end_edit)

    def SetStrings(self, strings):
        """
        This method overrides the appending of items to the ListCtrl because, guess what, the default one is broken.

        :param strings: list of strings
        """
        self.grandparent.Freeze()
        self.control.DeleteAllItems()
        for s in strings:
            self.control.Append([s])
        self.grandparent.Thaw()

    def on_new(self, evt):
        """
        This method overrides the handling of the "new" button.
        In the category control a new item is appended and named using the EditLabel method,
        in the scene control a file dialog is opened and the files selected copied into the savestates folder.
        """
        if self.label == "Categories":
            self.IsMakingNew = True
            self.control.Append(["New Category"])
            newest = self.control.GetItemCount()-1
            self.control.EditLabel(newest)

        else:
            # Prompting a multiple chioce file dialog to select savestates to add
            wcard = "JSON files (*.json)|*.json"
            fdial_style = wx.FD_OPEN | wx.FD_MULTIPLE
            message = "Select savestates to add to this category"
            with wx.FileDialog(self, message, wildcard=wcard, style=fdial_style) as selection:
                if selection.ShowModal() == wx.ID_CANCEL:
                    return
                files = selection.GetPaths()
                category = self.grandparent.current_category

                # Manipulating the names of the files selected so that they are unique (also adding a progress bar)
                progress = wx.ProgressDialog("Copying the files...", "Please wait until the process is finished")
                for file in files:
                    progress.Pulse()
                    temp_name = file.split("\\")[-1]
                    adjust = sum(temp_name[:-5] in s for s in self.GetStrings())
                    name = f"{temp_name[:-5]} ({adjust})" if adjust else temp_name[:-5]
                    filename = f"{name}.json"

                    # Adding the files selected to the control and copying them into the right folder
                    self.control.Append([name])
                    with open(file) as ss_file:
                        temp = json.load(ss_file)
                        temp["category"] = category.split("\\")[-1]
                        temp["saveStateIdentifier"] = name
                    with open(f"{category}\\{filename}", "w") as new_file:
                        json.dump(temp, new_file, indent=4)
                self.grandparent.Raise()

    def on_start_edit(self, evt):
        """
        This method overrides the handling of the "Edit" button, as the default one doesn't recognize the selected item.
        Seriously, how's this class so screwed up?
        """
        to_edit = self.control.GetFirstSelected()
        self.control.EditLabel(to_edit)

    def on_end_edit(self, evt):
        """
        This method overrides the "wx.EVT_LIST_END_LABEL_EDIT" event in order to manipulate the user input
        when it is not valid and copying the json files into the savestates directory when required.
        """
        box = evt.GetEventObject()
        current_item = box.GetFirstSelected()
        previous_name = box.GetItemText(current_item)
        new_name = box.GetEditControl().GetValue()
        found = box.FindItem(-1, new_name)
        main_path = self.grandparent.main_path
        category_path = self.grandparent.current_category

        # Checking for uniqueness and emptiness of the name in input, defaulting to other options when it happens
        if not new_name or (found != wx.NOT_FOUND and found != current_item):
            evt.Veto()
            if new_name:
                adjust = sum(new_name in s for s in self.GetStrings())
                new_name = f"{new_name} ({adjust})"
                new_path = f"{main_path}\\{new_name}"
                box.SetItemText(current_item, new_name)
                os.mkdir(new_path)
                self.IsMakingNew = False

                # Changing the current category according to the new selection
                self.grandparent.current_category = new_path

        # I'm not entirely sure why I repeated here the previous piece of code but the program breaks without it
        elif self.IsMakingNew:
            os.mkdir(f"{main_path}\\{new_name}")
            self.IsMakingNew = False
            self.grandparent.current_category = f"{main_path}\\{new_name}"

        # Handling the renaming of the folder (only when the name actually changed)
        elif self.label == "Categories":
            if previous_name == new_name:
                return
            new_path = f"{main_path}\\{new_name}"
            os.rename(category_path, new_path)
            progress = wx.ProgressDialog("Updating...", "Please wait until the process is finished")

            # Moving all files to the new location when a category is renamed
            for scene in os.listdir(new_path):
                progress.Pulse()
                with open(f"{new_path}\\{scene}")as file:
                    temp = json.load(file)
                    temp["category"] = new_name
                with open(f"{new_path}\\{scene}", "w")as file:
                    json.dump(temp, file, indent=4)
            self.grandparent.current_category = new_path
            self.grandparent.Raise()

        # Renaming a single savestate
        else:
            new_path = f"{category_path}\\{new_name}.json"
            os.rename(f"{category_path}\\{previous_name}.json", new_path)
            with open(new_path) as file:
                temp = json.load(file)
                temp["saveStateIdentifier"] = new_name
            with open(new_path, "w") as file:
                json.dump(temp, file, indent=4)

    def on_delete(self, evt):
        """
        This method handles the press of the "Delete" button.
        It removes the selected element from the control and deletes it from the computer.
        """

        # Setting up the message of the dialog based on the typeof selection
        to_delete = self.control.GetFirstSelected()
        message = "Are you sure you want to delete this entry?\n"
        if self.label == "Categories":
            message += "All savestates within this category will be eliminated!\n"
        message += "This action is irreversible!"

        with wx.MessageDialog(self, message, "Warning!", wx.ICON_WARNING | wx.OK | wx.CANCEL) as confirm:
            if confirm.ShowModal() == wx.ID_OK:
                category_path = self.grandparent.current_category

                # Deleting the folder and every file in it when the selection is a category,
                # deleting only the selected savestate otherwise
                if self.label == "Categories":
                    for file in os.listdir(category_path):
                        os.remove(f"{category_path}\\{file}")
                    os.rmdir(category_path)
                else:
                    scene = self.control.GetItemText(to_delete)
                    os.remove(f"{category_path}\\{scene}.json")

            # Deleting the element from the control and shifting the selection onto the next one
            self.control.DeleteItem(to_delete)
            count = self.control.GetItemCount()
            next_item = to_delete if to_delete < count else to_delete - 1
            next_text = self.control.GetItemText(next_item)
            next_path = self.grandparent.main_path
            self.control.Select(next_item)

            # Changing the current category according to the new selection
            self.grandparent.current_category = f"{next_path}\\{next_text}"


class ManageDialog(wx.Dialog):
    """
    Dialog subclass used to hold the "ELB" objects responsible for the creation, editing and deletion
    of both categories and savestates.
    """
    def __init__(self, parent, title="Edit savestates", size=(430, 480)):
        super().__init__(parent, title=title, size=size, style=dial_style)
        self.Centre()

        # Initializing panel and important attributes
        self.main_path = parent.ss_path
        self.current_category = None
        small_panel = wx.Panel(self, style=wx.SUNKEN_BORDER)
        small_panel.SetBackgroundColour(bground_color)

        # Creating and binding the "ELB" objects
        self.category_list = ELB(small_panel, "Categories", (10, 10), (150, 170), listbox_style)
        self.category_list.SetStrings(parent.current_categories)
        self.category_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_category_select)
        self.category_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_category_deselect)
        self.scenes_list = ELB(small_panel, "Scenes", (180, 10), (220, 400), listbox_style)
        self.scenes_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_scene_select)
        self.scenes_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_scene_deselect)

    def on_category_select(self, evt):
        """
        This method handles the selection of an item from the category box.
        Enables the required buttons and populates the scene box.
        """
        control = evt.GetEventObject()
        selected_index = control.GetFirstSelected()
        selection = control.GetItemText(selected_index)
        self.category_list.delete.Enable()
        self.category_list.edit.Enable()
        self.scenes_list.new.Enable()
        selection_path = f"{self.main_path}\\{selection}"

        # We populate the scenes box with savestates only if the path of the corresponding categories exists
        # (This might be a little overkill after the latest refactoring and could be deleted later)
        if os.path.exists(selection_path):
            self.current_category = selection_path
            category_path = os.listdir(self.current_category)
            filtered_files = filter(lambda x: x[-4:].lower() == "json", category_path)
            current_scenes = [*map(lambda x: x[:-5], filtered_files)]
        else:
            current_scenes = []
        self.scenes_list.SetStrings(current_scenes)
        self.scenes_list.edit.Disable()
        self.scenes_list.delete.Disable()

    def on_category_deselect(self, evt):
        """
        This method handles the deselection of an item from the category box.
        Disables the affected buttons and empties the scene box.
        """
        self.category_list.edit.Disable()
        self.category_list.delete.Disable()
        self.scenes_list.control.DeleteAllItems()
        self.scenes_list.new.Disable()
        self.scenes_list.edit.Disable()
        self.scenes_list.delete.Disable()

    def on_scene_select(self, evt):
        """
        This method handles the selection of an item from the scene box, enabling the affected buttons.
        """
        self.scenes_list.delete.Enable()
        self.scenes_list.edit.Enable()

    def on_scene_deselect(self, evt):
        """
        This method handles the deselection of an item from the scene box, disabling the affected buttons.
        """
        self.scenes_list.edit.Disable()
        self.scenes_list.delete.Disable()


class AddDialog(wx.Dialog):
    """
    Dialog subclass that handles the creation of new savestates
    based of the ones already present in the category and scene boxes.
    """
    def __init__(self, parent, ss_id, title="Add new savestate", size=(400, 200)):
        super().__init__(parent, title=title, size=size, style=dial_style)
        self.Centre()
        self.parent = parent
        self.ss_id = ss_id
        self.parent = parent

        # Initializing panel and labels
        small_panel = wx.Panel(self, style=wx.SUNKEN_BORDER)
        small_panel.SetBackgroundColour(bground_color)
        wx.StaticText(small_panel, label="Select category:", pos=(30, 35)).SetFont(small_font)
        wx.StaticText(small_panel, label="Enter scene name:", pos=(15, 75)).SetFont(small_font)

        # Creating the boxes and buttons
        self.category_choice = wx.ComboBox(small_panel, pos=(155, 35), size=(200, 100), style=combo_style)
        self.category_choice.AppendItems(self.parent.current_categories)
        self.new_name = wx.TextCtrl(small_panel, pos=(155, 75), size=(200, 25))
        self.ok_button = wx.Button(small_panel, label="Ok", pos=(130, 120), name="ok")
        self.cancel_button = wx.Button(small_panel, label="Cancel", pos=(220, 120), name="cancel")

        # Binding the widgets previously created
        self.ok_button.Bind(wx.EVT_BUTTON, self.on_button_press)
        self.ok_button.Disable()
        self.cancel_button.Bind(wx.EVT_BUTTON, self.on_button_press)
        self.category_choice.Bind(wx.EVT_COMBOBOX, self.on_modify)
        self.new_name.Bind(wx.EVT_TEXT, self.on_modify)

    def on_modify(self, evt):
        """
        This method simply enables and disables the "OK" button when needed.
        """
        if self.new_name.GetValue() and self.category_choice.GetValue():
            self.ok_button.Enable()
        else:
            self.ok_button.Disable()

    def on_button_press(self, evt):
        """
        This method handles the press of both the OK and Cancel buttons.
        When the Cancel button is selected no changes are saved before the dialog is destroyed.
        """

        # The information submitted in the boxes is retrieved
        if evt.GetEventObject().GetName() == "ok":
            new_scene = self.new_name.GetValue()
            new_cat = self.category_choice.GetValue()
            new_path = f"savestates\\{self.parent.patch}\\{new_cat}\\{new_scene}.json"

            # If a savestate with the name chosen already exists the user is prompted with the option of replacing it
            if os.path.exists(new_path):
                message = "Do you want to overwrite the savestate with the same name?"
                style = wx.YES_NO | wx.ICON_WARNING
                dialog = wx.MessageDialog(self, caption="This savestate already exists!", message=message, style=style)
                if dialog.ShowModal() == wx.ID_NO:
                    return

            # The savestate category and scene information are updated
            with open(f"{self.parent.current_path}\\savestate{self.ss_id}.json") as file:
                temp = json.load(file)
                temp["category"] = new_cat
                temp["saveStateIdentifier"] = new_scene

            # The new savestate is saved both in the savestate folder and the HK game data folder
            with open(f"{self.parent.current_path}\\savestate{self.ss_id}.json", "w") as file:
                json.dump(temp, file, indent=4)
            with open(new_path, "w") as file:
                json.dump(temp, file, indent=4)

            self.parent.load()
        self.Destroy()
