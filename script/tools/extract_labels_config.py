
from parser_settings import files_of_interest
default_string_blacklist = ["0", "set at runtime", "tree", "Replace Me", "replace me", "", "^shadow;$dmg$",
                            "-todo-", "--TODO--", "replaceme", "recruit name", "mission text", "recruit description"]
file_list = [
    {
        "name": "Test",
        "para": {"id": "", "subdir": ""},
        "files_of_interest": files_of_interest,
        "processer": "stbtran_para",
        "root_dir": "",
        "prefix": "",
        "texts_prefix": "raw",
        "ignore_filelist": [
        ],
        "dir_blacklist": [
        ],
        "path_blacklist": {
        },
        "patch_serialization": {
        },
        "string_blacklist": default_string_blacklist,
    },
    
]
