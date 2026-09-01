#!/usr/bin/python3
"""
JSON 处理器模块
处理 JSON 文件、路径操作和文件系统操作
"""

from json import dump, loads
from os import remove
from os.path import basename, exists, join
from patch_tool import trans_patch
from json_tools import prepare
from pathlib import Path


def get_category_list(root_dir, default_list):
    """
    从指定目录获取类别列表

    Args:
        root_dir: 根目录路径
        default_list: 默认类别列表

    Returns:
        合并后的类别列表
    """
    file_path = Path(join(root_dir, "items/categories.config.patch")).as_posix()
    if exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                category_data = trans_patch(f)
                result = [v.split("/")[1] for v in category_data.keys()] + default_list
                return result
        except Exception as e:
            print(f"Error reading category list: {e}")
            return default_list
    else:
        return default_list


def process_label_para(database, prefix, header, outdata=False):
    """
    处理标签数据并准备补丁文件

    Args:
        database: 包含标签数据的数据库
        prefix: 输出路径前缀
        header: 输出目录名
        outdata: 是否输出额外上下文数据

    Returns:
        文件路径到内容的映射字典
    """
    result = {}

    def load_old_data(file_path):
        """加载旧的补丁数据"""
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                return loads(prepare(f), strict=False)
        except Exception as e:
            print(f"Cannot open old data {basename(file_path)}: {e}")
            return None

    # 处理数据库中的每个条目
    for key, objects in database.items():
        if key == "":
            continue

        # 构建补丁文件路径
        file_path = Path(join(prefix, header, f"{key}.patch")).as_posix()

        # 如果文件不存在，创建新的补丁内容
        if not exists(file_path):
            result[file_path] = [
                {"op": "replace", "path": obj_path, "raw": obj_value, "value": ""}
                for obj_path, obj_value in objects.items()
            ]
            continue

        # 加载现有补丁数据
        old_data = load_old_data(file_path)
        if old_data is None:
            continue

        # 构建引用映射
        reference = {data["path"]: [data["raw"], data["value"]] for data in old_data}
        old_dict = {data["raw"]: data["value"] for data in old_data}

        # 处理每个对象
        patch_entries = []
        for obj_path, obj_value in objects.items():
            content = {"op": "replace", "path": obj_path, "raw": obj_value}

            if obj_path in reference:
                if reference[obj_path][0] != obj_value:
                    # 原始值已更改，尝试从旧数据获取翻译
                    content["value"] = old_dict.get(obj_value, "")
                    if outdata:
                        prev_text = (
                            reference[obj_path][1] or reference[obj_path][2]
                            if len(reference[obj_path]) > 2
                            else ""
                        )
                        content["context"] = (
                            f"之前文本：\n{prev_text}" if prev_text else ""
                        )
                else:
                    # 原始值未更改，保持翻译
                    content["value"] = reference[obj_path][1]
            else:
                # 新条目，初始化为空字符串
                content["value"] = ""

            patch_entries.append(content)

        result[file_path] = patch_entries

    return result


def find_dangling_files(target_path, file_buffer, ignore_filelist=None):
    """
    查找不在文件缓冲区中的文件（待删除文件）

    Args:
        target_path: 目标目录路径
        file_buffer: 文件缓冲区
        ignore_filelist: 忽略的文件列表

    Returns:
        待删除的文件列表
    """
    if ignore_filelist is None:
        ignore_filelist = {}

    to_remove = []

    # 使用pathlib进行文件遍历
    target_path_obj = Path(target_path)

    for file_path in target_path_obj.rglob("*"):
        if file_path.is_file():
            full_path = file_path.as_posix()
            file_name = file_path.name

            if ignore_filelist:
                # 仅当文件不在忽略列表中且不在缓冲区中时添加到删除列表
                if file_name not in ignore_filelist and full_path not in file_buffer:
                    to_remove.append(full_path)
            else:
                # 当文件不在缓冲区中时添加到删除列表
                if full_path not in file_buffer:
                    to_remove.append(full_path)

    return to_remove


def write_file(filename, content):
    """
    将内容写入文件

    Args:
        filename: 目标文件路径
        content: 要写入的内容
    """
    # 使用pathlib确保目录存在
    file_path = Path(filename)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # 写入文件
    with file_path.open("w", encoding="utf-8-sig") as f:
        dump(content, f, ensure_ascii=False, indent=2, sort_keys=True)


def write_files(file_buffer, header, prefix, ignore_filelist=None):
    """
    将文件缓冲区写入磁盘并删除多余文件

    Args:
        file_buffer: 文件内容缓冲区
        header: 输出目录名
        prefix: 输出路径前缀
        ignore_filelist: 忽略的文件列表
    """
    # 查找待删除文件
    target_path = join(prefix, header)
    dangling_files = find_dangling_files(
        target_path, file_buffer, ignore_filelist=ignore_filelist
    )

    # 显示将被删除的文件
    print(f"These {header} files will be deleted:")
    for file_path in dangling_files:
        print(f"  {file_path}")

    print("Writing files...")

    # 使用进程池并行删除文件和写入新文件
    from multiprocessing import Pool

    with Pool(8) as pool:
        pool.map_async(remove, dangling_files)
        pool.starmap_async(write_file, list(file_buffer.items()))
        pool.close()
        pool.join()
