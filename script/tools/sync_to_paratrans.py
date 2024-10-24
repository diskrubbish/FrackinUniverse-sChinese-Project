from sys import platform
import functools
import os
import json
from json_tools import prepare

if platform == "win32":
    from os.path import normpath as normpath_old

    def normpath(path):
        return normpath_old(path).replace("\\", "/")

else:
    from os.path import normpath

import para_api
from translation_memory import import_memory_para

para_id = "7650"
para_path = normpath((os.environ.get("GITHUB_WORKSPACE") + "/translations/texts"))
temp_path = normpath((os.environ.get("GITHUB_WORKSPACE") + "/temp"))


para_token = os.environ.get("PARA_TOKEN")


def load_json_file(file_path):
    with open(file_path, "r", encoding="utf-8-sig") as f:
        return json.loads(prepare(f))


def walk_files(local_path, endswith=".patch"):
    result = list()
    local_path = normpath(local_path)
    for dir, d, files in os.walk(local_path):
        for file in files:
            if file.endswith(endswith):
                result.append(
                    normpath(
                        os.path.relpath(os.path.join(dir, file), local_path)
                    ).lstrip("/")
                )
    return result


if __name__ == "__main__":
    print("Import Translation Memory...")
    import_memory_para(
        para_path, os.environ.get("GITHUB_WORKSPACE") + "/translations/memory.json"
    )
    import_memory_para(
        para_path,
        os.environ.get("GITHUB_WORKSPACE") + "/script/tools/starcore_memory.json",
    )
    print("Walking local dir...")
    local_list = walk_files(para_path)
    # para_list = walk_files(normpath(temp_path+"/data/texts"))
    online_list = {i["name"]: i["id"] for i in para_api.file_list(para_id, para_token)}
    if online_list == None:
        print("Online List is None")
        upload_list = list()
        add_list = local_list
        del_list = list()
    else:
        upload_list = list(set(local_list).intersection(online_list.keys()))
        add_list = list(set(local_list).difference(online_list.keys()))
        del_list = list(set(online_list.keys()).difference(local_list))
    if len(upload_list) != 0:
        print("\nCheck Upload files...")
        for upload_file in upload_list:
            local_json = load_json_file(normpath(os.path.join(para_path, upload_file)))
            para_json_path = normpath(
                normpath(os.path.join(temp_path, "data/texts/", upload_file))
            )
            need_upload = False
            if os.path.exists(para_json_path):
                para_json = load_json_file(para_json_path)
                if local_json != para_json:
                    need_upload = True
            else:
                need_upload = True
            if need_upload:
                print(upload_file)
                para_api.upload_file(
                    para_id,
                    para_token,
                    normpath(os.path.join(para_path, upload_file)),
                    online_list[upload_file],
                    encoding="utf-8-sig",
                )
                para_api.upload_file_trans(
                    para_id,
                    para_token,
                    normpath(os.path.join(para_path, upload_file)),
                    online_list[upload_file],
                    encoding="utf-8-sig",
                )
    if len(del_list) != 0:
        print("\nDelete outdated files...")
        for del_file in del_list:
            print(del_file)
            para_api.del_file(para_id, para_token, online_list[del_file])

    if len(add_list) != 0:
        print("\nUploading new files...")
        for add_file in add_list:
            print(add_file)
            para_api.create_file(
                para_id,
                para_token,
                os.path.join(para_path, add_file),
                normpath(os.path.dirname(add_file)),
                encoding="utf-8-sig",
            )
        online_list = {
            i["name"]: i["id"] for i in para_api.file_list(para_id, para_token)
        }
        for add_file in add_list:
            para_api.upload_file_trans(
                para_id,
                para_token,
                os.path.join(para_path, add_file),
                online_list[add_file],
                encoding="utf-8-sig",
            )
