# infrastructure/adapters/outbound/openai_client.py

import openai
from core.ports.outbound import ILLMClientPort
import logging
from typing import Optional

class OpenAIClientAdapter(ILLMClientPort):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        openai.api_key = api_key

    async def generate_response(
        self, 
        prompt: str, 
        model_name: str, 
        temperature: float,
        top_p: float,
        frequency_penalty: float,
        presence_penalty: float
    ) -> str:
        try:


            response = await openai.ChatCompletion.acreate(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error generating response with OpenAI: {e}")
            raise