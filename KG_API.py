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
from langchain.graphs import Neo4jGraph
from knowledge_graph import make_kg
from knowledge_graph.kag import full_retriever, graph_retriever
from langchain.embeddings import OllamaEmbeddings

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


log_config = uvicorn.config.LOGGING_CONFIG
log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
uvicorn.run(app, host="127.0.0.1", port=8090, log_config=log_config)
