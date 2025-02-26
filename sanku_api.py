from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import uvicorn
from workflow_component.jiansuo import Retrieval
from workflow_component.generate import Generate
from model_link.OllamaChat import OllamaChat
from model_link.OllamaEmbedding import OllamaEmbed
from entire_file_deal import entire_file

ollama_embedding = OllamaEmbed(model_name="bge-m3", base_url="172.20.200.181:11434")  # embedding
ollama_chat = OllamaChat(model_name="deepseek-r1:70b_ctx10k", base_url="172.20.200.181:11434")
# ollama_chat = OllamaChat(model_name="qwen2.5:72b_ctx10k", base_url="172.20.200.181:11434")

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
    # history = data['messages']
    ask = data['ask']
    # print(history[-1]['content'])
    # 知识库召回检测
    re = Retrieval()
    try:
        ref = re.run(query=ask, embd_mdl=ollama_embedding, rerank_mdl=None,
                 similarity_threshold=0.3,
                 keywords_similarity_weight=0.5, top_n=20, top_k=1024, empty_response="", knowledgebase_name="ckh2")
        ref_s = ""
        # 召回数据处理
        for i in range(len(ref["chunk_id"])):
            ref_s += str(i + 1) + "、文件名：{" + ref["docnm_kwd"][i] + "}\n内容：{" + ref["content_ltks"][i] + "}\n\n"
        print(ref_s)
        unique_list = list(set(ref["docnm_kwd"]))
        print(unique_list)
        reference=""
        for i in range(len(unique_list[:6])):
            reference=reference+"## "+str(i + 1)+"、"+entire_file(unique_list[i])
        print(reference)
    except:
        reference = ""
    # return
    return EventSourceResponse(ge.stream_output(history=[{"role": "user", "content": ask}], chat_mdl=ollama_chat,
                                                retrieval_res=None,
                                                embd_mdl=None,max_tokens=512000,temperature=0.6,
prompt="""
# 以下内容是基于用户发送的消息的搜索结果:
{results}
在回答时，请注意以下几点:
- 并非搜索结果的所有内容都与用户的问题密切相关，你需要结合问题，对搜索结果进行别、筛选.
- 对于列举类的问题(如列举所有航班信息)，请将答案尽量找完整，并告诉用户可以查看搜索来源、获得完整信息，优先提供信息完整、最相关的列举项。一对于创作类的问题(如写论文)，你需要解读并概括用户的题目要求，选择合运的格式，充分利用搜索结果并抽取重要信息，生成符合用户要求、极具思想深度、富有创造力与专业性的答案。你的创作篇幅需要尽可能延长，对于每一个要点的论述要推测用户的意图，给出尽可能多角度的回答要点、目务必信息量大、论述详凤。如果回答很长，请尽量结构化、分段落总结。如果需要分点作答，尽量控制在5个点以内，并合并相关的内容。、对于客观类的问答，如果问题的答案非常简短，可以适当补充一到两句相关信息，以丰富内容。
- 你需要根据用户要求和回答内容选择合适、美观的回答格式，确保可读性强。
- 你的回答应该综合多个相关结果来回答，不能重复引用一条信息。
- 除非用户要求，否则你回答的语言需要和用户提问的语言保持一致。
- 对搜索结果中案例的具体公司名、地名、人名等信息请注意保密。
- 回答用户问题时不需要引用或指出具体相关案例。
- 思考过程中，把具体的企业名、地名使用XXX代替。
""", cite=False, sse=True,results=reference))


log_config = uvicorn.config.LOGGING_CONFIG
log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
uvicorn.run(app, host="59.74.169.92", port=8976, log_config=log_config)
