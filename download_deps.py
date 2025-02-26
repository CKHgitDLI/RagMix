from huggingface_hub import snapshot_download
import nltk
import os
import urllib.request
from subprocess import call
from settings import get_project_base_directory

urls = [
    "http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2_amd64.deb",
]

repos = [
    "InfiniFlow/text_concat_xgb_v1.0",
    "InfiniFlow/deepdoc",
    "BAAI/bge-large-zh-v1.5",
    "BAAI/bge-reranker-v2-m3",
    "maidalun1020/bce-embedding-base_v1",
    "maidalun1020/bce-reranker-base_v1",
]

def download_model(repo_id):
    local_dir = os.path.abspath(os.path.join("huggingface.co", repo_id))
    os.makedirs(local_dir, exist_ok=True)
    snapshot_download(repo_id=repo_id, local_dir=local_dir)

def install_package(python_env, pack_path):
    """
    :param python_env: python 环境
    :param pack_path: requirements.txt 的路径
    :return: install failed package
    """
    result = set()
    with open(pack_path, "r",encoding="utf-16") as f:
        packs = f.readlines()
        print(packs)
    for pack in packs:
        print(pack)
        print("%s -m pip install %s" % (python_env, pack))
        if not pack:
            continue
        try:
            call("%s -m pip install %s" % (python_env, pack), shell=True)
        except Exception:
            result.add(pack)
    return result


if __name__ == "__main__":
    install_package(r"D:\CondaEnv\RagMix\python.exe", r"requirements.txt")

    # for url in urls:
    #     filename = url.split("/")[-1]
    #     print(f"Downloading {url}...")
    #     if not os.path.exists(filename):
    #         urllib.request.urlretrieve(url, filename)
    #
    # local_dir = os.path.abspath('nltk_data')
    # print(local_dir)
    # for data in ['wordnet', 'punkt', 'punkt_tab']:
    #     print(f"Downloading nltk {data}...")
    #     nltk.download(data)
    #
    # snapshot_download(repo_id="InfiniFlow/deepdoc",
    #                   local_dir=os.path.join(get_project_base_directory(), "res/deepdoc"),
    #                   local_dir_use_symlinks=False)
    #
    # for repo_id in repos:
    #     print(f"Downloading huggingface repo {repo_id}...")
    #     download_model(repo_id)
