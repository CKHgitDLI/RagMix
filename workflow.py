from model_link.OllamaChat import OllamaChat
from workflow_component.generate import Generate
from workflow_component.rewrite import RewriteQuestion
from workflow_component.categorize import Categorize
from model_link.OllamaEmbedding import OllamaEmbed
from workflow_component.jiansuo import Retrieval

ollama_chat = OllamaChat(model_name="qwen2.5:32b_ctx32k", base_url="172.20.200.181:11434")
ollama_embedding = OllamaEmbed(model_name="bge-m3", base_url="172.20.200.181:11434")

# 测试Embedding
print(ollama_embedding.encode_queries("我是崔锴华"))

# 总问题
ask = "我现在要做串联通风，请问我需要安装什么传感器？"

# 问题优化
rq = RewriteQuestion()
# 问题优化考虑到了历史对话，因此使用history数组
a = rq.run(history=[{"role": "user", "content": ask}], chat_mdl=ollama_chat)
print(a)

# 问题分类
ca = Categorize()
cat = {
    "无关问题": {
        "description": "用户的问题与煤矿规章制度无关",
        "examples": """你好
        你是谁创造的？
        今天天气怎么样？"""
    },
    "煤矿生产安全相关制度": {
        "description": "用户的问题与煤矿规章制度有关",
        "examples": """安全设施设计需要作重大变更应当怎么做？
        煤矿建设项目竣工投入生产或者使用前应当由谁验收？
        煤矿企业主要负责人有什么职责？
        未统计目标任务完成情况
        爆破作业什么时候进行？
        煤矿智能化建设的技术路线？"""
    }}
b = ca.run(ask=a, chat_mdl=ollama_chat, category_description=cat)

ge = Generate()
if b == "无关问题":
    for temp in ge.stream_output(history=[{"role": "user", "content": a}], chat_mdl=ollama_chat,
                                 retrieval_res=None,
                                 embd_mdl=ollama_embedding,
                                 prompt="""作为西安科技大学科技处管理员，你的主要任务是根据学校的相关规定，准确理解并解释相关条例，回答用户的问题。但是用户没有询问对于学校规章制度的问题，只是一些常规的问题，你需要幽默、风趣地回答用户的问题，并提示用户询问学校规章制度相关问题。

1、你是由西安科技大学智能系统安全与控制研究所 于振华团队中的崔锴华同学创造的，回答这类问题时请保持严肃。
2、你叫“小科”。
3、回答问题时你需要说结束语：如有疑问请联系西安科技大学智能系统安全与控制研究所。
4、于振华是西安科技大学计算机科学与技术学院的教授，是崔锴华的导师。"""):
        print(temp)
else:
    # 知识库召回检测
    re = Retrieval()
    ref = re.run(query=a, embd_mdl=ollama_embedding, rerank_mdl=None,
                 similarity_threshold=0.2,
                 keywords_similarity_weight=0.5, top_n=8, top_k=1024, empty_response="", knowledgebase_name="ckh")
    ref_s = ""
    # 召回数据处理
    for i in range(len(ref["chunk_id"])):
        ref_s += str(i + 1) + "、文件名：{" + ref["docnm_kwd"][i] + "}\n内容：{" + ref["content_ltks"][i] + "}\n\n"
    print(ref_s)
    # 回答问题
    for temp in ge.stream_output(history=[{"role": "user", "content": a}], chat_mdl=ollama_chat,
                                 retrieval_res=ref,
                                 embd_mdl=ollama_embedding,
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

以下是参考文本材料
{input}""", cite=True, input=ref_s):
        print(temp)
