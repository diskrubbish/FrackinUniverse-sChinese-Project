import json  # 导入 JSON 处理库
import re
from json_tools import field_by_path, list_field_paths, prepare
from sys import platform
from os.path import join

if platform == "win32":
    from os.path import normpath as normpath_old

    def normpath(path):
        return normpath_old(path).replace("\\", "/")

else:
    from os.path import normpath


def detect_patch(patch_content):  # 检测补丁内容并返回路径
    result = json.loads(prepare(patch_content))  # 解析 JSON 补丁内容
    return [item if "path" in item else subitem for item in result for subitem in item]  # 返回包含路径的补丁项


def trans_patch(patch_content, array_index_rules=None):  # 转换补丁内容为路径-值映射
    json_text = detect_patch(patch_content)  # 检测并获取补丁内容
    path_value_mapping = {}  # 存储路径-值映射结果

    def process_path(target_path, value, is_add):  # 处理路径和对应的值
        if isinstance(value, str):  # 处理字符串值
            new_path = target_path[1:] if target_path.startswith("/") else target_path  # 处理路径前缀
            if is_add and target_path.endswith("/-") and array_index_rules is not None:  # 处理添加操作
                for end in array_index_rules.keys():
                    if target_path.rstrip("/-").endswith(end):
                        new_path = normpath(target_path.replace("/-", f"/{array_index_rules[end]['index']}"))  # 替换数组索引
                        path_value_mapping[new_path] = value  # 更新路径-值映射
                        if array_index_rules[end]["increase"]:  # 检查是否需要增加索引
                            array_index_rules[end]["index"] += 1
            else:
                path_value_mapping[new_path] = value  # 更新路径-值映射
        elif isinstance(value, (list, dict)):  # 处理列表或字典
            contexts = list_field_paths(value)  # 获取值的字段路径
            for v in contexts:
                new_path = normpath(join(target_path, str(v)))  # 生成新路径
                new_path = new_path[1:] if new_path.startswith("/") else new_path  # 处理路径前缀
                path_value_mapping[new_path] = field_by_path(value, str(v))  # 更新路径-值映射

    for item in json_text:  # 遍历检测到的补丁项
        try:
            target_path = item["path"]  # 获取目标路径
            value = item.get("value", "")  # 获取值
            is_add = item["op"] == "add"  # 检查操作类型
            is_replace = item["op"] == "replace"  # 检查操作类型

            if is_add or is_replace:  # 处理添加或替换操作
                process_path(target_path, value, is_add)
        except Exception as error:  # 捕获处理错误
            print(f"Error processing item: {error}")
            continue

    return path_value_mapping  # 返回路径-值映射结果