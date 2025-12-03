import asyncio
import json
from fastapi import FastAPI, HTTPException, Request
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
        self.current_abort_event: asyncio.Event = None  # Track current request's abort event
        self.setup_routes()
        self.start_worker()

    def setup_routes(self):
        @self.app.post("/v1/chat/completions")
        async def chat_completions(request: ChatCompletionRequest, raw_request: Request):
            if not self.driver.is_running:
                raise HTTPException(status_code=503, detail="DeepSeek Driver is not running")

            # Create a queue for the response chunks
            response_queue = asyncio.Queue()
            
            # Create an abort event for this request
            abort_event = asyncio.Event()
            
            # Put the request, response queue, and abort event into the main request queue
            await self.request_queue.put((request, response_queue, abort_event))
            
            if request.stream:
                return StreamingResponse(
                    self.stream_generator(response_queue, abort_event, raw_request), 
                    media_type="text/event-stream"
                )
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

    async def stream_generator(self, response_queue: asyncio.Queue, abort_event: asyncio.Event, raw_request: Request):
        try:
            while True:
                # Check if client disconnected
                if await raw_request.is_disconnected():
                    print("Client disconnected, aborting request...")
                    abort_event.set()
                    # Signal the driver to abort (don't await, just set the flag)
                    self.driver.abort_requested = True
                    break
                
                try:
                    # Use a timeout so we can periodically check for disconnection
                    chunk = await asyncio.wait_for(response_queue.get(), timeout=0.5)
                    if chunk is None:
                        yield "data: [DONE]\n\n"
                        break
                    yield chunk
                except asyncio.TimeoutError:
                    # No chunk available, continue to check for disconnection
                    continue
        except asyncio.CancelledError:
            print("Stream generator cancelled, aborting...")
            abort_event.set()
            # Just set the flag, don't await anything during cancellation
            self.driver.abort_requested = True
        except GeneratorExit:
            # Client disconnected abruptly
            print("Generator exit, aborting...")
            abort_event.set()
            self.driver.abort_requested = True

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
                request, response_queue, abort_event = await self.request_queue.get()
                self.current_abort_event = abort_event
                try:
                    # Call the driver with the raw messages list
                    # The driver will handle formatting
                    async for chunk in self.driver.generate_response(
                        message=request.messages,
                        model=request.model,
                        stream=request.stream,
                        temperature=request.temperature,
                        top_p=request.top_p,
                        abort_event=abort_event
                    ):
                        # Check if aborted before putting chunk
                        if abort_event.is_set():
                            print("Request aborted, stopping chunk forwarding...")
                            break
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
                    self.current_abort_event = None
                    await response_queue.put(None)
        except asyncio.CancelledError:
            print("API Worker cancelled")
            raise
