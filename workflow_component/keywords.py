import re
from abc import ABC
from settings import DEBUG
from workflow_component.generate import GenerateParam,Generate


class KeywordExtractParam(GenerateParam):
    """
    Define the KeywordExtract component parameters.
    """

    def __init__(self):
        super().__init__()
        self.top_n = 1

    def check(self):
        super().check()
        self.check_positive_integer(self.top_n, "Top N")

    def get_prompt(self):
        self.prompt = """
- Role: You're a question analyzer. 
- Requirements: 
  - Summarize user's question, and give top %s important keyword/phrase.
  - Use comma as a delimiter to separate keywords/phrases.
- Answer format: (in language of user's question)
  - keyword: 
""" % self.top_n
        return self.prompt


class KeywordExtract(ABC):
    component_name = "KeywordExtract"
    _param=KeywordExtractParam()
    def run(self, ask,chat_mdl, **kwargs):
        ans,_ = chat_mdl.chat(self._param.get_prompt(), [{"role": "user", "content": ask}],
                            self._param.gen_conf())

        ans = re.sub(r".*keyword:", "", ans).strip()
        ans = re.sub(r".*关键词:", "", ans).strip()
        if DEBUG: print("关键词：",ans)
        return ans

if __name__ == '__main__':
    from model_link.OllamaChat import OllamaChat
    ollama_chat = OllamaChat(model_name="qwen2.5:32b_ctx32k", base_url="172.20.200.181:11434")
    k=KeywordExtract()
    k.run("我是一个博士生，我没有女朋友。",ollama_chat)

