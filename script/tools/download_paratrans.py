from sys import platform
import functools
import os
import json
import time
from multiprocessing import Pool, cpu_count, Manager
from json_tools import prepare

if platform == "win32":
    from os.path import normpath as normpath_old

    def normpath(path):
        return normpath_old(path).replace("\\", "/")

else:
    from os.path import normpath
from extract_labels import file_list
from translation_memory import export_memory_para, import_memory_para

import shutil
import para_api


import zipfile

para_id = "7650"
para_path = normpath((os.environ.get("GITHUB_WORKSPACE") + "/translations/texts"))

temp_path = normpath((os.environ.get("GITHUB_WORKSPACE") + "/temp"))


def load_json_file(file_path):
    with open(file_path, "r", encoding="utf-8-sig") as f:
        return json.loads(prepare(f))


para_token = os.environ.get("PARA_TOKEN")


def fix_translation(local_path, para_path, file_path):
    if not file_path.endswith(".patch"):
        return

    local_file = file_path
    para_file = normpath(para_path + "/" + os.path.relpath(file_path, local_path))

    if not os.path.exists(para_file):
        return

    para_dict = load_json_file(para_file)
    local_dict = load_json_file(local_file)
    # updated_dict = local_dict
    updated_dict = list()
    for v in local_dict:
        found_match = False
        for i in para_dict:
            if v["path"] == i["path"]:
                if v["value"] != i["value"]:
                    updated_dict.append({**v, "value": i["value"]})
                else:
                    updated_dict.append(v)
                found_match = True
                break

        if not found_match:
            updated_dict.append(v)

    if updated_dict != local_dict:
        with open(local_file, "w", encoding="utf-8-sig") as f:
            print(file_path)
            json.dump(updated_dict, f, ensure_ascii=False, indent=2, sort_keys=True)


if __name__ == "__main__":
    print("Export Translation Memory...")
    export_memory_para(
        para_path, os.environ.get("GITHUB_WORKSPACE") + "/translations/memory.json"
    )
    print("DownLoading Artifacts...")
    trigger_time = time.mktime(
        time.strptime(
            para_api.trigger_artifacts(para_id, para_token)["createdAt"],
            "%Y-%m-%dT%H:%M:%S.%f%z",
        )
    )
    loop_time = 0
    while (
        (
            time.mktime(
                time.strptime(
                    para_api.get_artifacts(para_id, para_token)["createdAt"],
                    "%Y-%m-%dT%H:%M:%S.%f%z",
                )
            )
            <= trigger_time
        )
    ) or loop_time > 5:
        print("Waiting For Creating...")
        time.sleep(80)
        loop_time = +1
    para_api.download_artifacts(para_id, para_token, temp_path)
    print("DownLoading Artifacts Finished")
    print("Unzip Artifacts...")
    fz = zipfile.ZipFile(normpath(temp_path + "/data.zip"))
    for file in fz.namelist():
        fz.extract(file, normpath(temp_path + "/data"))
    print("Unzip Artifacts Finished")
    file_list = list()
    for path, d, files in os.walk(para_path):
        for thefile in files:
            file_list.append(normpath(os.path.join(path, thefile)))
    print("Download Translations...")
    for file in file_list:
        fix_translation(para_path, normpath(temp_path + "/data/utf8"), file)
    shutil.copytree(para_path, normpath(temp_path + "/data/texts"))