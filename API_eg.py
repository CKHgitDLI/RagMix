# 此API示例仅为了给出流式输出的核心代码，并未实现完整的流程。
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import uvicorn

from workflow_component.generate import Generate
from model_link.OllamaChat import OllamaChat

ollama_chat = OllamaChat(model_name="qwen2.5:32b_ctx32k", base_url="172.20.200.181:11434")
ge = Generate()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.post("/chat")
async def response(data: Dict):
    history = data['history']
    return EventSourceResponse(ge.stream_output(history=history, chat_mdl=ollama_chat,
                                                retrieval_res=None,
                                                embd_mdl=None,
                                                prompt="""你是煤矿安全员，你只能依据后文给你的参考文本材料回答用户问题，不能使用自己的知识，严格按照要求作答。
    你的工作是根据参考文本材料的内容以及文本材料的文件名称，一步一步地思考，按照以下步骤和要求完成任务。
    请记住：思考过程应该是原始的、有机的和自然的，捕捉真实的人类思维流程，而不是遵循结构化的格式；这意味着，你的思维应该更像是一个意识流。

    以下是思考过程：
    1、首先默认用户的所有问题都是在询问参考文本材料中的相关规定，不能用其它知识进行作答。
    2、然后针对用户提出的问题找到参考文本材料中的依据，注意专业名词的准确性，如果有多个相关的依据，请分别作答。
    3、然后请用找到的依据原文作为依据，开始解答用户问题的答案，回答时合理分段，找到的每个相关依据使用以下格式：
        "XXX（文件名）规定：XXX。
        因此XXX（详细解答用户问题）。"
    4、然后猜测三个用户接下来想问的问题，分段换行回答，使用以下格式：
        "如果回答不够准确或检索的文件不正确，猜测您可能想追问的问题有：
            1.XXX?
            2.XXX?"
    5、最后换行输出以下结束语：
        "西安科技大学智能系统安全与控制研究所发布。鲁ICP备2023026495号（仅用于个人开发）"
""", cite=False, sse=True))


log_config = uvicorn.config.LOGGING_CONFIG
log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
uvicorn.run(app, host="59.74.169.90", port=8080, log_config=log_config)
