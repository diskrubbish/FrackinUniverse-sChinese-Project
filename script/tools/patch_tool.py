import json
import os
import re
from codecs import open as open_n_decode
from json_tools import field_by_path, list_field_paths, prepare
from sys import platform
from os.path import abspath, basename, dirname, exists, join, relpath

if platform == "win32":
    from os.path import normpath as normpath_old

    def normpath(path):
        return normpath_old(path).replace("\\", "/")

else:
    from os.path import normpath


def detect_patch(jsons):
    result = json.loads(prepare(jsons))
    new_list = list()
    for i in result:
        if "path" in i:
            new_list.append(i)
        else:
            for v in i:
                new_list.append(v)
    return new_list


# 绝对可靠的扫描方式，针对普通的patch，摒弃了繁琐的转换和词典筛选！


"""
def trans_patch(jsons, ex=None):
    json_text = detect_patch(jsons)
    fin_result = dict()
    for i in json_text:
        try:
            if i['op'] == "add" or i['op'] == "replace":
                subpath = i['path']
                if isinstance(i['value'], str):
                    if i['op'] == "add" and subpath.endswith("/-") and ex != None:
                        for end in ex.keys():
                            if subpath.rstrip("/-").endswith(end):
                                fin_result[normpath(subpath.replace(
                                    "/-", "/"+str(ex[end]["index"])))] = i['value']
                                if ex[end]["increase"] == True:
                                    ex[end]["index"] = ex[end]["index"]+1
                        else:
                            pass
                    else:
                        fin_result[subpath] = i['value']
                elif isinstance(i['value'], (list, dict)):
                    contexts = list_field_paths(i['value'])
                    if i['op'] == "add" and subpath.endswith("/-") and ex != None:
                        for v in contexts:
                            for end in ex.keys():
                                if subpath.rstrip("/-").endswith(end):
                                    fin_result[normpath(join(subpath.replace(
                                            "/-", "/"+str(ex[end]["index"])), str(v)))] = field_by_path(i['value'], str(v))
                                    if ex[end]["increase"] == True:
                                        ex[end]["index"] = ex[end]["index"]+1
                                else:
                                    continue
                    else:
                        for v in contexts:
                            fin_result[normpath(join(subpath, str(v)))] = field_by_path(
                                i['value'], str(v))
        except:
            return fin_result
    return fin_result
"""


def trans_patch(jsons, ex=None):
    json_text = detect_patch(jsons)
    fin_result = {}

    def add_or_replace(subpath, value):
        if isinstance(value, str):
            fin_result[subpath[1 : len(subpath)] if subpath[0] == "/" else subpath] = (
                value
            )
        elif isinstance(value, (list, dict)):
            contexts = list_field_paths(value)
            for v in contexts:
                fin_path = normpath(join(subpath, str(v)))
                fin_result[
                    fin_path[1 : len(fin_path)] if fin_path[0] == "/" else fin_path
                ] = field_by_path(value, str(v))

    for i in json_text:
        try:
            if "value" in  i.keys():
                subpath = i["path"]
                value = i["value"]
                is_add = i["op"] == "add"
                is_replace = i["op"] == "replace"
                if is_add or is_replace:
                    if is_add and subpath.endswith("/-") and ex is not None:
                        for end in ex.keys():
                            if subpath.rstrip("/-").endswith(end):
                                index_path = normpath(
                                subpath.replace("/-", f"/{ex[end]['index']}")
                                )
                                fin_result[index_path] = value
                                if ex[end]["increase"]:
                                    ex[end]["index"] += 1
                                break  # Exit loop after processing the first match
                    else:
                        add_or_replace(subpath, value)

        except:
            return fin_result

    return fin_result


def replace_the_path(path, rule):
    path_list_3 = list()
    o = rule[1]
    for text in path:
        if rule[2] == 1:
            if not re.search(rule[0] + "/" + "-", text) == None:
                wait = text.replace(rule[0] + "/" + "-", rule[0] + "/" + str(o))
                path_list_3.append(wait)
                o = o + 1
            else:
                path_list_3.append(text)
        else:
            if not re.search(rule[0] + "/" + "-", text) == None:
                wait = text.replace(rule[0] + "/-", rule[0] + "/" + str(rule[1]))
                path_list_3.append(wait)
            else:
                path_list_3.append(text)
    return path_list_3


def items_subset(items):
    file_list = []
    for originfile, jsonpaths in items:
        if isinstance(jsonpaths, list):
            for i in jsonpaths:
                file_list.append([originfile, i])
        else:
            file_list.append([originfile, jsonpaths])
    return file_list
