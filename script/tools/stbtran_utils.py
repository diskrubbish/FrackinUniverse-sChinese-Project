#!/usr/bin/python3

from json import dump, loads
from functools import partial
from multiprocessing import Pool
from os import makedirs, remove, walk
from os.path import abspath, basename, dirname, exists, join, relpath
from re import compile as regex
from sys import platform
from patch_tool import trans_patch
from json_tools import field_by_path, list_field_paths, prepare
from special_cases import specialSections


# 平台特定的路径规范化处理
if platform == "win32":
    from os.path import normpath as normpath_old

    def normpath(path):
        """Windows平台下的路径规范化，替换反斜杠为正斜杠"""
        return normpath_old(path).replace("\\", "/")
else:
    from os.path import normpath


def get_category_list(root_dir, default_list):
    """
    从指定目录获取类别列表
    
    Args:
        root_dir: 根目录路径
        default_list: 默认类别列表
        
    Returns:
        合并后的类别列表
    """
    file_path = normpath(join(root_dir, "items/categories.config.patch"))
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


def parse_chunk(chunk, database, assets_dir, path_blacklist=None):
    """
    解析文件块并更新数据库
    
    Args:
        chunk: 包含文本块的列表，每个项目为 (section, value, filename, path)
        database: 要更新的数据库
        assets_dir: 资源目录路径
        path_blacklist: 路径黑名单字典
        
    Returns:
        更新后的数据库
    """
    if path_blacklist is None:
        path_blacklist = {}
        
    for section, value, filename, path in chunk:
        dir_name = dirname(filename)
        
        # 检查黑名单
        if path_blacklist and dir_name in path_blacklist:
            if path in path_blacklist[dir_name]:
                continue
                
        # 生成规范化的相对路径
        norm_filename = normpath(relpath(abspath(filename), abspath(assets_dir)))
        
        # 更新数据库
        if norm_filename not in database:
            database[norm_filename] = dict()
            
        if path not in database[norm_filename]:
            database[norm_filename][path] = value
            
    return database


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
        file_path = normpath(join(prefix, header, f"{key}.patch"))
        
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
                        prev_text = reference[obj_path][1] or reference[obj_path][2] if len(reference[obj_path]) > 2 else ""
                        content["context"] = f"之前文本：\n{prev_text}" if prev_text else ""
                else:
                    # 原始值未更改，保持翻译
                    content["value"] = reference[obj_path][1]
            else:
                # 新条目，初始化为空字符串
                content["value"] = ""

            patch_entries.append(content)

        result[file_path] = patch_entries

    return result


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
    构造翻译数据库
    
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
                # 收集直接匹配的文件和补丁文件
                if file_name.endswith(file_extensions):
                    file_paths.append(normpath(join(subdir, file_name)))
                elif file_name.endswith(".patch") and file_name.replace(".patch", "").endswith(file_extensions):
                    file_paths.append(normpath(join(subdir, file_name)))
                    
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


def parse_file(
    filename,
    files_of_interest,
    ignore_filelist,
    string_blacklist,
    category_list,
    patch_serialization=None,
    show_fname=False,
):
    """
    解析单个文件以提取可翻译文本
    
    Args:
        filename: 要解析的文件名
        files_of_interest: 感兴趣的文件类型及匹配规则
        ignore_filelist: 忽略的文件列表
        string_blacklist: 字符串黑名单
        category_list: 类别列表
        patch_serialization: 补丁序列化规则
        show_fname: 是否显示文件名
        
    Returns:
        提取的文本块列表，每个项目为 (section, value, filename, path)
    """
    if patch_serialization is None:
        patch_serialization = {}
        
    result = []
    is_patch_file = filename.endswith(".patch")
    base_name = basename(filename)

    # 检查文件是否应该被忽略
    if base_name in ignore_filelist or (show_fname and print(base_name)):
        return result

    try:
        # 解析文件内容
        with open(filename, "r", encoding="utf_8_sig") as f:
            try:
                if is_patch_file:
                    # 解析补丁文件
                    patch_data = trans_patch(f, array_index_rules=patch_serialization.get(base_name))
                    paths = patch_data.keys()
                else:
                    # 解析JSON文件
                    json_string = prepare(f)
                    json_data = loads(json_string, strict=False)
                    paths = list_field_paths(json_data)
            except Exception as e:
                print(f"Cannot parse {filename}: {e}")
                return result

            # 如果是补丁文件，移除扩展名以获取原始文件名
            if is_patch_file:
                filename = filename.replace(".patch", "")

            # 检查文件是否是对话文件
            is_dialog = dirname(filename).endswith("dialog")

            # 处理每种感兴趣的文件类型
            for extension, regexes in files_of_interest.items():
                if filename.endswith(extension) or extension == "*":
                    for path in paths:
                        # 跳过过长的路径
                        if len(path.split("/")) >= 15:
                            print(f"Path too long in {filename}: {path}")
                            continue

                        # 检查路径是否匹配兴趣点
                        for regex_pattern in regexes:
                            if (regex_pattern.match(path) or is_dialog) and (not is_patch_file or path in patch_data):
                                # 提取值
                                value = patch_data[path] if is_patch_file else field_by_path(json_data, path)
                                
                                # 跳过类别
                                if regex("category").match(path) and value in category_list:
                                    continue
                                    
                                # 跳过非字符串、空字符串或黑名单中的字符串
                                if (not isinstance(value, str) or 
                                    value == "" or 
                                    (string_blacklist and value in string_blacklist)):
                                    continue
                                    
                                # 确定部分类型
                                section = ""
                                for pattern in specialSections:
                                    if pattern.match(filename, "/" + path):
                                        section = pattern.name
                                        break
                                        
                                # 添加到结果
                                result.append((section, value, filename, "/" + path))
                                break
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        
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
    
    for subdir, dirs, files in walk(target_path):
        for file_name in files:
            full_path = normpath(join(subdir, file_name))
            
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
    file_dir = dirname(filename)
    
    # 确保目录存在
    if file_dir:
        makedirs(file_dir, exist_ok=True)
    else:
        raise ValueError(f"Filename without directory: {filename}")
        
    # 写入文件
    with open(filename, "w", encoding="utf-8-sig") as f:
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
    dangling_files = find_dangling_files(target_path, file_buffer, ignore_filelist=ignore_filelist)
    
    # 显示将被删除的文件
    print(f"These {header} files will be deleted:")
    for file_path in dangling_files:
        print(f"  {file_path}")
        
    print("Writing files...")
    
    # 使用进程池并行删除文件和写入新文件
    with Pool(8) as pool:
        pool.map_async(remove, dangling_files)
        pool.starmap_async(write_file, list(file_buffer.items()))
        pool.close()
        pool.join()


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
catch_danglings_para = find_dangling_files
write_file_para = write_file
final_write_para = write_files
