from knowledgebase.link import ELASTICSEARCH
from elasticsearch_dsl import Q
from knowledgebase.link import retrievaler


def rm_chunk(knowledgebase_name, title):
    query = {
        "docnm_kwd": title, "page": 1, "size": 1024, "question": "", "sort": True}
    sres = retrievaler.search(query, knowledgebase_name, highlight=True)
    if not ELASTICSEARCH.deleteByQuery(
            Q("ids", values=sres.ids), knowledgebase_name):
        return False
    deleted_chunk_ids = sres.ids
    chunk_number = len(deleted_chunk_ids)
    return chunk_number


if __name__ == '__main__':
    rm_chunk("ckh", "2022版煤矿安全规程.docx")
