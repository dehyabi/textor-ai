# AssemblyAI Speech-to-Text API

A Django REST API wrapper for AssemblyAI's transcription service that provides multi-language audio transcription capabilities with advanced features.

## Features

- Multi-language transcription support with auto-detection
- Token-based authentication
- File upload with size validation (10MB limit)
- Real-time transcription status tracking
- Support for various audio formats (MP3, WAV, M4A, etc.)
- Dashboard-like status tracking (Queued, Processing, Completed, Error)
- Automatic sync with AssemblyAI

## Setup

1. Clone the repository:
```bash
git clone [repository-url]
cd be
```

2. Create a virtual environment and activate it:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your AssemblyAI API key:
```
ASSEMBLYAI_API_KEY=your_api_key_here
```

5. Run migrations:
```bash
python3 manage.py migrate
```

6. Create a superuser:
```bash
python3 manage.py createsuperuser
```

7. Run the server:
```bash
python3 manage.py runserver
```

## Authentication

The API uses token-based authentication. To get your token:

1. Create a superuser if you haven't already:
```bash
python3 manage.py createsuperuser
```

2. Log in to the Django admin interface at `http://localhost:8000/admin/` and create a token for your user.

3. Use the token in your API requests:
```bash
Authorization: Bearer your_token_here
```

## API Endpoints

### 1. Upload Audio for Transcription
- **URL:** `/api/transcribe/upload/`
- **Method:** `POST`
- **Authentication:** Required
- **Content-Type:** `multipart/form-data`
- **Parameters:**
  - `file`: Audio file (required, max 10MB)
  - `language_code`: ISO language code (optional)
  - `auto_detect`: Boolean for auto language detection (optional, default: true)
- **Example:**
```bash
curl -X POST \
  -H "Authorization: Bearer your_token" \
  -F "file=@audio.mp3" \
  -F "language_code=en" \
  http://localhost:8000/api/transcribe/upload/
```
- **Response:**
```json
{
    "message": "File uploaded and transcription started",
    "transcript_id": "abc123xyz",
    "status": "queued"
}
```

### 2. List All Transcriptions
- **URL:** `/api/transcribe/`
- **Method:** `GET`
- **Authentication:** Required
- **Description:** Returns all transcriptions with status counts and grouping
- **Pagination Parameters:**
  - `page`: Page number (default: 1)
  - `page_size`: Number of items per page (default: 10, max: 100)
- **Example without pagination:**
```bash
curl -H "Authorization: Bearer your_token" \
  http://localhost:8000/api/transcribe/
```
- **Example with pagination:**
```bash
curl -H "Authorization: Bearer your_token" \
  http://localhost:8000/api/transcribe/?page=1&page_size=10
```
- **Response:**
```json
{
    "count": 15,
    "next": "http://localhost:8000/api/transcribe/?page=2&page_size=10",
    "previous": null,
    "current_page": 1,
    "total_pages": 2,
    "total_count": 3,
    "status_counts": {
        "queued": 1,
        "processing": 1,
        "completed": 1,
        "error": 0
    },
    "transcriptions": {
        "queued": [{
            "id": "abc123",
            "text": null,
            "audio_url": "https://example.com/audio1.mp3",
            "language_code": "en",
            "created_at": "2024-01-24T10:30:00Z",
            "completed_at": null,
            "error": null,
            "status": "queued"
        }],
        "processing": [{
            "id": "def456",
            "text": null,
            "audio_url": "https://example.com/audio2.mp3",
            "language_code": "es",
            "created_at": "2024-01-24T10:35:00Z",
            "completed_at": null,
            "error": null,
            "status": "processing"
        }],
        "completed": [{
            "id": "ghi789",
            "text": "Your transcribed text here...",
            "audio_url": "https://example.com/audio3.mp3",
            "language_code": "en",
            "created_at": "2024-01-24T10:25:00Z",
            "completed_at": "2024-01-24T10:27:00Z",
            "error": null,
            "status": "completed"
        }],
        "error": []
    }
}
```

The response includes:
- `count`: Total number of transcriptions across all pages
- `next`: URL for the next page (null if on last page)
- `previous`: URL for the previous page (null if on first page)
- `current_page`: Current page number
- `total_pages`: Total number of pages available
- `total_count`: Number of transcriptions in the current response
- `status_counts`: Counts for each status in the current response
- `transcriptions`: Grouped transcriptions for the current page

### 3. Get Transcription Status
- **URL:** `/api/transcribe/{transcript_id}/`
- **Method:** `GET`
- **Authentication:** Required
- **Example:**
```bash
curl -H "Authorization: Bearer your_token" \
  http://localhost:8000/api/transcribe/abc123/
```
- **Response:**
```json
{
    "id": "abc123",
    "status": "completed",
    "text": "Your transcribed text here...",
    "audio_url": "https://example.com/audio.mp3",
    "language_code": "en",
    "created_at": "2024-01-24T10:30:00Z",
    "completed_at": "2024-01-24T10:32:00Z"
}
```

### 4. Get All Transcriptions (Flat List)
- **URL:** `/api/transcribe/all/`
- **Method:** `GET`
- **Authentication:** Required
- **Description:** Returns all transcriptions in a single flat list, sorted by creation date (newest first)
- **Example:**
```bash
curl -H "Authorization: Bearer your_token" \
  http://localhost:8000/api/transcribe/all/
```
- **Response:**
```json
{
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "abc123",
            "text": "Your transcribed text here...",
            "audio_url": "https://example.com/audio1.mp3",
            "language_code": "en",
            "created_at": "2024-01-24T10:30:00Z",
            "completed_at": "2024-01-24T10:32:00Z",
            "status": "completed",
            "error": null
        },
        {
            "id": "def456",
            "text": null,
            "audio_url": "https://example.com/audio2.mp3",
            "language_code": "es",
            "created_at": "2024-01-24T10:35:00Z",
            "completed_at": null,
            "status": "processing",
            "error": null
        }
    ]
}
```

## Status Definitions

- **Queued**: The file has been uploaded and is waiting to be processed
- **Processing**: AssemblyAI is currently transcribing the audio
- **Completed**: Transcription is finished and text is available
- **Error**: An error occurred during transcription

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- 400: Bad Request (invalid input)
- 401: Unauthorized (invalid or missing token)
- 403: Forbidden (insufficient permissions)
- 404: Not Found
- 500: Internal Server Error

Error responses include detailed messages:
```json
{
    "error": "Error message here",
    "details": "Additional error details if available"
}
```

## File Requirements

- Maximum file size: 10MB
- Supported formats: MP3, WAV, M4A, and other common audio formats
- Clear audio quality recommended for best results

## Security Features

- Token-based authentication required for all endpoints
- File size validation
- Automatic temporary file cleanup
- Rate limiting on transcription requests
- Secure handling of API keys and tokens

## Development

To run tests:
```bash
python3 manage.py test
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

The MIT License is a permissive license that is short and to the point. It lets people do anything they want with your code as long as they provide attribution back to you and don't hold you liable.

### Key Points:
- ✓ Commercial use
- ✓ Modification
- ✓ Distribution
- ✓ Private use
- ✓ Liability limitations
- ✓ Warranty limitations

### Requirements:
- License and copyright notice must be included with the code
- The same license must be used for derivatives
