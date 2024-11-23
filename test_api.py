import requests
import os
import time
import unittest

def test_transcription(audio_file_path):
    url = "http://localhost:8000/api/transcribe/"
    
    if not os.path.exists(audio_file_path):
        print(f"Error: Audio file not found at {audio_file_path}")
        return
    
    print("Sending audio file for transcription...")
    
    # Open the audio file
    with open(audio_file_path, 'rb') as f:
        files = {'audio_file': f}
        
        # Send POST request to the API
        response = requests.post(url, files=files)
        
        # Print the response
        if response.status_code == 200:
            result = response.json()
            print("\nTranscription successful!")
            print("Text:", result['text'])
        else:
            print("\nError:", response.json())

class TestTranscriptionAPI(unittest.TestCase):

    def test_transcription_api(self):
        audio_file_path = "test_audio.mp3"
        if not os.path.exists(audio_file_path):
            self.fail("Audio file not found at " + audio_file_path)
        
        url = "http://localhost:8000/api/transcribe/"
        
        # Open the audio file
        with open(audio_file_path, 'rb') as f:
            files = {'audio_file': f}
            
            # Send POST request to the API
            response = requests.post(url, files=files)
            
            # Check the response
            self.assertEqual(response.status_code, 200)
            result = response.json()
            self.assertIn('text', result)

if __name__ == "__main__":
    # Use the generated test audio file
    audio_file_path = "test_audio.mp3"
    test_transcription(audio_file_path)
    unittest.main(argv=[''], verbosity=2, exit=False)
