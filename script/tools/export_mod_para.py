from os.path import dirname, join, exists
from os import walk, makedirs
import shutil
import os
import json
from sys import platform
if platform == "win32":
    from os.path import normpath as normpath_old

    def normpath(path):
        return normpath_old(path).replace('\\', '/')
else:
    from os.path import normpath


def export_mod_para(path, texts_prfix="texts", mods_prfix="mods", others_prfix="others"):
    if exists(normpath(join(path, mods_prfix))):
        shutil.rmtree(normpath(join(path, mods_prfix)))
    shutil.copytree(normpath(join(path, others_prfix)),
                    normpath(join(path, mods_prfix)))
    for dir, temp, files in walk(normpath(join(path, texts_prfix))):
        for file in files:
            if file.endswith(".patch"):
                file_path = normpath(join(dir, file))
                result = list()
                patch_path = file_path.replace(
                    normpath(join(path, texts_prfix)), normpath(join(path, mods_prfix)))
                if exists(patch_path):
                    replace_result = list()
                    for patch in json.load(open(patch_path, "r+", encoding="utf-8")):
                        if patch["op"] != "replace":
                            result.append(
                                [{"op": "test", "path": patch["path"]}, patch])
                        else:
                            replace_result.append(
                               patch)
                    for patch in json.load(open(file_path, "r+", encoding="utf-8")):
                        if patch["value"] != "" and patch["value"] != patch["raw"]:
                            replace_result.append(
                                {key: val for key, val in patch.items() if key != "raw"})
                    result.append(replace_result)
                else:
                    for patch in json.load(open(file_path, "r+", encoding="utf-8")):
                        if patch["value"] != "" and patch["value"] != patch["raw"]:
                            result.append(
                                {key: val for key, val in patch.items() if key != "raw"})
                if len(result) != 0:
                    if len(dirname(patch_path)) > 0:
                        makedirs(dirname(patch_path), exist_ok=True)
                    with open(patch_path, "w+", encoding="utf-8") as f:

                        json.dump(result, f, ensure_ascii=False,
                                  indent=2, sort_keys=True)
if __name__ == '__main__':
    export_mod_para(normpath((os.environ.get('GITHUB_WORKSPACE')+"/translations")))
    
  
