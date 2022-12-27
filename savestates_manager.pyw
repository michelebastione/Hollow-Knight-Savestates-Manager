import os
import json
import wx
from frame import Frame

default_data = {"path": "C:\\Users\\{}\\AppData\\LocalLow\\Team Cherry\\Hollow Knight", "patch": "1221"}
username = os.environ.get("USERNAME")
with open("game_data.json") as file:
    data = json.load(file)
    base_path = os.path.abspath(data["path"].format(username))
    data["path"] = base_path
    patch = data["patch"]
# Todo: add reset to default condition

if __name__ == "__main__":
    main_app = wx.App()
    frame = Frame(data)
    if os.path.exists(base_path):
        frame.load()
    else:
        frame.path_error()
    main_app.MainLoop()
