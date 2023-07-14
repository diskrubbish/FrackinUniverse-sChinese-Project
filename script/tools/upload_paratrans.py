from sys import platform
import os
if platform == "win32":
    from os.path import normpath as normpath_old
    def normpath(path):
        return normpath_old(path).replace('\\', '/')
else:
    from os.path import normpath

from requests_tool import sync_trans, upload_translation



para_id = "7650"
para_path = normpath((os.environ.get('GITHUB_WORKSPACE')+"/translations/texts"))
para_token = os.environ.get('PARA_TOKEN')
if __name__ == '__main__':
    sync_trans(para_path, para_id, para_token, reupload=False)
    upload_translation(para_path, para_id, para_token)