import requests
import json
base_url = "https://paratranz.cn/api/projects/"


def filelist(project_id, Authorization):
    return json.loads(
        requests.get(base_url + str(project_id) + "/files", headers={"Authorization": Authorization}).content)


def file(project_id, Authorization, fileid=None ,page=None, pageSize=50):
    params = {"pageSize": pageSize, "page": page,
                  "file": fileid}
    return json.loads(
        requests.get(base_url + str(project_id) + "/strings", params = params ,headers={"Authorization": Authorization},).content)["results"]


def revision(project_id, Authorization, page=None, pageSize=50, fileid=None, type=None):
    if type not in [None, "create", "update", "import"]:
        return None
    else:
        params = {"pageSize": pageSize, "page": page,
                  "file": fileid, "type": type}
        return json.loads(
            requests.get(base_url + str(project_id) + "/files/revisions", headers={"Authorization": Authorization}, params=params).content)["results"]


def create_file(project_id, Authorization, file, path, encoding="utf-8"):
    files = {"file": open(file, "r+", encoding=encoding)}
    data = {"path": path}
    requests.post(base_url + str(project_id) + "/files", files=files,
                  data=data, headers={"Authorization": Authorization})


def upload_file(project_id, Authorization, file, fileid, encoding="utf-8"):
    files = {"file": open(file, "r+", encoding=encoding)}
    requests.post(base_url + str(project_id) + "/files/"+fileid,
                  files=files, headers={"Authorization": Authorization})


def del_file(project_id, Authorization, fileid):
    requests.delete(base_url + str(project_id) + "/files/"+fileid,
                    headers={"Authorization": Authorization})


def upload_translation(project_id, Authorization, strid, translation, uid=None):
    data = {"translation": translation, "uid": uid}
    requests.put(base_url + str(project_id) + "/strings/" + str(strid),
                 headers={"Authorization": Authorization}, json=data)
    
def get_string(project_id, Authorization, strid):
     return json.loads(requests.get(base_url + str(project_id) + "/strings/" + str(strid),
                 headers={"Authorization": Authorization}).content)