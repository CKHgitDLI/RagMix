import uuid
from elasticsearch_dsl import Q
from nlp import search
from es_conn import ELASTICSEARCH
import hashlib
import pathlib
import re
from strenum import StrEnum
from io import BytesIO
from PIL import Image
import pdfplumber

def get_uuid():
    return uuid.uuid1().hex

def duplicate_name(query_func, **kwargs):
    fnm = kwargs["name"]
    objs = query_func(**kwargs)
    if not objs: return fnm
    ext = pathlib.Path(fnm).suffix #.jpg
    nm = re.sub(r"%s$"%ext, "", fnm)
    r = re.search(r"\(([0-9]+)\)$", nm)
    c = 0
    if r:
        c = int(r.group(1))
        nm = re.sub(r"\([0-9]+\)$", "", nm)
    c += 1
    nm = f"{nm}({c})"
    if ext: nm += f"{ext}"

    kwargs["name"] = nm
    return duplicate_name(query_func, **kwargs)

class FileType(StrEnum):
    PDF = 'pdf'
    DOC = 'doc'
    VISUAL = 'visual'
    AURAL = 'aural'
    VIRTUAL = 'virtual'
    FOLDER = 'folder'
    OTHER = "other"

def filename_type(filename):
    filename = filename.lower()
    if re.match(r".*\.pdf$", filename):
        return FileType.PDF.value

    if re.match(
             r".*\.(eml|doc|docx|ppt|pptx|yml|xml|htm|json|csv|txt|ini|xls|xlsx|wps|rtf|hlp|pages|numbers|key|md|py|js|java|c|cpp|h|php|go|ts|sh|cs|kt|html|sql)$", filename):
        return FileType.DOC.value

    if re.match(
            r".*\.(wav|flac|ape|alac|wavpack|wv|mp3|aac|ogg|vorbis|opus|mp3)$", filename):
        return FileType.AURAL.value

    if re.match(r".*\.(jpg|jpeg|png|tif|gif|pcx|tga|exif|fpx|svg|psd|cdr|pcd|dxf|ufo|eps|ai|raw|WMF|webp|avif|apng|icon|ico|mpg|mpeg|avi|rm|rmvb|mov|wmv|asf|dat|asx|wvx|mpe|mpa|mp4)$", filename):
        return FileType.VISUAL.value

    return FileType.OTHER.value

def thumbnail_img(filename, blob):
    filename = filename.lower()
    if re.match(r".*\.pdf$", filename):
        pdf = pdfplumber.open(BytesIO(blob))
        buffered = BytesIO()
        pdf.pages[0].to_image(resolution=32).annotated.save(buffered, format="png")
        return buffered.getvalue()

    if re.match(r".*\.(jpg|jpeg|png|tif|gif|icon|ico|webp)$", filename):
        image = Image.open(BytesIO(blob))
        image.thumbnail((30, 30))
        buffered = BytesIO()
        image.save(buffered, format="png")
        return buffered.getvalue()

    if re.match(r".*\.(ppt|pptx)$", filename):
        import aspose.slides as slides
        import aspose.pydrawing as drawing
        try:
            with slides.Presentation(BytesIO(blob)) as presentation:
                buffered = BytesIO()
                presentation.slides[0].get_thumbnail(0.03, 0.03).save(
                    buffered, drawing.imaging.ImageFormat.png)
                return buffered.getvalue()
        except Exception as e:
            pass
    return None

def parsePDF(tenant_id="4d30c534914e11ef90c40242ac120006",id="473b17f3953411ef89270242ac120005"):
    ELASTICSEARCH.deleteByQuery(
        Q("match", doc_id=id), idxnm=search.index_name(tenant_id))

if __name__ == '__main__':
    print(search.index_name("4d30c534914e11ef90c40242ac120006"))
