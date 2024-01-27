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
        return normpath_old(path).replace('\\', '/')
else:
    from os.path import normpath
from extract_labels import file_list
from translation_memory import export_memory_para, import_memory_para

import shutil
import para_api


import zipfile
para_id = "7650"
para_path = normpath(
    (os.environ.get('GITHUB_WORKSPACE')+"/translations/texts"))

temp_path = normpath(
    (os.environ.get('GITHUB_WORKSPACE')+"/temp"))

    

para_token = os.environ.get('PARA_TOKEN')
def fix_transltion(local_path,para_path,thefile):
    if thefile.endswith(".patch"):
        local_file = thefile
        para_file = normpath(para_path+"/"+os.path.relpath(thefile,local_path))+".json"
        if os.path.exists(para_file):
            with open(para_file, "r", encoding="utf-8-sig") as f:
                para_dict = json.loads(prepare(f))
                f.close
            with open(local_file, "r", encoding="utf-8-sig") as f2:
                local_dict = json.loads(prepare(f2))
                f2.close
            with open(local_file, "r", encoding="utf-8-sig") as f2:
                result_dict = json.loads(prepare(f2))
                f2.close
            for i in para_dict:
                for x, v in enumerate(result_dict):
                    if i["key"].split("#")[2] == v["path"] and i["key"].split("#")[1] == v["op"]:
                        if v["value"] != i["translation"].replace("\\n","\n") and v["raw"] == i["original"]:
                            result_dict[x]["value"] = i["translation"].replace("\\n","\n")
            if result_dict!=local_dict:
                with open(local_file, "w", encoding="utf-8-sig") as f:
                    print(thefile)
                    json.dump(
                            result_dict, f, ensure_ascii=False, indent=2, sort_keys=True)
                    f.close
    
 
if __name__ == "__main__":
    print("Export Translation Memory...")
    export_memory_para(para_path,os.environ.get('GITHUB_WORKSPACE')+"/translations/memory.json")
    print("DownLoading Artifacts...")
    trigger_time = time.mktime(time.strptime(para_api.trigger_artifacts(para_id, para_token)['createdAt'],"%Y-%m-%dT%H:%M:%S.%f%z"))
    while time.mktime(time.strptime(para_api.get_artifacts(para_id, para_token)['createdAt'],"%Y-%m-%dT%H:%M:%S.%f%z")) <= trigger_time:
        print("Waiting For Creating...")
        time.sleep( 80 )
    para_api.download_artifacts(para_id,para_token,temp_path)
    print("DownLoading Artifacts Finished")    
    print("Unzip Artifacts...")
    fz=zipfile.ZipFile(normpath(temp_path+"/data.zip"))
    for file in fz.namelist():
            fz.extract(file, normpath(temp_path+"/data"))
    print("Unzip Artifacts Finished")
    file_list = list()
    for path, d, files in os.walk(para_path):
        for thefile in files:
            file_list.append(normpath(os.path.join(path, thefile)))
    print("Download Translations...")
    """
    with Pool(cpu_count()) as p:
        p.map_async(functools.partial(fix_transltion, para_path , normpath(temp_path+"/data/raw") ), file_list)
        p.close()
        p.join()
    """
    for file in file_list:
        fix_transltion(para_path , normpath(temp_path+"/data/raw"),file)
    shutil.copytree(para_path,normpath(temp_path+"/data/texts"))
    print("Import Translation Memory...")
    import_memory_para(para_path,os.environ.get('GITHUB_WORKSPACE')+"/translations/memory.json")
    
        
            