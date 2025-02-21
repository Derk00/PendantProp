import pyttsx3

# def _play_sound(text: str):
#     engine = pyttsx3.init()
#     engine.say(text)
#     engine.runAndWait()

# _play_sound("Kankerl")


# To list available voices
engine = pyttsx3.init()
voices = engine.getProperty("voices")
for voice in voices:
    print(f"Voice ID: {voice.id}, Name: {voice.name}")
