# Speech-to-Text API

A Django REST API that converts speech to text using AssemblyAI's transcription service.

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Create a `.env` file in the project root
   - Add your AssemblyAI API key:
     ```
     ASSEMBLYAI_API_KEY=your_api_key_here
     ```

5. Run migrations:
   ```bash
   python3 manage.py migrate
   ```

6. Create a superuser (for admin access):
   ```bash
   python3 create_superuser.py
   ```

7. Start the development server:
   ```bash
   python3 manage.py runserver
   ```

## API Endpoints

### Available Endpoints

### Authentication Endpoints

The API uses admin-only authentication. Use the superuser credentials created with `python3 create_superuser.py` to login.

#### POST /api/auth/login/
Login with admin credentials to obtain authentication token.

**Request:**
- Method: POST
- Content-Type: application/json
- Body:
  ```json
  {
    "username": "admin_username",
    "password": "admin_password"
  }
  ```

**Response:**
```json
{
    "token": "your_authentication_token",
    "user_id": 1,
    "username": "admin_username"
}
```

#### POST /api/auth/logout/
Logout and invalidate the current token.

**Request:**
- Method: POST
- Headers:
  ```
  Authorization: Token your_token_here
  ```

**Response:**
- Status: 204 No Content

### Transcription Endpoints

#### POST /api/transcribe/
Upload and transcribe an audio file. The transcription process happens asynchronously. Supports multiple languages with automatic language detection.

**Features:**
- Automatic language detection
- Multi-language support
- High-accuracy transcription
- Word-level timing and confidence scores

**Supported Languages:**
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Dutch (nl)
- Hindi (hi)
- Japanese (ja)
- Chinese (zh)
- Korean (ko)
- And many more...

**Request:**
- Method: POST
- Headers:
  ```
  Authorization: Token your_token_here
  Content-Type: multipart/form-data
  ```
- Body Parameters:
  - `file`: Audio file to transcribe (Required)
    - Supported formats: MP3, WAV, M4A, etc.
    - Maximum file size: 10MB
  - `language_code`: ISO 639-1 language code (Optional)
    - If not provided, language will be automatically detected
    - Example: "en" for English, "es" for Spanish
    - Set to "auto" for automatic detection (default)

**Response States:**

1. Initial Upload Response (202 Accepted):
```json
{
    "id": "transcription_id_123",
    "status": "processing",
    "text": null,
    "audio_url": "http://example.com/media/audio/file.mp3",
    "created_at": "2023-12-20T10:30:00Z",
    "detected_language": null,
    "error": null
}
```

2. Processing Complete Response (200 OK):
```json
{
    "id": "transcription_id_123",
    "status": "completed",
    "text": "Este es un ejemplo de transcripción en español con puntuación y formato adecuados.",
    "audio_url": "http://example.com/media/audio/file.mp3",
    "created_at": "2023-12-20T10:30:00Z",
    "completed_at": "2023-12-20T10:31:30Z",
    "detected_language": {
        "code": "es",
        "name": "Spanish",
        "confidence": 0.98
    },
    "words": [
        {
            "text": "Este",
            "start": 0,
            "end": 400,
            "confidence": 0.98
        },
        {
            "text": "es",
            "start": 400,
            "end": 600,
            "confidence": 0.99
        }
        // ... more words
    ],
    "error": null
}
```

3. Error Response (400 Bad Request):
```json
{
    "error": "Invalid file format. Supported formats are: MP3, WAV, M4A"
}
```

4. File Size Error (413 Request Entity Too Large):
```json
{
    "error": "File size exceeds maximum limit of 10MB"
}
```

5. Processing Error (500 Internal Server Error):
```json
{
    "id": "transcription_id_123",
    "status": "error",
    "text": null,
    "audio_url": "http://example.com/media/audio/file.mp3",
    "created_at": "2023-12-20T10:30:00Z",
    "error": "An error occurred during transcription processing"
}
```

**Status Codes:**
- 202: Accepted - File uploaded successfully and processing started
- 200: OK - Transcription completed successfully
- 400: Bad Request - Invalid file format or missing file
- 413: Request Entity Too Large - File size exceeds limit
- 500: Internal Server Error - Processing error
- 401: Unauthorized - Invalid or missing authentication token

**Notes:**
- The transcription process is asynchronous. Initially, you'll receive a response with status "processing"
- Use the GET /api/transcribe/{id}/ endpoint to check the transcription status
- Large files may take longer to process
- The words array provides detailed timing and confidence information for each word
- All timestamps (start/end) are in milliseconds
- Language detection is automatic by default but can be overridden by specifying a language code
- Language detection confidence is included in the response when automatic detection is used
- For best results in non-English languages, you can optionally specify the language code
- The API will still attempt to transcribe audio even if the language is not in the supported list, but accuracy may vary

#### GET /api/transcribe/{id}/
Retrieve a specific transcription by ID.

**Request:**
- Method: GET
- Headers:
  ```
  Authorization: Token your_token_here
  ```

**Response:**
```json
{
    "id": "transcription_id",
    "text": "Transcribed text content",
    "status": "completed",
    "audio_url": "url_to_audio_file",
    "created_at": "2023-XX-XX:XX:XX:XX",
    "completed_at": "2023-XX-XX:XX:XX:XX",
    "words": [
        {
            "text": "word",
            "start": 0,
            "end": 1000,
            "confidence": 0.99
        }
    ]
}
```

#### GET /api/transcribe/
List all transcriptions for the authenticated user.

**Request:**
- Method: GET
- Headers:
  ```
  Authorization: Token your_token_here
  ```

**Response:**
```json
{
    "count": 10,
    "next": "url_to_next_page",
    "previous": null,
    "results": [
        {
            "id": "transcription_id",
            "text": "Transcribed text content",
            "status": "completed",
            "audio_url": "url_to_audio_file",
            "created_at": "2023-XX-XX:XX:XX:XX",
            "completed_at": "2023-XX-XX:XX:XX:XX"
        }
        // ... more transcriptions
    ]
}
```

## Error Responses

### Authentication Errors
```json
{
    "detail": "Invalid credentials"
}
```
Status: 401 Unauthorized

### Validation Errors
```json
{
    "file": ["This field is required."]
}
```
Status: 400 Bad Request

### Server Errors
```json
{
    "error": "An error occurred while processing the transcription"
}
```
Status: 500 Internal Server Error

## Error Handling

The API returns appropriate HTTP status codes and error messages:
- 400: Bad Request (e.g., no file provided)
- 500: Internal Server Error (e.g., transcription failed)

## Notes

- Maximum file size: 10MB
- Supported audio formats: MP3, WAV, M4A, and more
- The API uses AssemblyAI's service for transcription
