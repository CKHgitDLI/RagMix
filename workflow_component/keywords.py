import re
from abc import ABC
from settings import DEBUG
from workflow_component.generate import GenerateParam,Generate


class KeywordExtractParam(GenerateParam):
    """
    Define the KeywordExtract component parameters.
    """

    def __init__(self, top_n=1):
        super().__init__()
        self.top_n = top_n

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

    def run(self, ask, chat_mdl, top_n):
        """
        获取关键词，多个关键词之间使用逗号隔开
        @param ask:用户问题字符串
        @param chat_mdl:Chat模型对象
        @param top_n:提取top_n个关键词
        @return:
        """
        self._param = KeywordExtractParam(top_n)
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
    k.run("""因为你时时刻刻都是忙的，我次次找你你都是忙的，我知道你忙是应该的，但是希望你能抽出时间陪我聊聊天。我是一个安全感极低的人，我就觉得我在你身边呆着很安逸，就那么坐着我都觉得很安逸，我不是非得每次找你就想跟你亲。我几天不见你真的很想你，明明离得不远，搞得跟异地一样，我一般周一周二，周四周五健身，所以周内周三一般抽空会去看你，然后周末去找你，我就是想跟你多见见面。我不喜欢线上聊天，看来我过于热情了，过于热情对于你来说是种负担。
    你这是谈对象吗，都是我每次去找你，感情的付出都是相互的，你想想看，每次都是我在迁就你吧，我就是性情中人，有啥话当面说，有啥不爽我就表现出来了，但是哪次我生气不是你惹的。一没时间二没精力，我已经很理解你了，要不然我为啥每次都过去找你，一陪就陪你一下午，一晚上。天天担心你回去晚，吃不饱，吃饭不好好吃。你说是谈对象，一很少见面，二见面了，不喜欢亲不喜欢抱，你是谈了个情绪垃圾桶嘛。""",
          ollama_chat, 10)
