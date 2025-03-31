from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from langchain_community.embeddings import DashScopeEmbeddings
from langchain.graphs import Neo4jGraph
from knowledge_graph import make_kg
from knowledge_graph.kag import full_retriever

load_dotenv()
os.environ["DASHSCOPE_API_KEY"] = "sk-b5883e47d69a417daae9f529e8e3ebf8"
url = "bolt://localhost:7687"
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "1609936983"
os.environ["NEO4J_DATABASE"] = "ckh"

llm = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus",
    temperature=0
)

embeddings = DashScopeEmbeddings(
    model="text-embedding-v3",
)

graph_db = Neo4jGraph(
    url=os.environ["NEO4J_URI"],
    username=os.environ["NEO4J_USERNAME"],
    password=os.environ["NEO4J_PASSWORD"],
    database=os.environ["NEO4J_DATABASE"]
)

doc = make_kg.read_doc_for_kg(file_path="text.txt")

graph_documents = make_kg.make_kg(llm=llm, documents=doc)

graph_db.add_graph_documents(
    graph_documents,
    baseEntityLabel=True,
    include_source=True
)

template = """
仅根据下列上下文回答问题:
{context}

Question: {question}
使用自然语言，简洁明了.
"""
prompt = ChatPromptTemplate.from_template(template)

chain = ({"context": full_retriever, "question": RunnablePassthrough(), }
         | prompt
         | llm
         | StrOutputParser()
         )

chain.invoke(input="中国高净值")

make_kg.showGraph()
