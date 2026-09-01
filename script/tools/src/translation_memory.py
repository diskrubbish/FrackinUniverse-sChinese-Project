"""
翻译记忆库模块
管理翻译记忆的导出和导入（para 格式）
"""

import json
from os import walk
from os.path import basename
from os.path import join as join_path

from json_tools import prepare

# 遍历时忽略的文件名
_IGNORE_FILES = {
    "substitutions.json",
    "totallabels.json",
    "translatedlabels.json",
    "patch_substitutions.json",
    "parse_problem.txt",
    "_metadata",
    "_previewimage",
    "memory.json",
}


def _walk_patch_files(path, show_fname=False):
    """遍历目录，生成所有需要处理的文件路径（过滤忽略文件）"""
    for root_dir, _, filelist in walk(path):
        for filename in filelist:
            if filename in _IGNORE_FILES:
                continue
            file_path = join_path(root_dir, filename)
            if show_fname:
                print(basename(file_path))
            yield file_path


def export_memory_para(path, memory_file, show_fname=False):
    """从 para 补丁文件中导出翻译记忆（raw -> value 映射）"""
    memory = {}
    for file_path in _walk_patch_files(path, show_fname):
        with open(file_path, "r", encoding="utf-8-sig") as f:
            jsondata = json.loads(prepare(f))
            for idx, item in enumerate(jsondata):
                if "value" not in item:
                    continue
                if item["raw"] in memory:
                    continue
                if item["value"] != "":
                    memory[item["raw"]] = item["value"]

    result = json.dumps(memory, ensure_ascii=False, sort_keys=True, indent=2)
    with open(memory_file, "w", encoding="utf-8-sig") as f:
        f.write(result)


def import_memory_para(path, memory_file, glitch=False, show_fname=False):
    """将翻译记忆导入 para 补丁文件（填充空 value 字段）"""
    with open(memory_file, "r", encoding="utf-8-sig") as mf:
        memory = json.loads(prepare(mf))

    for file_path in _walk_patch_files(path, show_fname):
        with open(file_path, "r", encoding="utf-8-sig") as f:
            jsondata = json.load(f)

        for idx, item in enumerate(jsondata):
            if item["value"] != "":
                continue

            raw_text = item["raw"]
            if raw_text in memory:
                jsondata[idx]["value"] = memory[raw_text]
        text = json.dumps(jsondata, ensure_ascii=False, sort_keys=True, indent=2)
        with open(file_path, "w", encoding="utf-8-sig") as f:
            f.write(text)