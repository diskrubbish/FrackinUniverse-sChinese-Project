#!/usr/bin/python3

from bisect import insort_left
from json import dump, load, loads, dumps
from functools import partial
from multiprocessing import Pool
from os import makedirs, remove, walk
from os.path import abspath, basename, dirname, exists, join, relpath
from re import compile as regex
from sys import platform
from patch_tool import trans_patch
from json_tools import field_by_path, list_field_paths, prepare
from special_cases import specialSections


if platform == "win32":
    from os.path import normpath as normpath_old

    def normpath(path):
        return normpath_old(path).replace("\\", "/")

else:
    from os.path import normpath


def defaultHandler(val, filename, path):
    sec = ""
    for pattern in specialSections:
        if pattern.match(filename, path):
            sec = pattern.name
            break
    return [(sec, val, filename, path)]


textHandlers = [defaultHandler]

specialSharedPaths = {
    "glitchEmote": "glitchEmotes",
}


def get_category_list(root_dir, default_list):
    file = normpath(join(root_dir, "items/categories.config.patch"))
    if exists(file):
        try:
            with open(file, "r", encoding="utf-8-sig") as f:
                category_data = trans_patch(f)
                result = [v.split("/")[1] for v in category_data.keys()] + default_list
                return result
        except:
            return default_list
    else:
        return default_list


def chunk_parse_para(chunk, database, assets_dir, path_blacklist=dict()):
    for sec, val, fname, path in chunk:
        dname = dirname(fname)
        if len(path_blacklist) != 0:
            if dname in path_blacklist.keys():
                if path in path_blacklist[dname]:
                    continue
        filename = normpath(relpath(abspath(fname), abspath(assets_dir)))
        if filename not in database:
            database[filename] = dict()
        if path not in database[filename].keys():
            database[filename][path] = val
    return database


def process_label_para(database, prefix, header, outdata=False):
    result = {}

    def load_old_data(file):
        try:
            with open(file, "r", encoding="utf-8-sig") as f:
                return loads(prepare(f),strict=False)
        except Exception as e:
            print(f"Can not open old data {basename(file)}")
            return None

    for key, objs in database.items():
        if key == "":
            continue

        file = normpath(join(prefix, header, f"{key}.patch"))
        if not exists(file):
            result[file] = [
                {"op": "replace", "path": obj, "raw": obj_value, "value": ""}
                for obj, obj_value in objs.items()
            ]
            continue

        olddata = load_old_data(file)
        if olddata is None:
            continue

        reference = {data["path"]: [data["raw"], data["value"]] for data in olddata}
        old_dict = {data["raw"]: data["value"] for data in olddata}

        temp = []
        for obj, obj_value in objs.items():
            content = {"op": "replace", "path": obj, "raw": obj_value}

            if obj in reference:
                if reference[obj][0] != obj_value:
                    content["value"] = old_dict.get(obj_value, "")
                    if outdata:
                        content["context"] = (
                            "之前文本：\n" + reference[obj][1]
                            if reference[obj][1]
                            else reference[obj][2] if reference[obj][2] else ""
                        )
                else:
                    content["value"] = reference[obj][1]
            else:
                content["value"] = ""

            temp.append(content)

        result[file] = temp

    return result


def construct_db_para(
    assets_dir,
    files_of_interest,
    patch_serialization,
    dir_blacklist,
    path_blacklist,
    ignore_filelist,
    string_blacklist,
    category=None,
    parse_process_number=8,
):
    if isinstance(assets_dir, str):
        assets_dir_list = [assets_dir]
    elif isinstance(assets_dir, list):
        assets_dir_list = assets_dir
    else:
        raise ValueError("assets_dir should be a string or a list of strings.")

    endings = tuple(files_of_interest.keys())
    db = [{}, {}] if isinstance(assets_dir, str) else [{"": dict()}]
    foi = {}
    category_list = category

    for assets_dir in assets_dir_list:
        category_list = get_category_list(assets_dir, category_list)

        cache = []

        print("Scanning assets at " + assets_dir)
        for subdir, dirs, files in walk(assets_dir):
            for thefile in files:
                if len(dir_blacklist) != 0 and dirname(subdir) in dir_blacklist:
                    continue
                if thefile.endswith(endings):
                    cache.append(normpath(join(subdir, thefile)))
                elif thefile.endswith(".patch") and thefile.replace(
                    ".patch", ""
                ).endswith(endings):
                    cache.append(normpath(join(subdir, thefile)))
        foi[assets_dir] = cache

    print("Scanning files...")
    for assets_dir in foi.keys():
        database_process_files(
            files=foi[assets_dir],
            db=db[0],
            assets_dir=assets_dir,
            files_of_interest=files_of_interest,
            ignore_filelist=ignore_filelist,
            string_blacklist=string_blacklist,
            category_list=category_list,
            path_blacklist=path_blacklist,
            parse_process_number=parse_process_number,
            patch_serialization=patch_serialization,
        )

    return db


def database_process_files(
    files,
    db,
    assets_dir,
    files_of_interest,
    ignore_filelist,
    string_blacklist,
    category_list,
    path_blacklist,
    parse_process_number,
    patch_serialization,
):
    with Pool(parse_process_number) as p:
        r = p.imap_unordered(
            partial(
                parseFile,
                files_of_interest=files_of_interest,
                ignore_filelist=ignore_filelist,
                string_blacklist=string_blacklist,
                category_list=category_list,
                patch_serialization=patch_serialization,
            ),
            files,
        )
        for chunk in r:
            chunk_parse_para(chunk, db, assets_dir, path_blacklist=path_blacklist)


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
        filename = normpath(relpath(abspath(fname), abspath(assets_dir)))
        if filename not in database[sec][val]:
            database[sec][val][filename] = list()
        if path not in database[sec][val][filename]:
            insort_left(database[sec][val][filename], path)
    return database


def parseFile(
    filename,
    files_of_interest,
    ignore_filelist,
    string_blacklist,
    category_list,
    patch_serialization=dict(),
    show_fname=False,
):
    chunk = []
    is_patch_file = filename.endswith(".patch")
    base_name = basename(filename)

    if base_name in ignore_filelist or (show_fname and print(base_name)):
        return []

    with open(filename, "r", encoding="utf_8_sig") as f:
        try:
            if is_patch_file:
                patchdata = trans_patch(f, ex=patch_serialization.get(base_name))
                paths = patchdata.keys()
            else:
                string = prepare(f)
                jsondata = loads(string,strict=False)
                paths = list_field_paths(jsondata)
        except Exception as e:
            print("Cannot parse " + filename)
            return []

        if is_patch_file:
            filename = filename.replace(".patch", "")

        dialog = dirname(filename).endswith("dialog")

        for k in files_of_interest.keys():
            if filename.endswith(k) or k == "*":
                for path in paths:
                    if len(path.split("/")) >= 15:
                        print("Some path in " + filename + "'s len > 15！")
                        continue

                    for roi in files_of_interest[k]:
                        if (roi.match(path) or dialog) and (
                            not is_patch_file or path in patchdata
                        ):
                            val = (
                                patchdata[path]
                                if is_patch_file
                                else field_by_path(jsondata, path)
                            )

                            if regex("category").match(path) and val in category_list:
                                continue

                            if (
                                not isinstance(val, str)
                                or val == ""
                                or (string_blacklist and val in string_blacklist)
                            ):
                                continue

                            for handler in textHandlers:
                                res = handler(
                                    val, filename, "/" + path
                                )
                                if res:
                                    chunk += res
                                    break

                            break

    return chunk


def file_by_assets(assets_fname, field, substitutions, header):
    if assets_fname in substitutions and field in substitutions[assets_fname]:
        return substitutions[assets_fname][field]
    else:
        return normpath(join(header, assets_fname)) + ".json"


def catch_danglings_para(target_path, file_buffer, ignore_filelist=dict()):
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
    with open(filename, "w", encoding="utf-8-sig") as f:
        dump(content, f, ensure_ascii=False, indent=2, sort_keys=True)


def final_write_para(file_buffer, header, prefix, ignore_filelist=None):
    danglings = catch_danglings_para(
        join(prefix, header), file_buffer, ignore_filelist=ignore_filelist
    )
    print("These " + header + " files will be deleted:")
    for d in danglings:
        print("  " + d)
    print("Writing...")
    with Pool(8) as p:
        p.map_async(remove, danglings)
        p.starmap_async(write_file_para, list(file_buffer.items()))
        # write_result = p.starmap_async(write_file, file_buffer)
        p.close()
        p.join()


def stbtran_para(
    root_dir,
    prefix,
    files_of_interest,
    patch_serialization,
    dir_blacklist,
    path_blacklist,
    ignore_filelist,
    string_blacklist,
    category,
    parse_process_number=8,
    texts_prefix="texts",
):
    thedatabase = construct_db_para(
        root_dir,
        files_of_interest,
        patch_serialization,
        dir_blacklist,
        path_blacklist,
        ignore_filelist,
        string_blacklist,
        category=category,
        parse_process_number=parse_process_number,
    )
    file_buffer = process_label_para(thedatabase[0], prefix, texts_prefix)
    final_write_para(file_buffer, texts_prefix, prefix, ignore_filelist=ignore_filelist)
