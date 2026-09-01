"""FU 汉化 CI headless 入口。

替代旧版扁平脚本（download_paratrans.py / extract_labels.py / sync_to_paratrans.py /
export_mod_para.py 的 __main__），统一走新工具链（src/ 包 + sysc_paratrans）。

用法：
    python run_ci.py all          # 下载 → 提取 → 同步 → 导出（本地一条龙）
    python run_ci.py download     # 仅从 ParaTranz 下载翻译并回填
    python run_ci.py process      # 仅提取（需先解包 FU.pak 到 temp/FrackinUniverse）
    python run_ci.py sync         # 仅同步到 ParaTranz
    python run_ci.py export       # 仅生成 metadata + 合并导出

CI 里解包/打包由 workflow 用 asset_unpacker / asset_packer 二进制完成，
本入口不碰二进制。
"""

import os
import sys
import json

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, SRC_DIR)

from translation_console_utils import sysc_paratrans
from export_mod_para import create_metadata, export_mod_para


def _posix(p):
    """规范化路径分隔符，兼容 Windows 本地调试与 Linux CI。"""
    return os.path.normpath(p).replace("\\", "/")


def load_config(workspace):
    cfg_dir = os.path.join(SRC_DIR, "config")
    with open(os.path.join(cfg_dir, "extract_labels_config.json"), "r", encoding="utf-8-sig") as f:
        database = json.load(f)
    with open(os.path.join(cfg_dir, "parser_settings.json"), "r", encoding="utf-8-sig") as f:
        parser_settings = json.load(f)
    with open(os.path.join(cfg_dir, "other_settings.json"), "r", encoding="utf-8-sig") as f:
        other_settings = json.load(f)

    cfg = database["FrackinUniverse"]
    # 注入 CI 运行时路径（config 内留空，避免写死绝对路径）
    cfg["prefix"] = _posix(os.path.join(workspace, "translations"))
    cfg["root_dir"] = _posix(os.path.join(workspace, "temp", "FrackinUniverse"))
    cfg["extra_memory_files"] = [
        _posix(os.path.join(workspace, "script", "tools", "starcore_memory.json"))
    ]
    return cfg, parser_settings, other_settings


def main():
    workspace = os.environ["GITHUB_WORKSPACE"]
    token = os.environ["PARA_TOKEN"]
    stage = sys.argv[1] if len(sys.argv) > 1 else "all"

    cfg, parser_settings, other_settings = load_config(workspace)

    if stage == "export":
        create_metadata(
            cfg["root_dir"],
            cfg["prefix"],
            _posix(os.path.join(workspace, "temp", "paks")),
            _posix(os.path.join(workspace, "temp")),
        )
        export_mod_para(cfg["prefix"])
        return

    sysc_paratrans(
        cfg,
        parser_settings,
        other_settings["default_string_blacklist"],
        other_settings["starcore_category_list"],
        token,
        solo_process=(stage == "process"),
        solo_download=(stage == "download"),
        solo_sysc=(stage == "sync"),
    )


if __name__ == "__main__":
    main()
