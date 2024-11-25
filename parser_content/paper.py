import copy
import re
import os
from nlp import rag_tokenizer, tokenize, tokenize_table, add_positions, bullets_category, title_frequency, \
    tokenize_chunks
from parser_file.ragflow_pdf import RAGFlowPdfParser, PlainParser
import numpy as np


class Pdf(RAGFlowPdfParser):
    def __init__(self):
        self.model_speciess = "paper"
        super().__init__()

    def __call__(self, filename, binary=None, from_page=0,
                 to_page=100000, zoomin=3, callback=print):
        print("OCR开始")
        self.__images__(
            filename if not binary else binary,
            zoomin,
            from_page,
            to_page,
            callback
        )
        print("OCR结束")

        from timeit import default_timer as timer
        start = timer()
        self._layouts_rec(zoomin)
        print("布局解析结束")
        print("布局:", timer() - start)
        self._table_transformer_job(zoomin)
        print("表格分析结束")
        self._text_merge()
        tbls = self._extract_table_figure(True, zoomin, True, True)
        column_width = np.median([b["x1"] - b["x0"] for b in self.boxes])
        self._concat_downward()
        self._filter_forpages()
        print("文本融合结束")

        # clean mess
        if column_width < self.page_images[0].size[0] / zoomin / 2:
            print("two_column...................", column_width,
                  self.page_images[0].size[0] / zoomin / 2)
            self.boxes = self.sort_X_by_page(self.boxes, column_width / 2)
        for b in self.boxes:
            b["text"] = re.sub(r"([\t 　]|\u3000){2,}", " ", b["text"].strip())

        def _begin(txt):
            return re.match(
                "[0-9. 一、i]*(introduction|abstract|摘要|引言|keywords|key words|关键词|background|背景|目录|前言|contents)",
                txt.lower().strip())

        if from_page > 0:
            return {
                "title": "",
                "authors": "",
                "abstract": "",
                "sections": [(b["text"] + self._line_tag(b, zoomin), b.get("layoutno", "")) for b in self.boxes if
                             re.match(r"(text|title)", b.get("layoutno", "text"))],
                "tables": tbls
            }
        # get title and authors
        title = ""
        authors = []
        i = 0
        while i < min(32, len(self.boxes) - 1):
            b = self.boxes[i]
            i += 1
            if b.get("layoutno", "").find("title") >= 0:
                title = b["text"]
                if _begin(title):
                    title = ""
                    break
                for j in range(3):
                    if _begin(self.boxes[i + j]["text"]):
                        break
                    authors.append(self.boxes[i + j]["text"])
                    break
                break
        # get abstract
        abstr = ""
        i = 0
        while i + 1 < min(32, len(self.boxes)):
            b = self.boxes[i]
            i += 1
            txt = b["text"].lower().strip()
            if re.match("(abstract|摘要)", txt):
                if len(txt.split(" ")) > 32 or len(txt) > 64:
                    abstr = txt + self._line_tag(b, zoomin)
                    break
                txt = self.boxes[i]["text"].lower().strip()
                if len(txt.split(" ")) > 32 or len(txt) > 64:
                    abstr = txt + self._line_tag(self.boxes[i], zoomin)
                i += 1
                break
        if not abstr:
            i = 0

        print(
            0.8, "Page {}~{}: Text merging finished".format(
                from_page, min(
                    to_page, self.total_page)))
        for b in self.boxes:
            print(b["text"], b.get("layoutno"))
        print(tbls)

        return {
            "title": title,
            "authors": " ".join(authors),
            "abstract": abstr,
            "sections": [(b["text"] + self._line_tag(b, zoomin), b.get("layoutno", "")) for b in self.boxes[i:] if
                         re.match(r"(text|title)", b.get("layoutno", "text"))],
            "tables": tbls
        }


def chunk(filename, binary=None, from_page=0, to_page=100000,
          lang="Chinese", callback=None, **kwargs):
    """
        Only pdf is supported.
        The abstract of the paper will be sliced as an entire chunk, and will not be sliced partly.
    """
    if re.search(r"\.pdf$", filename, re.IGNORECASE):
        if not kwargs.get("parser_config", {}).get("layout_recognize", True):
            pdf_parser = PlainParser()
            paper = {
                "title": os.path.split(filename)[-1],
                "authors": " ",
                "abstract": "",
                "sections": pdf_parser(filename if not binary else binary, from_page=from_page, to_page=to_page)[0],
                "tables": []
            }
        else:
            pdf_parser = Pdf()
            paper = pdf_parser(filename if not binary else binary,
                               from_page=from_page, to_page=to_page, callback=callback)
    else:
        raise NotImplementedError("file type not supported yet(pdf supported)")

    doc = {"docnm_kwd": os.path.split(filename)[-1], "authors_tks": rag_tokenizer.tokenize(paper["authors"]),
           "title_tks": rag_tokenizer.tokenize(paper["title"] if paper["title"] else filename)}
    doc["title_sm_tks"] = rag_tokenizer.fine_grained_tokenize(doc["title_tks"])
    doc["authors_sm_tks"] = rag_tokenizer.fine_grained_tokenize(doc["authors_tks"])
    # is it English
    eng = lang.lower() == "english"  # pdf_parser.is_english
    print("It's English.....", eng)

    res = tokenize_table(paper["tables"], doc, eng)

    if paper["abstract"]:
        d = copy.deepcopy(doc)
        txt = pdf_parser.remove_tag(paper["abstract"])
        d["important_kwd"] = ["abstract", "总结", "概括", "summary", "summarize"]
        d["important_tks"] = " ".join(d["important_kwd"])
        d["image"], poss = pdf_parser.crop(
            paper["abstract"], need_position=True)
        add_positions(d, poss)
        tokenize(d, txt, eng)
        res.append(d)

    sorted_sections = paper["sections"]
    # set pivot using the most frequent type of title,
    # then merge between 2 pivot
    bull = bullets_category([txt for txt, _ in sorted_sections])
    most_level, levels = title_frequency(bull, sorted_sections)
    assert len(sorted_sections) == len(levels)
    sec_ids = []
    sid = 0
    for i, lvl in enumerate(levels):
        if lvl <= most_level and i > 0 and lvl != levels[i - 1]:
            sid += 1
        sec_ids.append(sid)
        print(lvl, sorted_sections[i][0], most_level, sid)

    chunks = []
    last_sid = -2
    for (txt, _), sec_id in zip(sorted_sections, sec_ids):
        if sec_id == last_sid:
            if chunks:
                chunks[-1] += "\n" + txt
                continue
        chunks.append(txt)
        last_sid = sec_id
    res.extend(tokenize_chunks(chunks, doc, eng, pdf_parser))
    return res


if __name__ == "__main__":
    print(chunk(r"E:\Rag-CKH\test_file\构造煤变形能及在煤与瓦斯突出中的作用_程远平.pdf"))
