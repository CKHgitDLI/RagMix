from abc import ABC
from openai import OpenAI
import openai
from ollama import Client
from nlp import is_english
import os

from nlp.token_num import num_tokens_from_string

class Base(ABC):
    def __init__(self, key, model_name, base_url):
        timeout = int(os.environ.get('LM_TIMEOUT_SECONDS', 600))
        self.client = OpenAI(api_key=key, base_url=base_url, timeout=timeout)
        self.model_name = model_name

    def chat(self, system, history, gen_conf):
        if system:
            history.insert(0, {"role": "system", "content": system})
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=history,
                **gen_conf)
            ans = response.choices[0].message.content.strip()
            if response.choices[0].finish_reason == "length":
                ans += "...\nFor the content length reason, it stopped, continue?" if is_english(
                    [ans]) else "······\n由于长度的原因，回答被截断了，要继续吗？"
            return ans, response.usage.total_tokens
        except openai.APIError as e:
            return "**ERROR**: " + str(e), 0

    def chat_streamly(self, system, history, gen_conf):
        if system:
            history.insert(0, {"role": "system", "content": system})
        ans = ""
        total_tokens = 0
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=history,
                stream=True,
                **gen_conf)
            for resp in response:
                if not resp.choices: continue
                if not resp.choices[0].delta.content:
                    resp.choices[0].delta.content = ""
                ans += resp.choices[0].delta.content

                if not hasattr(resp, "usage") or not resp.usage:
                    total_tokens = (
                                total_tokens
                                + num_tokens_from_string(resp.choices[0].delta.content)
                        )
                elif isinstance(resp.usage, dict):
                    total_tokens = resp.usage.get("total_tokens", total_tokens)
                else: total_tokens = resp.usage.total_tokens

                if resp.choices[0].finish_reason == "length":
                    ans += "...\nFor the content length reason, it stopped, continue?" if is_english(
                        [ans]) else "······\n由于长度的原因，回答被截断了，要继续吗？"
                yield ans

        except openai.APIError as e:
            yield ans + "\n**ERROR**: " + str(e)

        yield total_tokens


class OllamaChat(Base):
    def __init__(self, model_name, **kwargs):
        self.client = Client(host=kwargs["base_url"])
        self.model_name = model_name

    def chat(self, system, history, gen_conf):
        if system:
            history.insert(0, {"role": "system", "content": system})
        try:
            options = {}
            if "temperature" in gen_conf: options["temperature"] = gen_conf["temperature"]
            if "max_tokens" in gen_conf: options["num_predict"] = gen_conf["max_tokens"]
            if "top_p" in gen_conf: options["top_k"] = gen_conf["top_p"]
            if "presence_penalty" in gen_conf: options["presence_penalty"] = gen_conf["presence_penalty"]
            if "frequency_penalty" in gen_conf: options["frequency_penalty"] = gen_conf["frequency_penalty"]
            response = self.client.chat(
                model=self.model_name,
                messages=history,
                options=options,
                keep_alive=-1
            )
            ans = response["message"]["content"].strip()
            return ans, response["eval_count"] + response.get("prompt_eval_count", 0)
        except Exception as e:
            return "**ERROR**: " + str(e), 0

    def chat_streamly(self, system, history, gen_conf):
        if system:
            history.insert(0, {"role": "system", "content": system})
        options = {}
        if "temperature" in gen_conf: options["temperature"] = gen_conf["temperature"]
        if "max_tokens" in gen_conf: options["num_predict"] = gen_conf["max_tokens"]
        if "top_p" in gen_conf: options["top_k"] = gen_conf["top_p"]
        if "presence_penalty" in gen_conf: options["presence_penalty"] = gen_conf["presence_penalty"]
        if "frequency_penalty" in gen_conf: options["frequency_penalty"] = gen_conf["frequency_penalty"]
        ans = ""
        try:
            response = self.client.chat(
                model=self.model_name,
                messages=history,
                stream=True,
                options=options,
                keep_alive=-1
            )
            for resp in response:
                if resp["done"]:
                    # yield resp.get("prompt_eval_count", 0) + resp.get("eval_count", 0)
                    pass
                ans += resp["message"]["content"]
                yield ans
        except Exception as e:
            # yield ans + "\n**ERROR**: " + str(e)
            print(e)
        return

    def describe(self, image, gen_conf={"temperature": 0}):
        messages = [{
            'role': 'user',
            'content': '请用中文详细描述一下图中的内容，比如时间，地点，人物，事情，人物心情等，如果有数据请提取出数据。',
            'images': [image]
        }]
        return self.chat("请用中文详细描述一下图中的内容，比如时间，地点，人物，事情，人物心情等，如果有数据请提取出数据。",
                         messages, gen_conf=gen_conf)

if __name__ == '__main__':
    ollama = OllamaChat(model_name="llama3.2-vision", base_url="172.20.200.181:11434")
    gen_conf = {"temperature": 1}
    messages = [{
        'role': 'user',
        'content': '请描述一下这张图片？墙上挂着什么？',
        'images': [r'E:\Rag-CKH\test_file\1.png']
    }]
    ans, _ = ollama.chat("你是煤矿的安全员，用户的所有问题都是在询问煤矿相关知识。", messages, gen_conf=gen_conf)
    print(ans)
