import json
from os import walk, makedirs, remove
from multiprocessing import Pool
import re
from codecs import open
from os.path import dirname, exists, relpath, abspath, basename
from os.path import join as join_path
from sys import platform
from functools import partial
from json_tools import prepare, field_by_path, list_field_paths

def export_memory_para_old(path, memory_file,show_fname=False):
    memory = dict()
    for path, d, filelist in walk(path):
        for filename in filelist:
            if basename(filename) in ["substitutions.json", "totallabels.json", "translatedlabels.json", "patch_substitutions.json", "parse_problem.txt", "_metadata", "_previewimage", "memory.json"]:
                continue
            i = join_path(path, filename)
            if show_fname  == True: 
                print(basename(i))
            with open(i, "rb+", "utf-8-sig") as f:
                jsondata = json.loads(prepare(f))
                for i, v in enumerate(jsondata):
                    if 'translation' in jsondata[i]:
                        if jsondata[i]['original'] in memory.keys():
                            pass
                        elif jsondata[i]['translation'] != "":
                            if jsondata[i]['original'] != jsondata[i]['translation']:
                                memory[jsondata[i]['original']
                                       ] = jsondata[i]['translation']
                    else:
                        pass
    result = json.dumps(memory, ensure_ascii=False,
                        sort_keys=True, indent=2)
    f = open(memory_file, "wb+", "utf-8-sig")
    f.write(result)
    f.close

def export_memory_para(path, memory_file,show_fname=False):
    memory = dict()
    for path, d, filelist in walk(path):
        for filename in filelist:
            if basename(filename) in ["substitutions.json", "totallabels.json", "translatedlabels.json", "patch_substitutions.json", "parse_problem.txt", "_metadata", "_previewimage", "memory.json"]:
                continue
            i = join_path(path, filename)
            if show_fname  == True: 
                print(basename(i))
            with open(i, "rb+", "utf-8-sig") as f:
                jsondata = json.loads(prepare(f))
                for i, v in enumerate(jsondata):
                    if 'value' in jsondata[i]:
                        if jsondata[i]['raw'] in memory.keys():
                            pass
                        elif jsondata[i]['value'] != "":
                            memory[jsondata[i]['raw']
                                       ] = jsondata[i]['value']
                    else:
                        pass
    result = json.dumps(memory, ensure_ascii=False,
                        sort_keys=True, indent=2)
    f = open(memory_file, "wb+", "utf-8-sig")
    f.write(result)
    f.close


def export_memory(path, memory_file,show_fname=False):
    memory = dict()
    for path, d, filelist in walk(path):
        for filename in filelist:
            if basename(filename) in ["substitutions.json", "totallabels.json", "translatedlabels.json", "patch_substitutions.json", "parse_problem.txt", "_metadata", "_previewimage", "memory.json"]:
                continue
            i = join_path(path, filename)
            if show_fname  == True: 
                print(basename(i))
            with open(i, "rb+", "utf-8-sig") as f:
                jsondata = json.loads(prepare(f))
                for i, v in enumerate(jsondata):
                    if 'Chs' in jsondata[i]['Texts']:
                        if jsondata[i]['Texts']['Eng'] in memory.keys():
                            pass
                        else:
                            memory[jsondata[i]['Texts']['Eng']
                                   ] = jsondata[i]['Texts']['Chs']
                    else:
                        pass
    result = json.dumps(memory, ensure_ascii=False,
                        sort_keys=True, indent=2)
    f = open(memory_file, "wb+", "utf-8-sig")
    f.write(result)
    f.close


def import_memory(path, memory_file,show_fname=False):
    memory = json.loads(prepare(open(memory_file, "r", "utf-8-sig")))
    for path, d, filelist in walk(path):
        for filename in filelist:
            if basename(filename) in ["substitutions.json", "totallabels.json", "translatedlabels.json", "patch_substitutions.json", "parse_problem.txt", "_metadata", "_previewimage", "memory.json"]:
                continue
            i = join_path(path, filename)
            if show_fname  == True: 
                print(basename(i))
            with open(i, "rb+", "utf-8-sig") as f:
                jsondata = json.loads(prepare(f))
                for t, v in enumerate(jsondata):
                    if 'Chs' in jsondata[t]['Texts']:
                        pass
                    else:
                        if jsondata[t]['Texts']['Eng'] in memory.keys():
                            jsondata[t]['Texts']['Chs'] = memory[jsondata[t]
                                                                 ['Texts']['Eng']]
            text = json.dumps(jsondata, ensure_ascii=False,
                              sort_keys=True, indent=2)
            f = open(i, "wb+", "utf-8-sig")
            f.write(text)
            f.close


def import_memory_para(path, memory_file,glitch=False,show_fname=False):
    memory = json.loads(prepare(open(memory_file, "r", "utf-8-sig")))
    for path, d, filelist in walk(path):
        for filename in filelist:
            if basename(filename) in ["substitutions.json", "totallabels.json", "translatedlabels.json", "patch_substitutions.json", "parse_problem.txt", "_metadata", "_previewimage", "memory.json"]:
                continue
            i = join_path(path, filename)
            if show_fname  == True: 
                print(basename(i))
            with open(i, "rb+", "utf-8-sig") as f:
                jsondata = json.load(f)
                for t, v in enumerate(jsondata):
                    if v['value'] != "":
                        pass
                    else:
                        if v['raw'] in memory.keys():
                            jsondata[t]['value'] = memory[jsondata[t]['raw']]
                        elif len(v['raw'].split(". ",1))>=2 and glitch==True:
                            if v['raw'].split(". ",1)[0]+"." in memory.keys() and v['raw'].split(". ",1)[1] in memory.keys():
                                jsondata[t]['value'] = memory[jsondata[t]['raw'].split(". ",1)[0]+"."]+memory[jsondata[t]['raw'].split(". ",1)[1]]
            text = json.dumps(jsondata, ensure_ascii=False,
                              sort_keys=True, indent=2)
            f = open(i, "wb+", "utf-8-sig")
            f.write(text)
            f.close


#export_memory_para("/workplace/StarBound_Mods_SChinese_Project/text/SChinese_para/raw","/workplace/StarBound_Mods_SChinese_Project/text/SChinese_para/memory.json")
#export_memory("F:/workplace/FFS-sChinese-Project/translations","F:/workplace/StarBound_Mods_SChinese_Project/text/FFS/memory.json")
#import_memory_para("/workplace/FrackinUniverse-sChinese-Project/translations/texts","F:/workplace/FrackinUniverse-sChinese-Project/memory.json")
#import_memory("F:/workplace/FrackinUniverse-sChinese-Project/translations","F:/workplace/FrackinUniverse-sChinese-Project-50f2f901921bf33addce960a95b157e379309e66/memory.json")
