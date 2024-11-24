from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework import generics
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from api_auth.authentication import BearerTokenAuthentication
import requests
import os
import time
import mimetypes
import hashlib
import logging
from dotenv import load_dotenv
from datetime import datetime
import pytz
from tempfile import NamedTemporaryFile

load_dotenv()

logger = logging.getLogger(__name__)

ASSEMBLYAI_API_KEY = os.getenv('ASSEMBLYAI_API_KEY')
if not ASSEMBLYAI_API_KEY:
    raise ValueError("ASSEMBLYAI_API_KEY environment variable is not set")

logger.info(f"Using AssemblyAI API Key: {ASSEMBLYAI_API_KEY}")

headers = {
    "authorization": ASSEMBLYAI_API_KEY,
    "content-type": "application/json"
}

UPLOAD_URL = "https://api.assemblyai.com/v2/upload"
TRANSCRIPT_URL = "https://api.assemblyai.com/v2/transcript"

# Supported audio formats
SUPPORTED_FORMATS = {
    # Audio formats
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
    '.m4a': 'audio/mp4',
    '.flac': 'audio/flac',
    '.aac': 'audio/aac',
    '.ogg': 'audio/ogg',
    '.wma': 'audio/x-ms-wma',
    # Video formats (AssemblyAI can extract audio)
    '.mp4': 'video/mp4',
    '.avi': 'video/x-msvideo',
    '.mov': 'video/quicktime',
    '.wmv': 'video/x-ms-wmv',
    '.webm': 'video/webm'
}

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

# Supported languages by AssemblyAI
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'nl': 'Dutch',
    'hi': 'Hindi',
    'ja': 'Japanese',
    'zh': 'Chinese',
    'ko': 'Korean',
    'te': 'Telugu',
    'ta': 'Tamil'
}

class TranscriptionRateThrottle(UserRateThrottle):
    rate = '100/hour'

class AnonTranscriptionRateThrottle(AnonRateThrottle):
    rate = '3/hour'

class TranscriptionViewSet(ViewSet):
    """
    ViewSet for handling audio file transcriptions
    """
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    authentication_classes = [BearerTokenAuthentication]
    throttle_classes = [TranscriptionRateThrottle, AnonTranscriptionRateThrottle]

    def validate_file(self, file):
        """Validate file format and size"""
        try:
            logger.info(f"Validating file: {file.name}")
            logger.info(f"File size: {file.size} bytes")
            logger.info(f"Content type: {file.content_type}")

            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:  # 10MB in bytes
                logger.error(f"File too large: {file.size} bytes")
                return False, "File too large. Maximum size is 10MB"

            # List of allowed audio formats and their MIME types
            allowed_formats = [
                'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/wave',
                'audio/x-wav', 'audio/aac', 'audio/ogg', 'audio/flac',
                'audio/x-m4a', 'audio/mp4', 'audio/x-mp3'
            ]

            if not file.content_type in allowed_formats:
                logger.error(f"Invalid content type: {file.content_type}")
                return False, f"Invalid file format. Supported formats: MP3, WAV, AAC, OGG, FLAC, M4A"

            # Try to read a small part of the file to verify it's valid
            try:
                chunk = file.read(1024)
                file.seek(0)  # Reset file pointer
                logger.info("Successfully read file chunk")
            except Exception as e:
                logger.error(f"Error reading file: {str(e)}")
                return False, "Could not read file content"

            logger.info("File validation successful")
            return True, "File is valid"

        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            return False, f"File validation failed: {str(e)}"

    def upload_file(self, file_path):
        """Upload file to AssemblyAI"""
        try:
            logger.info(f"Starting file upload: {file_path}")
            logger.info(f"Using AssemblyAI API Key: {ASSEMBLYAI_API_KEY}")
            
            # Verify file exists and is readable
            if not os.path.exists(file_path):
                raise Exception(f"File not found: {file_path}")
            
            # Get file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise Exception("File is empty")
            
            logger.info(f"File size: {file_size} bytes")
            
            # Read file content
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Upload file directly
            logger.info("Uploading file to AssemblyAI")
            upload_response = requests.post(
                UPLOAD_URL,
                headers={"authorization": ASSEMBLYAI_API_KEY},
                data=file_data
            )
            
            logger.info(f"Upload response status: {upload_response.status_code}")
            logger.info(f"Upload response: {upload_response.text}")
            
            if upload_response.status_code != 200:
                logger.error(f"Upload failed. Status: {upload_response.status_code}")
                logger.error(f"Response: {upload_response.text}")
                raise Exception(f"Upload failed: {upload_response.text}")
            
            return upload_response.json()["upload_url"]
                
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL Error during upload: {str(e)}")
            raise Exception(f"SSL Error during upload: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text}")
            raise Exception(f"Upload request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            raise Exception(f"File upload failed: {str(e)}")
        finally:
            # Clean up temp file if it exists
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {str(e)}")

    def cleanup_stuck_transcripts(self):
        """Clean up stuck transcripts"""
        try:
            # Get list of transcripts
            response = requests.get(
                "https://api.assemblyai.com/v2/transcript",
                headers=headers,
                params={"limit": 10},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            # Find stuck transcripts (processing for more than 10 minutes)
            for transcript in data.get('transcripts', []):
                if transcript['status'] == 'processing':
                    created_time = datetime.fromisoformat(transcript['created'].replace('Z', '+00:00'))
                    if (datetime.now(pytz.utc) - created_time).total_seconds() > 600:  # 10 minutes
                        # Delete stuck transcript
                        logger.info(f"Deleting stuck transcript {transcript['id']}")
                        requests.delete(
                            f"https://api.assemblyai.com/v2/transcript/{transcript['id']}",
                            headers=headers
                        )
        except Exception as e:
            logger.error(f"Error cleaning up transcripts: {str(e)}")

    def create_transcript(self, audio_url, language_code=None, auto_detect=False):
        """Create transcription request with optional language detection"""
        try:
            # Clean up stuck transcripts first
            self.cleanup_stuck_transcripts()
            
            # Map of supported languages - Updated to match AssemblyAI's supported languages
            LANGUAGE_CODES = {
                'en': 'en',      # English (Global)
                'en_us': 'en',   # English (US)
                'en_uk': 'en',   # English (UK)
                'en_au': 'en',   # English (Australia)
                'fr': 'fr',      # French
                'de': 'de',      # German
                'it': 'it',      # Italian
                'pt': 'pt',      # Portuguese
                'nl': 'nl',      # Dutch
                'hi': 'hi',      # Hindi
                'ja': 'ja',      # Japanese
                'es': 'es',      # Spanish
                'ko': 'ko',      # Korean
                'pl': 'pl',      # Polish
                'id': 'id',      # Indonesian
                'ta': 'ta',      # Tamil
                'te': 'te',      # Telugu
                'tr': 'tr',      # Turkish
                'ru': 'ru',      # Russian
                'vi': 'vi',      # Vietnamese
                'zh': 'zh',      # Chinese (Simplified)
                'zh_tw': 'zh',   # Chinese (Traditional)
                'da': 'da',      # Danish
                'fil': 'fil',    # Filipino
                'fi': 'fi',      # Finnish
                'el': 'el',      # Greek
                'hu': 'hu',      # Hungarian
                'ml': 'ml',      # Malayalam
                'no': 'no',      # Norwegian
                'sv': 'sv',      # Swedish
                'th': 'th',      # Thai
                'uk': 'uk',      # Ukrainian
                'bn': 'bn',      # Bengali
                'ro': 'ro',      # Romanian
                'si': 'si',      # Sinhala
                'mr': 'mr',      # Marathi
                'gu': 'gu',      # Gujarati
                'kn': 'kn',      # Kannada
                'ar': 'ar',      # Arabic
                'fa': 'fa',      # Persian
                'ur': 'ur',      # Urdu
                'hr': 'hr',      # Croatian
                'bg': 'bg',      # Bulgarian
                'sr': 'sr',      # Serbian
                'sk': 'sk',      # Slovak
                'sl': 'sl',      # Slovenian
                'ca': 'ca',      # Catalan
                'he': 'he',      # Hebrew
                'lv': 'lv',      # Latvian
                'lt': 'lt',      # Lithuanian
                'ne': 'ne',      # Nepali
                'et': 'et',      # Estonian
                'ms': 'ms',      # Malay
                'tl': 'tl',      # Tagalog
                'pa': 'pa',      # Punjabi
                'sw': 'sw',      # Swahili
                'az': 'az',      # Azerbaijani
                'hy': 'hy',      # Armenian
                'bs': 'bs',      # Bosnian
                'my': 'my',      # Burmese
                'af': 'af',      # Afrikaans
                'ka': 'ka',      # Georgian
                'is': 'is',      # Icelandic
                'km': 'km',      # Khmer
                'lo': 'lo',      # Lao
                'mk': 'mk',      # Macedonian
                'mn': 'mn',      # Mongolian
                'gl': 'gl',      # Galician
                'kk': 'kk',      # Kazakh
            }
            
            # Basic request with required fields
            transcript_request = {
                "audio_url": audio_url,
            }

            # Handle language detection and language code
            if auto_detect:
                logger.info("Using automatic language detection")
                transcript_request["language_detection"] = True
            elif language_code:
                # Convert to lowercase and remove any region specifier
                base_lang = language_code.lower().split('_')[0]
                # Get the simplified language code
                normalized_lang = LANGUAGE_CODES.get(base_lang) or LANGUAGE_CODES.get(language_code.lower())
                if not normalized_lang:
                    logger.warning(f"Unsupported language code: {language_code}, defaulting to English")
                    normalized_lang = 'en'
                logger.info(f"Using language code: {normalized_lang}")
                transcript_request["language_code"] = normalized_lang
            else:
                # Default to automatic language detection if no language specified
                logger.info("No language specified, using automatic language detection")
                transcript_request["language_detection"] = True
            
            # Optional parameters based on language support
            if not language_code or language_code.startswith('en'):
                # Full features for English or auto-detected language
                transcript_request.update({
                    "punctuate": True,
                    "format_text": True,
                    "auto_highlights": True,
                    "speaker_labels": True,
                    "auto_chapters": True,
                    "entity_detection": True,
                    "iab_categories": True
                })
            else:
                # Basic features for non-English
                transcript_request.update({
                    "punctuate": True,
                    "format_text": True
                })
            
            logger.info(f"Creating transcript request for URL: {audio_url}")
            logger.info(f"Request payload: {transcript_request}")
            logger.info(f"Using headers: {headers}")
            
            # Create transcription request without verifying SSL for AssemblyAI CDN
            transcript_response = requests.post(
                TRANSCRIPT_URL,
                json=transcript_request,
                headers=headers,
                timeout=30,
                verify=False  # Disable SSL verification for AssemblyAI CDN
            )
            
            # Log response details
            logger.info(f"Transcript request response status: {transcript_response.status_code}")
            logger.info(f"Transcript request content: {transcript_response.text}")
            
            if transcript_response.status_code != 200:
                error_detail = transcript_response.json() if transcript_response.text else "No error details provided"
                logger.error(f"AssemblyAI API error: {error_detail}")
                raise Exception(f"AssemblyAI API error: {error_detail}")
            
            response_data = transcript_response.json()
            
            if 'id' in response_data:
                logger.info(f"Transcript request created. ID: {response_data['id']}")
                return response_data
            else:
                logger.error(f"Transcript ID not found in response: {response_data}")
                raise Exception("No transcript ID in response")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text}")
                try:
                    error_json = e.response.json()
                    logger.error(f"Error details: {error_json}")
                    raise Exception(f"AssemblyAI API error: {error_json}")
                except ValueError:
                    logger.error(f"Raw error text: {e.response.text}")
                    raise Exception(f"AssemblyAI API error: {e.response.text}")
            raise Exception(f"Request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Transcription request failed: {str(e)}")
            raise

    def get_transcript_result(self, transcript_id):
        """Get transcription result with progress updates"""
        polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
        max_retries = 600  # Increased to 15 minutes total (1.5s * 600)
        retry_count = 0
        last_status = None
        last_progress = None

        while retry_count < max_retries:
            try:
                polling_response = requests.get(
                    polling_endpoint,
                    headers=headers,
                    timeout=30
                )
                polling_response.raise_for_status()
                result = polling_response.json()
                
                logger.info(f"Polling response for {transcript_id}: {result}")
                
                current_status = result.get('status')
                current_progress = result.get('percentage', 0)
                
                # Return any status change immediately
                if current_status != last_status or current_progress != last_progress:
                    logger.info(f"Transcript {transcript_id} - Status: {current_status}, Progress: {current_progress}%")
                    last_status = current_status
                    last_progress = current_progress
                    
                    # Build response based on status
                    response = {
                        'status': current_status,
                        'progress': current_progress,
                        'text': result.get('text'),  
                        'error': result.get('error'),
                        'language_code': result.get('language_code'),
                        'audio_duration': result.get('audio_duration'),
                        'punctuate': result.get('punctuate', True),
                        'format_text': result.get('format_text', True),
                        'confidence': result.get('confidence'),
                        'words': result.get('words'),
                        'utterances': result.get('utterances'),
                        'chapters': result.get('chapters'),
                        'highlights': result.get('auto_highlights_result')
                    }
                    
                    # Add status message for clarity
                    if current_status == 'queued':
                        response['message'] = 'Your audio is queued for processing'
                    elif current_status == 'processing':
                        response['message'] = f'Processing your audio: {current_progress}% complete'
                    elif current_status == 'completed':
                        if not response['text']:
                            response['message'] = 'Warning: Transcription completed but no text was generated'
                            logger.warning(f"Completed transcription {transcript_id} has no text: {result}")
                        else:
                            response['message'] = 'Transcription completed successfully'
                    elif current_status == 'error':
                        response['message'] = f'Error during transcription: {result.get("error")}'
                    
                    # Remove None values
                    response = {k: v for k, v in response.items() if v is not None}
                    
                    return response
                
                if current_status == 'completed':
                    break
                
                time.sleep(1.5)
                retry_count += 1
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error polling transcript {transcript_id}: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"API Response: {e.response.text}")
                return {
                    'status': 'error',
                    'error': str(e),
                    'progress': 0,
                    'message': f'Error checking transcription status: {str(e)}'
                }

        logger.error(f"Transcription timed out after {max_retries} attempts")
        return {
            'status': 'error',
            'error': 'Transcription timed out',
            'progress': last_progress or 0,
            'message': 'Transcription timed out after 15 minutes'
        }

    def list(self, request):
        """List all transcriptions"""
        return Response({"message": "Use POST /upload/ to start a transcription"})

    def retrieve(self, request, pk=None):
        """Get transcription status or result"""
        try:
            if not pk:
                return Response({
                    "error": "Transcript ID is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            result = self.get_transcript_result(pk)
            return Response(result)

        except Exception as e:
            logger.error(f"Error getting transcript {pk}: {str(e)}")
            return Response({
                "error": "Failed to get transcript",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload audio file and start transcription"""
        temp_file = None
        try:
            # Validate request
            if 'file' not in request.FILES:
                return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

            file = request.FILES['file']
            language_code = request.data.get('language_code')
            auto_detect = request.data.get('auto_detect', 'false').lower() == 'true'

            # Log request details
            logger.info(f"Processing file upload: {file.name}")
            logger.info(f"Language code: {language_code}")
            logger.info(f"Auto detect: {auto_detect}")

            # Validate file size (10MB limit)
            if file.size > 10 * 1024 * 1024:  # 10MB in bytes
                return Response(
                    {'error': 'File size exceeds 10MB limit'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate file type
            content_type = file.content_type.lower()
            if not any(type in content_type for type in ['audio', 'video', 'application/octet-stream']):
                return Response(
                    {'error': 'Invalid file type. Please upload an audio file'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create temporary directory if it doesn't exist
            temp_dir = '/tmp/assemblyai_uploads'
            os.makedirs(temp_dir, exist_ok=True)

            # Create temporary file with original extension
            file_extension = os.path.splitext(file.name)[1] or '.tmp'
            temp_file = os.path.join(temp_dir, f"upload_{int(time.time())}{file_extension}")
            
            logger.info(f"Creating temporary file: {temp_file}")
            
            # Write file in binary mode
            with open(temp_file, 'wb') as f:
                for chunk in file.chunks():
                    f.write(chunk)

            try:
                # Upload to AssemblyAI
                logger.info("Uploading file to AssemblyAI")
                upload_url = self.upload_file(temp_file)
                logger.info(f"File uploaded successfully. URL: {upload_url}")

                # Create transcription request
                logger.info("Creating transcription request")
                transcript = self.create_transcript(upload_url, language_code, auto_detect)
                logger.info(f"Transcription request created: {transcript}")

                return Response({
                    'message': 'File uploaded and transcription started',
                    'transcript_id': transcript['id'],
                    'status': 'processing'
                }, status=status.HTTP_202_ACCEPTED)

            finally:
                # Clean up temporary file
                if temp_file and os.path.exists(temp_file):
                    logger.info(f"Cleaning up temporary file: {temp_file}")
                    os.unlink(temp_file)

        except Exception as e:
            logger.error(f"Error processing upload: {str(e)}")
            # Clean up temporary file in case of error
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up temporary file: {cleanup_error}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
