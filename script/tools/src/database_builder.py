#!/usr/bin/python3
"""
数据库构建器模块
翻译数据库构建和主工作流
"""

from functools import partial
from multiprocessing import Pool
from os import walk
from os.path import dirname
from pathlib import Path

# 导入其他模块
from pak_extractor import is_pak_file, construct_database_from_pak
from translation_extractor import parse_file, parse_chunk
from json_processor import get_category_list, process_label_para, write_files


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


def construct_database_original(
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
    """
    构造翻译数据库（原始函数，用于处理文件夹）

    Args:
        assets_dir: 资源目录路径(字符串或列表)
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
    # 规范化资源目录为列表
    if isinstance(assets_dir, str):
        assets_dir_list = [assets_dir]
        database = [{}, {}]  # 为单个资源目录创建两个数据库
    elif isinstance(assets_dir, list):
        assets_dir_list = assets_dir
        database = [{"": dict()}]  # 为多个资源目录创建一个数据库
    else:
        raise ValueError("assets_dir should be a string or a list of strings.")

    # 获取感兴趣的文件扩展名
    file_extensions = tuple(files_of_interest.keys())

    # 文件缓存字典
    files_cache = {}

    # 初始化类别列表
    category_list = category

    # 扫描每个资源目录
    for curr_assets_dir in assets_dir_list:
        # 获取类别列表
        category_list = get_category_list(curr_assets_dir, category_list)

        # 缓存符合条件的文件
        file_paths = []
        print(f"Scanning assets at {curr_assets_dir}")

        for subdir, dirs, files in walk(curr_assets_dir):
            # 跳过黑名单目录
            if dir_blacklist and dirname(subdir) in dir_blacklist:
                continue

            for file_name in files:
                # 使用共享函数检查文件是否应该被处理
                if should_process_file(file_name, file_extensions):
                    file_paths.append((Path(subdir) / file_name).as_posix())

        files_cache[curr_assets_dir] = file_paths

    # 处理每个资源目录的文件
    print("Processing files...")
    for curr_assets_dir, file_paths in files_cache.items():
        process_files(
            files=file_paths,
            database=database[0],
            assets_dir=curr_assets_dir,
            files_of_interest=files_of_interest,
            ignore_filelist=ignore_filelist,
            string_blacklist=string_blacklist,
            category_list=category_list,
            path_blacklist=path_blacklist,
            parse_process_number=parse_process_number,
            patch_serialization=patch_serialization,
        )

    return database


def construct_database(
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
    """
    构造翻译数据库（统一函数，自动处理文件夹或.pak文件）

    Args:
        assets_dir: 资源目录路径(字符串或列表) 或 .pak 文件路径
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
    # 如果 assets_dir 是字符串且以 .pak 结尾，则使用 .pak 处理函数
    if isinstance(assets_dir, str) and is_pak_file(assets_dir):
        # 注意：construct_database_from_pak 内部会处理 starbound 依赖
        return construct_database_from_pak(
            pak_file_path=assets_dir,
            files_of_interest=files_of_interest,
            patch_serialization=patch_serialization,
            dir_blacklist=dir_blacklist,
            path_blacklist=path_blacklist,
            ignore_filelist=ignore_filelist,
            string_blacklist=string_blacklist,
            category=category,
            parse_process_number=parse_process_number,
        )
    else:
        # 否则使用原始文件夹处理函数
        return construct_database_original(
            assets_dir=assets_dir,
            files_of_interest=files_of_interest,
            patch_serialization=patch_serialization,
            dir_blacklist=dir_blacklist,
            path_blacklist=path_blacklist,
            ignore_filelist=ignore_filelist,
            string_blacklist=string_blacklist,
            category=category,
            parse_process_number=parse_process_number,
        )


def process_files(
    files,
    database,
    assets_dir,
    files_of_interest,
    ignore_filelist,
    string_blacklist,
    category_list,
    path_blacklist,
    parse_process_number,
    patch_serialization,
):
    """
    使用多进程处理文件并更新数据库

    Args:
        files: 要处理的文件列表
        database: 要更新的数据库
        assets_dir: 资源目录路径
        files_of_interest: 感兴趣的文件类型及匹配规则
        ignore_filelist: 忽略的文件列表
        string_blacklist: 字符串黑名单
        category_list: 类别列表
        path_blacklist: 路径黑名单
        parse_process_number: 解析进程数
        patch_serialization: 补丁序列化规则
    """
    with Pool(parse_process_number) as pool:
        # 创建偏函数以固定除文件名外的所有参数
        parse_file_partial = partial(
            parse_file,
            files_of_interest=files_of_interest,
            ignore_filelist=ignore_filelist,
            string_blacklist=string_blacklist,
            category_list=category_list,
            patch_serialization=patch_serialization,
        )

        # 使用进程池并行处理文件
        results = pool.imap_unordered(parse_file_partial, files)

        # 处理结果并更新数据库
        for chunk in results:
            if chunk:  # 只处理非空结果
                parse_chunk(chunk, database, assets_dir, path_blacklist=path_blacklist)


def extract_translations(
    root_dir,
    prefix,
    files_of_interest,
    patch_serialization=None,
    dir_blacklist=None,
    path_blacklist=None,
    ignore_filelist=None,
    string_blacklist=None,
    category=None,
    parse_process_number=8,
    texts_prefix="texts",
):
    """
    主函数：提取翻译并生成补丁文件

    Args:
        root_dir: 根目录路径（字符串或列表）
        prefix: 输出路径前缀
        files_of_interest: 感兴趣的文件类型及匹配规则
        patch_serialization: 补丁序列化规则
        dir_blacklist: 目录黑名单
        path_blacklist: 路径黑名单
        ignore_filelist: 忽略的文件列表
        string_blacklist: 字符串黑名单
        category: 类别列表
        parse_process_number: 解析进程数
        texts_prefix: 文本输出目录前缀
    """
    # 初始化默认参数
    if patch_serialization is None:
        patch_serialization = {}
    if dir_blacklist is None:
        dir_blacklist = []
    if path_blacklist is None:
        path_blacklist = {}
    if ignore_filelist is None:
        ignore_filelist = []
    if string_blacklist is None:
        string_blacklist = []
    if category is None:
        category = []

    # 构建翻译数据库
    database = construct_database(
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

    # 处理标签并生成文件缓冲区
    file_buffer = process_label_para(database[0], prefix, texts_prefix)

    # 写入文件
    write_files(file_buffer, texts_prefix, prefix, ignore_filelist=ignore_filelist)


# 为了保持向后兼容性而保留的别名函数
stbtran_para = extract_translations
chunk_parse_para = parse_chunk
construct_db_para = construct_database
database_process_files = process_files
