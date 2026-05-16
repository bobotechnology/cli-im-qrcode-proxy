# QR Code Recognition API Proxy

代理草料二维码识别服务，提供本地 REST API 接口。

## 功能

- 代理草料二维码识别 API
- 支持图片文件上传与二维码内容解码
- 自动处理请求和响应转换

## API 接口

### POST /decode_qrcode/

**参数：**
- `file`：multipart/form-data 格式的图片文件

**成功响应 (200)：**
```json
{
    "content": "二维码内容"
}
```

**错误响应：**
- `400`：上传或解码失败
- `502`：第三方接口返回异常数据
- `504`：网络错误

**示例请求：**
```bash
curl -X POST -F "file=@qrcode.jpg" http://localhost:8000/decode_qrcode/
```

## 运行

### 安装依赖

```
pip install fastapi uvicorn aiohttp python-multipart qrcode[pil]
```

### 启动服务

```
python app.py
```

服务地址：`http://localhost:8000`

## 测试

### 单元测试（无需联网）

使用 mock 隔离外部依赖，无需启动服务即可运行。

```
pip install pytest qrcode[pil]
python -m unittest test.test.QRCodeAPITest -v
```

### 集成测试（需联网 + 已启动服务）

真实调用 cli.im 接口，验证完整链路。

```bash
# 终端1：启动服务
python app.py

# 终端2：运行集成测试
$env:INTEGRATION_TEST="1"; python -m unittest test.test.QRCodeIntegrationTest -v
```

不设置 `INTEGRATION_TEST` 环境变量时自动跳过。

### 全部测试

```
python -m unittest test.test -v
```

### 测试用例

**单元测试 (QRCodeAPITest)**

| 用例 | 说明 |
|------|------|
| test_valid_qrcode_decoding | 正常二维码解码 |
| test_upload_failure | 上传失败返回 400 |
| test_decode_api_returns_invalid_json | 识别接口返回非 JSON |

**集成测试 (QRCodeIntegrationTest)**

| 用例 | 说明 |
|------|------|
| test_real_qrcode_decode | 真实二维码联网识别 |
| test_real_invalid_file | 真实无效文件上传 |

## 作者
bobo

## 版本
v1.3
