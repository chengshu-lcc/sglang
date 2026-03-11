from typing import Any, Dict
from sglang.srt.entrypoints.openai.protocol import ChatCompletionRequest, StreamOptions, EmbeddingRequest, CompletionRequest
from pydantic import Field
import base64
import json
import numpy as np
import os

use_item_token = bool(os.getenv('USE_ITEM_TOKEN', False))

global_lora_names = []

def get_default_model_name(model_name: str) -> str:
    if len(global_lora_names) == 0:
        return "rtp"
    if len(global_lora_names) == 1:
        return global_lora_names[0]
    return model_name

class ChatCompletionRequestWrapper(ChatCompletionRequest):
    extra_configs: Dict[str, Any] = Field(default=None)
    extend_fields: Dict[str, Any] = Field(default=None)
    max_new_tokens: int = Field(default=None)

    # unused params
    trace_id: str = Field(default=None)
    debug_info: bool = Field(default=False)
    private_request: bool = Field(default=False)
    aux_info: bool = Field(default=False)

    def update_request(self) -> None:
        if self.extra_configs:
            for key, value in self.extra_configs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        if self.extend_fields:
            for key, value in self.extend_fields.items():
                if hasattr(self, key):
                    if key == 'input_placeholder_embs':
                        arr_bytes = base64.urlsafe_b64decode(value)
                        vec_dim_str = os.getenv('VEC_DIM', '896')
                        vec_dim = int(vec_dim_str)
                        arr = np.frombuffer(arr_bytes, dtype=np.float32).reshape(-1, vec_dim)
                        value = arr.tolist()
                    setattr(self, key, value)
        if self.max_new_tokens:
            self.max_tokens = self.max_new_tokens
        if self.stream and not self.stream_options:
            self.stream_options = StreamOptions(include_usage=True, continuous_usage_stats=True)
        self.model = get_default_model_name(self.model)
        if not use_item_token and self.messages:
            messages = []
            for param in self.messages:
                if isinstance(param, str):
                    param.content = param.content.replace("<|item|>", "<mask>")
                messages.append(param)
            self.messages = messages



class CompletionRequestWrapper(CompletionRequest):
    extra_configs: Dict[str, Any] = Field(default=None)
    extend_fields: Dict[str, Any] = Field(default=None)
    max_new_tokens: int = Field(default=None)
    yield_generator: bool = Field(default=False)
    generate_config: Dict[str, Any] = Field(default=None)

    # unused params
    trace_id: str = Field(default=None)
    debug_info: bool = Field(default=False)
    private_request: bool = Field(default=False)

    def update_request(self) -> None:
        if self.extra_configs:
            for key, value in self.extra_configs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        if self.extend_fields:
            for key, value in self.extend_fields.items():
                # 离线评测易用性需求，extend_fields={"prompt_logprobs": 0}
                if key == "prompt_logprobs":
                    self.logprobs = int(value) + 1
                    self.echo = True
                elif hasattr(self, key):
                    setattr(self, key, value)
        if self.generate_config:
            for key, value in self.generate_config.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        if self.max_new_tokens:
            self.max_tokens = self.max_new_tokens
        if self.yield_generator:
            self.stream = self.yield_generator
        if self.stream and not self.stream_options:
            self.stream_options = StreamOptions(include_usage=True, continuous_usage_stats=True)
        self.model = get_default_model_name(self.model)

class EmbeddingCompletionRequestWrapper(EmbeddingRequest):
    extra_configs: Dict[str, Any] = Field(default=None)
    extend_fields: Dict[str, Any] = Field(default=None)
    max_new_tokens: int = Field(default=None)

    # unused params
    trace_id: str = Field(default=None)
    debug_info: bool = Field(default=False)
    private_request: bool = Field(default=False)

    def update_request(self) -> None:
        if self.extra_configs:
            for key, value in self.extra_configs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        if self.extend_fields:
            for key, value in self.extend_fields.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        if self.max_new_tokens:
            self.max_tokens = self.max_new_tokens
        self.model = get_default_model_name(self.model)
