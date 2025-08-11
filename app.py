"""
QR Code Recognition API Proxy

Description:
- Provides RESTful API to proxy Caoliao QR Code recognition service
- Supports image file upload and QR code content decoding
- Handles API requests and response transformation automatically

API Specification:
POST /decode_qrcode/
- Parameter: file (image file in multipart/form-data format)
- Success response: {"content": "decoded QR code content"}
- Error response: {"error": "error description"}

Example:
curl -X POST -F "file=@qrcode.jpg" http://localhost:8000/decode_qrcode/

Error Handling:
- 400: Upload/Decode failure
- 502: Third-party API returned invalid data

Author: bobo
Version: v1.1
"""

import colorama
colorama.init()

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import aiohttp
import json
import uvicorn

app = FastAPI()

UPLOAD_URL = "https://upload.api.cli.im/upload.php?kid=cliim"
DECODE_URL = "https://qrdetector-api.cli.im/v1/detect_binary"

UPLOAD_HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Origin": "https://cli.im",
    "Pragma": "no-cache",
    "Referer": "https://cli.im/deqr/other",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
}

DECODE_HEADERS = {
    **UPLOAD_HEADERS,
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

async def upload_file(session, file):
    form = aiohttp.FormData()
    # 读取SpooledTemporaryFile内容 / Read file content from SpooledTemporaryFile
    file_content = await file.read()
    form.add_field("Filedata", file_content, filename=file.filename,
                   content_type=file.content_type or "image/jpeg")
    # 重置文件指针以便重用 / Reset file pointer for potential reuse
    await file.seek(0)
    async with session.post(UPLOAD_URL, data=form,
                            headers=UPLOAD_HEADERS) as r:
        raw = await r.text()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise HTTPException(502, f"Upload API returned non-JSON: {raw[:200]}")
    if str(data.get("status")) != "1":
        raise HTTPException(400, data.get("info", "Upload failed"))
    return data["data"]["path"]

async def decode_qrcode(session, oss_path):
    payload = {"remove_background": "1", "image_path": oss_path}
    async with session.post(DECODE_URL, headers=DECODE_HEADERS,
                            data=payload) as r:
        raw = await r.text()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise HTTPException(502, f"Decode API returned non-JSON: {raw[:200]}")
    if data.get("status") != 1:
        raise HTTPException(400, data.get("message", "Decode failed"))
    return data["data"]["qrcode_content"]

@app.post("/decode_qrcode/")
async def decode_endpoint(file: UploadFile = File(...)):
    async with aiohttp.ClientSession() as session:
        try:
            path = await upload_file(session, file)
            content = await decode_qrcode(session, path)
            return JSONResponse({"content": content})
        except HTTPException as e:
            return JSONResponse({"error": e.detail}, status_code=e.status_code)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
