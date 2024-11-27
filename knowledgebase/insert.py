from knowledgebase.link import ELASTICSEARCH
from knowledgebase.server import get_uuid

def embedding(embd_mdl, cnts, batch_size=16):
    chunk_counts=0
    token_counts=0
    vects = []
    for i in range(0, len(cnts), batch_size):
        vts, c = embd_mdl.encode(cnts[i: i + batch_size])
        vects.extend(vts.tolist())
        chunk_counts += len(cnts[i:i + batch_size])
        token_counts += c
    return vects,chunk_counts,token_counts

def addChunk(embd_mdl,chunk,knowledgebase_name,batch_size=128):
    """
    将Chunk（统一格式）添加到知识库中
    @param embd_mdl: Embedding模型
    @param chunk: 统一格式Chunk
    @param knowledgebase_name: 知识库名
    @param batch_size: 批量处理量
    @return: 
    """
    vects,_,_ = embedding(embd_mdl, [c["content_with_weight"] for c in chunk],batch_size)
    for i, d in enumerate(chunk):
        v = vects[i]
        d["q_%d_vec" % len(v)] = v
        d["id"]=get_uuid()
    es_bulk_size = 64
    for b in range(0, len(chunk), es_bulk_size):
        ELASTICSEARCH.bulk(chunk[b:b + es_bulk_size], idx_nm=knowledgebase_name)

if __name__ == '__main__':
    from model_link.OllamaEmbedding import OllamaEmbed
    ollama_embedding = OllamaEmbed(model_name="quentinz/bge-large-zh-v1.5", base_url="172.20.200.181:11434")
    from parser_content import laws
    a=laws.chunk
    chunk=a("D:\\Rag-CKH\\关于印发《西安科技大学听课制度（修订）》的通知.docx")
    addChunk(embd_mdl=ollama_embedding,chunk=chunk)
    # doc_parse(kb="111",embd_mdl=ollama_embedding)
