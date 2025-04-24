from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
import json
from langchain_community.graphs import Neo4jGraph
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.graph_transformers import LLMGraphTransformer
from neo4j import GraphDatabase
# from yfiles_jupyter_graphs import GraphWidget
from langchain_community.vectorstores import Neo4jVector
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars


def read_doc_for_kg(file_path, encoding="gbk", chunk_size=90, chunk_overlap=10):
    loader = TextLoader(file_path=file_path, encoding=encoding)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    documents = text_splitter.split_documents(documents=docs)
    print("文档的分块数量为：%d" % (len(documents)))
    return documents


def chunks_for_kg(chunks):
    pass


def make_kg(llm, documents):
    llm_transformer = LLMGraphTransformer(llm=llm)
    graph_documents = llm_transformer.convert_to_graph_documents(documents)
    print("共创建了%d个知识图谱" % (len(graph_documents)))
    return graph_documents

# def showGraph():
#     driver = GraphDatabase.driver(
#         uri=os.environ["NEO4J_URI"],
#         auth=(os.environ["NEO4J_USERNAME"],
#               os.environ["NEO4J_PASSWORD"]))
#     session = driver.session()
#     widget = GraphWidget(graph=session.run("MATCH (s)-[r:!MENTIONS]->(t) RETURN s,r,t").graph())
#     widget.node_label_mapping = 'id'
#     return widget
