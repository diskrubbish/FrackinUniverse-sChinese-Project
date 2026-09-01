"""
ParaTranz API 客户端

提供ParaTranz API的同步和异步访问，支持所有核心功能
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Union, Any

# 异步HTTP客户端
import httpx
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# API基础URL
BASE_URL = "https://paratranz.cn/api/projects/"


class APIError(Exception):
    """API调用错误"""

    def __init__(
        self, status_code: int, message: str, error_code: Optional[int] = None
    ):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        super().__init__(
            f"API错误 {status_code}: {message}"
            + (f" (代码: {error_code})" if error_code else "")
        )


class AsyncParaTranzClient:
    """异步ParaTranz API客户端"""

    def __init__(
        self,
        token: str,
        base_url: str = "https://paratranz.cn/api",
        timeout: float = 30.0,
        max_connections: int = 10,
        retries: int = 3,
    ):
        """
        初始化异步API客户端

        Args:
            token: ParaTranz API Token
            base_url: API基础URL
            timeout: 请求超时时间(秒)
            max_connections: 最大并发连接数
            retries: 失败自动重试次数
        """
        self.token = token
        self.base_url = base_url
        self.timeout = timeout
        self.max_connections = max_connections
        self.retries = retries

        # 延迟初始化客户端
        self._client = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        # 确保客户端被初始化
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": self.token,
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip, deflate",
                    "User-Agent": "ParaTranzAsyncClient/1.0",
                },
                timeout=self.timeout,
                limits=httpx.Limits(max_connections=self.max_connections),
                follow_redirects=True,
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @property
    def client(self):
        """获取httpx客户端，如果未初始化则创建新实例"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": self.token,
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip, deflate",
                    "User-Agent": "ParaTranzAsyncClient/1.0",
                },
                timeout=self.timeout,
                limits=httpx.Limits(max_connections=self.max_connections),
                follow_redirects=True,
            )
        return self._client

    async def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """
        发送异步HTTP请求并处理错误

        Args:
            method: HTTP方法 (GET, POST等)
            url: API终端URL
            **kwargs: 传递给httpx的参数

        Returns:
            解析后的JSON响应

        Raises:
            APIError: 当API返回错误时
        """
        # 重试逻辑
        for attempt in range(self.retries + 1):
            try:
                response = await self.client.request(method=method, url=url, **kwargs)

                # 处理频率限制
                if response.status_code == 429:
                    if attempt < self.retries:
                        # 指数退避策略
                        wait_time = (2**attempt) * 1.5
                        print(f"API频率限制，等待 {wait_time:.1f} 秒后重试...")
                        await asyncio.sleep(wait_time)
                        continue

                # 处理错误
                if not response.is_success:
                    try:
                        error_data = response.json()
                        message = error_data.get("message", "未知错误")
                        error_code = error_data.get("code")
                    except:
                        message = response.text or "未知错误"
                        error_code = None

                    raise APIError(response.status_code, message, error_code)

                # 检查响应体是否为空
                if response.text:
                    try:
                        return response.json()
                    except json.JSONDecodeError:
                        # 如果响应不是有效的JSON，但请求成功，可以根据需要处理
                        # 这里我们返回一个包含原始文本的字典，或直接返回文本
                        return {"content": response.text}
                else:
                    # 对于没有响应体的成功请求(如DELETE)，返回空字典
                    return {}

            except httpx.RequestError as e:
                if attempt < self.retries:
                    wait_time = (2**attempt) * 1.0
                    logger.warning("请求错误(第%d次): %s", attempt + 1, e)
                    print(f"请求错误: {str(e)}, 等待 {wait_time:.1f} 秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("请求最终失败: %s", e, exc_info=True)
                    raise APIError(0, f"请求失败: {str(e)}")

        # 不应该到达这里
        raise APIError(0, "所有重试均失败")

    async def file_list(self, project_id: Union[str, int]) -> List[Dict[str, Any]]:
        """
        获取项目文件列表

        Args:
            project_id: 项目ID

        Returns:
            文件列表
        """
        url = f"/projects/{project_id}/files"
        result = await self._request("GET", url)
        # 确保返回的是列表类型
        return result if isinstance(result, list) else []

    async def file(
        self,
        project_id: Union[str, int],
        fileid: Optional[int] = None,
        page: Optional[int] = None,
        page_size: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        获取项目字符串

        Args:
            project_id: 项目ID
            fileid: 文件ID
            page: 页码
            page_size: 每页数量

        Returns:
            字符串列表
        """
        url = f"/projects/{project_id}/strings"
        params = {"pageSize": page_size, "page": page, "file": fileid}
        # 过滤None值
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._request("GET", url, params=params)
        return response.get("results", [])

    async def revision(
        self,
        project_id: Union[str, int],
        page: Optional[int] = None,
        page_size: int = 50,
        fileid: Optional[int] = None,
        type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取文件历史

        Args:
            project_id: 项目ID
            page: 页码
            page_size: 每页数量
            fileid: 文件ID
            type: 历史类型 (create, update, import)

        Returns:
            历史记录列表
        """
        if type not in [None, "create", "update", "import"]:
            raise ValueError("type 必须是 None, 'create', 'update' 或 'import'")

        url = f"/projects/{project_id}/files/revisions"
        params = {"pageSize": page_size, "page": page, "file": fileid, "type": type}
        # 过滤None值
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._request("GET", url, params=params)
        return response.get("results", [])

    async def create_file(
        self,
        project_id: Union[str, int],
        file_path: str,
        target_path: str,
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:
        """
        创建项目文件

        Args:
            project_id: 项目ID
            file_path: 本地文件路径
            target_path: 目标路径
            encoding: 文件编码

        Returns:
            创建结果
        """
        url = f"/projects/{project_id}/files"

        with open(file_path, "r", encoding=encoding) as f:
            file_content = f.read()

        files = {"file": (os.path.basename(file_path), file_content)}
        data = {"path": target_path}

        return await self._request("POST", url, files=files, data=data)

    async def upload_file(
        self,
        project_id: Union[str, int],
        file_path: str,
        fileid: Union[str, int],
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:
        """
        更新项目文件

        Args:
            project_id: 项目ID
            file_path: 本地文件路径
            fileid: 文件ID
            encoding: 文件编码

        Returns:
            更新结果
        """
        url = f"/projects/{project_id}/files/{fileid}"

        with open(file_path, "r", encoding=encoding) as f:
            file_content = f.read()

        files = {"file": (os.path.basename(file_path), file_content)}

        return await self._request("POST", url, files=files)

    async def upload_file_trans(
        self,
        project_id: Union[str, int],
        file_path: str,
        fileid: Union[str, int],
        encoding: str = "utf-8",
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        上传文件翻译

        Args:
            project_id: 项目ID
            file_path: 本地文件路径
            fileid: 文件ID
            encoding: 文件编码
            force: 是否强制覆盖

        Returns:
            上传结果
        """
        url = f"/projects/{project_id}/files/{fileid}/translation"

        with open(file_path, "r", encoding=encoding) as f:
            file_content = f.read()

        files = {"file": (os.path.basename(file_path), file_content)}
        data = {"force": "true" if force else "false"}

        return await self._request("POST", url, files=files, data=data)

    async def del_file(
        self, project_id: Union[str, int], fileid: Union[str, int]
    ) -> Dict[str, Any]:
        """
        删除项目文件

        Args:
            project_id: 项目ID
            fileid: 文件ID

        Returns:
            删除结果
        """
        url = f"/projects/{project_id}/files/{fileid}"
        return await self._request("DELETE", url)

    async def upload_translation(
        self,
        project_id: Union[str, int],
        strid: Union[str, int],
        translation: str,
        uid: Optional[Union[str, int]] = None,
    ) -> Dict[str, Any]:
        """
        上传翻译

        Args:
            project_id: 项目ID
            strid: 字符串ID
            translation: 翻译内容
            uid: 用户ID

        Returns:
            上传结果
        """
        url = f"/projects/{project_id}/strings/{strid}"
        data = {"translation": translation}
        if uid is not None:
            data["uid"] = uid

        return await self._request("PUT", url, json=data)

    async def get_string(
        self, project_id: Union[str, int], strid: Union[str, int]
    ) -> Dict[str, Any]:
        """
        获取字符串

        Args:
            project_id: 项目ID
            strid: 字符串ID

        Returns:
            字符串信息
        """
        url = f"/projects/{project_id}/strings/{strid}"
        return await self._request("GET", url)

    async def get_artifacts(self, project_id: Union[str, int]) -> Dict[str, Any]:
        """
        获取制品列表

        Args:
            project_id: 项目ID

        Returns:
            制品列表
        """
        url = f"/projects/{project_id}/artifacts"
        return await self._request("GET", url)

    async def trigger_artifacts(self, project_id: Union[str, int]) -> Dict[str, Any]:
        """
        触发制品构建

        Args:
            project_id: 项目ID

        Returns:
            触发结果
        """
        url = f"/projects/{project_id}/artifacts"
        return await self._request("POST", url)

    async def download_artifacts(
        self,
        project_id: Union[str, int],
        download_path: str,
        chunk_size: int = 8192,
        show_progress: bool = True,
    ) -> str:
        """
        下载制品文件

        Args:
            project_id: 项目ID
            download_path: 下载路径
            chunk_size: 分块大小
            show_progress: 是否显示进度

        Returns:
            下载文件路径
        """
        url = f"/projects/{project_id}/artifacts/download"

        # 创建下载目录
        os.makedirs(download_path, exist_ok=True)
        file_path = os.path.join(download_path, "data.zip")

        # 流式下载
        async with self.client.stream("GET", url) as response:
            if not response.is_success:
                try:
                    error_data = response.json()
                    message = error_data.get("message", "未知错误")
                    error_code = error_data.get("code")
                except:
                    message = response.text or "下载失败"
                    error_code = None

                raise APIError(response.status_code, message, error_code)

            # 获取文件大小
            total_size = int(response.headers.get("content-length", 0))

            # 打开文件进行写入
            with open(file_path, "wb") as f:
                downloaded = 0
                start_time = asyncio.get_event_loop().time()

                async for chunk in response.aiter_bytes(chunk_size):
                    f.write(chunk)
                    downloaded += len(chunk)

                    # 显示下载进度
                    if show_progress and total_size > 0:
                        elapsed = asyncio.get_event_loop().time() - start_time
                        speed = downloaded / elapsed if elapsed > 0 else 0
                        percent = (downloaded / total_size) * 100

                        # 格式化速度
                        if speed < 1024:
                            speed_str = f"{speed:.1f} B/s"
                        elif speed < 1024 * 1024:
                            speed_str = f"{speed/1024:.1f} KB/s"
                        else:
                            speed_str = f"{speed/(1024*1024):.1f} MB/s"

                        print(
                            f"\r下载进度: {percent:.1f}% | {downloaded}/{total_size} | {speed_str}",
                            end="",
                        )

        if show_progress:
            print(f"\n下载完成: {file_path}")

        return file_path


###########################################
# 同步包装函数，保持兼容性
# 所有函数直接委托给 AsyncParaTranzClient，
# 移除了冗余的 requests 回退实现
###########################################


def _sync_run(coro_func, *args, **kwargs):
    """统一的同步调用包装器：运行协程函数并返回结果"""
    return asyncio.run(coro_func(*args, **kwargs))


def file_list(project_id, para_token):
    """获取项目文件列表(同步版本)"""
    async def _impl():
        async with AsyncParaTranzClient(para_token) as client:
            return await client.file_list(project_id)
    return _sync_run(_impl)


def file(project_id, para_token, fileid=None, page=None, pageSize=50):
    """获取项目字符串(同步版本)"""
    async def _impl():
        async with AsyncParaTranzClient(para_token) as client:
            return await client.file(project_id, fileid, page, pageSize)
    return _sync_run(_impl)


def revision(project_id, para_token, page=None, pageSize=50, fileid=None, type=None):
    """获取文件历史(同步版本)"""
    async def _impl():
        async with AsyncParaTranzClient(para_token) as client:
            return await client.revision(project_id, page, pageSize, fileid, type)
    return _sync_run(_impl)


def create_file(project_id, para_token, file, path, encoding="utf-8-sig"):
    """创建项目文件(同步版本)"""
    async def _impl():
        async with AsyncParaTranzClient(para_token) as client:
            return await client.create_file(project_id, file, path, encoding)
    return _sync_run(_impl)


def upload_file(project_id, para_token, file, fileid, encoding="utf-8-sig"):
    """更新项目文件(同步版本)"""
    async def _impl():
        async with AsyncParaTranzClient(para_token) as client:
            return await client.upload_file(project_id, file, fileid, encoding)
    return _sync_run(_impl)


def upload_file_trans(project_id, para_token, file, fileid, encoding="utf-8-sig", force=False):
    """上传文件翻译(同步版本)"""
    async def _impl():
        async with AsyncParaTranzClient(para_token) as client:
            return await client.upload_file_trans(project_id, file, fileid, encoding, force)
    return _sync_run(_impl)


def del_file(project_id, para_token, fileid):
    """删除项目文件(同步版本)"""
    async def _impl():
        async with AsyncParaTranzClient(para_token) as client:
            return await client.del_file(project_id, fileid)
    return _sync_run(_impl)


def upload_translation(project_id, para_token, strid, translation, uid=None):
    """上传翻译(同步版本)"""
    async def _impl():
        async with AsyncParaTranzClient(para_token) as client:
            return await client.upload_translation(project_id, strid, translation, uid)
    return _sync_run(_impl)


def get_string(project_id, para_token, strid):
    """获取字符串(同步版本)"""
    async def _impl():
        async with AsyncParaTranzClient(para_token) as client:
            return await client.get_string(project_id, strid)
    return _sync_run(_impl)


def get_artifacts(project_id, para_token):
    """获取制品列表(同步版本)"""
    async def _impl():
        async with AsyncParaTranzClient(para_token) as client:
            return await client.get_artifacts(project_id)
    return _sync_run(_impl)


def trigger_artifacts(project_id, para_token):
    """触发制品构建(同步版本)"""
    async def _impl():
        async with AsyncParaTranzClient(para_token) as client:
            return await client.trigger_artifacts(project_id)
    return _sync_run(_impl)


def download_artifacts(project_id, para_token, download_path, show_progress=True):
    """
    下载项目制品文件(同步版本)

    Args:
        project_id: 项目ID
        para_token: API令牌
        download_path: 下载路径
        show_progress: 是否显示下载进度

    Returns:
        下载文件的路径
    """
    async def _impl():
        async with AsyncParaTranzClient(para_token) as client:
            return await client.download_artifacts(
                project_id, download_path, show_progress=show_progress
            )
    return _sync_run(_impl)
