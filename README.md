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
   python manage.py migrate
   ```

6. Start the development server:
   ```bash
   python manage.py runserver
   ```

## API Endpoints

### POST /api/transcribe/
Converts an audio file to text.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: 
  - audio_file: Audio file to transcribe (supports various formats)

**Response:**
```json
{
    "text": "Transcribed text here",
    "status": "completed"
}
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:
- 400: Bad Request (e.g., no audio file provided)
- 500: Internal Server Error (e.g., transcription failed)

## Notes

- Maximum file size: 10MB
- Supported audio formats: MP3, WAV, M4A, and more
- The API uses AssemblyAI's service for transcription
