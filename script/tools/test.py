
import os
#from stbtran_utils import create_metadata
from para_api import get_string,file,get_artifacts,download_artifacts,file_list,get_artifacts,trigger_artifacts
import time
"""

from requests_tool import get_files_list,process_trans

#from download_paratrans import fix_transltion
#"cd11860c565ed926ea5b2aa41697fd57"
"""
if __name__ == "__main__":
    #create_metadata("F:/workplace/FrackinUniverse","F:/workplace/FrackinUniverse-sChinese-Project/translations")
    #print(trigger_artifacts(7650, "cd11860c565ed926ea5b2aa41697fd57"))
    print(time.mktime(time.strptime(get_artifacts(7650, "cd11860c565ed926ea5b2aa41697fd57")['createdAt'],"%Y-%m-%dT%H:%M:%S.%f%z")))
    #print(get_files_list(7650,os.environ.get('PARA_TOKEN')))
    #download_artifacts(7650, "cd11860c565ed926ea5b2aa41697fd57","F:/workplace/FrackinUniverse-sChinese-Project/script/tools")
    #print("#replace#/shipStatus/0/text".split("#")[2])
    #print(os.path.relpath("F:/workplace/FrackinUniverse-sChinese-Project/translations/texts/ai/ai.config.patch","F:/workplace/FrackinUniverse-sChinese-Project/translations/texts"))
    #fix_transltion("F:/workplace/FrackinUniverse-sChinese-Project/translations/texts","F:/workplace/FrackinUniverse-sChinese-Project/temp/data/raw","F:/workplace/FrackinUniverse-sChinese-Project/translations/texts/ai/ai.config.patch")