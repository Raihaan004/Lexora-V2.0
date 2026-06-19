import json
import aiohttp
from typing import AsyncGenerator, List, Dict, Optional
from app.core.config import settings

class LLMService:
    """
    Service wrapper around Ollama local API to run Qwen:4b inference.
    Handles streaming responses asynchronously.
    """
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.LLM_MODEL

    async def generate_stream(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Send a prompt to local Ollama server and yield chunks of response in real-time.
        
        Args:
            prompt: Formatted user query prompt (optionally containing context).
            system_prompt: Optional system-level prompt guiding assistant behavior.
            
        Yields:
            chunk: Decoded text tokens string.
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "keep_alive": -1,  # Keep the model loaded in memory indefinitely to avoid reload latency
            "options": {
                "num_ctx": 2048,      # Limit context size to 2048 tokens to minimize evaluation overhead on CPU
                "temperature": 0.2,    # Factual responses, low temperature
                "num_predict": 1024    # Output token prediction limit
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            # Connect asynchronously to local Ollama API
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        yield f"Ollama Server Error ({response.status}): {error_text}"
                        return
                        
                    async for line in response.content:
                        if line:
                            try:
                                data = json.loads(line.decode('utf-8'))
                                chunk = data.get("response", "")
                                if chunk:
                                    yield chunk
                                if data.get("done", False):
                                    break
                            except Exception:
                                # Ignore malformed json lines
                                continue
                                
        except aiohttp.ClientConnectorError:
            yield (
                "Error: Connection to Ollama failed. Please make sure that:\n"
                f"1. Ollama is installed and running on your system (base URL: {self.base_url}).\n"
                f"2. The model '{self.model}' has been downloaded locally by running: `ollama run {self.model}`."
            )
        except Exception as e:
            yield f"Error during generation: {str(e)}"

    async def generate_chat_stream(
        self, 
        messages: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """
        Send conversational message logs to Ollama /api/chat endpoint and yield responses.
        
        Args:
            messages: List of dialog entries: [{"role": "user", "content": "hello"}]
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "keep_alive": -1,  # Keep the model loaded in memory indefinitely
            "options": {
                "num_ctx": 2048,
                "temperature": 0.2,
                "num_predict": 1024
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        yield f"Ollama Chat Error ({response.status}): {error_text}"
                        return
                        
                    async for line in response.content:
                        if line:
                            try:
                                data = json.loads(line.decode('utf-8'))
                                chunk = data.get("message", {}).get("content", "")
                                if chunk:
                                    yield chunk
                                if data.get("done", False):
                                    break
                            except Exception:
                                continue
                                
        except aiohttp.ClientConnectorError:
            yield f"Error: Connection to Ollama failed. Please ensure Ollama is serving at {self.base_url}."
        except Exception as e:
            yield f"Error during chat generation: {str(e)}"

# Singleton client instance
llm_service = LLMService()
