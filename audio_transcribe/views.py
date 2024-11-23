from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
import requests
import os
import time
import mimetypes
import hashlib
from dotenv import load_dotenv

load_dotenv()

ASSEMBLYAI_API_KEY = os.getenv('ASSEMBLYAI_API_KEY')
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

headers = {
    "authorization": ASSEMBLYAI_API_KEY,
    "content-type": "application/json"
}

class TranscriptionRateThrottle(UserRateThrottle):
    rate = '100/hour'

class AnonTranscriptionRateThrottle(AnonRateThrottle):
    rate = '3/hour'

class TranscriptionView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    throttle_classes = [TranscriptionRateThrottle, AnonTranscriptionRateThrottle]

    def validate_file(self, file):
        """Validate file format and size"""
        # Check file size
        if file.size > MAX_FILE_SIZE:
            return False, f"File size exceeds maximum limit of {MAX_FILE_SIZE/1024/1024}MB"

        # Get file extension and mime type
        file_name = file.name.lower()
        file_ext = os.path.splitext(file_name)[1]
        
        # Check if format is supported
        if file_ext not in SUPPORTED_FORMATS:
            return False, f"Unsupported file format. Supported formats: {', '.join(SUPPORTED_FORMATS.keys())}"

        # Calculate file hash for integrity
        file_content = file.read()
        file.seek(0)  # Reset file pointer
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        return True, {"message": "File is valid", "hash": file_hash}

    def upload_file(self, audio_file):
        def read_file(file_obj):
            content = file_obj.read()
            return content

        try:
            upload_response = requests.post(
                UPLOAD_URL,
                headers={"authorization": ASSEMBLYAI_API_KEY},
                data=read_file(audio_file),
                timeout=30  # 30 seconds timeout
            )
            upload_response.raise_for_status()
            return upload_response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"File upload failed: {str(e)}")

    def create_transcript(self, audio_url, language_code=None):
        transcript_request = {
            "audio_url": audio_url,
            "language_detection": True,
            "content_safety": True,  # Enable content safety detection
            "webhook_url": None,  # Add your webhook URL here if needed
            "speaker_labels": True  # Enable speaker diarization
        }

        if language_code:
            transcript_request["language_code"] = language_code

        try:
            transcript_response = requests.post(
                TRANSCRIPT_URL,
                json=transcript_request,
                headers=headers,
                timeout=30
            )
            transcript_response.raise_for_status()
            return transcript_response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Transcription request failed: {str(e)}")

    def get_transcript_result(self, transcript_id):
        polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
        max_retries = 100  # Maximum number of retries
        retry_count = 0

        while retry_count < max_retries:
            try:
                polling_response = requests.get(
                    polling_endpoint,
                    headers=headers,
                    timeout=30
                )
                polling_response.raise_for_status()
                result = polling_response.json()
                
                if result['status'] == 'completed' or result['status'] == 'error':
                    return result
                
                time.sleep(3)  # Wait 3 seconds before polling again
                retry_count += 1
            except requests.exceptions.RequestException as e:
                raise Exception(f"Error getting transcription result: {str(e)}")

        raise Exception("Transcription timed out")

    def post(self, request, *args, **kwargs):
        try:
            # Get audio file
            audio_file = request.FILES.get('audio_file')
            if not audio_file:
                return Response(
                    {"error": "No audio file provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate file
            is_valid, validation_result = self.validate_file(audio_file)
            if not is_valid:
                return Response(
                    {"error": validation_result},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get language code (optional)
            language_code = request.data.get('language_code')
            if language_code and language_code not in SUPPORTED_LANGUAGES:
                return Response(
                    {
                        "error": "Invalid language code",
                        "supported_languages": SUPPORTED_LANGUAGES
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Upload the file
            upload_response = self.upload_file(audio_file)
            if 'upload_url' not in upload_response:
                return Response({
                    "error": "File upload failed",
                    "details": upload_response.get('error', 'Unknown error')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            audio_url = upload_response['upload_url']

            # Request transcript with or without specific language
            transcript_response = self.create_transcript(audio_url, language_code)
            
            if 'error' in transcript_response:
                return Response({
                    "error": "Transcription request failed",
                    "details": transcript_response.get('error', 'Unknown error')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            transcript_id = transcript_response['id']

            # Get transcription result
            result = self.get_transcript_result(transcript_id)
            
            if result['status'] == 'completed':
                detected_language = result.get('language_code', 'unknown')
                response_data = {
                    "text": result['text'],
                    "detected_language": SUPPORTED_LANGUAGES.get(detected_language, detected_language),
                    "detected_language_code": detected_language,
                    "requested_language": SUPPORTED_LANGUAGES.get(language_code) if language_code else "auto",
                    "audio_format": os.path.splitext(audio_file.name)[1][1:].upper(),
                    "file_hash": validation_result["hash"],
                    "status": "completed"
                }

                # Add speaker labels if available
                if 'speaker_labels' in result and result['speaker_labels']:
                    response_data['speakers'] = result['speaker_labels']

                # Add content safety results if available
                if 'content_safety_labels' in result:
                    response_data['content_safety'] = result['content_safety_labels']

                return Response(response_data)
            else:
                return Response({
                    "error": "Transcription failed",
                    "details": result.get('error', 'Unknown error')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response(
                {
                    "error": "Internal server error",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
