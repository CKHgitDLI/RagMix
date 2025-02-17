# 使用内置Laws解析方法
from parser_content import laws
from knowledgebase.insert import addChunk
from model_link.OllamaEmbedding import OllamaEmbed

ollama_embedding = OllamaEmbed(model_name="bge-m3", base_url="172.20.200.181:11434")  # embedding
a=laws.chunk


import os

# 指定要遍历的文件夹路径
folder_path = 'D:\program_work\三库资料'
files_docx=[]
files_temp=[]
# 使用os.walk遍历文件夹
for root, dirs, files in os.walk(folder_path):
    for file in files:
        # 获取文件的绝对路径
        file_path = os.path.join(root, file)
        print(file_path)
        files_temp.append(file_path)

for i in files_temp:
    if i.split(".")[-1]!="pdf":
        files_docx.append(i)

print(files_docx)

error=[]
for i in files_docx:
    print(i)
    try:
        chunk = a(i)
    except:
        print("无法解析："+i)
        error.append(i)
        continue
    print(chunk)
    addChunk(embd_mdl=ollama_embedding, chunk=chunk, knowledgebase_name="ckh")
print("无法解析的有："+error)