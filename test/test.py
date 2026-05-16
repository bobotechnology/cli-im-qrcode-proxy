import os
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import requests
from fastapi.testclient import TestClient
from qrcode import make as create_qrcode

from app import app


class QRCodeAPITest(unittest.TestCase):
    """单元测试 - 使用 mock 隔离外部依赖"""

    def setUp(self):
        self.client = TestClient(app)
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        qr_img = create_qrcode("TEST_DATA")
        qr_img.save(self.temp_file.name)
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    @patch("app.aiohttp.ClientSession")
    def test_valid_qrcode_decoding(self, MockSession):
        """正常二维码解码"""
        responses = iter([
            '{"status":"1","data":{"path":"/tmp/test.jpg"}}',
            '{"status":1,"data":{"qrcode_content":"TEST_DATA"}}',
        ])

        def mock_post(*args, **kwargs):
            text = next(responses)
            ctx = AsyncMock()
            ctx.__aenter__.return_value = MagicMock(text=AsyncMock(return_value=text))
            ctx.__aexit__.return_value = False
            return ctx

        mock_session = AsyncMock()
        mock_session.post = mock_post
        MockSession.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        MockSession.return_value.__aexit__ = AsyncMock(return_value=False)

        with open(self.temp_file.name, "rb") as f:
            resp = self.client.post("/decode_qrcode/", files={"file": f})

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["content"], "TEST_DATA")

    @patch("app.aiohttp.ClientSession")
    def test_upload_failure(self, MockSession):
        """上传失败返回 400"""

        def mock_post(*args, **kwargs):
            ctx = AsyncMock()
            ctx.__aenter__.return_value = MagicMock(
                text=AsyncMock(return_value='{"status":"0","info":"invalid file"}')
            )
            ctx.__aexit__.return_value = False
            return ctx

        mock_session = AsyncMock()
        mock_session.post = mock_post
        MockSession.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        MockSession.return_value.__aexit__ = AsyncMock(return_value=False)

        with open(self.temp_file.name, "rb") as f:
            resp = self.client.post("/decode_qrcode/", files={"file": f})

        self.assertEqual(resp.status_code, 400)
        self.assertIn("detail", resp.json())

    @patch("app.aiohttp.ClientSession")
    def test_decode_api_returns_invalid_json(self, MockSession):
        """识别接口返回非 JSON"""
        responses = iter([
            '{"status":"1","data":{"path":"/tmp/test.jpg"}}',
            "this is not json",
        ])

        def mock_post(*args, **kwargs):
            text = next(responses)
            ctx = AsyncMock()
            ctx.__aenter__.return_value = MagicMock(text=AsyncMock(return_value=text))
            ctx.__aexit__.return_value = False
            return ctx

        mock_session = AsyncMock()
        mock_session.post = mock_post
        MockSession.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        MockSession.return_value.__aexit__ = AsyncMock(return_value=False)

        with open(self.temp_file.name, "rb") as f:
            resp = self.client.post("/decode_qrcode/", files={"file": f})

        self.assertEqual(resp.status_code, 502)


@unittest.skipUnless(os.getenv("INTEGRATION_TEST"), "设置 INTEGRATION_TEST=1 跳过联网测试")
class QRCodeIntegrationTest(unittest.TestCase):
    """集成测试 - 需要联网 + 已启动的服务"""

    API_URL = "http://localhost:8000/decode_qrcode/"

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        qr_img = create_qrcode("HELLO_INTEGRATION")
        qr_img.save(self.temp_file.name)
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_real_qrcode_decode(self):
        """真实二维码解码 - 联网调用 cli.im"""
        with open(self.temp_file.name, "rb") as f:
            resp = requests.post(self.API_URL, files={"file": f}, timeout=30)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("content", data)
        self.assertEqual(data["content"], "HELLO_INTEGRATION")

    def test_real_invalid_file(self):
        """真实无效文件上传"""
        invalid = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
        invalid.write(b"not an image")
        invalid.close()
        try:
            with open(invalid.name, "rb") as f:
                resp = requests.post(
                    self.API_URL,
                    files={"file": ("bad.txt", f, "text/plain")},
                    timeout=30,
                )
            self.assertEqual(resp.status_code, 400)
        finally:
            os.unlink(invalid.name)


if __name__ == "__main__":
    unittest.main()
