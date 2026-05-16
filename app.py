"""
QR Code Recognition API Proxy

代理草料二维码识别服务，提供本地 REST API 接口。

API:
    POST /decode_qrcode/
        参数: file (multipart/form-data 图片文件)
        成功: {"content": "二维码内容"}
        失败: {"error": "错误信息"}

Example:
    curl -X POST -F "file=@qrcode.jpg" http://localhost:8000/decode_qrcode/

Author: bobo
Version: v1.3
"""

import json
import logging

import aiohttp
import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

app = FastAPI(title="QR Code Proxy", version="1.3.0")

UPLOAD_URL = "https://upload.api.cli.im/upload.php?kid=cliim"
DECODE_URL = "https://qrdetector-api.cli.im/v1/detect_binary"

COMMON_HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Origin": "https://cli.im",
    "Pragma": "no-cache",
    "Referer": "https://cli.im/deqr/other",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
    ),
}

UPLOAD_HEADERS = {**COMMON_HEADERS}
DECODE_HEADERS = {**COMMON_HEADERS, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}


async def upload_file(session: aiohttp.ClientSession, file: UploadFile) -> str:
    """上传图片到草料 OSS，返回图片路径"""

    form = aiohttp.FormData()
    file_content = await file.read()
    form.add_field(
        "Filedata",
        file_content,
        filename=file.filename,
        content_type=file.content_type or "image/jpeg",
    )
    await file.seek(0)

    async with session.post(UPLOAD_URL, data=form, headers=UPLOAD_HEADERS) as resp:
        raw = await resp.text()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        log.error("Upload API returned non-JSON: %s", raw[:200])
        raise HTTPException(status_code=502, detail=f"Upload API returned non-JSON: {raw[:200]}")

    if str(data.get("status")) != "1":
        log.warning("Upload failed: %s", data.get("info"))
        raise HTTPException(status_code=400, detail=data.get("info", "Upload failed"))

    path = data.get("data", {}).get("path")
    if not path:
        log.error("Invalid upload response: missing path")
        raise HTTPException(status_code=502, detail="Invalid upload API response structure")

    log.info("File uploaded: %s", path)
    return path


async def decode_qrcode(session: aiohttp.ClientSession, oss_path: str) -> str:
    """调用识别接口，返回二维码内容"""

    payload = {"remove_background": "1", "image_path": oss_path}

    try:
        async with session.post(DECODE_URL, headers=DECODE_HEADERS, data=payload) as resp:
            raw = await resp.text()
    except aiohttp.ClientError as e:
        log.error("Network error calling decode API: %s", e)
        raise HTTPException(status_code=504, detail=f"Network error: {e}")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        log.error("Decode API returned non-JSON: %s", raw[:200])
        raise HTTPException(status_code=502, detail=f"Decode API returned non-JSON: {raw[:200]}")

    if data.get("status") != 1:
        log.warning("Decode failed: %s", data.get("message"))
        raise HTTPException(status_code=400, detail=data.get("message", "Decode failed"))

    content = data.get("data", {}).get("qrcode_content")
    if not content:
        log.error("Invalid decode response: missing qrcode_content")
        raise HTTPException(status_code=502, detail="Invalid decode API response structure")

    log.info("QR code decoded successfully")
    return content


@app.post("/decode_qrcode/")
async def decode_endpoint(file: UploadFile = File(...)) -> JSONResponse:
    """接收图片文件，返回解码后的二维码内容"""

    log.info("Received file: %s (%s)", file.filename, file.content_type)

    async with aiohttp.ClientSession() as session:
        oss_path = await upload_file(session, file)
        content = await decode_qrcode(session, oss_path)

    return JSONResponse({"content": content})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
