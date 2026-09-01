"""补丁工具模块 - 检测和转换 Starbound 补丁文件"""

import json
import re
from typing import Dict, List, Optional, Any
from json_tools import field_by_path, list_field_paths, prepare
from os.path import join
from pathlib import Path


def detect_patch(patch_content: Any) -> List[Dict[str, Any]]:
    """解析补丁内容并返回扁平的补丁项列表。

    支持两种补丁格式：
    1. 扁平格式: [{"op": "replace", "path": "/...", "value": "..."}, ...]
    2. 嵌套格式: [[{...}], [{...}]] — 自动展开为扁平列表
    """
    result = json.loads(prepare(patch_content))
    if not isinstance(result, list):
        return []

    # 检测格式：如果第一个元素是列表，则是嵌套格式，需要展开
    if result and isinstance(result[0], list):
        # 嵌套格式：[[{...}], [{...}], ...]
        flattened: List[Dict[str, Any]] = []
        for sublist in result:
            if isinstance(sublist, list):
                for item in sublist:
                    if isinstance(item, dict) and "path" in item:
                        flattened.append(item)
        return flattened

    # 扁平格式：[{...}, {...}]
    return [item for item in result if isinstance(item, dict) and "path" in item]


def trans_patch(
    patch_content: Any,
    array_index_rules: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """转换补丁内容为路径-值映射

    Args:
        patch_content: JSON 补丁内容（文件对象或字符串）
        array_index_rules: 数组索引规则，用于处理 "/-" 路径

    Returns:
        路径到值的映射字典
    """
    json_text = detect_patch(patch_content)
    path_value_mapping: Dict[str, Any] = {}

    def process_path(target_path: str, value: Any, is_add: bool) -> None:
        if isinstance(value, str):
            new_path = target_path[1:] if target_path.startswith("/") else target_path
            if is_add and target_path.endswith("/-") and array_index_rules is not None:
                for end in array_index_rules.keys():
                    if target_path.rstrip("/-").endswith(end):
                        new_path = Path(
                            target_path.replace(
                                "/-", f"/{array_index_rules[end]['index']}"
                            )
                        ).as_posix()
                        path_value_mapping[new_path] = value
                        if array_index_rules[end].get("increase", False):
                            array_index_rules[end]["index"] += 1
            else:
                path_value_mapping[new_path] = value
        elif isinstance(value, (list, dict)):
            contexts = list_field_paths(value)
            for v in contexts:
                new_path = Path(join(target_path, str(v))).as_posix()
                new_path = new_path[1:] if new_path.startswith("/") else new_path
                path_value_mapping[new_path] = field_by_path(value, str(v))

    for item in json_text:
        try:
            target_path = item["path"]
            value = item.get("value", "")
            is_add = item["op"] == "add"
            is_replace = item["op"] == "replace"

            if is_add or is_replace:
                process_path(target_path, value, is_add)
        except Exception as error:
            print(f"Error processing item: {error}")
            continue

    return path_value_mapping