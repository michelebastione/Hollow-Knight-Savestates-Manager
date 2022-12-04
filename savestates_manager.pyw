import json, os, wx
from gui_assets import Frame

default_data = {"path": "C:\\Users\\{}\\AppData\\LocalLow\\Team Cherry\\Hollow Knight", "patch": "1221"}
username = os.environ.get("USERNAME")
with open("game_data.json") as file:
    data = json.load(file)
    base_path = os.path.abspath(data["path"].format(username))
    data["path"] = base_path
    patch = data["patch"]
#Todo: add condition for when current user is different than in the json file

if __name__ == "__main__":
    app = wx.App()
    frame = Frame(data)
    if os.path.exists(base_path):
        # if "0" in os.listdir(frame.current_path):
        #     frame.current_path += "\\0"
        frame.load()
    else:
        frame.path_error()
    app.MainLoop()
