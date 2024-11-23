from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

ASSEMBLYAI_API_KEY = os.getenv('ASSEMBLYAI_API_KEY')
UPLOAD_URL = "https://api.assemblyai.com/v2/upload"
TRANSCRIPT_URL = "https://api.assemblyai.com/v2/transcript"

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

# Create your views here.

class TranscriptionView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def upload_file(self, audio_file):
        def read_file(file_obj):
            content = file_obj.read()
            return content

        upload_response = requests.post(
            UPLOAD_URL,
            headers={"authorization": ASSEMBLYAI_API_KEY},
            data=read_file(audio_file)
        )
        return upload_response.json()

    def create_transcript(self, audio_url, language_code=None):
        transcript_request = {
            "audio_url": audio_url,
            "language_detection": True,  # Enable auto language detection
        }

        # Only set specific language if requested
        if language_code:
            transcript_request["language_code"] = language_code

        transcript_response = requests.post(
            TRANSCRIPT_URL,
            json=transcript_request,
            headers=headers
        )
        return transcript_response.json()

    def get_transcript_result(self, transcript_id):
        polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
        while True:
            polling_response = requests.get(polling_endpoint, headers=headers)
            result = polling_response.json()
            
            if result['status'] == 'completed' or result['status'] == 'error':
                return result
            
            time.sleep(3)  # Wait 3 seconds before polling again

    def post(self, request, *args, **kwargs):
        try:
            # Get audio file
            audio_file = request.FILES.get('audio_file')
            if not audio_file:
                return Response(
                    {"error": "No audio file provided"},
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
                return Response({
                    "text": result['text'],
                    "detected_language": SUPPORTED_LANGUAGES.get(detected_language, detected_language),
                    "detected_language_code": detected_language,
                    "requested_language": SUPPORTED_LANGUAGES.get(language_code) if language_code else "auto",
                    "status": "completed"
                })
            else:
                return Response({
                    "error": "Transcription failed",
                    "details": result.get('error', 'Unknown error')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
