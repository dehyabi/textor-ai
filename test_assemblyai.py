import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_assemblyai_key():
    api_key = os.getenv('ASSEMBLYAI_API_KEY')
    if not api_key:
        print("Error: ASSEMBLYAI_API_KEY not found in environment variables")
        return
        
    print(f"Using API Key: {api_key}")
    
    headers = {
        "authorization": api_key
    }
    
    # First, test with a direct file upload
    print("\nTesting file upload...")
    audio_file_path = "test_audio.mp3"
    
    with open(audio_file_path, 'rb') as f:
        response = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers=headers,
            data=f
        )
    
    print(f"Upload Status Code: {response.status_code}")
    print(f"Upload Response: {response.text}")
    
    if response.status_code == 200:
        print("\nTesting transcription...")
        upload_url = response.json()['upload_url']
        
        transcript_request = {
            "audio_url": upload_url,
            "language_detection": True
        }
        
        response = requests.post(
            "https://api.assemblyai.com/v2/transcript",
            json=transcript_request,
            headers=headers
        )
        
        print(f"Transcription Status Code: {response.status_code}")
        print(f"Transcription Response: {response.text}")

if __name__ == "__main__":
    test_assemblyai_key()
