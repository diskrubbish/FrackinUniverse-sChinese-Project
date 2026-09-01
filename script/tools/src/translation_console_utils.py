from database_builder import stbtran_para

from translation_memory import *
from download_paratrans import ParaTranzManager
from collections import defaultdict, ChainMap
import re
from logging_utils import setup_logging, get_logger


def sysc_paratrans(
    selected_file_config,
    default_parser_settings,
    default_string_blacklist,
    starcore_category_list,
    Authorization,
    solo_process=False,
    solo_download=False,
    solo_sysc=False,
):
    setup_logging()
    log = get_logger("console_utils")
    log.info("=" * 60)
    log.info("sysc_paratrans 开始")
    log.info("prefix=%s", selected_file_config.get("prefix"))
    log.info("root_dir=%s", selected_file_config.get("root_dir"))
    para_cfg = selected_file_config.get("para", {})
    log.info("para.id=%s subdir=%s", para_cfg.get("id"), para_cfg.get("subdir"))
    log.info(
        "solo_process=%s solo_download=%s solo_sysc=%s",
        solo_process,
        solo_download,
        solo_sysc,
    )

    def merge_dicts(dict1, dict2):
        merged_dict = defaultdict(list)
        inter_kays = list(set(dict1).intersection(dict2.keys()))
        for key, value in ChainMap(dict1, dict2).items():
            if key not in inter_kays:
                merged_dict[key].extend(value)
            else:
                merged_dict[key].extend(dict1[key] + dict2[key])

        return dict(merged_dict)

    files_of_interest = {
        ext: [re.compile(p) for p in poi]
        for ext, poi in merge_dicts(
            default_parser_settings, selected_file_config["extra_files_of_interest"]
        ).items()
    }
    string_blacklist = (
        default_string_blacklist + selected_file_config["extra_string_blacklist"]
    )
    category = starcore_category_list + selected_file_config["extra_category_list"]

    manager = ParaTranzManager(
        para_path=selected_file_config["prefix"],
        para_id=selected_file_config["para"]["id"],
        para_token=Authorization,
        subdir=selected_file_config["para"]["subdir"],
        raw_dir=selected_file_config.get("texts_prefix", "raw"),
        extra_memory_files=selected_file_config.get("extra_memory_files"),
    )

    if (
        solo_download == False and solo_process == False and solo_sysc == False
    ) or solo_download == True:
        manager.download_translations()
    if (
        solo_download == False and solo_process == False and solo_sysc == False
    ) or solo_process == True:
        stbtran_para(
            selected_file_config["root_dir"],
            selected_file_config["prefix"],
            files_of_interest,
            selected_file_config["patch_serialization"],
            selected_file_config["dir_blacklist"],
            selected_file_config["path_blacklist"],
            selected_file_config["ignore_filelist"],
            string_blacklist,
            category=category,
            texts_prefix=selected_file_config["texts_prefix"],
        )
    if (
        solo_download == False and solo_process == False and solo_sysc == False
    ) or solo_sysc == True:
        manager.sync_to_paratranz()


def merge_dicts(dict1, dict2):
    merged_dict = defaultdict(list)
    inter_kays = list(set(dict1).intersection(dict2.keys()))
    for key, value in ChainMap(dict1, dict2).items():
        if key not in inter_kays:
            merged_dict[key].extend(value)
        else:
            merged_dict[key].extend(dict1[key] + dict2[key])

    return dict(merged_dict)
