import os
import json
import wx
from frame import Frame

default_data = {"path": "C:\\Users\\{}\\AppData\\LocalLow\\Team Cherry\\Hollow Knight", "patch": "1221"}
username = os.environ.get("USERNAME")

# The path and patch selected are saved into "settings" file
with open("settings.json") as file:
    data = json.load(file)
    base_path = os.path.abspath(data["path"].format(username))
    data["path"] = base_path
    patch = data["patch"]
    # Todo: add reset to default condition

if __name__ == "__main__":
    main_app = wx.App()
    main_window = Frame(data)
    if os.path.exists(base_path):
        main_window.load()
    else:
        # The user is prompted with a dialog to choose a new HK save data directory if the default one is not found
        main_window.path_error()
    main_app.MainLoop()
