from os.path import basename, dirname
from platform import platform
import json
from os.path import join
from sys import platform
if platform == "win32":
    from os.path import normpath as normpath_old

    def normpath(path):
        return normpath_old(path).replace('\\', '/')
else:
    from os.path import normpath
from os import walk
from functools import partial
from multiprocessing import Pool, cpu_count, Manager
import hashlib
import para_api

base_url = "https://paratranz.cn/api/projects/"


def walk_hash(local_path, endswith=".patch"):
    result = dict()
    local_path = normpath(local_path)
    for dir, temp, files in walk(local_path):
        for file in files:
            if file.endswith(endswith):
                result[normpath(join(dir, file)).replace(local_path, "").lstrip("/")] = hashlib.md5(
                    open(normpath(join(dir, file)), 'rb').read()).hexdigest()
    return result


def process_filelist(project_id, Authorization, file, result, subdir="", get_hash=False):
    if subdir != "":
        if file["name"].startswith(subdir):
            data = {key: val for key, val in file.items() if key != "name"}
            if get_hash is True:
                data.update({"hash": val for val in [para_api.revision(
                    project_id, Authorization, fileid=file["id"])[0]["hash"]]})
            result[normpath(file["name"].lstrip(subdir)).lstrip("/")] = data
        else:
            pass
    else:
        data = {key: val for key, val in file.items() if key != "name"}
        if get_hash is True:
            data.update({"hash": val for val in [para_api.revision(
                project_id, Authorization, fileid=file["id"])[0]["hash"]]})
        result[file["name"]] = data
    return result


def get_files_list(project_id, Authorization, subdir="", get_hash=False, process=cpu_count()):
    result = Manager().dict()
    try:
        raw_list = para_api.file_list(project_id, Authorization)
    except:
        return None
    with Pool(process) as p:
        p.map_async(partial(process_filelist, str(project_id), Authorization,
                    result=result, subdir=subdir, get_hash=get_hash), raw_list)
        p.close()
        p.join()
    return result


def get_files_content(project_id, file_id, Authorization, pageSize):
    result = dict()
    try:
        datas = para_api.file(project_id, Authorization,
                              fileid=file_id, pageSize=pageSize)
    except:
        return None
    for data in datas:
        result[data["key"].lstrip("#replace#")] = {
            key: val for key, val in data.items()}
    return result


def operate_file(local_list, para_list, local_path, project_id, Authorization, file, subdir="", operate="", reupload=False,output=False):
    if output!=False:
        print(basename(file))
    if operate == "up":
        if local_list[file] != para_list[file]["hash"] or reupload == True:
            files = normpath(local_path + "/" + file)
            para_api.upload_file(project_id, Authorization, files, str(
                para_list[file]["id"]), encoding="utf-8")
    elif operate == "add":
        if subdir != "":
            para_api.create_file(project_id, Authorization, normpath(
                join(local_path, file)),  normpath(join(subdir, dirname(file))), encoding="utf-8")
        else:
            para_api.create_file(project_id, Authorization, normpath(
                join(local_path, file)), dirname(file), encoding="utf-8")
    elif operate == "del":
        para_api.del_file(project_id, Authorization,
                          str(para_list[file]["id"]))
    else:
        pass


def sync_trans(local_path, project_id, Authorization, subdir="", process=cpu_count(), reupload=False,output=False):
    print("Walking local dir...")
    local_list = walk_hash(local_path)
    print("\nGet online list...")
    para_list = get_files_list(
        project_id, Authorization, subdir=subdir, get_hash=True)
    if para_list == None:
        print("para_list is None")
        upload_list = list()
        add_list = local_list.keys()
        del_list = list()
    else:
        upload_list = list(set(local_list.keys()).intersection(para_list.keys()))
        add_list = list(set(local_list.keys()).difference(para_list.keys()))
        del_list = list(set(para_list.keys()).difference(local_list.keys()))
    if len(upload_list) != 0:
        print("\nComparing exist files...")
        with Pool(process) as p:
            p.map_async(partial(operate_file, local_list, para_list, local_path,
                        project_id, Authorization, subdir=subdir, operate="up", reupload=reupload,output=False), upload_list)
            p.close()
            p.join()
    if len(add_list) != 0:
        print("\nUploading new files...")
        with Pool(process) as p:
            p.map_async(partial(operate_file, local_list, para_list,
                        local_path, project_id, Authorization, subdir=subdir, operate="add", reupload=reupload,output=False), add_list)
            p.close()
            p.join()
    if len(del_list) != 0:
        print("\nDelete outdated files...")
        with Pool(process) as p:
            p.map_async(partial(operate_file, local_list, para_list,
                        local_path, project_id, Authorization, subdir=subdir, operate="del", reupload=reupload,output=False), del_list)
            p.close()
            p.join()


def uploadtrans_process(local_path, project_id, Authorization, files_list, file, uid=None, force_updata=False):
   #print(basename(file))
    if files_list[file]["translated"] == files_list[file]["total"]:
        pass
    else:
        local_file = json.load(
            open(normpath(local_path + "/" + file), "r+", encoding="utf-8")
        )
        para_file = get_files_content(
            project_id, files_list[file]["id"], Authorization, len(local_file)+10)
        for item in para_file.keys():
            for v in local_file:
                if item.lstrip("#replace#") == v["path"]:
                    if v["value"] == "":
                        continue
                    elif v["raw"] == para_file[item]["original"] and  v["value"] != para_file[item]["translation"]:
                        para_api.upload_translation(project_id, Authorization, str(
                            para_file[item]["id"]),  v["value"], uid=uid)


def upload_translation(local_path, project_id, Authorization, subdir="", uid=None, force_updata=False, process=cpu_count()):
    files_list = get_files_list(project_id, Authorization, subdir=subdir)
    with Pool(process) as p:
        p.map_async(partial(uploadtrans_process, local_path, project_id,
                    Authorization, files_list, uid=uid, force_updata=force_updata), list(files_list.keys()))
        p.close()
        p.join()


def process_trans(local_path, files_list, project_id, Authorization, file, output=False):
    if output == True:
        print(basename(file))
    local_file = json.load(
        open(normpath(local_path + "/" + file), "r+", encoding="utf-8")
    )
    para_file = get_files_content(
        project_id, files_list[file]["id"], Authorization, len(local_file)+10)
    result = local_file
    for item in para_file.keys():
        if para_file[item]["translation"] == "" or para_file[item]["translation"] == None:
            continue
        else:
            for i, v in enumerate(result):
                if item.lstrip("#replace#") == v["path"]:
                    if (
                        v["value"] != para_file[item]["translation"].replace(
                            "\\n", "\n")
                        and v["raw"] == para_file[item]["original"]
                    ):
                        result[i]["value"] = para_file[item]["translation"].replace(
                            "\\n", "\n"
                        )
    f = open(normpath(local_path + "/" + file), "w", encoding="utf-8")
    json.dump(result, f, ensure_ascii=False, indent=2, sort_keys=True)
    f.close


def download_translation(local_path, project_id, Authorization, subdir="", process=cpu_count()):
    files_list = get_files_list(project_id, Authorization, subdir=subdir)
    print("Downloading translation...")
    with Pool(process) as download:
        download.map_async(partial(process_trans, local_path, files_list,
                           project_id, Authorization), list(files_list.keys()))
        download.close()
        download.join()


if __name__ == "__main__":
    #print(get_files_list( "2464", "cd11860c565ed926ea5b2aa41697fd57", subdir="Enhanced Storage", get_hash=False))
    """
    # print(json.loads(requests.get(base_url + "3531" + "/files", headers={"Authorization": Authorization}).content)
    #print(get_files_content("2747", "316916", "cd11860c565ed926ea5b2aa41697fd57"))
    # upload_translation("F:\workplace\StarBound_-Mod_Misc_Chinese_Project/text/novakidquest/raw","3694","cd11860c565ed926ea5b2aa41697fd57")
    #print(walk_hash("F:\workplace\StarBound_-Mod_Misc_Chinese_Project/text/neo+/raw", endswith=".patch"))
    #print(para_api.file_list("3694", "cd11860c565ed926ea5b2aa41697fd57"))
    #download_translation("/workplace/StarBound_-Mod_Misc_Chinese_Project/text/Project Knightfall/raw","2472", "cd11860c565ed926ea5b2aa41697fd57")
    fl = get_files_list("3092", "cd11860c565ed926ea5b2aa41697fd57", subdir="",get_hash=False)
    partial(process_trans, "/workplace/StarBound_Mods_SChinese_Project/text/EP's Expansion of Shadows/raw",fl,"3092", "cd11860c565ed926ea5b2aa41697fd57")(dialog/epviolence.config.patch)
    result1 = dict()
    simple = {
        "id": 280615,
        "createdAt": "2021-06-12T16:43:46.297Z",
        "updatedAt": "2021-06-12T16:44:14.347Z",
        "name": "Aging Alien Alcohols/items/aging.config.patch",
        "project": 2464,
        "format": "stbpatch",
        "total": 5,
        "translated": 5,
        "disputed": 0,
        "checked": 5,
        "reviewed": 5,
        "hidden": 0,
        "locked": 0,
        "words": 13,
        "extra": None,
        "folder": "Aging Alien Alcohols/items",
        "progress": {
            "translate": 1,
            "review": 1,
            "check": 1
        }}
    #partial(process_filelist, "2464", "cd11860c565ed926ea5b2aa41697fd57",result=result1, subdir="Aging Alien Alcohols", get_hash=True)(simple)
    #process_filelist("2464", "cd11860c565ed926ea5b2aa41697fd57", simple, result1, subdir="Aging Alien Alcohols", get_hash=True)
    # print(result1)
    #sync_trans("/git/StarBound_Mods_SChinese_Project/text/neo+/raw","3694",  "cd11860c565ed926ea5b2aa41697fd57", subdir="neo+")
    # requests.post(base_url+project_id+"/files",
    # files=files, headers=headers, data=data)
    # requests.delete(base_url+project_id+"/files/448483",headers=headers)

f = open(normpath("F:/workplace/StarBound_Mods_SChinese_Project/script/tools/test.json"), "w", encoding="utf-8")
#test = para_api.file("4025", "cd11860c565ed926ea5b2aa41697fd57",fileid="764802")
test = get_files_content("4025", "764802","cd11860c565ed926ea5b2aa41697fd57",20)
text = json.dump(test,f, ensure_ascii=False,
                              sort_keys=True, indent=2)
        """
