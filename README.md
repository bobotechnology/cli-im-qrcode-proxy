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

```
curl -X POST -F "file=@qrcode.jpg" http://localhost:8000/decode_qrcode/
```

## Error Handling

- `400 Bad Request`: Upload or decode failure
- `502 Bad Gateway`: Third-party API returned invalid data

## How to Run

1. Install dependencies:
```
pip install fastapi uvicorn aiohttp python-multipart
```

2. Run the service:
```
python app.py
```

The service will be available at `http://localhost:8000`

## Testing

### Test Environment Setup
```
pip install pytest requests pillow qrcode[pil]
```

### Running Tests
1. First start the service:
```
python app.py
```

2. In a new terminal, run API tests:
```
python -m unittest test.test
```

### Expected Results
- Valid QR code: Returns 200 status with `content` field
- Invalid file: Returns 400 status with `error` field

## Author
bobo

## Version
v1.1
