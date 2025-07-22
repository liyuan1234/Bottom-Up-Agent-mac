import requests
import json
import anthropic
import time

class Claude():
    def __init__(self, model_name="claude-3-7-sonnet-20250219", api_key=None):
        self.client = anthropic.Client(api_key=api_key)
        self.model_name = model_name
    
    def call_text(self, text_prompt, tools=None, max_iterations=3):

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": text_prompt
                    }
                ]
            }
        ]

        for i in range(max_iterations):
            try:
                response = self.client.messages.create(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=3000,
                    tools=tools if tools else []
                )

                answer = None
                tool_call = None

                for block in response.content:
                    if block.type == "text" and answer is None:
                        answer = block.text
                    elif block.type == "tool_use":
                        tool_call = {
                            "name": block.name,
                            "input": block.input
                        }

                return {
                    "message": answer,
                    "function": tool_call,
                    "usage": {
                        "input": response.usage.input_tokens,
                        "output": response.usage.output_tokens,
                        "total": response.usage.input_tokens + response.usage.output_tokens
                    }
                }
            except:
                time.sleep(0.1)
        raise Exception("Claude API call failed after multiple attempts.")
    
    
    def call_text_images(self, text_prompt, imgs, tools=None, max_iterations=3, pre_knowledge=None):

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": text_prompt
                    }
                ]
            }   
        ]

        for img in imgs:
            messages[0]["content"].append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img
                }
            })

        
        for i in range(max_iterations):
            try:
                response = self.client.messages.create(
                    model=self.model_name,
                    system=pre_knowledge if pre_knowledge else "you are a helpful assistant",
                    messages=messages,
                    max_tokens=3000,
                    tools=tools if tools else []
                )

                answer = None
                tool_call = None

                for block in response.content:
                    if block.type == "text" and answer is None:
                        answer = block.text
                    elif block.type == "tool_use":
                        tool_call = {
                            "name": block.name,
                            "input": block.input
                        }

                return {
                    "message": answer,
                    "function": tool_call,
                    "usage": {
                        "input": response.usage.input_tokens,
                        "output": response.usage.output_tokens,
                        "total": response.usage.input_tokens + response.usage.output_tokens
                    }
                }
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(0.1)
        raise Exception("Claude API call failed after multiple attempts.")

    


