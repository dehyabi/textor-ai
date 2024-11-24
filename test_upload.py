import requests
import os
from requests_toolbelt.multipart.encoder import MultipartEncoder
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_upload():
    url = "http://localhost:8000/api/transcribe/upload/"
    audio_file_path = "test_audio.mp3"
    
    if not os.path.exists(audio_file_path):
        print(f"Error: Audio file not found at {audio_file_path}")
        return
    
    print("Sending audio file for transcription...")
    
    # Read the file content
    with open(audio_file_path, 'rb') as f:
        file_content = f.read()
    
    # Create multipart form data
    multipart_data = MultipartEncoder(
        fields={
            'file': ('test_audio.mp3', file_content, 'audio/mpeg')
        }
    )
    
    # Set headers with content-type from multipart and authorization
    headers = {
        'Content-Type': multipart_data.content_type,
        'Authorization': 'Bearer 4620811705e9bcfb809af8628c008e41e704cb7d'
    }
    
    # Send POST request to the API
    response = requests.post(url, data=multipart_data, headers=headers)
    
    # Print request details for debugging
    print("\nRequest Details:")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"File size: {len(file_content)} bytes")
    
    # Print the response
    print(f"\nResponse Status Code: {response.status_code}")
    print("Response Headers:", dict(response.headers))
    print("Response Body:", response.text)

if __name__ == "__main__":
    test_upload()
