import asyncio
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from deepseek_driver import DeepSeekDriver

class Message(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    messages: List[Message]
    model: str = "deepseek-chat"
    stream: bool = False
    temperature: Optional[float] = None
    top_p: Optional[float] = None

class API:
    def __init__(self, driver: DeepSeekDriver):
        self.app = FastAPI()
        self.driver = driver
        self.request_queue = asyncio.Queue()
        self.setup_routes()
        self.start_worker()

    def setup_routes(self):
        @self.app.post("/v1/chat/completions")
        async def chat_completions(request: ChatCompletionRequest):
            if not self.driver.is_running:
                raise HTTPException(status_code=503, detail="DeepSeek Driver is not running")

            # Create a queue for the response chunks
            response_queue = asyncio.Queue()
            
            # Put the request and response queue into the main request queue
            await self.request_queue.put((request, response_queue))
            
            if request.stream:
                return StreamingResponse(self.stream_generator(response_queue), media_type="text/event-stream")
            else:
                # Accumulate response for non-streaming
                full_content = ""
                finish_reason = None
                
                while True:
                    chunk_str = await response_queue.get()
                    if chunk_str is None:
                        break
                    
                    if chunk_str.startswith("data: "):
                        data_str = chunk_str[6:].strip()
                        if data_str == "[DONE]":
                            continue
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    full_content += delta["content"]
                                finish_reason = data["choices"][0].get("finish_reason")
                        except:
                            pass
                
                return {
                    "id": "chatcmpl-custom",
                    "object": "chat.completion",
                    "created": 0,
                    "model": request.model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": full_content
                            },
                            "finish_reason": finish_reason or "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    }
                }

    async def stream_generator(self, response_queue: asyncio.Queue):
        while True:
            chunk = await response_queue.get()
            if chunk is None:
                yield "data: [DONE]\n\n"
                break
            yield chunk

    def start_worker(self):
        self.worker_task = asyncio.create_task(self.worker())

    async def stop(self):
        print("Stopping API worker...")
        if hasattr(self, 'worker_task'):
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        print("API worker stopped.")

    async def worker(self):
        print("API Worker started")
        try:
            while True:
                request, response_queue = await self.request_queue.get()
                try:
                    # Call the driver with the raw messages list
                    # The driver will handle formatting
                    async for chunk in self.driver.generate_response(
                        message=request.messages,
                        model=request.model,
                        stream=request.stream,
                        temperature=request.temperature,
                        top_p=request.top_p
                    ):
                        await response_queue.put(chunk)
                    
                except Exception as e:
                    print(f"Error in worker: {e}")
                    error_chunk = {
                        "error": {
                            "message": str(e),
                            "type": "internal_error",
                            "param": None,
                            "code": None
                        }
                    }
                    await response_queue.put(f"data: {json.dumps(error_chunk)}\n\n")
                finally:
                    await response_queue.put(None)
        except asyncio.CancelledError:
            print("API Worker cancelled")
            raise
