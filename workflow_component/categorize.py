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
from abc import ABC
from workflow_component.generate import GenerateParam
from settings import DEBUG


class CategorizeParam(GenerateParam):

    """
    Define the Categorize component parameters.
    """
    def __init__(self,category_description):
        super().__init__()
        self.category_description = category_description
        self.prompt = ""

    def check(self):
        super().check()
        self.check_empty(self.category_description, "[Categorize] Category examples")
        for k, v in self.category_description.items():
            if not k: raise ValueError(f"[Categorize] Category name can not be empty!")
            if not v.get("to"): raise ValueError(f"[Categorize] 'To' of category {k} can not be empty!")

    def get_prompt(self):
        cate_lines = []
        for c, desc in self.category_description.items():
            for l in desc.get("examples", "").split("\n"):
                if not l: continue
                cate_lines.append("Question: {}\tCategory: {}".format(l, c))
        descriptions = []
        for c, desc in self.category_description.items():
            if desc.get("description"):
                descriptions.append(
                    "--------------------\nCategory: {}\nDescription: {}\n".format(c, desc["description"]))

        self.prompt = """
        You're a text classifier. You need to categorize the user’s questions into {} categories, 
        namely: {}
        Here's description of each category:
        {}

        You could learn from the following examples:
        {}
        You could learn from the above examples.
        Just mention the category names, no need for any additional words.
        """.format(
            len(self.category_description.keys()),
            "/".join(list(self.category_description.keys())),
            "\n".join(descriptions),
            "- ".join(cate_lines)
        )
        return self.prompt


class Categorize(ABC):
    component_name = "Categorize"

    def run(self, ask, chat_mdl, category_description):
        """
        问题分类
        @param ask: 用户问题字符串
        @param chat_mdl: Chat模型对象
        @param category_description: 统一格式字典
        @return: 字符串，问题类型
        """
        self._param = CategorizeParam(category_description)
        input = "Question: " + ask + "\tCategory: "
        if DEBUG:print("问题分类提示词",self._param.get_prompt())
        ans,_ = chat_mdl.chat(self._param.get_prompt(), [{"role": "user", "content": input}],
                            self._param.gen_conf())
        print("问题分类：",ans)

        return ans


