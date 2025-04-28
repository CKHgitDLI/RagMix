import os
from fastapi import FastAPI, UploadFile, File
from sse_starlette.sse import EventSourceResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import uvicorn
from langchain_community.llms.tongyi import Tongyi
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.graphs import Neo4jGraph
from knowledge_graph import make_kg
from knowledge_graph.kag import full_retriever, graph_retriever
from langchain_community.embeddings import OllamaEmbeddings
from knowledgebase.link import ELASTICSEARCH
from model_link.OllamaEmbedding import OllamaEmbed
from knowledgebase.delete import rm_chunk
from workflow_component.jiansuo import Retrieval
from langchain_core.documents import Document
from neo4j import GraphDatabase

ollama_embedding = OllamaEmbed(model_name="bge-m3:latest", base_url="127.0.0.1:11434")  # embedding
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

load_dotenv()
os.environ["DASHSCOPE_API_KEY"] = "sk-b5883e47d69a417daae9f529e8e3ebf8"
url = "bolt://localhost:7687"
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "1609936983"
os.environ["NEO4J_DATABASE"] = "ckh"

llm1 = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus",
    temperature=0,
    top_p=0.7
)
llm2 = Tongyi(model="qwen-plus",
              api_key="sk-b5883e47d69a417daae9f529e8e3ebf8",
              temperature=0,
              top_p=0.7)

embeddings = OllamaEmbeddings(model="bge-large")

graph_db = Neo4jGraph(
    url=os.environ["NEO4J_URI"],
    username=os.environ["NEO4J_USERNAME"],
    password=os.environ["NEO4J_PASSWORD"],
    database=os.environ["NEO4J_DATABASE"]
)

graph_db_t = Neo4jGraph(
    url=os.environ["NEO4J_URI"],
    username=os.environ["NEO4J_USERNAME"],
    password=os.environ["NEO4J_PASSWORD"],
    database="neo4j"
)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.post("/kag")
async def response(data: Dict):
    ask = data['ask']
    graph_data, vector_data = full_retriever(ask, llm2, embeddings, graph_db)
    return {"graph_data": graph_data, "vector_data": vector_data}


@app.post("/upload")
async def create_upload_file(file: UploadFile = File(...)):
    print(file.filename)
    dirs = 'uploads_doc'
    if not os.path.exists(dirs):
        os.makedirs(dirs)
    file_location = f"{dirs}/{file.filename}"
    with open(file_location, "wb") as file_object:
        file_object.write(file.file.read())
    return {"filename": file.filename}


@app.post("/parse_rag")
async def parse_rag(data: Dict):
    filename = data['filename']
    dir = "D:\\program_work\\RAGMix_KG-CKH\\test_file\\" + filename
    chunk = a(dir)
    rm_chunk("ckh", filename)
    addChunk(embd_mdl=ollama_embedding, chunk=chunk, knowledgebase_name="ckh")
    return {"chunk": chunk}


graph_documents_g = ""


def clear_database(tx):
    # 删除所有关系
    tx.run("MATCH ()-[r]->() DELETE r")
    # 删除所有节点
    tx.run("MATCH (n) DELETE n")


@app.post("/parse_kg")
async def parse_kg(data: Dict):
    driver = GraphDatabase.driver(uri=os.environ["NEO4J_URI"],
                                  database="neo4j",
                                  auth=(os.environ["NEO4J_USERNAME"],
                                        os.environ["NEO4J_PASSWORD"]))
    with driver.session() as session:
        session.write_transaction(clear_database)
    driver.close()
    filename = data['filename']
    dir = "D:\\program_work\\RAGMix_KG-CKH\\test_file\\" + filename
    chunk = a(dir)
    doc = []
    for i in chunk:
        doc.append(Document(page_content=i['content_with_weight']))
    graph_documents = make_kg.make_kg(llm=Tongyi(model="qwen-plus",
                                                 api_key="sk-b5883e47d69a417daae9f529e8e3ebf8",
                                                 temperature=0,
                                                 top_p=0.7), documents=doc)
    graph_db_t.add_graph_documents(
        graph_documents,
        baseEntityLabel=True,
        include_source=True
    )
    global graph_documents_g
    graph_documents_g = graph_documents
    return {"status": 200}


@app.post("/parse_kg_apply")
async def parse_rag(data: Dict):
    global graph_documents_g
    status = 100
    if graph_documents_g == "":
        status = 100
    else:
        graph_db.add_graph_documents(
            graph_documents_g,
            baseEntityLabel=True,
            include_source=True
        )
        status = 200
    return {"status": status}


@app.post("/del_doc")
async def del_doc(data: Dict):
    filename = data['filename']
    rm_chunk("ckh", filename)
    return {"status": 200}


@app.post("/rag")
async def rag(data: Dict):
    re = Retrieval()
    ref = re.run(query=data["ask"], embd_mdl=ollama_embedding, rerank_mdl=None,
                 similarity_threshold=data["similarity_threshold"],
                 keywords_similarity_weight=data['keywords_similarity_weight'],
                 top_n=data['top_n'],
                 top_k=data['top_k'],
                 empty_response="",
                 knowledgebase_name="ckh")
    ref_s = ""
    try:
        for i in range(len(ref["chunk_id"])):
            ref_s += str(i + 1) + "、文件名：{" + ref["docnm_kwd"][i] + "}\n内容：{" + ref["content_ltks"][i] + "}\n\n"
    except:
        ref_s = "未检索到相关文件"
    return {"rag": ref, "rag_s": ref_s}


log_config = uvicorn.config.LOGGING_CONFIG
log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
uvicorn.run(app, host="127.0.0.1", port=8090, log_config=log_config)
