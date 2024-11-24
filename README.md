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
git clone https://github.com/dehyabi/textor-ai.git
cd textor-ai
```

2. Create and activate a virtual environment:
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

## Deployment

### Prerequisites
- Heroku CLI installed
- Git repository initialized
- AssemblyAI API key
- PostgreSQL installed locally (for testing)

### Local Deployment Testing
Before deploying to Heroku, test your deployment locally:

1. Install all requirements:
```bash
pip install -r requirements.txt
```

2. Create a .env file with required variables:
```bash
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
ASSEMBLYAI_API_KEY=your-assemblyai-api-key
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

3. Test with gunicorn locally:
```bash
gunicorn speech_to_text_api.wsgi:application
```

### Heroku Deployment

1. Install the Heroku CLI and login:
```bash
curl https://cli-assets.heroku.com/install.sh | sh
heroku login
```

2. Create a new Heroku app:
```bash
heroku create textor-ai
```

3. Add PostgreSQL addon:
```bash
heroku addons:create heroku-postgresql:mini
```

4. Configure environment variables:
```bash
# Generate a secure secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Set environment variables
heroku config:set DJANGO_SECRET_KEY=<generated-secret-key>
heroku config:set DJANGO_DEBUG=False
heroku config:set ASSEMBLYAI_API_KEY=your-assemblyai-api-key
heroku config:set DJANGO_ALLOWED_HOSTS=your-app-name.herokuapp.com
heroku config:set CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
```

5. Deploy to Heroku:
```bash
# Add Heroku remote
heroku git:remote -a your-app-name

# Push to Heroku
git push heroku main
```

6. Run migrations and create superuser:
```bash
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

7. Verify deployment:
```bash
# Open the app in browser
heroku open

# Check logs for any errors
heroku logs --tail
```

### Container Deployment

Textor-AI supports both traditional and containerized deployment on Heroku.

#### Option 1: Traditional Deployment

Follow the standard Heroku deployment steps mentioned above.

#### Option 2: Container Deployment

1. Install the Heroku CLI and login:
```bash
curl https://cli-assets.heroku.com/install.sh | sh
heroku login
heroku container:login
```

2. Create a new Heroku app:
```bash
heroku create textor-ai
```

3. Set stack to container:
```bash
heroku stack:set container
```

4. Configure environment variables:
```bash
heroku config:set DJANGO_SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
heroku config:set DJANGO_DEBUG=False
heroku config:set ASSEMBLYAI_API_KEY=your-assemblyai-api-key
heroku config:set DJANGO_ALLOWED_HOSTS=your-app-name.herokuapp.com
```

5. Push and release the container:
```bash
# Build and push the container
heroku container:push web

# Release the container
heroku container:release web
```

6. Run migrations:
```bash
heroku run python manage.py migrate
```

#### Container Development

For local development with Docker:

1. Build the container:
```bash
docker build -t textor-ai .
```

2. Run the container:
```bash
docker run -p 8000:8000 \
  -e PORT=8000 \
  -e DJANGO_SECRET_KEY=your-secret-key \
  -e DJANGO_DEBUG=True \
  -e ASSEMBLYAI_API_KEY=your-api-key \
  -e DJANGO_ALLOWED_HOSTS=localhost \
  textor-ai
```

3. Run tests in container:
```bash
docker run textor-ai python manage.py test
```

#### Container Configuration

The container is configured with:
- Python 3.10.12 slim base image
- Non-root user for security
- Optimized gunicorn settings
- Static file collection
- Health checks
- Environment variable configuration

Key container features:
- Multi-stage builds for smaller images
- Security best practices
- Performance optimizations
- Health monitoring
- Automatic migrations
- Static file handling

#### Container Scaling

1. Scale horizontally:
```bash
heroku ps:scale web=3
```

2. Scale vertically:
```bash
heroku ps:resize web=standard-2x
```

3. Enable auto-scaling:
```bash
heroku addons:create adept-scale:basic
```

#### Container Monitoring

1. View container metrics:
```bash
# View container status
heroku container:status

# View container logs
heroku logs --tail

# View process metrics
heroku ps:metrics
```

2. Container health checks:
```bash
# Check container health
curl https://your-app-name.herokuapp.com/health/

# View detailed metrics
heroku ps:metrics --json
```

### Troubleshooting

1. If static files are not serving:
```bash
heroku run python manage.py collectstatic --noinput
```

2. If database migrations fail:
```bash
heroku run python manage.py migrate --noinput
```

3. To restart the application:
```bash
heroku restart
```

4. To check application status:
```bash
heroku ps
```

5. To view recent logs:
```bash
heroku logs --tail
```

### Production Checklist

- [ ] Generate new Django secret key
- [ ] Set DEBUG to False
- [ ] Configure allowed hosts
- [ ] Set up CORS properly
- [ ] Configure SSL/HTTPS
- [ ] Set up proper database backup
- [ ] Configure rate limiting
- [ ] Set up monitoring
- [ ] Configure error logging

### Production Configuration

#### Monitoring and Error Tracking

1. Set up Sentry for error tracking:
```bash
heroku config:set SENTRY_DSN=your-sentry-dsn
```

2. Enable application monitoring:
```bash
# Add New Relic
heroku addons:create newrelic:wayne
# Add Papertrail for log management
heroku addons:create papertrail:choklad
```

#### Performance Optimization

1. Configure Redis caching:
```bash
# Add Redis
heroku addons:create heroku-redis:mini

# Set cache configuration
heroku config:set REDIS_URL=$(heroku config:get REDIS_TLS_URL)
```

2. Set up AWS S3 for file storage:
```bash
heroku config:set AWS_ACCESS_KEY_ID=your-access-key
heroku config:set AWS_SECRET_ACCESS_KEY=your-secret-key
heroku config:set AWS_STORAGE_BUCKET_NAME=your-bucket-name
heroku config:set AWS_S3_REGION_NAME=your-region
```

#### Security Configuration

1. Enable SSL:
```bash
heroku config:set SECURE_SSL_REDIRECT=True
heroku config:set SECURE_PROXY_SSL_HEADER=True
```

2. Set security headers:
```bash
heroku config:set SECURE_HSTS_SECONDS=31536000
heroku config:set SECURE_HSTS_INCLUDE_SUBDOMAINS=True
heroku config:set SECURE_HSTS_PRELOAD=True
```

#### Scaling

1. Scale web dynos:
```bash
# Scale to 2 dynos
heroku ps:scale web=2:basic

# Enable auto-scaling
heroku addons:create adept-scale:basic
```

2. Database maintenance:
```bash
# Enable automatic backups
heroku pg:backups:schedule DATABASE_URL --at '02:00 UTC'

# Manual backup
heroku pg:backups:capture

# Download latest backup
heroku pg:backups:download
```

#### Health Checks

The application includes Django Health Check. Access health status at:
- `/health/`: Overall health status
- `/health/db/`: Database connectivity
- `/health/cache/`: Cache service status
- `/health/storage/`: Storage service status

#### Maintenance Mode

To enable maintenance mode:
```bash
heroku maintenance:on
```

To disable:
```bash
heroku maintenance:off
```

#### Logging and Debugging

View application logs:
```bash
# View recent logs
heroku logs --tail

# Filter logs
heroku logs --source app --tail
heroku logs --source heroku --tail

# Search logs
heroku logs --grep "Error|Exception" --tail
```

#### Performance Monitoring

1. View application metrics:
```bash
# View dyno status
heroku ps

# View resource usage
heroku ps:utilization

# View response times
heroku logs:router --tail
```

2. Database monitoring:
```bash
# View database status
heroku pg:info

# View database connections
heroku pg:ps

# View slow queries
heroku pg:outliers
```

#### Backup and Recovery

1. Database backups:
```bash
# Create manual backup
heroku pg:backups:capture

# Download backup
heroku pg:backups:download

# List backups
heroku pg:backups

# Restore from backup
heroku pg:backups:restore b101 DATABASE_URL
```

2. Application rollback:
```bash
# View release history
heroku releases

# Rollback to previous release
heroku rollback v102
```

## Environment Variables

The following environment variables are required:

- `DJANGO_SECRET_KEY`: Django secret key
- `DJANGO_DEBUG`: Set to 'False' in production
- `ASSEMBLYAI_API_KEY`: Your AssemblyAI API key
- `DJANGO_ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `CORS_ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins
- `DATABASE_URL`: Set automatically by Heroku PostgreSQL addon

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
