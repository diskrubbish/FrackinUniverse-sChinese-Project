import os

from para_api import get_string,file,get_artifacts,download_artifacts,file_list

from requests_tool import get_files_list,process_trans
from download_paratrans import fix_transltion
#"cd11860c565ed926ea5b2aa41697fd57"
if __name__ == "__main__":
    #print(get_string(7650, os.environ.get('PARA_TOKEN'), 318776779))

    #print(file(7650, os.environ.get('PARA_TOKEN'), fileid=998028))

    #print(get_files_list(7650,os.environ.get('PARA_TOKEN')))
    #download_artifacts(7650, "cd11860c565ed926ea5b2aa41697fd57","F:/workplace/FrackinUniverse-sChinese-Project/script/tools")
    #print("#replace#/shipStatus/0/text".split("#")[2])
    #print(os.path.relpath("F:/workplace/FrackinUniverse-sChinese-Project/translations/texts/ai/ai.config.patch","F:/workplace/FrackinUniverse-sChinese-Project/translations/texts"))
    #fix_transltion("F:/workplace/FrackinUniverse-sChinese-Project/translations/texts","F:/workplace/FrackinUniverse-sChinese-Project/temp/data/raw","F:/workplace/FrackinUniverse-sChinese-Project/translations/texts/ai/ai.config.patch")
    print({i["name"]:i["id"] for i in file_list(7650, "cd11860c565ed926ea5b2aa41697fd57")})