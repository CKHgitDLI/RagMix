import io
import numpy as np
from PIL import Image
from nlp import tokenize
from parser_file.vision import OCR
import os
from model_link.OllamaChat import OllamaChat

ocr = OCR()


def chunk(filename, cv_mdl, lang="chinese", **kwargs):
    img = Image.open(filename).convert('RGB')
    doc = {
        "docnm_kwd": os.path.split(filename)[-1],
        "image": img
    }
    bxs = ocr(np.array(img))
    txt = "\n".join([t[0] for _, t in bxs if t[0]])
    eng = lang.lower() == "english"
    print("OCR结束:%s" % txt)
    if (eng and len(txt.split(" ")) > 32) or len(txt) > 32:
        tokenize(doc, txt, eng)
        print("OCR结果太长，不能使用CV LLM。")
        return [doc]
    try:
        print("使用LLM描述图片")
        ans, _ = cv_mdl.describe(filename)
        print("LLM解释: %s" % ans)
        txt += "\n" + ans
        tokenize(doc, txt, eng)
        return [doc]
    except Exception as e:
        print(e)
    return []


if __name__ == '__main__':
    print(chunk(r"E:\Rag-CKH\test_file\1.png",
                cv_mdl=OllamaChat(model_name="llama3.2-vision", base_url="172.20.200.181:11434")))
