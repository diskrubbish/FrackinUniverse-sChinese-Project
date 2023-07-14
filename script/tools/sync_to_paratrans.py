from sys import platform
import functools
import os
import json
from multiprocessing import Pool, cpu_count, Manager
from json_tools import prepare
if platform == "win32":
    from os.path import normpath as normpath_old
    def normpath(path):
        return normpath_old(path).replace('\\', '/')
else:
    from os.path import normpath
from extract_labels_config import file_list

from requests_tool import operate_file,get_files_list
import hashlib
import shutil
import para_api


import zipfile
para_id = "7650"
para_path = normpath(
    (os.environ.get('GITHUB_WORKSPACE')+"/translations/texts"))
temp_path = normpath(
    (os.environ.get('GITHUB_WORKSPACE')+"/temp"))
    

para_token = os.environ.get('PARA_TOKEN')

def walk_hash(local_path, endswith=".patch"):
    result = dict()
    local_path = normpath(local_path)
    for dir, d, files in os.walk(local_path):
        for file in files:
            if file.endswith(endswith):
                result[normpath(os.path.relpath(os.path.join(dir, file),local_path)).lstrip("/")] = hashlib.md5(
                    open(normpath(os.path.join(dir, file)), 'rb').read()).hexdigest()
    return result

if __name__ == "__main__":
    print("Walking local dir...")
    local_list = walk_hash(para_path)
    para_list = walk_hash(normpath(temp_path+"/data/texts"))
    online_list = {i["name"]:i["id"] for i in para_api.file_list(para_id,para_token)}
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
        print("\nCheck Upload files...")
        for upload_file in upload_list:
            with open(normpath(para_path+"/"+upload_file), "r", encoding="utf-8-sig") as f:
                local_json =json.loads(prepare(f))
                f.close
            with open(normpath(temp_path+"/data/texts/"+upload_file), "r", encoding="utf-8-sig") as f2:
                para_json =json.loads(prepare(f2))
                f2.close
            if local_json!=para_json:
                print(upload_file)
                #para_api.upload_file(para_id, para_token, os.path.join(local_list,upload_file), online_list[upload_file], encoding="utf-8")
                #para_api.upload_file_trans(para_id, para_token, os.path.join(local_list,upload_file), online_list[upload_file], encoding="utf-8")
    if len(del_list) != 0:
        print("\nDelete outdated files...")
        for del_file in del_list:
            print(del_file)
            #para_api.del_file(para_id, para_token, online_list[del_file])
           
    if len(add_list) != 0:
        print("\nUploading new files...")
        for add_file in add_list:
            print(add_file)
            #para_api.create_file(para_id, para_token, os.path.join(local_list,add_file), normpath(os.path.dirname(add_file)), encoding="utf-8")