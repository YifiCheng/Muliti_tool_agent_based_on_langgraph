import argparse
import time
import uuid
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: float = 0.2
    max_tokens: int = Field(default=512, ge=1, le=4096)


class RemoteQwenServer:
    def __init__(self, model_path: str, served_model_name: str) -> None:
        self.model_path = model_path
        self.served_model_name = served_model_name
        self.model: Any | None = None
        self.processor: Any | None = None

    def load(self) -> None:
        import torch
        from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

        self.processor = AutoProcessor.from_pretrained(
            self.model_path,
            trust_remote_code=True,
        )
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            self.model_path,
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
            trust_remote_code=True,
        )

    def chat(self, messages: list[ChatMessage], max_tokens: int) -> str:
        if self.model is None or self.processor is None:
            raise RuntimeError("model is not loaded")

        prompt_messages = [
            {"role": item.role, "content": item.content}
            for item in messages
        ]
        text = self.processor.apply_chat_template(
            prompt_messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = self.processor(
            text=[text],
            return_tensors="pt",
        ).to(self.model.device)

        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=False,
        )
        generated_ids = generated_ids[:, inputs.input_ids.shape[1] :]
        output = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]
        return output.strip()


def create_app(server: RemoteQwenServer, api_key: str) -> FastAPI:
    app = FastAPI(title="Remote Qwen OpenAI-Compatible Server")

    def authorize(authorization: str | None) -> None:
        if not api_key:
            return
        if authorization != f"Bearer {api_key}":
            raise HTTPException(status_code=401, detail="unauthorized")

    @app.get("/v1/models")
    def list_models(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        authorize(authorization)
        return {
            "object": "list",
            "data": [
                {
                    "id": server.served_model_name,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "local",
                }
            ],
        }

    @app.post("/v1/chat/completions")
    def chat_completions(
        request: ChatCompletionRequest,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        authorize(authorization)
        if request.model != server.served_model_name:
            raise HTTPException(status_code=404, detail="model not found")

        answer = server.chat(request.messages, max_tokens=request.max_tokens)
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": server.served_model_name,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": answer},
                    "finish_reason": "stop",
                }
            ],
        }

    return app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--served-model-name", default="qwen2.5-vl-3b")
    parser.add_argument("--api-key", default="dev-token")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18080)
    args = parser.parse_args()

    import uvicorn

    server = RemoteQwenServer(
        model_path=args.model_path,
        served_model_name=args.served_model_name,
    )
    server.load()
    app = create_app(server, api_key=args.api_key)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
