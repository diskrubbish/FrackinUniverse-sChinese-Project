from os import makedirs, remove, walk
from os.path import join as join_path
from os.path import abspath, basename, dirname, exists
from json_tools import prepare, field_by_path, list_field_paths
import json
from codecs import open
import platform
from os.path import normpath as normpath_old
def normpath(path):
        return normpath_old(path).replace('\\', '/')
file_dir = "F:/workplace/FrackinUniverse-sChinese-Project/translations/texts"
patch_dir = "F:/Fu Schinese"
for path, d, filelist in walk(file_dir):
    for thefile in filelist:
        if thefile in ["substitutions.json", "totallabels.json", "translatedlabels.json", "patch_substitutions.json", "parse_problem.txt", "_metadata", "_previewimage"]:
            continue
        if thefile.endswith(".patch"):
            para_file = normpath(join_path(path, thefile))
            patch_file = normpath(patch_dir+join_path(path, thefile).lstrip(file_dir))
            if exists(patch_file):
                with open(para_file, "rb+", "utf-8-sig") as f:
                    json_dict = json.loads(prepare(f))
                    print(basename(para_file))
                with open(patch_file, "rb", "utf-8-sig") as f2:
                    patch_dict = json.loads(prepare(f2))
                if json_dict != patch_dict:
                    for i in patch_dict:
                        for x, v in enumerate(json_dict):
                            if i["path"] == v["path"]:
                                if v["value"] != i["value"]:
                                    json_dict[x]["value"] = i["value"]
                    f = open(para_file, "wb+", "utf-8")
                    json.dump(
                        json_dict, f, ensure_ascii=False, indent=2, sort_keys=True)
                    f.close
