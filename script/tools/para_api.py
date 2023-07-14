import requests
import json
base_url = "https://paratranz.cn/api/projects/"
import platform
if platform == "win32":
    from os.path import normpath as normpath_old

    def normpath(path):
        return normpath_old(path).replace('\\', '/')
else:
    from os.path import normpath

def file_list(project_id, para_token):
    return json.loads(
        requests.get(base_url + str(project_id) + "/files", headers={"Authorization": para_token,'accept': 'application/json'}).content)


def file(project_id, para_token, fileid=None ,page=None, pageSize=50):
    params = {"pageSize": pageSize, "page": page,
                  "file": fileid}
    return json.loads(
        requests.get(base_url + str(project_id) + "/strings", params = params ,headers={"Authorization": para_token,'accept': 'application/json'},).content)["results"]


def revision(project_id, para_token, page=None, pageSize=50, fileid=None, type=None):
    if type not in [None, "create", "update", "import"]:
        return None
    else:
        params = {"pageSize": pageSize, "page": page,
                  "file": fileid, "type": type}
        return json.loads(
            requests.get(base_url + str(project_id) + "/files/revisions", headers={"Authorization": para_token,'accept': 'application/json'}, params=params).content)["results"]


def create_file(project_id, para_token, file, path, encoding="utf-8"):
    files = {"file": open(file, "r+", encoding=encoding)}
    data = {"path": path}
    requests.post(base_url + str(project_id) + "/files", files=files,
                  data=data, headers={"Authorization": para_token,'accept': 'application/json'})


def upload_file(project_id, para_token, file, fileid, encoding="utf-8"):
    files = {"file": open(file, "r+", encoding=encoding)}
    requests.post(base_url + str(project_id) + "/files/"+fileid,
                  files=files, headers={"Authorization": para_token,'accept': 'application/json'})

def upload_file_trans(project_id, para_token, file, fileid, encoding="utf-8",force=False):
    files = {"file": open(file, "r+", encoding=encoding),"force":force}
    requests.post(base_url + str(project_id) + "/files/"+fileid+"/translation",
                  files=files, headers={"Authorization": para_token,'accept': 'application/json'})


def del_file(project_id, para_token, fileid):
    requests.delete(base_url + str(project_id) + "/files/"+fileid,
                    headers={"Authorization": para_token,'accept': 'application/json'})


def upload_translation(project_id, para_token, strid, translation, uid=None):
    data = {"translation": translation, "uid": uid}
    requests.put(base_url + str(project_id) + "/strings/" + str(strid),
                 headers={"Authorization": para_token,'accept': 'application/json'}, json=data)
    
def get_string(project_id, para_token, strid):
    return json.loads(requests.get(base_url + str(project_id) + "/strings/" + str(strid),
                 headers={"Authorization": para_token,'accept': 'application/json'}).content)

def get_artifacts(project_id, para_token):
    return json.loads(requests.get(base_url + str(project_id) + "/artifacts" ,
                 headers={"Authorization": para_token,'accept': 'application/json'}).content)

def trigger_artifacts(project_id, para_token):
    return json.loads(requests.post(base_url + str(project_id) + "/artifacts" ,
                 headers={"Authorization": para_token,'accept': 'application/json'}).content)
    
def download_artifacts(project_id, para_token,download_path):
    link = requests.get(base_url + str(project_id) + "/artifacts/download" ,
                 headers={"Authorization": para_token,'accept': 'application/json'})
    if link.status_code == 200:
            with open(normpath(download_path+"/data.zip"),"wb") as f:
                        f.write(link.content)
        