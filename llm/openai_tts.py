from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()


def generate_speech(text, voice="alloy", model="tts-1", output_file="response.mp3"):
    speech_file_path = output_file
    response = client.audio.speech.create(
      model="tts-1",
      voice="alloy",
      input=text
    )
    response.write_to_file(speech_file_path)
    return speech_file_path