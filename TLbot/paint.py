import openai
import os
import io
import warnings
from PIL import Image
from decouple import config

class DallE:
    def to_image(self, prompt):

        openai.api_key = config("OPENAI_API_KEY")
        try:
            response = openai.Image.create(
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            return response['data'][0]['url']
        except openai.error.OpenAIError as e:
            print(e.http_status)
            print(e.error)
            return