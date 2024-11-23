from gtts import gTTS

def create_test_audio():
    text = "Hello! This is a test audio file for our speech to text API. It should transcribe this message accurately."
    tts = gTTS(text=text, lang='en')
    tts.save("test_audio.mp3")
    print("Test audio file created: test_audio.mp3")

if __name__ == "__main__":
    create_test_audio()
