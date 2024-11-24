# Textor-AI

A powerful Speech-to-Text API built with Django REST Framework and AssemblyAI. Textor-AI provides enterprise-grade transcription capabilities with advanced features like multi-language support, real-time status tracking, and comprehensive transcription management.

## Features

- 🎯 High-accuracy speech-to-text conversion
- 🌍 Multi-language transcription support
- 📊 Real-time transcription status tracking
- 🔄 Automatic synchronization with AssemblyAI
- 🔐 Secure token-based authentication
- 📱 RESTful API with comprehensive documentation
- 📂 Support for multiple audio formats
- 📋 Grouped transcription listing with pagination
- ⚡ Rate limiting and error handling

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

Authentication is optional but recommended for higher rate limits. The API uses token-based authentication.

**With Authentication:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/transcribe/
```

**Without Authentication:**
```bash
curl http://localhost:8000/api/transcribe/
```

See [Rate Limiting](#rate-limiting) section for details on request limits.

### Obtaining an Authentication Token

To get higher rate limits, you can obtain an authentication token:

1. Create a user account through the Django admin interface
2. Generate a token for your user
3. Include the token in your API requests using the Authorization header

## API Endpoints

### 1. Upload Audio for Transcription
- **URL:** `/api/transcribe/upload/`
- **Method:** `POST`
- **Authentication:** Optional
- **Content-Type:** `multipart/form-data`
- **Constraints:**
  - Maximum file size: 5MB
  - Supported formats: MP3, WAV, M4A, AAC, OGG, FLAC
- **Parameters:**
  - `file`: Audio file (required)
  - `language_code`: ISO language code (optional)
  - `auto_detect`: Boolean to enable language auto-detection (optional, default: true)
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

### 2. List Transcriptions

**Endpoint:** `GET /api/transcribe/`

List all transcriptions for the authenticated user, grouped by status. Results are paginated.

**Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Number of items per page (default: 10, max: 100)

**Example Request:**
```bash
curl -X GET \
  'http://localhost:8000/api/transcribe/?page=1&page_size=10' \
  -H 'Authorization: Bearer YOUR_TOKEN'
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
- **Authentication:** Optional
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
- **URL:** `/api/transcribe/`
- **Method:** `GET`
- **Authentication:** Optional
- **Description:** Returns all transcriptions in a single flat list, sorted by creation date (newest first)
- **Example:**
```bash
curl -H "Authorization: Bearer your_token" \
  http://localhost:8000/api/transcribe/
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

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Authenticated Users:**
  - 25 requests per day
  - Resets at midnight UTC
  - Access to all transcriptions
  - Full pagination support
  - Rate limit headers included in response

- **Anonymous Users:**
  - 5 requests per day
  - Resets at midnight UTC
  - Limited to viewing 5 most recent transcriptions
  - Same upload capabilities as authenticated users
  - Consider authentication for full access

**Rate Limit Response Headers:**
```
X-RateLimit-Limit: 25
X-RateLimit-Remaining: 24
X-RateLimit-Reset: 1706745600
```

When rate limit is exceeded, the API returns:
```json
{
    "detail": "Request limit exceeded. Please try again tomorrow."
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

- Maximum file size: 5MB
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
