from typing import Any, Dict
from sglang.srt.entrypoints.openai.protocol import CompletionRequest, CompletionResponse
from pydantic import Field

class CompletionResponseWrapper(CompletionResponse):
    aux_info: Dict[str, Any] = Field(default=None)
    extend_fields: Dict[str, Any] = Field(default=None)

    def __init__(self, request: CompletionRequest, response : CompletionResponse):
        super().__init__(id=response.id,
                         created=response.created,
                         model=response.model,
                         choices=response.choices,
                         usage=response.usage)
        if request.echo and request.logprobs:
            self.aux_info = {'prompt_logprobs': response.choices[0].logprobs}
