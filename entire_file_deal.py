import os
from docx import Document
import re
import settings

def extract_text_from_docx(file_path):
    if re.search(r"\.doc$", file_path, re.IGNORECASE):
        print("正在转换为docx，临时文件在解析后将被自动清理")
        filename = settings.convert_doc_to_docx(file_path)
        file_path = os.path.join(settings.get_project_base_directory(), filename)
    # 加载Word文档
    doc = Document(file_path)
    # 提取所有段落中的文字
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    # 提取所有表格中的文字
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                full_text.append(cell.text)
    # 合并所有文本为一个字符串，可以根据需要添加分隔符
    return '\n'.join(full_text)

def search_files(directory, keyword):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if keyword.lower() in file.lower():
                print(os.path.join(root, file))
                return os.path.join(root, file)

def remove_blank_lines(text):
    return re.sub(r'\n\s*\n', '\n', text)

def entire_file(filename):
    temp=search_files('D:\program_work\三库资料',filename)
    text = extract_text_from_docx(temp)
    print(remove_blank_lines(text))
    return "文件名：{"+filename+"}\n\n内容：{"+remove_blank_lines(text)+"}\n\n\n\n"

if __name__ == '__main__':
    entire_file("6月24号梨园河煤矿21105局扇风机双电源真空电磁启动器抢修分析报告")