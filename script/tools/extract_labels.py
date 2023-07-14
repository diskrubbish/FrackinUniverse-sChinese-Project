from sys import platform
from multiprocessing import cpu_count
import os
from parser_settings import files_of_interest
if platform == "win32":
    from os.path import normpath as normpath_old

    def normpath(path):
        return normpath_old(path).replace('\\', '/')
else:
    from os.path import normpath

from translation_memory import *

import stbtran_utils

root_dir = normpath((os.environ.get('GITHUB_WORKSPACE')+"/temp/FrackinUniverse"))

prefix = normpath((os.environ.get('GITHUB_WORKSPACE')+"/translations"))
patch_serialization = {
    "craftingmedical.object.patch": {'upgradeStages':{"index": 2, "increase":False}},
    "statuses.config.patch": {"generic": {"index": 70, "increase": True}, "cheerful": {"index": 31, "increase": True}, "jerk": {"index": 31, "increase": True}, "flirty": {"index": 31, "increase": True}, "anxious": {"index": 31, "increase": True}, "easilyspooked": {"index": 32, "increase": True}, "clumsy": {"index": 31, "increase": True}, "excited": {"index": 31, "increase": True}, "intrusive": {"index": 31, "increase": True}, "dumb": {"index": 32, "increase": True}, "emo": {"index": 30, "increase": True}, "fast": {"index": 31, "increase": True}, "nocturnal": {"index": 32, "increase": True}, "socialite": {"index": 31, "increase": True}, "ambitious": {"index": 30, "increase": True}},
    'craftingfurnace.object.patch': {'upgradeStages':{"index": 2, "increase":False}},
    'craftingwheel.object.patch': {'upgradeStages':{"index": 2, "increase":False}}
}
dir_blacklis = "" 
path_blacklist = ""
ignore_filelist = ""
string_blacklist = ["0", "set at runtime", "tree", "Replace Me", "replace me", "", "^shadow;$dmg$",
                            "-todo-", "--TODO--", "replaceme", "recruit name", "mission text", "recruit description"]
texts_prefix = "texts"
if __name__ == '__main__':
    stbtran_utils.stbtran_para(root_dir, prefix, files_of_interest,
                           patch_serialization, dir_blacklis, path_blacklist, ignore_filelist, string_blacklist, texts_prefix=texts_prefix)
