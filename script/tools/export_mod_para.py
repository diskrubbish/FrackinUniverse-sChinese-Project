from os.path import dirname, exists
from os.path import join as join_path
from os import walk, makedirs
import shutil
import os
import json
from sys import platform
from json_tools import prepare
from datetime import datetime
import pytz

if platform == "win32":
    from os.path import normpath as normpath_old

    def normpath(path):
        return normpath_old(path).replace("\\", "/")

else:
    from os.path import normpath


def create_metadata(root_dir, prefix, contentfolder, vdf_save_path):
    if exists(normpath(join_path(root_dir, ".metadata"))):
        original_metadata = json.loads(
            prepare(
                open(normpath(join_path(root_dir, ".metadata")), "r+", encoding="utf-8-sig")
            )
        )
    else:
        original_metadata = json.loads(
            prepare(
                open(normpath(join_path(root_dir, "_metadata")), "r+", encoding="utf-8-sig")
            )
        )
    old_mod_metadata = json.loads(
        prepare(
            open(
                normpath(join_path(prefix, "others/_metadata")), "r+", encoding="utf-8-sig"
            )
        )
    )
    mod_metadata = old_mod_metadata
    mod_adapt_version = original_metadata["version"]
    mod_creat_time = str(datetime.now(pytz.timezone("Asia/Shanghai")))
    mod_description = old_mod_metadata["description"].split("\n")
    mod_description[2] = (
        "[*] 自动构建于 "
        + mod_creat_time
        + "，当前适配 Frackin' Universe "
        + (mod_adapt_version)
        + " 版本"
    )
    mod_description = "\n".join(mod_description)
    mod_metadata["description"] = mod_description
    mod_metadata["version"] = mod_adapt_version
    raw_steam_vdf = {
        "appid": "211820",
        # "contentfolder": os.environ.get("GITHUB_WORKSPACE")+"/temp/paks",
        "contentfolder": contentfolder,
        "description": mod_description,
        "publishedfileid": str(mod_metadata["steamContentId"]),
    }
    steaam_vdf = ['"workshopitem"', "{"]
    for vdf_key in raw_steam_vdf.keys():
        steaam_vdf.append(
            '"' + vdf_key + '"' + "		" + '"' + raw_steam_vdf[vdf_key] + '"'
        )
    steaam_vdf.append("}")

    with open(
        normpath(join_path(prefix, "others/_metadata")), "w+", encoding="utf-8-sig"
    ) as f:
        json.dump(mod_metadata, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.close
    with open(
        normpath(join_path(prefix, "others/_metadata.bak")), "w+", encoding="utf-8-sig"
    ) as f:
        json.dump(old_mod_metadata, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.close
    with open(join_path(vdf_save_path, "mod.vdf"), "w+", encoding="utf-8-sig") as f:
        for i in steaam_vdf:
            f.write(i + "\n")


def export_mod_para(
    path, texts_prfix="texts", mods_prfix="mods", others_prfix="others"
):
    if exists(normpath(join_path(path, mods_prfix))):
        shutil.rmtree(normpath(join_path(path, mods_prfix)))
    shutil.copytree(
        normpath(join_path(path, others_prfix)), normpath(join_path(path, mods_prfix))
    )
    for dir, temp, files in walk(normpath(join_path(path, texts_prfix))):
        for file in files:
            if file.endswith(".patch"):
                file_path = normpath(join_path(dir, file))
                result = list()
                patch_path = file_path.replace(
                    normpath(join_path(path, texts_prfix)),
                    normpath(join_path(path, mods_prfix)),
                )
                if exists(patch_path):
                    replace_result = list()
                    for patch in json.load(open(patch_path, "r+", encoding="utf-8-sig")):
                        if patch["op"] != "replace":
                            result.append(
                                [{"op": "test", "path": patch["path"]}, patch]
                            )
                        else:
                            replace_result.append(patch)
                    for patch in json.load(open(file_path, "r+", encoding="utf-8-sig")):
                        if patch["value"] != "" and patch["value"] != patch["raw"]:
                            replace_result.append(
                                {key: val for key, val in patch.items() if key != "raw"}
                            )
                    result.append(replace_result)
                else:
                    for patch in json.load(open(file_path, "r+", encoding="utf-8-sig")):
                        if patch["value"] != "" and patch["value"] != patch["raw"]:
                            result.append(
                                {key: val for key, val in patch.items() if key != "raw"}
                            )
                if len(result) != 0:
                    if len(dirname(patch_path)) > 0:
                        makedirs(dirname(patch_path), exist_ok=True)
                    with open(patch_path, "w+", encoding="utf-8-sig") as f:
                        json.dump(
                            result, f, ensure_ascii=False, indent=2, sort_keys=True
                        )


if __name__ == "__main__":
    create_metadata(
        normpath(os.environ.get("GITHUB_WORKSPACE") + "/temp/FrackinUniverse"),
        normpath(os.environ.get("GITHUB_WORKSPACE") + "/translations"),
        normpath(os.environ.get("GITHUB_WORKSPACE") + "/temp/paks"),
        normpath(os.environ.get("GITHUB_WORKSPACE") + "/temp"),
    )
    export_mod_para(normpath((os.environ.get("GITHUB_WORKSPACE") + "/translations")))
