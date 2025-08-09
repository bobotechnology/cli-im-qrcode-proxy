# QR Code Recognition API Proxy

A FastAPI-based proxy service for Caoliao QR code recognition API.

## Features

- Proxy service for Caoliao QR code recognition
- Supports image file upload and QR code content decoding
- Automatic API request handling and response transformation

## API Specification

### POST /decode_qrcode/

**Parameters:**
- `file`: Image file in multipart/form-data format

**Success Response:**
```json
{
    "content": "decoded QR code content"
}
```

**Error Responses:**
- 400: Upload/Decode failure
- 502: Third-party API returned invalid data

## Example Request

```bash
curl -X POST -F "file=@qrcode.jpg" http://localhost:8000/decode_qrcode/
```

## Error Handling

- `400 Bad Request`: Upload or decode failure
- `502 Bad Gateway`: Third-party API returned invalid data

## How to Run

1. Install dependencies:
```bash
pip install fastapi uvicorn aiohttp python-multipart
```

2. Run the service:
```bash
python request.py
```

The service will be available at `http://localhost:8000`

## Author
bobo

## Version
v1.1
