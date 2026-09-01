import os
import json
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Any

from json_tools import prepare
from translation_memory import export_memory_para, import_memory_para
import para_api
import logging

logger = logging.getLogger(__name__)

class ParaTranzManager:
    """
    用于管理与ParaTranz项目交互的类，包括下载、同步和文件处理。
    """

    def __init__(
        self,
        para_path: str,
        para_id: str,
        para_token: str,
        subdir: str = "",
        raw_dir: str = "raw",
        extra_memory_files=None,
    ):
        """
        初始化ParaTranzManager。

        Args:
            para_path (str): 本地ParaTranz项目目录的路径。
            para_id (str): ParaTranz项目ID。
            para_token (str): ParaTranz API令牌。
            subdir (str, optional): 在ParaTranz项目中使用的子目录。默认为""。
            raw_dir (str, optional): raw 补丁所在子目录名。默认为"raw"。
            extra_memory_files (list, optional): 额外导入的翻译记忆文件列表。
        """
        self.para_path = Path(para_path).resolve()
        self.para_id = para_id
        self.para_token = para_token
        self.subdir = subdir

        self.raw_path = self.para_path / raw_dir
        self.temp_path = self.para_path / "temp"
        self.memory_file = self.para_path / "memory.json"
        self.extra_memory_files = list(extra_memory_files) if extra_memory_files else []

    def _load_json_file(self, file_path: Path) -> Any:
        """加载并解析JSON文件。"""
        try:
            with file_path.open("r", encoding="utf-8-sig") as f:
                return json.loads(prepare(f))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"错误：无法加载JSON文件 {file_path}: {e}")
            return None

    def _write_json_file(self, file_path: Path, data: Any):
        """将数据写入JSON文件。"""
        try:
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        except IOError as e:
            print(f"错误：无法写入JSON文件 {file_path}: {e}")

    def _fix_translation_file(self, local_file: Path, para_data_path: Path):
        """
        使用从ParaTranz下载的数据修复本地翻译文件。
        """
        if not local_file.name.endswith(".patch"):
            return

        rel_path = local_file.relative_to(self.raw_path)
        para_file = para_data_path / rel_path

        if not para_file.exists():
            return

        local_dict = self._load_json_file(local_file)
        para_dict_list = self._load_json_file(para_file)

        if local_dict is None or para_dict_list is None:
            return
            
        para_dict = {item["path"]: item for item in para_dict_list}

        updated_dict = []
        has_changes = False
        for v in local_dict:
            if v["path"] in para_dict:
                para_item = para_dict[v["path"]]
                if v["value"] != para_item["value"]:
                    updated_dict.append({**v, "value": para_item["value"]})
                    has_changes = True
                else:
                    updated_dict.append(v)
            else:
                updated_dict.append(v)
        if has_changes:
            print(f"正在更新文件：{local_file}")
            self._write_json_file(local_file, updated_dict)

    def download_translations(self):
        """
        从ParaTranz下载最新的翻译并更新本地文件。
        """
        if not self.raw_path.exists():
            print("错误：'raw'目录不存在。")
            return

        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)
        self.temp_path.mkdir(exist_ok=True)

        print("正在导出翻译记忆库...")
        export_memory_para(self.raw_path.as_posix(), self.memory_file.as_posix())

        if not para_api.file_list(self.para_id, self.para_token):
            print("ParaTranz上没有文件，跳过下载。")
            return

        print("正在触发构建...")
        para_api.trigger_artifacts(self.para_id, self.para_token)
        
        print("正在下载构建产物...")
        try:
            para_api.download_artifacts(self.para_id, self.para_token, self.temp_path.as_posix())
        except Exception as e:
            logger.error("下载构建产物失败: %s", e, exc_info=True)
            print(f"下载构建产物失败: {e}")
            return

        print("下载完成，正在解压...")
        zip_path = self.temp_path / "data.zip"
        extract_path = self.temp_path / "data"
        try:
            with zipfile.ZipFile(zip_path, 'r') as fz:
                fz.extractall(extract_path)
        except zipfile.BadZipFile:
            print("错误：下载的文件不是有效的zip文件。")
            return
        print("解压完成。")

        para_data_path = extract_path / "utf8" / self.subdir if self.subdir else extract_path / "utf8"

        print("正在更新翻译...")
        for file_path in self.raw_path.rglob("*.patch"):
            self._fix_translation_file(file_path, para_data_path)
        
        shutil.copytree(str(self.raw_path), str(self.temp_path / "data" / "texts"))
        print("翻译更新完成。")


    def _walk_files(self, path: Path, extension=".patch") -> List[str]:
        """遍历目录并返回具有特定扩展名的文件的相对路径列表。"""
        return [
            p.relative_to(path).as_posix()
            for p in path.rglob(f"*{extension}")
        ]

    def sync_to_paratranz(self):
        """
        将本地更改同步到ParaTranz，包括上传新文件、更新现有文件和删除过时的文件。
        """
        print("正在导入翻译记忆库...")
        import_memory_para(self.raw_path.as_posix(), self.memory_file.as_posix())
        for extra_mem in self.extra_memory_files:
            print(f"正在导入额外翻译记忆库: {extra_mem}")
            import_memory_para(self.raw_path.as_posix(), extra_mem)

        print("正在遍历本地目录...")
        local_files = self._walk_files(self.raw_path)

        print("正在获取在线文件列表...")
        online_files_raw = para_api.file_list(self.para_id, self.para_token)
        if not online_files_raw:
            print("在线列表为空。")
            online_files = {}
        else:
            online_files = {item["name"]: item["id"] for item in online_files_raw}

        if self.subdir:
            online_files = {
                name[len(self.subdir) + 1:]: online_files[name]
                for name in online_files
                if name.startswith(self.subdir + "/")
            }

        local_set = set(local_files)
        online_set = set(online_files.keys())

        files_to_upload = list(local_set.intersection(online_set))
        files_to_add = list(local_set.difference(online_set))
        files_to_delete = list(online_set.difference(local_set))

        if files_to_upload:
            print("\n正在检查要上传的文件...")
            for file_rel_path in files_to_upload:
                local_path = self.raw_path / file_rel_path
                
                # 在temp目录中寻找对应的paratranz文件 
                para_json_path = self.temp_path / "data" / "texts" / file_rel_path
                
                local_json = self._load_json_file(local_path)
                
                needs_upload = True
                if para_json_path.exists():
                    para_json = self._load_json_file(para_json_path)
                    if local_json == para_json:
                        needs_upload = False
                
                if needs_upload:
                    print(f"正在上传: {file_rel_path}")
                    file_id = online_files[file_rel_path]
                    para_api.upload_file(self.para_id, self.para_token, local_path.as_posix(), file_id, encoding="utf-8-sig")
                    para_api.upload_file_trans(self.para_id, self.para_token, local_path.as_posix(), file_id, encoding="utf-8-sig")

        if files_to_delete:
            print("\n正在删除过时的文件...")
            for file_rel_path in files_to_delete:
                print(f"正在删除: {file_rel_path}")
                file_id = online_files[file_rel_path]
                para_api.del_file(self.para_id, self.para_token, file_id)

        if files_to_add:
            print("\n正在上传新文件...")
            for file_rel_path in files_to_add:
                print(f"正在创建: {file_rel_path}")
                local_path = self.raw_path / file_rel_path
                target_dir = (Path(self.subdir) / Path(file_rel_path).parent).as_posix()
                para_api.create_file(self.para_id, self.para_token, local_path.as_posix(), target_dir, encoding="utf-8-sig")
            
            print("正在重新获取在线列表以上传翻译...")
            online_files_raw = para_api.file_list(self.para_id, self.para_token)
            online_files = {item["name"]: item["id"] for item in online_files_raw}
            if self.subdir:
                online_files = {
                    name[len(self.subdir) + 1:]: online_files[name]
                    for name in online_files
                    if name.startswith(self.subdir + "/")
                }

            for file_rel_path in files_to_add:
                if file_rel_path in online_files:
                    print(f"正在上传翻译: {file_rel_path}")
                    local_path = self.raw_path / file_rel_path
                    file_id = online_files[file_rel_path]
                    para_api.upload_file_trans(self.para_id, self.para_token, local_path.as_posix(), file_id, encoding="utf-8-sig")

        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)
        print("同步完成。")
"""
if __name__ == "__main__":
    # 这是一个示例用法。
    # 你需要根据你的项目配置来设置这些值。
    # 例如，从配置文件、环境变量或命令行参数中读取。
    
    # 从环境变量加载配置
    PARA_PATH = os.getenv("PARA_PATH", "path/to/your/paratranz/project")
    PARA_ID = os.getenv("PARA_ID", "your_project_id")
    PARA_TOKEN = os.getenv("PARA_TOKEN", "your_api_token")
    SUBDIR = os.getenv("SUBDIR", "your_subdir")

    # 检查配置是否已设置
    if PARA_PATH == "path/to/your/paratranz/project" or not PARA_ID or not PARA_TOKEN:
        print("请设置 PARA_PATH, PARA_ID, 和 PARA_TOKEN 环境变量。")
        print("例如: export PARA_PATH=/path/to/project")
    else:
        manager = ParaTranzManager(
            para_path=PARA_PATH,
            para_id=PARA_ID,
            para_token=PARA_TOKEN,
            subdir=SUBDIR,
        )

        # 选择要执行的操作
        # manager.download_translations()
        # manager.sync_to_paratranz()
        print("要执行操作，请取消注释上面的 manager.download_translations() 或 manager.sync_to_paratranz()。")
"""
