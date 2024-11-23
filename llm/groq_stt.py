from groq import Groq
import os
import time
from dotenv import load_dotenv
load_dotenv()

client = Groq()



def stt(filename: str, lang: str, system):
  # Open the audio file
  try:
    with open(filename, "rb") as file:
        
        # Create a transcription of the audio file
        transcription = client.audio.transcriptions.create(
          file=(filename, file.read()), # Required audio file
          model="whisper-large-v3-turbo", # Required model to use for transcription
          prompt=system,  # Optional
          response_format="json",  # Optional
          language=lang,  # Optional
          temperature=0.0  # Optional
        )
        # Print the transcription text
        return transcription.text
  except Exception as e:
     raise e