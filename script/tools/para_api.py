import requests
import json
base_url = "https://paratranz.cn/api/projects/"
import platform
import time
if platform == "win32":
    from os.path import normpath as normpath_old

    def normpath(path):
        return normpath_old(path).replace('\\', '/')
else:
    from os.path import normpath
defalt_delay = 2
def file_list(project_id, para_token,delay = defalt_delay):
    time.sleep(delay)
    return json.loads(
        requests.get(base_url + str(project_id) + "/files", headers={"Authorization": para_token,'accept': 'application/json'}).content)


def file(project_id, para_token, fileid=None ,page=None, pageSize=50,delay = defalt_delay):
    params = {"pageSize": pageSize, "page": page,
                  "file": fileid}
    time.sleep(delay)
    return json.loads(
        requests.get(base_url + str(project_id) + "/strings", params = params ,headers={"Authorization": para_token,'accept': 'application/json'},).content)["results"]


def revision(project_id, para_token, page=None, pageSize=50, fileid=None, type=None,delay = defalt_delay):
    if type not in [None, "create", "update", "import"]:
        return None
    else:
        params = {"pageSize": pageSize, "page": page,
                  "file": fileid, "type": type}
        time.sleep(delay)
        return json.loads(
            requests.get(base_url + str(project_id) + "/files/revisions", headers={"Authorization": para_token,'accept': 'application/json'}, params=params).content)["results"]


def create_file(project_id, para_token, file, path, encoding="utf-8-sig",delay = defalt_delay):
    files = {"file": open(file, "r+", encoding=encoding)}
    data = {"path": path}
    time.sleep(delay)
    requests.post(base_url + str(project_id) + "/files", files=files,
                  data=data, headers={"Authorization": para_token,'accept': 'application/json'})


def upload_file(project_id, para_token, file, fileid, encoding="utf-8-sig",delay = defalt_delay):
    files = {"file": open(file, "r+", encoding=encoding)}
    time.sleep(delay)
    requests.post(base_url + str(project_id) + "/files/"+ str(fileid),
                  files=files, headers={"Authorization": para_token,'accept': 'application/json'})

def upload_file_trans(project_id, para_token, file, fileid, encoding="utf-8-sig",force=False,delay = defalt_delay):
    files = {"file": open(file, "r+", encoding=encoding),"force":force}
    time.sleep(delay)
    requests.post(base_url + str(project_id) + "/files/"+str(fileid)+"/translation",
                  files=files, headers={"Authorization": para_token,'accept': 'application/json'})


def del_file(project_id, para_token, fileid,delay = defalt_delay):
    time.sleep(delay)
    requests.delete(base_url + str(project_id) + "/files/"+str(fileid),
                    headers={"Authorization": para_token,'accept': 'application/json'})


def upload_translation(project_id, para_token, strid, translation, uid=None,delay = defalt_delay):
    data = {"translation": translation, "uid": uid}
    time.sleep(delay)
    requests.put(base_url + str(project_id) + "/strings/" + str(strid),
                 headers={"Authorization": para_token,'accept': 'application/json'}, json=data)
    
def get_string(project_id, para_token, strid,delay = defalt_delay):
    time.sleep(delay)
    return json.loads(requests.get(base_url + str(project_id) + "/strings/" + str(strid),
                 headers={"Authorization": para_token,'accept': 'application/json'}).content)

def get_artifacts(project_id, para_token,delay = defalt_delay):
    time.sleep(delay)
    return json.loads(requests.get(base_url + str(project_id) + "/artifacts" ,
                 headers={"Authorization": para_token,'accept': 'application/json'}).content)

def trigger_artifacts(project_id, para_token,delay = defalt_delay):
    time.sleep(delay)
    return json.loads(requests.post(base_url + str(project_id) + "/artifacts" ,
                 headers={"Authorization": para_token,'accept': 'application/json'}).content)
    
def download_artifacts(project_id, para_token,download_path,delay = defalt_delay):
    time.sleep(delay)
    link = requests.get(base_url + str(project_id) + "/artifacts/download" ,
                 headers={"Authorization": para_token,'accept': 'application/json'})
    if link.status_code == 200:
            with open(normpath(download_path+"/data.zip"),"wb") as f:
                        f.write(link.content)
    return link
        