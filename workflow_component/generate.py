#
#  Copyright 2024 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import re
from functools import partial
import pandas as pd
from litellm import max_tokens
from sympy.physics.units import temperature

from knowledgebase.link import retrievaler
from workflow_component.base import ComponentBase, ComponentParamBase


class GenerateParam(ComponentParamBase):
    """
    Define the Generate component parameters.
    """

    def __init__(self,max_tokens=512, temperature=0.50, top_p=0.50, presence_penalty=0.40, frequency_penalty=0.70):
        super().__init__()
        self.llm_id = ""
        self.prompt = ""
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty

    def check(self):
        self.check_decimal_float(self.temperature, "[Generate] Temperature")
        self.check_decimal_float(self.presence_penalty, "[Generate] Presence penalty")
        self.check_decimal_float(self.frequency_penalty, "[Generate] Frequency penalty")
        self.check_nonnegative_number(self.max_tokens, "[Generate] Max tokens")
        self.check_decimal_float(self.top_p, "[Generate] Top P")
        self.check_empty(self.llm_id, "[Generate] LLM")

    def gen_conf(self):
        conf = {}
        if self.max_tokens > 0: conf["max_tokens"] = self.max_tokens
        if self.temperature > 0: conf["temperature"] = self.temperature
        if self.top_p > 0: conf["top_p"] = self.top_p
        if self.presence_penalty > 0: conf["presence_penalty"] = self.presence_penalty
        if self.frequency_penalty > 0: conf["frequency_penalty"] = self.frequency_penalty
        return conf


class Generate(ComponentBase):
    component_name = "Generate"

    def set_cite(self, retrieval_res, answer, embd_mdl):
        retrieval_res = retrieval_res.dropna(subset=["vector", "content_ltks"]).reset_index(drop=True)
        if "empty_response" in retrieval_res.columns:
            retrieval_res["empty_response"].fillna("", inplace=True)
        answer, idx = retrievaler.insert_citations(answer, [ck["content_ltks"] for _, ck in retrieval_res.iterrows()],
                                                   [ck["vector"] for _, ck in retrieval_res.iterrows()],
                                                   embd_mdl, tkweight=0.7,
                                                   vtweight=0.3)
        doc_ids = set([])
        recall_docs = []
        for i in idx:
            did = retrieval_res.loc[int(i), "docnm_kwd"]
            if did in doc_ids: continue
            doc_ids.add(did)
            recall_docs.append({"doc_name": retrieval_res.loc[int(i), "docnm_kwd"]})

        del retrieval_res["vector"]
        del retrieval_res["content_ltks"]

        reference = {
            "chunks": [ck.to_dict() for _, ck in retrieval_res.iterrows()],
            "doc_aggs": recall_docs
        }

        res = {"content": answer, "reference": reference}

        return res

    def stream_output(self, history, chat_mdl, retrieval_res, embd_mdl, prompt, max_tokens=512, temperature=0.50, top_p=0.50, presence_penalty=0.40, frequency_penalty=0.70,cite=False, **kwargs):
        self._param=GenerateParam(max_tokens, temperature, top_p, presence_penalty, frequency_penalty)
        for n, v in kwargs.items():
            prompt = re.sub(r"\{%s\}" % re.escape(n), re.escape(str(v)), prompt)

        msg = [{"role": "system", "content": prompt}, *history]
        answer = ""
        for ans in chat_mdl.chat_streamly(msg[0]["content"], msg[1:], self._param.gen_conf()):
            res = {"content": ans, "reference": []}
            answer = ans
            yield res

        if cite:
            res = self.set_cite(retrieval_res, answer, embd_mdl=embd_mdl)
            yield res


if __name__ == '__main__':
    from workflow_component.jiansuo import Retrieval

    a = Retrieval()
    from model_link.OllamaEmbedding import OllamaEmbed

    ollama_embedding = OllamaEmbed(model_name="bge-m3", base_url="172.20.200.181:11434")
    d = a.run(query="介绍一下单体液压支柱", embd_mdl=ollama_embedding, rerank_mdl=None,
              similarity_threshold=0.2,
              keywords_similarity_weight=0.5, top_n=8, top_k=1024, empty_response="",
              knowledgebase_name="ragflow_4d30c534914e11ef90c40242ac120006")
    t = Generate()
    from model_link.OllamaChat import OllamaChat

    ollama_chat = OllamaChat(model_name="qwen2.5:32b", base_url="172.20.200.181:11434")
    for temp in t.stream_output(history=[{"role": "user", "content": "介绍一下单体液压支柱"}], chat_mdl=ollama_chat,
                                retrieval_res=d,
                                embd_mdl=ollama_embedding,
                                prompt="\u4f60\u662f\u7164\u77ff\u5b89\u5168\u5458\uff0c\u4f60\u53ea\u80fd\u4f9d\u636e\u540e\u6587\u7ed9\u4f60\u7684\u53c2\u8003\u6587\u672c\u6750\u6599\u56de\u7b54\u7528\u6237\u95ee\u9898\uff0c\u4e0d\u80fd\u4f7f\u7528\u81ea\u5df1\u7684\u77e5\u8bc6\uff0c\u4e25\u683c\u6309\u7167\u8981\u6c42\u4f5c\u7b54\u3002\n\u4f60\u7684\u5de5\u4f5c\u662f\u6839\u636e\u53c2\u8003\u6587\u672c\u6750\u6599\u7684\u5185\u5bb9\u4ee5\u53ca\u6587\u672c\u6750\u6599\u7684\u6587\u4ef6\u540d\u79f0\uff0c\u4e00\u6b65\u4e00\u6b65\u5730\u601d\u8003\uff0c\u6309\u7167\u4ee5\u4e0b\u6b65\u9aa4\u548c\u8981\u6c42\u5b8c\u6210\u4efb\u52a1\u3002\n\u8bf7\u8bb0\u4f4f\uff1a\u601d\u8003\u8fc7\u7a0b\u5e94\u8be5\u662f\u539f\u59cb\u7684\u3001\u6709\u673a\u7684\u548c\u81ea\u7136\u7684\uff0c\u6355\u6349\u771f\u5b9e\u7684\u4eba\u7c7b\u601d\u7ef4\u6d41\u7a0b\uff0c\u800c\u4e0d\u662f\u9075\u5faa\u7ed3\u6784\u5316\u7684\u683c\u5f0f\uff1b\u8fd9\u610f\u5473\u7740\uff0c\u4f60\u7684\u601d\u7ef4\u5e94\u8be5\u66f4\u50cf\u662f\u4e00\u4e2a\u610f\u8bc6\u6d41\u3002\n\n\u4ee5\u4e0b\u662f\u601d\u8003\u8fc7\u7a0b\uff1a\n1\u3001\u9996\u5148\u9ed8\u8ba4\u7528\u6237\u7684\u6240\u6709\u95ee\u9898\u90fd\u662f\u5728\u8be2\u95ee\u53c2\u8003\u6587\u672c\u6750\u6599\u4e2d\u7684\u76f8\u5173\u89c4\u5b9a\uff0c\u4e0d\u80fd\u7528\u5176\u5b83\u77e5\u8bc6\u8fdb\u884c\u4f5c\u7b54\u3002\n2\u3001\u7136\u540e\u9488\u5bf9\u7528\u6237\u63d0\u51fa\u7684\u95ee\u9898\u627e\u5230\u53c2\u8003\u6587\u672c\u6750\u6599\u4e2d\u7684\u4f9d\u636e\uff0c\u6ce8\u610f\u4e13\u4e1a\u540d\u8bcd\u7684\u51c6\u786e\u6027\uff0c\u5982\u679c\u6709\u591a\u4e2a\u76f8\u5173\u7684\u4f9d\u636e\uff0c\u8bf7\u5206\u522b\u4f5c\u7b54\u3002\n3\u3001\u7136\u540e\u8bf7\u7528\u627e\u5230\u7684\u4f9d\u636e\u539f\u6587\u4f5c\u4e3a\u4f9d\u636e\uff0c\u5f00\u59cb\u89e3\u7b54\u7528\u6237\u95ee\u9898\u7684\u7b54\u6848\uff0c\u56de\u7b54\u65f6\u5408\u7406\u5206\u6bb5\uff0c\u627e\u5230\u7684\u6bcf\u4e2a\u76f8\u5173\u4f9d\u636e\u4f7f\u7528\u4ee5\u4e0b\u683c\u5f0f\uff1a\"\u6587\u4ef6\u89c4\u5b9a\uff1aXXX\u3002\u56e0\u6b64XXX\uff08\u8be6\u7ec6\u89e3\u7b54\u7528\u6237\u95ee\u9898\uff09\u3002\"\n4\u3001\u7136\u540e\u731c\u6d4b\u4e09\u4e2a\u7528\u6237\u63a5\u4e0b\u6765\u60f3\u95ee\u7684\u95ee\u9898\uff0c\u5206\u6bb5\u6362\u884c\u56de\u7b54\uff0c\u4f7f\u7528\u4ee5\u4e0b\u683c\u5f0f\uff1a\"\u5982\u679c\u56de\u7b54\u4e0d\u591f\u51c6\u786e\u6216\u68c0\u7d22\u7684\u6587\u4ef6\u4e0d\u6b63\u786e\uff0c\u731c\u6d4b\u60a8\u53ef\u80fd\u60f3\u8ffd\u95ee\u7684\u95ee\u9898\u6709\uff1a1.XXX?\"\n5\u3001\u6700\u540e\u6362\u884c\u8f93\u51fa\u4ee5\u4e0b\u7ed3\u675f\u8bed\uff1a\"\u897f\u5b89\u79d1\u6280\u5927\u5b66\u667a\u80fd\u7cfb\u7edf\u5b89\u5168\u4e0e\u63a7\u5236\u7814\u7a76\u6240\u53d1\u5e03\u3002\u9c81ICP\u59072023026495\u53f7\uff08\u4ec5\u7528\u4e8e\u4e2a\u4eba\u5f00\u53d1\uff09\"\n\n\u4ee5\u4e0b\u662f\u53c2\u8003\u6587\u672c\u6750\u6599\n{input}"):
        print(temp)
