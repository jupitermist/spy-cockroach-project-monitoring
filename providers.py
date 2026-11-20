"""Model providers. Each one runs a turn of the same agent loop, with the same prompt and tools."""

import json

import anthropic
import openai

# Price per million tokens (input, cached input, output). Anthropic runs do not use caching yet.
MODELS = {
    "claude-haiku-5-5": {"provider": "anthropic", "price": (0.10, None, 0.50)},
    "claude-sonnet-5-5": {"provider": "anthropic", "price": (2.00, 0.10, 10.00)},
    "gpt-6.2-sol": {"provider": "openai", "price": (2.00, 0.10, 10.00)},
}


class Turn:
    def __init__(self, calls, input_tokens, output_tokens, cached_tokens=0, refused=False):
        self.calls = calls  # list of (call_id, name, args)
        self.input_tokens = input_tokens  # includes cached_tokens
        self.output_tokens = output_tokens
        self.cached_tokens = cached_tokens
        self.refused = refused


def cost_usd(model, input_tokens, cached_tokens, output_tokens):
    price_in, price_cached, price_out = MODELS[model]["price"]
    if price_cached is None:
        price_cached = price_in
    return ((input_tokens - cached_tokens) * price_in + cached_tokens * price_cached
            + output_tokens * price_out) / 1_000_000


class AnthropicProvider:
    def __init__(self, model, system, tools):
        self.client = anthropic.Anthropic()
        self.model, self.system, self.tools = model, system, tools
        self.messages = []

    def add_user(self, text):
        self.messages.append({"role": "user", "content": text})

    def step(self):
        response = self.client.messages.create(
            model=self.model, max_tokens=16000, system=self.system, tools=self.tools, messages=self.messages,
        )
        self.messages.append({"role": "assistant", "content": response.content})
        calls = [(b.id, b.name, b.input) for b in response.content if b.type == "tool_use"]
        return Turn(calls, response.usage.input_tokens, response.usage.output_tokens,
                    refused=response.stop_reason == "refusal")

    def add_results(self, results):
        self.messages.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": call_id, "content": content, "is_error": is_error}
            for call_id, content, is_error in results
        ]})


class OpenAIProvider:
    def __init__(self, model, system, tools):
        self.client = openai.OpenAI()
        self.model, self.system = model, system
        self.tools = [{"type": "function", "name": t["name"], "description": t["description"],
                       "parameters": t["input_schema"], "strict": True} for t in tools]
        self.input = []

    def add_user(self, text):
        self.input.append({"role": "user", "content": text})

    def step(self):
        response = self.client.responses.create(
            model=self.model, instructions=self.system, tools=self.tools, input=self.input, max_output_tokens=16000,
        )
        self.input += response.output
        calls = [(item.call_id, item.name, json.loads(item.arguments))
                 for item in response.output if item.type == "function_call"]
        refused = any(part.type == "refusal"
                      for item in response.output if item.type == "message" for part in item.content)
        details = response.usage.input_tokens_details
        return Turn(calls, response.usage.input_tokens, response.usage.output_tokens,
                    cached_tokens=details.cached_tokens if details else 0, refused=refused)

    def add_results(self, results):
        for call_id, content, is_error in results:
            self.input.append({"type": "function_call_output", "call_id": call_id,
                               "output": f"Error: {content}" if is_error else content})


def make_provider(model, system, tools):
    provider = {"anthropic": AnthropicProvider, "openai": OpenAIProvider}[MODELS[model]["provider"]]
    return provider(model, system, tools)
