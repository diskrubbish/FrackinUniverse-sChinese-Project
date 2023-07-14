#!/usr/bin/python3

from bisect import insort_left
from codecs import open as open_n_decode
from json import dump, load, loads, dumps
from functools import partial
from multiprocessing import Pool,cpu_count
from os import makedirs, remove, walk
from os.path import abspath, basename, dirname, exists, join, relpath
from re import compile as regex
from sys import platform
from patch_tool import trans_patch, items_subset
from json_tools import field_by_path, list_field_paths, prepare
##from adapt_translation import process_text
from shared_path import getSharedPath
from special_cases import specialSections

if platform == "win32":
    from os.path import normpath as normpath_old

    def normpath(path):
        return normpath_old(path).replace('\\', '/')
else:
    from os.path import normpath


class glitch:
    glitchEmoteExtractor = regex("^([In]{,3}\s?[A-Za-z-]+\.)\s+(.*)")
    glitchIsHere = regex("^.*[gG]litch.*")


def defaultHandler(val, filename, path):
    sec = ""
    for pattern in specialSections:
        if pattern.match(filename, path):
            sec = pattern.name
            break
    return [(sec, val, filename, path)]


def glitchDescriptionSpecialHandler(val, filename, path):
    extracted = glitch.glitchEmoteExtractor.match(val)
    is_glitch = glitch.glitchIsHere.match(path)
    if extracted is None or is_glitch is None:
        return False
    emote = extracted.groups()[0]
    text = extracted.groups()[1]
    t = defaultHandler(text, filename, normpath(
        join(path, "glitchEmotedText")))
    e = defaultHandler(emote, filename, normpath(join(path, "glitchEmote")))
    return t + e


textHandlers = [
    #glitchDescriptionSpecialHandler,
    defaultHandler
]

specialSharedPaths = {
    "glitchEmote": "glitchEmotes",
}


def chunk_parse_para(chunk, database, assets_dir, path_blacklist=None):
    for sec, val, fname, path in chunk:
        dname = dirname(fname)
        if len(path_blacklist) != 0:
            if dname in path_blacklist.keys():
                if path in path_blacklist[dname]:
                    continue
        filename = normpath(
            relpath(abspath(fname), abspath(assets_dir)))
        if filename not in database:
            database[filename] = dict()
        if path not in database[filename].keys():
            database[filename][path] = val
    return database


def process_label_para(database, prefix, header, outdata=False):
    result = dict()
    for key in database.keys():
        if key == "":
            continue
        objs = database[key]
        file = normpath(join(prefix, header, key + ".patch"))
        if exists(file):
            reference = dict()
            temp = list()
            try:
                with open_n_decode(file, 'r', 'utf-8') as f:
                    olddata = loads(prepare(f))
            except:
                print("Can not open old data " + basename(file))
                continue
            for data in olddata:
                reference[data["path"]] = [data["raw"], data["value"]]
            for obj in objs.keys():
                content = {"op": "replace", "path": obj, "raw": objs[obj]}
                if obj in reference.keys():
                    if reference[obj][0] != objs[obj]:
                        content["value"] = ""
                        if outdata == True:
                            if reference[obj][1] != "":
                                content["context"] = "之前文本：\n" + \
                                    reference[obj][1]
                            elif reference[obj][1] == "" and reference[obj][2] != "":
                                content["context"] = reference[obj][2]
                            else:
                                content["context"] = ""
                    elif reference[obj][0] == objs[obj]:
                        content["value"] = reference[obj][1]
                    else:
                        content["value"] = ""
                else:
                    content["value"] = ""
                temp.append(content)
        else:
            temp = list()
            for obj in objs.keys():
                content = {"op": "replace", "path": obj,
                           "raw": objs[obj], "value": ""}
                temp.append(content)
        result[file] = temp
    return result


def catch_danglings_para(target_path, file_buffer, ignore_filelist=None):
    to_remove = list()
    for subdir, dirs, files in walk(target_path):
        for thefile in files:
            fullname = normpath(join(subdir, thefile))
            if len(ignore_filelist) != 0:
                if thefile not in ignore_filelist:
                    if fullname not in file_buffer.keys():
                        to_remove.append(fullname)
            else:
                if fullname not in file_buffer.keys():
                    to_remove.append(fullname)
    return to_remove


def write_file_para(filename, content):
    filedir = dirname(filename)
    if len(filedir) > 0:
        makedirs(filedir, exist_ok=True)
    else:
        raise Exception("Filename without dir: " + filename)
    with open_n_decode(filename, "w", 'utf-8') as f:
        dump(content, f, ensure_ascii=False, indent=2, sort_keys=True)


def final_write_para(file_buffer, header, prefix, ignore_filelist=None):
    danglings = catch_danglings_para(
        join(prefix, header), file_buffer, ignore_filelist=ignore_filelist)
    print("These "+header+" files will be deleted:")
    for d in danglings:
        print('  ' + d)
    print('Writing...')
    with Pool(8) as p:
        p.map_async(remove, danglings)
        p.starmap_async(
            write_file_para, list(file_buffer.items()))
        #write_result = p.starmap_async(write_file, file_buffer)
        p.close()
        p.join()


def construct_db_para(assets_dir, files_of_interest, patch_serialization, dir_blacklist, path_blacklist, ignore_filelist, string_blacklist, parse_process_number=cpu_count()):
    print("Scanning assets at " + assets_dir)
    endings = tuple(files_of_interest.keys())
    db = [{}, {}]
    foi = list()
    foi_patch = list()
    for subdir, dirs, files in walk(assets_dir):
        for thefile in files:
            if len(dir_blacklist) != 0:
                if dirname(subdir) in dir_blacklist:
                    break
            if thefile.endswith(endings):
                foi.append(normpath(join(subdir, thefile)))
            elif thefile.endswith(".patch"):
                if thefile.replace(".patch", "").endswith(endings):
                    foi_patch.append(normpath(join(subdir, thefile)))
    print("Step 1: scanning normal files")
    with Pool(parse_process_number) as p:
        r = p.imap_unordered(
            partial(parseFile, files_of_interest=files_of_interest, ignore_filelist=ignore_filelist, string_blacklist=string_blacklist,), foi)
        for chunk in r:
            chunk_parse_para(chunk, db[0], assets_dir,
                             path_blacklist=path_blacklist)

    print("Step 2: scanning patch files")
    with Pool(parse_process_number) as p:
        r_patch = p.imap_unordered(
            partial(parsePatchFile, files_of_interest=files_of_interest, patch_serialization=patch_serialization, ignore_filelist=ignore_filelist, string_blacklist=string_blacklist,), foi_patch)

        for chunk in r_patch:
            chunk_parse_para(chunk,  db[0], assets_dir,
                             path_blacklist=path_blacklist)
    return db


def construct_db_para_muti(assets_dir_list, files_of_interest, patch_serialization, dir_blacklist, path_blacklist, ignore_filelist, string_blacklist, parse_process_number=cpu_count()):
    endings = tuple(files_of_interest.keys())
    db = [{"": dict()}]
    foi = list()
    foi_patch = list()
    for assets_dir in assets_dir_list:
        print("Scanning assets at " + assets_dir)
        for subdir, dirs, files in walk(assets_dir):
            for thefile in files:
                if len(dir_blacklist) != 0:
                    if dirname(subdir) in dir_blacklist:
                        continue
                if thefile.endswith(endings):
                    foi.append(normpath(join(subdir, thefile)))
                elif thefile.endswith(".patch"):
                    if thefile.replace(".patch", "").endswith(endings):
                        foi_patch.append(normpath(join(subdir, thefile)))
        print("Step 1: scanning normal files")
        with Pool(parse_process_number) as p:
            r = p.imap_unordered(
                partial(parseFile, files_of_interest=files_of_interest, ignore_filelist=ignore_filelist, string_blacklist=string_blacklist), foi)
            for chunk in r:
                chunk_parse_para(
                    chunk, db[0], assets_dir, path_blacklist=path_blacklist)

        print("Step 2: scanning patch files")
        with Pool(parse_process_number) as p:
            r_patch = p.imap_unordered(
                partial(parsePatchFile, files_of_interest=files_of_interest, patch_serialization=patch_serialization, ignore_filelist=ignore_filelist, string_blacklist=string_blacklist), foi_patch)

            for chunk in r_patch:
                chunk_parse_para(
                    chunk,  db[0], assets_dir, path_blacklist=path_blacklist)
    return db


def chunk_parse(chunk, database, assets_dir, path_blacklist):
    for sec, val, fname, path in chunk:
        true_fname = dirname(fname)
        if len(path_blacklist) != 0:
            if true_fname in path_blacklist.keys():
                if path in path_blacklist[true_fname]:
                    continue
        if sec not in database:
            database[sec] = dict()
        if val not in database[sec]:
            database[sec][val] = dict()
        filename = normpath(
            relpath(abspath(fname), abspath(assets_dir)))
        if filename not in database[sec][val]:
            database[sec][val][filename] = list()
        if path not in database[sec][val][filename]:
            insort_left(database[sec][val][filename], path)
    return database


def parseFile(filename, files_of_interest, ignore_filelist, string_blacklist, show_fname=False):
    chunk = list()
    if basename(filename)not in ignore_filelist:
        if show_fname == True:
            print(basename(filename))
        with open_n_decode(filename, "r", "utf_8_sig") as f:
            try:
                string = prepare(f)
                jsondata = loads(string)
                paths = list_field_paths(jsondata)
            except:
                print("Cannot parse " + filename)
                return []
            dialog = dirname(filename).endswith("dialog")

            for k in files_of_interest.keys():
                if filename.endswith(k) or k == "*":
                    for path in paths:
                        if len(path.split("/")) >= 15:
                            print("Some path in" + filename+"'s len > 15！")
                            continue
                        for roi in files_of_interest[k]:
                            if roi.match(path) or dialog:
                                val = field_by_path(jsondata, path)
                                if not type(val) is str:
                                    print("File: " + filename)
                                    print("Type of " + path +
                                          " is not a string!")
                                    continue
                                if val == "":
                                    continue
                                elif string_blacklist != None:
                                    if val in string_blacklist:
                                        continue
                                for handler in textHandlers:
                                    res = handler(val, filename, '/' + path)
                                    if res:
                                        chunk += res
                                        break
                                break

    return chunk


def parsePatchFile(filename, files_of_interest, patch_serialization, ignore_filelist, string_blacklist, show_fname=False):
    chunk = list()
    if basename(filename)not in ignore_filelist:
        if show_fname == True:
            print(basename(filename))
        with open_n_decode(filename, "r", "utf_8_sig") as f:
            try:
                if len(patch_serialization) != 0:
                    if basename(filename) in dict.keys(patch_serialization):
                        patchdata = trans_patch(
                            f, ex=patch_serialization[basename(filename)])
                    else:
                        patchdata = trans_patch(f)
                else:
                    patchdata = trans_patch(f)
                paths = patchdata.keys()
            except:
                print("Cannot parse " + filename)
                return []
            filename = filename.replace('.patch', "")
            dialog = dirname(filename).endswith("dialog")
            for k in files_of_interest.keys():
                if filename.endswith(k) or k == "*":
                    for i, path in enumerate(paths):
                        if len(path.split("/")) >= 15:
                            continue
                        for roi in files_of_interest[k]:
                            if roi.match(path) or dialog:
                                val = patchdata[path]
                                if not type(val) is str:
                                    print("File: " + filename)
                                    print("Type of " + path +
                                          " is not a string!")
                                    continue
                                if val == "":
                                    continue
                                elif string_blacklist != None:
                                    if val in string_blacklist:
                                        continue
                                for handler in textHandlers:
                                    res = handler(val, filename, path)
                                    if res:
                                        chunk += res
                                        break
                                break
    return chunk


def construct_db(assets_dir, files_of_interest, patch_serialization, dir_blacklist, path_blacklist, ignore_filelist, parse_process_number=cpu_count()):
    print("Scanning assets at " + assets_dir)
    endings = tuple(files_of_interest.keys())
    db = [{"": dict()}, {"": dict()}]
    foi = list()
    foi_patch = list()
    for subdir, dirs, files in walk(assets_dir):
        for thefile in files:
            if len(dir_blacklist) != 0:
                if dirname(subdir) in dir_blacklist:
                    break
            if thefile.endswith(endings):
                foi.append(normpath(join(subdir, thefile)))
            elif thefile.endswith(".patch"):
                if thefile.replace(".patch", "").endswith(endings):
                    foi_patch.append(normpath(join(subdir, thefile)))
    print("Step 1: scanning normal files")
    with Pool(parse_process_number) as p:
        r = p.imap_unordered(
            partial(parseFile, files_of_interest=files_of_interest, ignore_filelist=ignore_filelist), foi)
        for chunk in r:
            chunk_parse(chunk, db[0], assets_dir, path_blacklist)

    print("Step 2: scanning patch files")
    with Pool(parse_process_number) as p:
        r_patch = p.imap_unordered(
            partial(parsePatchFile, files_of_interest=files_of_interest, patch_serialization=patch_serialization, ignore_filelist=ignore_filelist), foi_patch)
        for chunk in r_patch:
            chunk_parse(chunk,  db[1], assets_dir, path_blacklist)
    return db


def construct_db_muti(assets_dir_list, files_of_interest, patch_serialization, dir_blacklist, path_blacklist, ignore_filelist, parse_process_number=cpu_count()):
    foi = list()
    foi_patch = list()
    db = [{"": dict()}, {"": dict()}]
    for assets_dir in assets_dir_list:
        print("Scanning assets at " + assets_dir)
        endings = tuple(files_of_interest.keys())
        cache = list()
        cache_patch = list()
        for subdir, dirs, files in walk(assets_dir):
            for thefile in files:
                if len(dir_blacklist) != 0:
                    if dirname(subdir) in dir_blacklist:
                        break
                if thefile.endswith(endings):
                    cache.append(normpath(join(subdir, thefile)))
                elif thefile.endswith(".patch"):
                    cache_patch.append(normpath(join(subdir, thefile)))
        foi = foi + cache
        foi_patch = foi_patch+cache_patch
    print("Step 1: scanning normal files")
    with Pool(parse_process_number) as p:
        r = p.imap_unordered(
            partial(parseFile, files_of_interest=files_of_interest, ignore_filelist=ignore_filelist), foi)
        for chunk in r:
            chunk_parse(chunk, db[0], assets_dir, path_blacklist)

    print("Step 2: scanning patch files")
    with Pool(parse_process_number) as p:
        r_patch = p.imap_unordered(
            partial(parsePatchFile, files_of_interest=files_of_interest, patch_serialization=patch_serialization, ignore_filelist=ignore_filelist), foi_patch)
        for chunk in r_patch:
            chunk_parse(chunk,  db[1], assets_dir, path_blacklist)
    return db


def file_by_assets(assets_fname, field, substitutions, header):
    if assets_fname in substitutions and field in substitutions[assets_fname]:
        return substitutions[assets_fname][field]
    else:
        return normpath(join(header, assets_fname)) + ".json"


def process_label(combo, prefix, adapt=False):
    label, files, oldsubs, section, header = combo
    substitutions = dict()
    obj_file = normpath(getSharedPath(files.keys()))
    translation = dict()
    if section:
        translation["Comment"] = section
    translation["Texts"] = dict()
    translation["Texts"]["Eng"] = label
    translation["DeniedAlternatives"] = list()
    filename = ""
    print(files)
    for thefile, fields in files.items():
        for field in fields:
            fieldend = basename(field)
            if fieldend in specialSharedPaths:
                obj_file = normpath(specialSharedPaths[fieldend])
            if obj_file == '.':
                obj_file = "wide_spread_fields"
            filename = normpath(join(prefix, header, obj_file + ".json"))
            if thefile != obj_file or fieldend in ["glitchEmotedText"]:
                if thefile not in substitutions:
                    substitutions[thefile] = dict()
                substitutions[thefile][field] = normpath(
                    relpath(filename, prefix))
            oldfile = normpath(
                join(prefix, file_by_assets(thefile, field, oldsubs, header)))
            if exists(oldfile):
                olddata = []
                try:
                    with open_n_decode(oldfile, 'r', 'utf-8') as f:
                        olddata = load(f)
                except:
                    pass
                for oldentry in olddata:
                    if oldentry["Texts"]["Eng"] == label:
                        if "Chs" in oldentry["Texts"].keys() and isinstance(oldentry["Texts"]["Chs"], dict):
                            if oldentry["Files"] == files:
                                break
                            else:
                                new_text_list = dict()
                                compare_list = list()
                                for a_i in items_subset(files.items()):
                                    if a_i in items_subset(oldentry["Files"].items()):
                                        compare_list.append(a_i)
                                for i in compare_list:
                                    if i in items_subset(oldentry["Files"].items()):
                                        if str(items_subset(oldentry["Files"].items()).index(i)+1) in oldentry["Texts"]["Chs"].keys():
                                            new_text_list[str(items_subset(files.items()).index(
                                                i)+1)] = oldentry["Texts"]["Chs"][str(items_subset(oldentry["Files"].items()).index(i)+1)]
                                if str(0) in oldentry["Texts"]["Chs"].keys():
                                    new_text_list[str(
                                        0)] = oldentry["Texts"]["Chs"][str(0)]
                                oldentry["Texts"]["Chs"] = new_text_list
                                """
                                if len(oldentry["Texts"]["Chs"]) == 1:
                                    oldentry["Texts"]["Chs"] = oldentry["Texts"]["Chs"].values()[
                                        0]
                                """
                        if "DeniedAlternatives" in oldentry:
                            for a in oldentry["DeniedAlternatives"]:
                                if a not in translation["DeniedAlternatives"]:
                                    insort_left(
                                        translation["DeniedAlternatives"], a)
                        translation["Texts"].update(oldentry["Texts"])
                        break
                    """
                    elif oldentry["Texts"]["Eng"] != label and adapt == True:
                        if "Chs" in oldentry["Texts"].keys() and isinstance(oldentry["Texts"]["Chs"], str):
                            try:
                                oldentry["Texts"]["Chs"] = process_text(
                                    oldentry["Texts"]["Chs"], oldentry["Texts"]["Eng"], label)
                                if oldentry["Texts"]["Chs"] == label:
                                    break
                                oldentry["Texts"]["Eng"] = label
                                if "DeniedAlternatives" in oldentry:
                                    for a in oldentry["DeniedAlternatives"]:
                                        if a not in translation["DeniedAlternatives"]:
                                            insort_left(
                                                translation["DeniedAlternatives"], a)
                                translation["Texts"].update(oldentry["Texts"])
                                break
                            except:
                                pass
                    """
    translation["Files"] = files
    print((filename, translation, substitutions))
    return (filename, translation, substitutions)


def prepare_to_write(database, sub_file, header, prefix, adapt=False):
    file_buffer = dict()
    substitutions = dict()
    oldsubs = dict()
    header = header
    print("Trying to merge with old "+header+" data...")
    try:
        with open_n_decode(sub_file, "r", 'utf-8') as f:
            oldsubs = load(f)
    except:
        print("No old data found, creating new database.")
    for section, thedatabase in database.items():
        with Pool(8) as p:
            result = p.imap_unordered(partial(process_label, prefix=prefix, adapt=adapt),
                                      [(f, d, oldsubs, section, header) for f, d in thedatabase.items()], 40)
            for fn, js, sb in result:
                for fs, flds in sb.items():
                    if fs not in substitutions:
                        substitutions[fs] = flds
                    else:
                        substitutions[fs].update(flds)
                if fn not in file_buffer:
                    file_buffer[fn] = list()
                file_buffer[fn].append(js)
    file_buffer[sub_file] = substitutions
    return file_buffer


def catch_danglings(target_path, file_buffer, ignore_filelist):
    to_remove = list()
    for subdir, dirs, files in walk(target_path):
        for thefile in files:
            fullname = normpath(join(subdir, thefile))
            if thefile not in ignore_filelist:
                if fullname not in file_buffer:
                    to_remove.append(fullname)
    return to_remove


def write_file(filename, content):
    filedir = dirname(filename)
    if not filename.endswith("substitutions.json"):
        content = sorted(content, key=lambda x: x["Texts"]["Eng"])
    if len(filedir) > 0:
        makedirs(filedir, exist_ok=True)
    else:
        raise Exception("Filename without dir: " + filename)
    with open_n_decode(filename, "w", 'utf-8') as f:
        dump(content, f, ensure_ascii=False, indent=2, sort_keys=True)
        # print("Written " + filename)


# auto processing
def final_write(file_buffer, header, prefix, ignore_filelist):
    danglings = catch_danglings(
        join(prefix, header), file_buffer, ignore_filelist)
    print("These "+header+" files will be deleted:")
    for d in danglings:
        print('  ' + d)
        print('Writing...')
    with Pool(8) as p:
        delete_result = p.map_async(remove, danglings)
        write_result = p.starmap_async(write_file, list(file_buffer.items()))
        p.close()
        p.join()


'''
def final_write(file_buffer):
  danglings = catch_danglings(join(prefix, "texts"), file_buffer)
  print("These files will be deleted:")
  for d in danglings:
    print('  ' + d)
  print('continue? (y/n)')
  ans = get_answer(['y', 'n'])
  if ans == 'n':
    print('Cancelled!')
    return
  print('Writing...')
  with Pool() as p:
    delete_result = p.map_async(remove, danglings)
    write_result = p.starmap_async(write_file, list(file_buffer.items()))
    p.close()
    p.join()
'''

"""
def extract_labels(root_dir, prefix):
    root_dir = root_dir
    prefix = prefix
    thedatabase = construct_db(root_dir)
    file_buffer = prepare_to_write(thedatabase)
    final_write(file_buffer)
"""


def stbtran(root_dir, prefix,
            files_of_interest, patch_serialization,  dir_blacklist, path_blacklist, ignore_filelist, parse_process_number=cpu_count(),
            sub_fname="substitutions.json", patch_sub_fname="patch_substitutions.json", texts_prefix="texts", patch_texts_prefix="patches", adapt=False):
    sub_file = normpath(join(prefix, sub_fname))
    patch_sub_file = normpath(join(prefix, patch_sub_fname))
    thedatabase = construct_db(
        root_dir, files_of_interest, patch_serialization,  dir_blacklist, path_blacklist, ignore_filelist, parse_process_number=parse_process_number)
    file_buffer = prepare_to_write(
        thedatabase[0], sub_file, texts_prefix, prefix, adapt=adapt)
    # with open_n_decode("F:/workplace/StarBound_-Mod_Misc_Chinese_Project/script/tools copy/test.json", "w", 'utf-8') as f:
    ##dump(file_buffer, f, ensure_ascii=False, indent=2, sort_keys=True)
    patch_file_buffer = prepare_to_write(
        thedatabase[1], patch_sub_file, patch_texts_prefix, prefix, adapt=adapt)
    final_write(file_buffer, texts_prefix, prefix, ignore_filelist)
    final_write(patch_file_buffer, patch_texts_prefix, prefix, ignore_filelist)


def stbtran_mutimods(root_dir_list, prefix,
                     files_of_interest, patch_serialization,  dir_blacklist, path_blacklist, ignore_filelist, parse_process_number=cpu_count(),
                     sub_fname="substitutions.json", patch_sub_fname="patch_substitutions.json", texts_prefix="texts", patch_texts_prefix="patches", adapt=False):
    sub_file = normpath(join(prefix, sub_fname))
    patch_sub_file = normpath(join(prefix, patch_sub_fname))
    thedatabase = construct_db_muti(
        root_dir_list, files_of_interest, patch_serialization, dir_blacklist, path_blacklist, ignore_filelist, parse_process_number=parse_process_number)
    file_buffer = prepare_to_write(
        thedatabase[0], sub_file, texts_prefix, prefix, adapt=adapt)
    patch_file_buffer = prepare_to_write(
        thedatabase[1], patch_sub_file, patch_texts_prefix, prefix, adapt=adapt)
    final_write(file_buffer, texts_prefix, prefix, ignore_filelist)
    final_write(patch_file_buffer, patch_texts_prefix, prefix, ignore_filelist)


def stbtran_para(root_dir, prefix,
                 files_of_interest, patch_serialization,  dir_blacklist, path_blacklist, ignore_filelist, string_blacklist, parse_process_number=cpu_count(), texts_prefix="texts", ):
    thedatabase = construct_db_para(
        root_dir, files_of_interest, patch_serialization,  dir_blacklist, path_blacklist, ignore_filelist, string_blacklist, parse_process_number=parse_process_number)
    file_buffer = process_label_para(thedatabase[0], prefix, texts_prefix)
    final_write_para(file_buffer, texts_prefix, prefix,
                     ignore_filelist=ignore_filelist)


def stbtran_mutimods_para(root_dir, prefix,
                          files_of_interest, patch_serialization,  dir_blacklist, path_blacklist, ignore_filelist, string_blacklist, parse_process_number=cpu_count(), texts_prefix="texts", ):
    thedatabase = construct_db_para_muti(
        root_dir, files_of_interest, patch_serialization,  dir_blacklist, path_blacklist, ignore_filelist, string_blacklist, parse_process_number=parse_process_number)
    file_buffer = process_label_para(thedatabase[0], prefix, texts_prefix)
    final_write_para(file_buffer, texts_prefix, prefix,
                     ignore_filelist=ignore_filelist)
