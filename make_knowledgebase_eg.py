from knowledgebase.link import ELASTICSEARCH

knowledgebase_name = "ckh"  # 知识库名称

# 判断知识库是否存在，否则创建新知识库
import json
from settings import get_project_base_directory
import os
if not ELASTICSEARCH.indexExist(knowledgebase_name):
    ELASTICSEARCH.createIdx(knowledgebase_name, json.load(
        open(os.path.join(get_project_base_directory(), "knowledgebase/mapping.json"), "r")))

# 使用内置Laws解析方法
from parser_content import laws
from knowledgebase.insert import addChunk

# 定义解析方法钩子
a = laws.chunk

# 指定文件解析Chunk
chunk = a(r"D:\program_work\三库资料\经验知识库\2024年3月28日黑龙关煤业主井皮带温度故障分析报告.docx")

# 添加到数据库中
from model_link.OllamaEmbedding import OllamaEmbed

ollama_embedding = OllamaEmbed(model_name="bge-m3", base_url="172.20.200.181:11434")  # embedding
print(ollama_embedding.encode_queries("你好啊，我今早吃了包子。"))
addChunk(embd_mdl=ollama_embedding, chunk=chunk, knowledgebase_name="ckh")

# 删除
from knowledgebase.delete import rm_chunk

rm_chunk("ckh", "2022版煤矿安全规程.docx")
