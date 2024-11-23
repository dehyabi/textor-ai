from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
import requests
import os
from dotenv import load_dotenv

load_dotenv()

ASSEMBLYAI_API_KEY = os.getenv('ASSEMBLYAI_API_KEY')
UPLOAD_URL = "https://api.assemblyai.com/v2/upload"
TRANSCRIPT_URL = "https://api.assemblyai.com/v2/transcript"

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

    def create_transcript(self, audio_url):
        transcript_request = {
            "audio_url": audio_url,
            "language_code": "en"
        }

        transcript_response = requests.post(
            TRANSCRIPT_URL,
            json=transcript_request,
            headers=headers
        )
        return transcript_response.json()

    def get_transcript_result(self, transcript_id):
        polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
        polling_response = requests.get(polling_endpoint, headers=headers)
        return polling_response.json()

    def post(self, request, *args, **kwargs):
        try:
            audio_file = request.FILES.get('audio_file')
            if not audio_file:
                return Response(
                    {"error": "No audio file provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Upload the file
            upload_response = self.upload_file(audio_file)
            audio_url = upload_response['upload_url']

            # Request transcript
            transcript_response = self.create_transcript(audio_url)
            transcript_id = transcript_response['id']

            # Get transcription result
            while True:
                result = self.get_transcript_result(transcript_id)
                if result['status'] == 'completed':
                    return Response({
                        "text": result['text'],
                        "status": "completed"
                    })
                elif result['status'] == 'error':
                    return Response({
                        "error": "Transcription failed",
                        "details": result.get('error', 'Unknown error')
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
