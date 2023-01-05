import os
import sys
import json
import wx
from dialogs import ManageDialog, AddDialog
from aesthetics import *


class Panel(wx.Panel):
    """
    This subclass exists solely because to draw an image with transparent background
    we need to override the EVT_PAINT handling of the Panel object.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ornament = wx.Image('ornament.png', wx.BITMAP_TYPE_PNG)
        x, y = self.ornament.GetSize()
        self.ornament.Rescale(x*0.7, y*0.7, wx.IMAGE_QUALITY_HIGH)
        self.Bind(wx.EVT_PAINT, self.paint)

    def paint(self, evt):
        """
        Overrides handling of EVT_PAINT to draw the image along with the background.
        """
        dc = wx.PaintDC(self)
        dc.DrawBitmap(wx.Bitmap(self.ornament), 135, 45)


class Frame(wx.Frame):
    """
    This subclass makes up the main window of the program where most of the savestates handling happens.
    """
    def __init__(self, settings, parent=None, title="Hollow Knight Savestates Manager", size=(760, 650)):
        super().__init__(parent, title=title, size=size, style=frame_style)
        self.Center()
        self.panel = Panel(self, style=wx.SUNKEN_BORDER)
        self.panel.SetBackgroundColour(bground_color)

        self.SetIcon(wx.Icon(wx.Bitmap("quill.png")))
        self.settings = settings
        self.patch = settings["patch"]

        # Containers to ease the handling of the many widgets on the frame
        self.cat_boxes = []
        self.saves_boxes = []
        self.buttons = []
        self.temporary_scenes = {}

        main_menu = wx.Menu()
        patch_submenu = wx.Menu()

        # switch-patch submenu initialization
        self.patch_1221_button = patch_submenu.Append(wx.ID_ANY, "Patch 1.2.2.1 Savestates")
        self.patch_cp_button = patch_submenu.Append(wx.ID_ANY, "Current Patch Savestates")
        if self.patch == "1221":
            self.patch_1221_button.Enable(False)
            self.patch_cp_button.Enable()
        else:
            self.patch_1221_button.Enable()
            self.patch_cp_button.Enable(False)

        # Adding elements to the menu
        main_menu.AppendSubMenu(patch_submenu, "Switch patches")
        edit_button = main_menu.Append(wx.ID_ANY, "Edit savestates")
        change_game_folder = main_menu.Append(wx.ID_ANY, "Change game data folder")
        main_menu.AppendSeparator()
        exit_button = main_menu.Append(wx.ID_EXIT, 'Exit')

        # Binding the elements of the menu
        self.Bind(wx.EVT_MENU, self.quit, exit_button)
        self.Bind(wx.EVT_MENU, self.switch_1221, self.patch_1221_button)
        self.Bind(wx.EVT_MENU, self.switch_cp, self.patch_cp_button)
        self.Bind(wx.EVT_MENU, self.select_folder, change_game_folder)
        self.Bind(wx.EVT_MENU, self.manage, edit_button)

        # Creating the menu bar
        self.menu = wx.MenuBar()
        self.menu.Append(main_menu, "&Settings")
        self.SetMenuBar(self.menu)

        # Title initialization
        self.text1221 = wx.StaticText(self.panel, label="Savestates for Patch 1.2.2.1")
        self.textCP = wx.StaticText(self.panel, label="Savestates for Current Patch")
        for title in (self.text1221, self.textCP):
            title.SetFont(title_font)
            if title.GetFont().GetFaceName() == "Gabriola":
                title.SetPosition((0, -10))
            title.Centre(wx.HORIZONTAL)
            title.Hide()

        # Creating the savestates page selection box
        self.page_box = wx.ComboBox(self.panel, size=(100, 30), pos=(10, 70), style=wx.CB_READONLY)
        self.page_box.Bind(wx.EVT_COMBOBOX, self.on_page_select)
        self.page_box.AppendItems([f"Page {n}" for n in range(10)])
        self.page_box.SetSelection(0)

        wx.StaticText(self.panel, label="Category", pos=(150, 95)).SetFont(small_font)
        wx.StaticText(self.panel, label="Scene", pos=(390, 95)).SetFont(small_font)

        # Title shown and savestates folder chosen based on the patch currently selected
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

        # Creating and binding the "Savestates" writings, the category and scene boxes, and the "Add" buttons
        for ss in range(10):
            text = wx.StaticText(self.panel, label=f"Savestate {ss}:", pos=(10, 120+43*ss))
            text.SetFont(list_font)
            category_box = wx.ComboBox(self.panel, size=(130, 30), pos=(120, 120+43*ss), style=combo_style)
            savestate_box = wx.ComboBox(self.panel, size=(300, 30), pos=(275, 120+43*ss), style=combo_style)
            button = wx.Button(self.panel, label=f"Add as new savestate", size=(130, 35), pos=(600, 115+43*ss))

            category_box.Disable()
            savestate_box.Disable()
            category_box.box_id = savestate_box.box_id = ss
            category_box.Bind(wx.EVT_COMBOBOX, self.on_category_select)
            savestate_box.Bind(wx.EVT_COMBOBOX, self.on_scene_select)
            self.cat_boxes.append(category_box)
            self.saves_boxes.append(savestate_box)

            button.button_id = ss
            button.Bind(wx.EVT_BUTTON, self.add)
            button.Disable()
            self.buttons.append(button)

        # Creation and binding of the "Apply" and "Cancel" buttons
        self.apply_changes = wx.Button(self.panel, label=f"Apply savestates", pos=(280, 550))
        self.cancel = wx.Button(self.panel, label=f"Cancel", pos=(400, 550))
        self.apply_changes.Bind(wx.EVT_BUTTON, self.overwrite)
        self.cancel.Bind(wx.EVT_BUTTON, self.revert)
        self.apply_changes.Disable()
        self.cancel.Disable()

        self.Bind(wx.EVT_CLOSE, self.quit)
        self.Show()

    def load(self):
        """
        This method reads the savestates present in the HK game data folder and fills the boxes with their information.
        It is called every time the savestates or their folder are manipulated in some capacity.
        The scene boxes and buttons are disabled at the beginning to be enabled when needed.
        """
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

            # Savestate #n information is prepared to be loaded into the boxes
            if os.path.exists(savestate):
                with open(savestate) as file:
                    temp = json.load(file)
                    if "category" in temp:
                        category = temp["category"]
                    scene = temp["saveStateIdentifier"]
                self.buttons[box].Enable()

                # The information is changed based on the existence of the category and the scene
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

            # The information is loaded into the boxes
            cat_box.Append(cat_choices)
            cat_box.SetValue(category)
            if category != "Unknown":
                save_box.Enable()
            save_box.Append(saves_choices)
            save_box.SetValue(scene)

        self.Thaw()

    def on_category_select(self, evt):
        """
        This method is called when an option is selected from one of the category boxes.
        It enables the "Cancel" button and calls the update_box method to let the user choose the savestates.
        If "Unknown" is selected nothing happens.
        """
        choice = evt.GetEventObject()
        box_id = choice.box_id
        value = choice.Value
        cat = self.cat_boxes[box_id]

        # The entry "Unknown" is deleted once another option is selected
        if "Unknown" in cat.GetStrings():
            if value == "Unknown":
                return
            cat.Clear()
            cat.AppendItems(self.current_categories)
            cat.SetValue(value)
        self.cancel.Enable()
        self.update_box(box_id, value)

    def on_scene_select(self, evt):
        """
        This method is called when an option is selected from one of the scene boxes.
        It adds the selection to the temporary_scenes dictionary from where it is either applied or reverted.
        All buttons are enabled.
        """
        choice = evt.GetEventObject()
        choice_id = choice.box_id
        corresponding_cat = self.cat_boxes[choice_id].Value
        scene_path = f"{self.ss_path}\\{corresponding_cat}\\{choice.Value}.json"
        self.temporary_scenes[choice_id] = scene_path
        self.apply_changes.Enable()
        self.cancel.Enable()
        self.buttons[choice_id].Enable()

    def update_box(self, box_id, category):
        """
        This method is called after the selection of an option from the category box
        for the purpose of updating the scene box list of options with the savestates relative to the category selected.
        """
        self.buttons[box_id].Disable()
        scene = self.saves_boxes[box_id]
        scene.Clear()
        scene.Enable()

        # The box is filled only if the category name is not empty
        if category:
            raw_list = os.listdir(f"{self.ss_path}\\{category}")
            filtered = filter(lambda x: x[-4:].lower() == "json", raw_list)
            pretty_list = [*map(lambda x: x[:-5], filtered)]
            scene.Enable()
            scene.Append(pretty_list)
        else:
            scene.Disable()

    def add(self, evt):
        """
        This method handles the press of the "Add savestate" button.
        The user is prompted with an instance of AddDialog to choose category and name of the new savestate.
        """
        button_id = evt.GetEventObject().button_id
        with AddDialog(self, button_id) as add_dialog:
            add_dialog.ShowModal()

    def overwrite(self, evt):
        """
        This method handles the press of the "Apply" button.
        The contents of the json files are copied into the HK savestates data folder
        """
        for choice_id, scene_path in self.temporary_scenes.items():
            category, savestate = scene_path.split("\\")[-2:]
            with open(scene_path) as file:
                current_ss = json.load(file)
            with open(f"{self.current_path}\\savestate{choice_id}.json", "w") as file:
                current_ss["saveStateIdentifier"] = savestate[:-5]
                current_ss["category"] = category
                json.dump(current_ss, file, indent=4)
        self.apply_changes.Disable()
        self.cancel.Disable()
        self.temporary_scenes.clear()

    def revert(self, evt=None):
        """
        This method gets called when the "Cancel" button is clicked, but can also be called without an event to handle.
        It reloads the current page disabling any unsaved changes previously made to the savestates.
        """
        self.load()
        self.apply_changes.Disable()
        self.cancel.Disable()
        self.temporary_scenes.clear()

    def on_page_select(self, evt):
        """
        This method is called when an option is selected from the savestates page box.
        The corresponding savestates are loaded and all unsaved changes disabled.
        """
        page = evt.GetEventObject().GetCurrentSelection()
        self.current_path = f"{self.current_path[:-1]}{page}"
        self.revert()

    def switch_1221(self, evt):
        """
        This method handles the selection of the 1221 patch from the "Swicth Patches" submenu.
        It updates the settings changing the subdirectory where to look savestates from
        and enables/disables the combination of 1221/CP buttons and titles.
        """
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
        """Same exact method as switch_1221 but handles the selection of the "CP" option instead."""
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

    def select_folder(self, evt=None):
        """
        This method is called either when the option "Change game data folder" is selected from the menu
        or subsequently the call of path_error when the HK save data folder cannot be found.
        It prompts the user with a dialog to choose a new directory for it.
        """
        with wx.DirDialog(self, 'Select the Hollow Knight save data folder', style=wx.FD_OPEN) as d_dialog:

            # The settings are updated only if a non empty directory is selected and the button "OK" is pressed
            if d_dialog.ShowModal() == wx.ID_OK:
                new_path = d_dialog.GetPath()
                if new_path:
                    self.settings['path'] = new_path
                    self.current_path = new_path
                    with open("settings.json", 'w') as file:
                        json.dump(self.settings, file)
                    self.load()

    def path_error(self):
        """
        This method gets called if the HK save data folder cannot be found at the start of the program.
        """
        message = "The Hollow Knight save data folder couldn't be found! \nPlease select it manually!"
        error = wx.MessageDialog(self, caption="Error!", style=error_style, message=message)
        if error.ShowModal() == wx.ID_OK:

            # The user is prompted with a dialog to choose a new directory for the HK save data
            self.select_folder()
            self.load()

    def manage(self, evt):
        """
        This method is called on the selection of the "Edit" option from the menu.
        To handle it, an instance of ManageDialog is created.
        """
        with ManageDialog(self) as manage_dialog:
            manage_dialog.ShowModal()

        # The categories are updated after modifications made in the ManageDialog
        self.current_categories = os.listdir(self.ss_path)
        self.load()

    def quit(self, evt):
        """
        This method handles the closing of the application.
        Before the window is destroyed, the current settings are saved.
        """
        with open("settings.json", 'w') as file:
            json.dump(self.settings, file)
        self.Destroy()
        sys.exit()
