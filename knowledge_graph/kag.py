from langchain_community.vectorstores import Neo4jVector

def remove_lucene_chars(input: str) -> str:
    # 这里可以实现去除 Lucene 特殊字符的逻辑
    return input  # 示例中直接返回输入

def prompt_query(query, llm):
    prompt = (
        "任务：query特征提取,只要输出词语，不要输出任何其他信息。\n"
        "例子：\n"
        "输入：小红和小丽都是谁呀？\n"
        "输出：小红，小丽\n"
        "输入：我不管我要吃巧克力和香蕉\n"
        "输出：巧克力，香蕉\n"
        "输入：巴黎奥运金牌第一名\n"
        "输出：巴黎奥运会，金牌\n"
        "按照上述事实回答问题:\n"
        f"输入：{query}\n"
        "输出："
    )
    response = llm.invoke(prompt).split("，")
    print(response)
    return response
    # response_list = [response.strip()] if response else []
    # print(response_list)
    # return ','.join(response) if isinstance(response, list) else response.strip()

def generate_full_text_query(input: str) -> str:
    words = [el for el in remove_lucene_chars(input).split() if el]
    if not words:
        return ""
    full_text_query = " AND ".join([f"{word}" for word in words])
    print(f"Generated Query: {full_text_query}")
    return full_text_query.strip()


def graph_retriever(question: str, graph_db, llm) -> str:
    """
    Collects the neighborhood of entities mentioned
    in the question
    """
    result = ""
    graph_db.query(
        "CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id]")
    # prompt_query提取特征实体
    entities = prompt_query(question, llm=llm)
    print(entities)
    for entity in entities:
        response = graph_db.query(
            """CALL db.index.fulltext.queryNodes('entity', $query)
            YIELD node,score
            CALL {
              WITH node
              MATCH (node)-[r:!MENTIONS]->(neighbor)
              RETURN node.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
              UNION ALL
              WITH node
              MATCH (node)<-[r:!MENTIONS]-(neighbor)
              RETURN neighbor.id + ' - ' + type(r) + ' -> ' +  node.id AS output
            }
            RETURN output
            """,
            {"query": generate_full_text_query(entity)},
        )
        result += "\n".join([el['output'] for el in response])
    return result


def full_retriever(question: str, llm, embeddings, graph_db):
    vector_index = Neo4jVector.from_existing_graph(
        embeddings,
        search_type="hybrid",
        node_label="Document",
        text_node_properties=["text"],
        embedding_node_property="embedding"
    )
    vector_retriever = vector_index.as_retriever()
    graph_data = graph_retriever(question, graph_db=graph_db, llm=llm)
    vector_data = [el.page_content for el in vector_retriever.invoke(question)]
    final_data = f"""Graph data:
{graph_data}
vector data:
{"#Document ".join(vector_data)}
    """
    print(final_data)
    return graph_data, vector_data
