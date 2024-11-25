from knowledgebase.link import ELASTICSEARCH
import json
from settings import get_project_base_directory
import os
from model_link.OllamaEmbedding import OllamaEmbed
knowledgebase_name="ckh"#知识库名称
ollama_embedding=OllamaEmbed(model_name="bge-m3", base_url="172.20.200.181:11434")#embedding
print(ollama_embedding.encode_queries("我是崔锴华"))
#判断知识库是否存在，否则创建新知识库
if not ELASTICSEARCH.indexExist(knowledgebase_name):
    ELASTICSEARCH.createIdx(knowledgebase_name, json.load(
        open(os.path.join(get_project_base_directory(), "knowledgebase/mapping.json"), "r")))

#Laws解析方法
from parser_content import laws
from knowledgebase.insert import addChunk
#定义解析方法钩子
a=laws.chunk
#指定文件解析Chunk
chunk=a(r"E:\Rag-CKH\test_file\2022版煤矿安全规程.docx")
#添加到数据库中
addChunk(embd_mdl=ollama_embedding,chunk=chunk,knowledgebase_name="ckh")
