# 使用内置Laws解析方法
from parser_content import laws
from knowledgebase.insert import addChunk
from model_link.OllamaEmbedding import OllamaEmbed
from pdf2docx import parse
import os
import signal

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException()

def limit_time(seconds=10):
    def decorator(func):
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            except TimeoutException:
                return None
            finally:
                signal.alarm(0)
            return result
        return wrapper
    return decorator

ollama_embedding = OllamaEmbed(model_name="bge-m3", base_url="172.20.200.181:11434")  # embedding
a = laws.chunk

# 指定要遍历的文件夹路径
folder_path = 'E:\\三库资料2\\'
files_docx = []
files_temp = []
files_pdf = []
# 使用os.walk遍历文件夹
for root, dirs, files in os.walk(folder_path):
    for file in files:
        # 获取文件的绝对路径
        file_path = os.path.join(root, file)
        print(file_path)
        files_temp.append(file_path)

for i in files_temp:
    if i.split(".")[-1] != "pdf":
        files_docx.append(i)
    else:
        files_pdf.append(i)

for i in files_pdf:
    try:
        print(i)
        parse(i, new_file=os.path.join(os.path.dirname(i), os.path.basename(i)[0] + '.docx'))  # 新的文件名
        os.remove(i)
    except:
        continue



# 指定要遍历的文件夹路径
folder_path = 'E:\\三库资料2\\'
files_docx = []
files_temp = []
files_pdf = []
# 使用os.walk遍历文件夹
for root, dirs, files in os.walk(folder_path):
    for file in files:
        # 获取文件的绝对路径
        file_path = os.path.join(root, file)
        print(file_path)
        files_temp.append(file_path)

for i in files_temp:
    if i.split(".")[-1] != "pdf":
        files_docx.append(i)
    else:
        files_pdf.append(i)
error = []
for i in files_docx:
    print(i)
    try:
        chunk = a(i)
    except:
        print("无法解析：" + i)
        error.append(i)
        continue
    print(chunk)
    addChunk(embd_mdl=ollama_embedding, chunk=chunk, knowledgebase_name="ckh2")
print("无法解析的有：")
print(error)
