#!/usr/bin/python3
"""
翻译提取器模块
核心文本提取逻辑
"""

import io
from json import loads
from os.path import basename, dirname
from re import compile as regex
from patch_tool import trans_patch
from json_tools import field_by_path, list_field_paths, prepare


def parse_file(
    filename,
    files_of_interest,
    ignore_filelist,
    string_blacklist,
    category_list,
    patch_serialization=None,
    show_fname=False,
    content=None,
):
    """
    解析单个文件以提取可翻译文本

    Args:
        filename: 要解析的文件名或虚拟路径
        files_of_interest: 感兴趣的文件类型及匹配规则
        ignore_filelist: 忽略的文件列表
        string_blacklist: 字符串黑名单
        category_list: 类别列表
        patch_serialization: 补丁序列化规则
        show_fname: 是否显示文件名
        content: 可选的字节内容，如果提供则从内容解析而非从文件读取

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

    # 跳过已知的非文本文件扩展名（如图像、音频、视频、脚本文件等）
    try:
        # 解析文件内容
        if content is not None:
            # 从内存内容解析
            # 尝试用utf-8-sig解码
            try:
                text = content.decode("utf-8-sig")
            except UnicodeDecodeError:
                # 如果不是文本文件（如图像、音频等），静默跳过
                return result
            # 使用字符串作为文件对象
            f = io.StringIO(text)
            should_close = False
        else:
            # 从文件读取
            f = open(filename, "r", encoding="utf_8_sig")
            should_close = True

        try:
            if is_patch_file:
                # 解析补丁文件
                patch_data = trans_patch(
                    f, array_index_rules=patch_serialization.get(base_name)
                )
                paths = patch_data.keys()
            else:
                # 解析JSON文件
                json_string = prepare(f)
                json_data = loads(json_string, strict=False)
                paths = list_field_paths(json_data)
        except Exception as e:
            print(f"Cannot parse {filename}: {e}")
            return result
        finally:
            if should_close:
                f.close()

        # 如果是补丁文件，移除扩展名以获取原始文件名
        if is_patch_file:
            filename = filename.replace(".patch", "")

        # 检查文件是否是对话文件
        is_dialog = dirname(filename).endswith("dialog")

        # 处理每种感兴趣的文件类型
        for extension, regexes in files_of_interest.items():
            if filename.endswith(extension) or extension == "*":
                # regexes 应该在传入前已经全部预编译，但为兼容性仍做检查
                # 注意：不再在此处重新编译正则，因为调用方已经处理

                for path in paths:
                    # 跳过过长的路径
                    if len(path.split("/")) >= 15:
                        print(f"Path too long in {filename}: {path}")
                        continue

                    # 检查路径是否匹配兴趣点
                    for regex_pattern in regexes:
                        # 向后兼容：如果调用方传入字符串，则即时编译
                        if isinstance(regex_pattern, str):
                            regex_pattern = regex(regex_pattern)
                        if (regex_pattern.match(path) or is_dialog) and (
                            not is_patch_file or path in patch_data
                        ):
                            # 提取值
                            value = (
                                patch_data[path]
                                if is_patch_file
                                else field_by_path(json_data, path)
                            )

                            # 跳过类别
                            if regex("category").match(path) and value in category_list:
                                continue

                            # 跳过非字符串、空字符串或黑名单中的字符串
                            if (
                                not isinstance(value, str)
                                or value == ""
                                or (string_blacklist and value in string_blacklist)
                            ):
                                continue

                            # 确定部分类型（已弃用 special_cases.py，始终返回空字符串）
                            section = ""

                            # 添加到结果
                            result.append((section, value, filename, "/" + path))
                            break
    except Exception as e:
        print(f"Error processing {filename}: {e}")

    return result


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

        # 使用pathlib进行路径规范化
        from pathlib import Path
        from os.path import relpath, abspath

        # 生成规范化的相对路径
        # 注意：filename可能是字符串路径或虚拟路径（来自.pak文件）
        try:
            # 确保filename是字符串类型
            filename_str = (
                str(filename) if isinstance(filename, (str, bytes)) else filename
            )
            assets_dir_str = (
                str(assets_dir) if isinstance(assets_dir, (str, bytes)) else assets_dir
            )
            norm_filename = Path(
                relpath(abspath(filename_str), abspath(assets_dir_str))
            ).as_posix()
        except (TypeError, ValueError, OSError):
            # 如果filename不是有效的文件路径（如来自.pak文件的虚拟路径），直接使用原值
            norm_filename = str(filename)

        # 更新数据库
        if norm_filename not in database:
            database[norm_filename] = dict()

        if path not in database[norm_filename]:
            database[norm_filename][path] = value

    return database
