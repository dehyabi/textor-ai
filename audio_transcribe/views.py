from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework import generics
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from api_auth.authentication import BearerTokenAuthentication
from .models import Transcription
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
from django.contrib.auth.models import User
from django.db.utils import IntegrityError

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

# Maximum file size (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes

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
    """
    Rate limiting for authenticated users:
    - 25 requests per day
    """
    rate = '25/day'

class AnonTranscriptionRateThrottle(AnonRateThrottle):
    """
    Rate limiting for anonymous users:
    - 5 requests per day
    """
    rate = '5/day'

class TranscriptionPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'current_page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
            'total_count': len(data.get('transcriptions', {}).get('queued', [])) +
                         len(data.get('transcriptions', {}).get('processing', [])) +
                         len(data.get('transcriptions', {}).get('completed', [])) +
                         len(data.get('transcriptions', {}).get('error', [])),
            'status_counts': data.get('status_counts', {}),
            'transcriptions': data.get('transcriptions', {})
        })

class TranscriptionViewSet(ViewSet):
    """
    ViewSet for handling audio file transcriptions
    """
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]  # Allow anonymous access
    authentication_classes = [BearerTokenAuthentication]
    throttle_classes = [TranscriptionRateThrottle, AnonTranscriptionRateThrottle]
    pagination_class = TranscriptionPagination

    def validate_file(self, file):
        """Validate file format and size"""
        try:
            logger.info(f"Validating file: {file.name}")
            logger.info(f"File size: {file.size} bytes")
            logger.info(f"Content type: {file.content_type}")

            # Check file size (5MB limit)
            if file.size > 5 * 1024 * 1024:  # 5MB in bytes
                logger.error(f"File too large: {file.size} bytes")
                return False, "File too large. Maximum size is 5MB"

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

    def sync_with_assemblyai(self):
        """Sync transcription data with AssemblyAI"""
        try:
            # Get list of transcripts from AssemblyAI
            response = requests.get(
                TRANSCRIPT_URL,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"Found {len(data.get('transcripts', []))} transcripts from AssemblyAI")

            # Process each transcript
            for transcript in data.get('transcripts', []):
                transcript_id = transcript.get('id')
                if not transcript_id:
                    continue

                # Get detailed transcript data
                result = self.get_transcript_result(transcript_id)
                status = result.get('status', 'unknown')
                
                # Get or create transcription record
                transcription, created = Transcription.objects.get_or_create(
                    transcript_id=transcript_id,
                    defaults={
                        'user': self.request.user,
                        'status': status,
                        'audio_url': transcript.get('audio_url', ''),
                        'language_code': transcript.get('language', 'en')
                    }
                )

                # Update record
                transcription.status = status
                transcription.text = result.get('text')
                if status == 'completed':
                    transcription.completed_at = datetime.now(pytz.utc)
                if result.get('error'):
                    transcription.error = result.get('error')
                    transcription.status = 'error'
                transcription.save()

                if created:
                    logger.info(f"Created new transcription record for {transcript_id}")
                else:
                    logger.info(f"Updated transcription {transcript_id}")

            return True
        except Exception as e:
            logger.error(f"Error syncing with AssemblyAI: {str(e)}")
            return False

    def get_paginated_transcriptions(self, transcriptions):
        """Helper method to paginate and group transcriptions"""
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(transcriptions, self.request)

        # Initialize status groups for paginated results
        grouped_transcriptions = {
            'queued': [],
            'processing': [],
            'completed': [],
            'error': []
        }

        # Group paginated transcriptions by status
        for trans in page:
            trans_data = {
                'id': trans.transcript_id,
                'text': trans.text,
                'audio_url': trans.audio_url,
                'language_code': trans.language_code,
                'created_at': trans.created_at.isoformat() if trans.created_at else None,
                'completed_at': trans.completed_at.isoformat() if trans.completed_at else None,
                'error': trans.error,
                'status': trans.status
            }

            if trans.status == 'queued':
                grouped_transcriptions['queued'].append(trans_data)
            elif trans.status == 'processing':
                grouped_transcriptions['processing'].append(trans_data)
            elif trans.status == 'completed':
                grouped_transcriptions['completed'].append(trans_data)
            elif trans.status == 'error':
                grouped_transcriptions['error'].append(trans_data)
            else:
                logger.warning(f"Unknown status {trans.status} for transcription {trans.transcript_id}")

        # Calculate status counts for the current page
        status_counts = {
            'queued': len(grouped_transcriptions['queued']),
            'processing': len(grouped_transcriptions['processing']),
            'completed': len(grouped_transcriptions['completed']),
            'error': len(grouped_transcriptions['error'])
        }

        response_data = {
            'status_counts': status_counts,
            'transcriptions': grouped_transcriptions
        }

        return paginator.get_paginated_response(response_data)

    def get_or_create_anonymous_user(self):
        """Get or create the default anonymous user"""
        try:
            anon_user, created = User.objects.get_or_create(
                username='anonymous_user',
                defaults={
                    'email': 'anonymous@example.com',
                    'is_active': True
                }
            )
            if created:
                logger.info("Created anonymous user")
            return anon_user
        except IntegrityError as e:
            logger.error(f"Error creating anonymous user: {str(e)}")
            return None

    def get_request_user(self, request):
        """Get the appropriate user for the request"""
        if request.user.is_authenticated:
            return request.user
        return self.get_or_create_anonymous_user()

    def list(self, request):
        """List transcriptions for the user, grouped by status"""
        try:
            # Sync with AssemblyAI first
            sync_success = self.sync_with_assemblyai()
            if not sync_success:
                logger.warning("Failed to sync with AssemblyAI, returning local data only")
            
            # Get all transcriptions for the current user
            user = self.get_request_user(request)
            if not user:
                return Response({
                    'error': 'Unable to process request. Please try again later.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Get transcriptions based on user type
            if request.user.is_authenticated:
                transcriptions = Transcription.objects.filter(user=user).order_by('-created_at')
            else:
                # For anonymous users, only show 5 most recent transcriptions
                transcriptions = Transcription.objects.filter(user=user).order_by('-created_at')[:5]
                logger.info(f"Limiting anonymous user to 5 most recent transcriptions")
            
            logger.info(f"Found {len(transcriptions)} transcriptions for user {user.username}")
            
            # Return paginated response
            return self.get_paginated_transcriptions(transcriptions)

        except Exception as e:
            logger.error(f"Error listing transcriptions: {str(e)}")
            return Response({
                'error': 'Failed to retrieve transcriptions',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload audio file and start transcription"""
        temp_file = None
        try:
            if 'file' not in request.FILES:
                return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

            file = request.FILES['file']
            language_code = request.POST.get('language_code', '')
            auto_detect = request.POST.get('auto_detect', 'true').lower() == 'true'

            # Get appropriate user
            user = self.get_request_user(request)
            if not user:
                return Response({
                    'error': 'Unable to process request. Please try again later.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Validate file size (5MB limit)
            if file.size > 5 * 1024 * 1024:
                return Response({'error': 'File size exceeds 5MB limit'}, status=status.HTTP_400_BAD_REQUEST)

            # Create temp file
            temp_file = NamedTemporaryFile(delete=False)
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file.close()

            # Validate file
            is_valid, error_message = self.validate_file(file)
            if not is_valid:
                return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)

            # Upload to AssemblyAI
            upload_url = self.upload_file(temp_file.name)
            if not upload_url:
                return Response({
                    'error': 'Failed to upload file to AssemblyAI'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Start transcription
            transcript_id = self.create_transcript(upload_url, language_code if language_code else None, auto_detect)
            if not transcript_id:
                return Response({
                    'error': 'Failed to start transcription'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Create transcription record
            transcription = Transcription.objects.create(
                transcript_id=transcript_id['id'],
                user=user,
                status='queued',
                audio_url=upload_url,
                language_code=language_code if language_code else 'auto'
            )

            return Response({
                'transcript_id': transcript_id['id'],
                'status': 'queued'
            })

        except Exception as e:
            logger.error(f"Error in upload: {str(e)}")
            return Response({
                'error': 'Failed to process upload',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        finally:
            if temp_file:
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    logger.error(f"Error removing temp file: {str(e)}")

    def retrieve(self, request, pk=None):
        """Get transcription status or result"""
        try:
            if not pk:
                return Response({
                    "error": "Transcript ID is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get result from AssemblyAI
            result = self.get_transcript_result(pk)
            
            # Update transcription in database
            try:
                transcription = Transcription.objects.get(transcript_id=pk)
                transcription.status = result.get('status', 'unknown')
                transcription.text = result.get('text')
                if result.get('status') == 'completed':
                    transcription.completed_at = datetime.now(pytz.utc)
                if result.get('error'):
                    transcription.error = result.get('error')
                transcription.save()
            except Transcription.DoesNotExist:
                logger.warning(f"Transcription {pk} not found in database")
            
            return Response(result)

        except Exception as e:
            logger.error(f"Error getting transcript {pk}: {str(e)}")
            return Response({
                "error": "Failed to get transcript",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
