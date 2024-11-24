from abc import ABC
import pandas as pd
from knowledgebase.link import retrievaler
from settings import DEBUG
from workflow_component.base import ComponentBase, ComponentParamBase


class RetrievalParam(ComponentParamBase):
    """
    Define the Retrieval component parameters.
    """

    def __init__(self, similarity_threshold, keywords_similarity_weight, top_n, top_k, empty_response):
        super().__init__()
        self.similarity_threshold = similarity_threshold
        self.keywords_similarity_weight = keywords_similarity_weight
        self.top_n = top_n
        self.top_k = top_k
        self.kb_ids = None
        self.empty_response = empty_response

    def check(self):
        self.check_decimal_float(self.similarity_threshold, "[Retrieval] Similarity threshold")
        self.check_decimal_float(self.keywords_similarity_weight, "[Retrieval] Keywords similarity weight")
        self.check_positive_number(self.top_n, "[Retrieval] Top N")


class Retrieval(ComponentBase, ABC):
    component_name = "Retrieval"

    def run(self, query, embd_mdl, rerank_mdl, similarity_threshold, keywords_similarity_weight, top_n, top_k,
            empty_response,  knowledgebase_name, **kwargs):
        self._param = RetrievalParam(similarity_threshold, keywords_similarity_weight, top_n, top_k, empty_response)
        kbinfos = retrievaler.retrieval(query, embd_mdl, knowledgebase_name,
                                        1, self._param.top_n,
                                        self._param.similarity_threshold, 1 - self._param.keywords_similarity_weight,
                                        aggs=False, rerank_mdl=rerank_mdl)
        if not kbinfos["chunks"]:
            df = Retrieval.be_output("")
            if self._param.empty_response and self._param.empty_response.strip():
                df["empty_response"] = self._param.empty_response
            return df
        df = pd.DataFrame(kbinfos["chunks"])
        df["content"] = df["content_with_weight"]
        del df["content_with_weight"]
        if DEBUG: print("检索结果为：\n\r", df)
        return df


if __name__ == '__main__':
    t = Retrieval()
    from model_link.OllamaEmbedding import OllamaEmbed

    ollama_embedding = OllamaEmbed(model_name="quentinz/bge-large-zh-v1.5", base_url="172.20.200.181:11434")
    d = t.run(query="校级领导每学期至少听课多少次", embd_mdl=ollama_embedding, rerank_mdl=None,
              similarity_threshold=0.2,
              keywords_similarity_weight=0.5, top_n=8, top_k=1024, empty_response="", knowledgebase_name="ckh")
    print(d)
