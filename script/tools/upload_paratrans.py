from sys import platform
from os.path import join
import os
if platform == "win32":
    from os.path import normpath as normpath_old
    def normpath(path):
        return normpath_old(path).replace('\\', '/')
else:
    from os.path import normpath
from extract_labels_config import file_list

from requests_tool import download_translation, sync_trans, upload_translation

from translation_memory import *


import configparser

para_id = "7650"
para_path = "F:/workplace/FrackinUniverse-sChinese-Project/translations/texts"
Authorization = "cd11860c565ed926ea5b2aa41697fd57"
if __name__ == '__main__':

    #sync_trans(para_path, para_id, Authorization, reupload=False)
    upload_translation(para_path, para_id, Authorization)