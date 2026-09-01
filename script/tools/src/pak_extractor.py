#!/usr/bin/python3
"""
.pak 文件提取器模块
处理 Starbound 的 .pak 和 .modpak 文件
"""

import tempfile
import codecs
import io
from os.path import dirname
from pathlib import Path


def should_process_file(filename, extensions):
    """
    检查文件是否应该被处理（匹配扩展名或补丁文件）

    Args:
        filename: 文件名
        extensions: 文件扩展名元组

    Returns:
        如果文件应该被处理返回True，否则返回False
    """
    return filename.endswith(extensions) or (
        filename.endswith(".patch")
        and filename.replace(".patch", "").endswith(extensions)
    )


# 尝试导入 starbound 模块以支持 .pak 文件
try:
    import starbound

    HAS_STARBOUND = True
except ImportError:
    HAS_STARBOUND = False
    print(
        "警告: 未安装 py-starbound 库，无法直接处理 .pak 文件。请使用 'pip install py-starbound' 安装。"
    )


def is_pak_file(path):
    """
    检查路径是否指向 .pak 文件

    Args:
        path: 文件或目录路径

    Returns:
        如果是 .pak 文件返回 True，否则返回 False
    """
    if isinstance(path, str) and (path.endswith(".pak") or path.endswith(".modpak")):
        return True
    return False


def extract_files_from_pak(pak_file_path, files_of_interest, temp_dir=None):
    """
    从 .pak 文件中提取感兴趣的文件到临时目录

    Args:
        pak_file_path: .pak 文件路径
        files_of_interest: 感兴趣的文件类型及匹配规则
        temp_dir: 临时目录路径，如果为None则创建临时目录

    Returns:
        (temp_dir_path, file_list) 临时目录路径和文件列表
    """
    if not HAS_STARBOUND:
        raise ImportError("需要安装 py-starbound 库来处理 .pak 文件")

    # 创建临时目录
    if temp_dir is None:
        temp_dir_obj = tempfile.TemporaryDirectory()
        temp_dir_path = temp_dir_obj.name
        # 保留引用以防止垃圾回收
        extract_files_from_pak._temp_dir_obj = temp_dir_obj
    else:
        temp_dir_path = temp_dir

    print(f"从 .pak 文件提取文件到临时目录: {temp_dir_path}")

    # 打开 .pak 文件
    with open(pak_file_path, "rb") as fh:
        package = starbound.SBAsset6(fh)

        # 读取索引以获取文件列表
        if not hasattr(package, "index"):
            package.read_index()

        file_extensions = tuple(files_of_interest.keys())
        extracted_files = []

        # 遍历 .pak 文件中的所有文件
        for file_path in package.index.keys():
            # 检查文件扩展名是否匹配
            if file_path.endswith(file_extensions) or "*" in file_extensions:
                # 获取文件内容
                file_content = package.get(file_path)

                # 创建目标文件路径
                # .pak 文件使用 Unix 风格路径，需要转换为本地路径
                local_path = Path(file_path).as_posix()
                full_local_path = Path(temp_dir_path) / local_path.lstrip("/")

                # 确保目录存在
                full_local_path.parent.mkdir(parents=True, exist_ok=True)

                # 写入文件
                with open(full_local_path, "wb") as out_file:
                    out_file.write(file_content)

                extracted_files.append(full_local_path)

    print(f"从 .pak 文件中提取了 {len(extracted_files)} 个文件")
    return temp_dir_path, extracted_files


def construct_database_from_pak(
    pak_file_path,
    files_of_interest,
    patch_serialization,
    dir_blacklist,
    path_blacklist,
    ignore_filelist,
    string_blacklist,
    category=None,
    parse_process_number=8,
):
    """
    从 .pak 文件构造翻译数据库（直接内存处理，无需临时文件）

    Args:
        pak_file_path: .pak 文件路径
        files_of_interest: 感兴趣的文件类型及匹配规则
        patch_serialization: 补丁序列化规则
        dir_blacklist: 目录黑名单
        path_blacklist: 路径黑名单
        ignore_filelist: 忽略的文件列表
        string_blacklist: 字符串黑名单
        category: 类别列表
        parse_process_number: 解析进程数

    Returns:
        包含翻译数据的数据库列表
    """
    if not HAS_STARBOUND:
        raise ImportError("需要安装 py-starbound 库来处理 .pak 文件")

    # 初始化数据库（与原始函数一致）
    database = [{}, {}]  # 为单个资源目录创建两个数据库

    # 获取感兴趣的文件扩展名
    file_extensions = tuple(files_of_interest.keys())

    # 初始化类别列表
    category_list = category

    print(f"Processing .pak file: {pak_file_path}")

    # 打开.pak文件并读取索引（只打开一次）
    with open(pak_file_path, "rb") as fh:
        package = starbound.SBAsset6(fh)

        # 确保读取索引
        if not hasattr(package, "index"):
            package.read_index()

        # 首先尝试从pak中获取类别列表（使用已读取的索引）
        try:
            categories_path = "items/categories.config.patch"
            if categories_path in package.index:
                content = package.get(categories_path)
                # 解析补丁内容获取类别
                bytes_io = io.BytesIO(content)
                text_stream = codecs.getreader("utf-8-sig")(bytes_io)
                from patch_tool import trans_patch

                category_data = trans_patch(text_stream)
                category_list = [v.split("/")[1] for v in category_data.keys()] + (
                    category if category else []
                )
        except Exception as e:
            print(f"Warning: Could not load categories from pak: {e}")

        # 收集匹配的文件
        matched_files = []
        for file_path in package.index.keys():
            # 使用共享函数检查文件是否应该被处理
            if should_process_file(file_path, file_extensions):
                matched_files.append(file_path)
        print(f"Found {len(matched_files)} matching files in .pak")

        # 处理每个匹配的文件
        processed_count = 0
        for file_path in matched_files:
            # 跳过黑名单目录检查（dir_blacklist针对文件系统目录，这里不适用）
            # 但我们可以模拟：dirname(file_path) 是类似 "/interface" 的路径
            # 由于pak内路径是Unix风格，我们转换为虚拟目录
            virtual_dir = dirname(file_path)
            # 如果virtual_dir在dir_blacklist中，跳过（注意：dir_blacklist中的路径是文件系统路径，可能不匹配）
            # 这里暂时不实现目录黑名单，因为通常用于文件系统

            # 检查路径黑名单
            skip = False
            if path_blacklist and virtual_dir in path_blacklist:
                if file_path in path_blacklist[virtual_dir]:
                    skip = True
            if skip:
                continue

            # 获取文件内容
            file_content = package.get(file_path)

            # 调用parse_file进行解析（使用content参数）
            # 注意：parse_file期望filename参数，我们使用虚拟路径（去掉前导斜杠）
            virtual_filename = file_path.lstrip("/")

            # 导入 translation_extractor 模块中的 parse_file 和 parse_chunk 函数
            from translation_extractor import parse_file, parse_chunk

            # 解析文件
            chunks = parse_file(
                filename=virtual_filename,
                files_of_interest=files_of_interest,
                ignore_filelist=ignore_filelist,
                string_blacklist=string_blacklist,
                category_list=category_list,
                patch_serialization=patch_serialization,
                content=file_content,
            )

            # 更新数据库
            if chunks:
                # 使用当前目录作为assets_dir（因为虚拟路径已经是相对路径）
                parse_chunk(
                    chunks, database[0], assets_dir=".", path_blacklist=path_blacklist
                )

            processed_count += 1
            if processed_count % 100 == 0:
                print(f"Processed {processed_count}/{len(matched_files)} files")

    print(f"Finished processing .pak file. Total files processed: {processed_count}")
    return database
