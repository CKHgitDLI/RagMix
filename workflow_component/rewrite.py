from abc import ABC

from settings import DEBUG
from workflow_component.generate import GenerateParam


class RewriteQuestionParam(GenerateParam):

    """
    Define the QuestionRewrite component parameters.
    """
    def __init__(self):
        super().__init__()
        self.temperature = 0.9
        self.prompt = ""
        self.loop = 1

    def check(self):
        super().check()

    def get_prompt(self, conv):
        self.prompt = """
        You are an expert at query expansion to generate a paraphrasing of a question.
        I can't retrieval relevant information from the knowledge base by using user's question directly.     
        You need to expand or paraphrase user's question by multiple ways such as using synonyms words/phrase, 
        writing the abbreviation in its entirety, adding some extra descriptions or explanations, 
        changing the way of expression, translating the original question into another language (English/Chinese), etc. 
        And return 5 versions of question and one is from translation.
        Just list the question. No other words are needed.
        """
        return f"""
Role: A helpful assistant
Task: Generate a full user question that would follow the conversation.
Requirements & Restrictions:
  - Text generated MUST be in the same language of the original user's question.
  - If the user's latest question is completely, don't do anything, just return the original question.
  - DON'T generate anything except a refined question.

######################
-Examples-
######################
# Example 1
## Conversation
USER: What is the name of Donald Trump's father?
ASSISTANT:  Fred Trump.
USER: And his mother?
###############
Output: What's the name of Donald Trump's mother?
------------
# Example 2
## Conversation
USER: What is the name of Donald Trump's father?
ASSISTANT:  Fred Trump.
USER: And his mother?
ASSISTANT:  Mary Trump.
User: What's her full name?
###############
Output: What's the full name of Donald Trump's mother Mary Trump?
######################
# Real Data
## Conversation
{conv}
###############
    """
        return self.prompt


class RewriteQuestion(ABC):
    component_name = "RewriteQuestion"
    _param=RewriteQuestionParam()

    def run(self, history, chat_mdl):
        """
        优化用户问题
        @param history:对话历史的字典列表
        @param chat_mdl:Chat模型对象
        @return:字符串，优化后的用户问题
        """
        hist = history
        conv = []
        for m in hist:
            if m["role"] not in ["user", "assistant"]: continue
            conv.append("{}: {}".format(m["role"].upper(), m["content"]))
        conv = "\n".join(conv)
        ans,_ = chat_mdl.chat(self._param.get_prompt(conv), [{"role": "user", "content": "Output: "}],
                            self._param.gen_conf())
        if DEBUG:print("问题优化提示词：",self._param.get_prompt(conv))
        print("问题优化：",ans)
        return ans
