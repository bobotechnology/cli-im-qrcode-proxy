import unittest
import os
import tempfile
import requests
from qrcode import make as create_qrcode

class QRCodeAPITest(unittest.TestCase):
    API_URL = "http://localhost:8000/decode_qrcode/"
    
    def setUp(self):
        # 创建临时QR码测试文件
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        qr_img = create_qrcode("TEST_DATA")
        qr_img.save(self.temp_file.name)
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_valid_qrcode_decoding(self):
        """测试有效的QR码解码"""
        with open(self.temp_file.name, "rb") as f:
            response = requests.post(
                self.API_URL,
                files={"file": f}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["content"], "TEST_DATA")

    def test_invalid_file(self):
        """测试无效文件上传"""
        # 创建纯文本文件作为无效文件
        invalid_file = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
        invalid_file.write(b"This is not an image file")
        invalid_file.close()
        
        try:
            with open(invalid_file.name, "rb") as f:
                response = requests.post(
                    self.API_URL,
                    files={"file": ("invalid.txt", f, "text/plain")}
                )
            self.assertEqual(response.status_code, 400)
            self.assertIn("error", response.json())
        finally:
            os.unlink(invalid_file.name)

    def test_empty_file(self):
        """测试空文件上传"""
        empty_file = tempfile.NamedTemporaryFile()
        response = requests.post(
            self.API_URL,
            files={"file": empty_file}
        )
        empty_file.close()
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

if __name__ == "__main__":
    unittest.main()
