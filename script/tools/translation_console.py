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

from export_mod import dump_patch
from export_mod_para import export_mod_para
from translation_memory import *


import configparser
config = configparser.ConfigParser()
root_dir = os.path.split(os.path.realpath(__file__))[0]

try:
    config.read(
        normpath(join(root_dir,"acess_key.ini")))
    para_api = config.get("SETTINGS", "para_apikey")
except:
    para_api = None

starcore_memory = normpath(join(root_dir,"starcore_memory.json"))


class Interface:
    handler = None

    def print_info(self):
        print("""
之前写的非常屑的小脚本的集合，界面很拙劣的模仿了龙骑士的写法，确切来说就是复制粘贴。
为了偷懒所以进行了大量的改装！
        """)

        def takename(elem):
            return elem["name"]
        for index, value in enumerate(file_list):
            print(str(index+1) + "："+value["name"])

        print("""
0：退出
        """)

    def get_keyword(self, kw):
        if kw == "0":
            exit(1)
        try:
            if int(kw) > 0 and int(kw) <= len(file_list):
                choice = input("""
请选择：
1：进行过滤并生成待翻译文件
2：导出并与other合并
3：翻译记忆
4:从paratranz下载翻译
5:将翻译上传至paratranz
6:同步至paratranz
请输入指令：
                                """)
                data = file_list[int(kw)-1]
                if choice == "1":
                    if data["processer"] in ["stbtran", "stbtran_mutimods", "stbtran_para", "stbtran_mutimods_para"]:
                        eval(data["processer"])(data["root_dir"], data["prefix"], data["files_of_interest"],
                                                data["patch_serialization"], data["dir_blacklist"], data["path_blacklist"], data["ignore_filelist"], data["string_blacklist"], texts_prefix=data["texts_prefix"])
                    else:
                        print("无指定过滤器"+data["processer"])
                elif choice == "2":
                    if data["processer"] in ["stbtran", "stbtran_mutimods"]:
                        dump_patch(data["prefix"], join(
                            data["prefix"], "utf8"), others_prfix="others")
                    elif data["processer"] in ["stbtran_para", "stbtran_mutimods_para"]:
                        export_mod_para(
                            data["prefix"], texts_prfix=data["texts_prefix"], mods_prfix="utf8", others_prfix="others")
                elif choice == "3":
                    choice = input("""
1.导出记忆
2.导入记忆
3.导入标准记忆
                    """)
                    if data["processer"] in ["stbtran", "stbtran_mutimods"]:
                        if choice == "1":
                            export_memory(normpath(join(data["prefix"], data["texts_prefix"])), normpath(
                                join(data["prefix"], "memory.json")))
                        elif choice == "2":
                            import_memory(normpath(join(data["prefix"], data["texts_prefix"])), normpath(
                                join(data["prefix"], "memory.json")))
                        elif choice == "3":
                            import_memory(normpath(
                                join(data["prefix"], data["texts_prefix"])), normpath(starcore_memory))
                    elif data["processer"] in ["stbtran_para", "stbtran_mutimods_para"]:
                        if choice == "1":
                            print(normpath(join(data["prefix"], data["texts_prefix"]))+normpath(
                                join(data["prefix"], "memory.json")))
                            export_memory_para(normpath(join(data["prefix"], data["texts_prefix"])), normpath(
                                join(data["prefix"], "memory.json")))
                        elif choice == "2":
                            import_memory_para(normpath(join(data["prefix"], data["texts_prefix"])), normpath(
                                join(data["prefix"], "memory.json")))
                        elif choice == "3":
                            import_memory_para(normpath(
                                join(data["prefix"], data["texts_prefix"])), normpath(starcore_memory))
                elif choice == "4":
                    if para_api != None:
                        Authorization = para_api
                    else:
                        Authorization = input("请输入token：")
                    download_translation(
                        data["prefix"]+"/"+data["texts_prefix"], data["para"]["id"], Authorization, subdir=data["para"]["subdir"])
                elif choice == "5":
                    if para_api != None:
                        Authorization = para_api
                    else:
                        Authorization = input("请输入token：")
                    choice = input("""
1.默认上传
2.强制上传
                    """)
                    if choice == "1":
                        upload_translation(
                            data["prefix"]+"/"+data["texts_prefix"], data["para"]["id"], Authorization, subdir=data["para"]["subdir"], force_updata=False)
                    elif choice == "2":
                        upload_translation(
                            data["prefix"]+"/"+data["texts_prefix"], data["para"]["id"], Authorization, subdir=data["para"]["subdir"], force_updata=True)
                elif choice == "6":
                    if para_api != None:
                        Authorization = para_api
                    else:
                        Authorization = input("请输入token：")
                    choice = input("""
1.默认同步
2.强制同步
                    """)
                    if choice == "1":
                        sync_trans(data["prefix"]+"/"+data["texts_prefix"], data["para"]
                                   ["id"], Authorization, subdir=data["para"]["subdir"], reupload=False)
                    elif choice == "2":
                        sync_trans(data["prefix"]+"/"+data["texts_prefix"], data["para"]
                                   ["id"], Authorization, subdir=data["para"]["subdir"], reupload=True)
                else:
                    print("输入的指令不正确！")
        except:
            print("输入的指令不正确！")


if __name__ == '__main__':
    interface = Interface()
    interface.print_info()
    keyword = ""
    while True:
        keyword = input("请输入指令：")
        interface.get_keyword(keyword)
