"""Utilitários para escrever seções no relatório (.docx) mantendo a formatação do documento.

A formatação é clonada de parágrafos já existentes no próprio relatório (título de seção,
subtítulo numerado, corpo de texto, figura, legenda e fonte), de modo que o texto inserido
fica idêntico ao restante do documento. Equações são escritas em LaTeX e convertidas para
equações nativas do Word (OMML) via MathML, usando o XSLT MML2OMML.XSL do Microsoft Office.

Marcações aceitas no texto corrido:
- $...$   -> equação em linha (LaTeX)
- *...*   -> itálico (termos em língua estrangeira)
- 4.X, 3.XX, (4.X.1) etc. -> marcadores provisórios de numeração, destacados em amarelo
"""

from __future__ import annotations

import copy
import re
import shutil
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence

import docx
import latex2mathml.converter
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm
from lxml import etree

MML2OMML_XSL = Path(r"C:/Program Files/Microsoft Office/root/Office16/MML2OMML.XSL")
_XSLT = etree.XSLT(etree.parse(str(MML2OMML_XSL)))

PLACEHOLDER_RE = re.compile(r"(\(?\d\.X+(?:\.\d+)?\)?)")
TEXT_WIDTH_TWIPS = 9085  # 21 cm - 3 cm - 2 cm = 16 cm


def backup(doc_path: Path) -> Path:
    """Copia o relatório para a pasta old/ com carimbo de data e hora."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = doc_path.parent / "old" / f"{doc_path.stem}_backup_{stamp}{doc_path.suffix}"
    dest.parent.mkdir(exist_ok=True)
    shutil.copy2(doc_path, dest)
    return dest


def latex_to_omml(latex: str) -> etree._Element:
    """Converte uma expressão LaTeX em um elemento <m:oMath> do Word."""
    mathml = latex2mathml.converter.convert(latex)
    omml = _XSLT(etree.fromstring(mathml)).getroot()
    if omml.tag != qn("m:oMath"):
        found = omml.find(".//" + qn("m:oMath"))
        omml = found if found is not None else omml
    # Integrais/somatórios sem corpo aparecem no Word como caixas vazias: o integrando
    # precisa estar agrupado entre chaves no LaTeX, p. ex. \int_{0}^{t}{\nu(\tau)\,d\tau}
    for e in omml.iter(qn("m:e")):
        if e.getparent().tag == qn("m:nary") and len(e) == 0:
            raise ValueError(f"Operador n-ário sem argumento (agrupe o integrando com {{}}): {latex}")
    return copy.deepcopy(omml)


def _norm(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().upper()


def _chave_ref(text: str) -> str:
    """Chave de ordenação ABNT: autoria, depois ano (mesmos autores em ordem cronológica), depois o resto."""
    anos = re.findall(r"\b(?:19|20)\d{2}\b", text)
    return _norm(text.split(".")[0][:25]) + "|" + (anos[-1] if anos else "") + "|" + _norm(text)


class SectionWriter:
    """Insere blocos de conteúdo antes de um parágrafo-âncora, clonando estilos de referência."""

    def __init__(self, doc: docx.document.Document, refs: dict, anchor) -> None:
        self.doc = doc
        self.refs = refs  # nome -> parágrafo de referência (CT_P)
        self.anchor = anchor  # elemento antes do qual o conteúdo é inserido
        self.inserted: List = []

    # ------------------------------------------------------------------ básicos
    def _new_par(self, ref_name: str):
        """Cria parágrafo vazio com o pPr do parágrafo de referência."""
        ref = self.refs[ref_name]
        p = parse_xml(f"<w:p {nsdecls('w')}/>")
        ppr = ref.find(qn("w:pPr"))
        if ppr is not None:
            p.append(copy.deepcopy(ppr))
        return p

    def _place(self, el) -> None:
        self.anchor.addprevious(el)
        self.inserted.append(el)

    @staticmethod
    def _run(text: str, bold=False, italic=False, highlight=False, color=None):
        r = parse_xml(f"<w:r {nsdecls('w')}><w:rPr/></w:r>")
        rpr = r.find(qn("w:rPr"))
        if bold:
            rpr.append(parse_xml(f'<w:b {nsdecls("w")} w:val="1"/>'))
            rpr.append(parse_xml(f'<w:bCs {nsdecls("w")} w:val="1"/>'))
        if italic:
            rpr.append(parse_xml(f'<w:i {nsdecls("w")} w:val="1"/>'))
            rpr.append(parse_xml(f'<w:iCs {nsdecls("w")} w:val="1"/>'))
        if highlight:
            rpr.append(parse_xml(f'<w:highlight {nsdecls("w")} w:val="yellow"/>'))
        if color:
            definir_cor(rpr, color)
        t = parse_xml(f"<w:t {nsdecls('w')} xml:space=\"preserve\"/>")
        t.text = text
        r.append(t)
        return r

    def _fill(self, p, text: str, bold_all=False, italic_all=False) -> None:
        """Preenche o parágrafo interpretando $math$, *itálico* e marcadores provisórios."""
        parts = re.split(r"(\$[^$]+\$)", text)
        for part in parts:
            if not part:
                continue
            if part.startswith("$") and part.endswith("$"):
                p.append(latex_to_omml(part[1:-1]))
                continue
            for j, chunk in enumerate(re.split(r"\*([^*]+)\*", part)):
                italic = italic_all or (j % 2 == 1)
                for k, piece in enumerate(PLACEHOLDER_RE.split(chunk)):
                    if piece:
                        p.append(self._run(piece, bold=bold_all, italic=italic, highlight=(k % 2 == 1)))

    # ------------------------------------------------------------------ blocos
    def heading(self, text: str) -> None:
        p = self._new_par("heading")
        self._fill(p, text)
        self._place(p)

    def subheading(self, text: str) -> None:
        p = self._new_par("subheading")
        self._fill(p, text)
        self._place(p)

    def paragraph(self, text: str) -> None:
        p = self._new_par("body")
        self._fill(p, text)
        self._place(p)

    def equation(self, latex: str, number: str) -> None:
        """Equação centralizada com numeração à direita (tabela sem bordas de 3 colunas)."""
        w_side, w_mid = 900, TEXT_WIDTH_TWIPS - 1800
        tbl = parse_xml(
            f"<w:tbl {nsdecls('w')}>"
            "<w:tblPr><w:tblW w:w=\"0\" w:type=\"auto\"/><w:jc w:val=\"center\"/>"
            "<w:tblBorders><w:top w:val=\"nil\"/><w:left w:val=\"nil\"/><w:bottom w:val=\"nil\"/>"
            "<w:right w:val=\"nil\"/><w:insideH w:val=\"nil\"/><w:insideV w:val=\"nil\"/></w:tblBorders>"
            "<w:tblLayout w:type=\"fixed\"/>"
            "<w:tblLook w:val=\"0000\"/></w:tblPr>"
            f"<w:tblGrid><w:gridCol w:w=\"{w_side}\"/><w:gridCol w:w=\"{w_mid}\"/><w:gridCol w:w=\"{w_side}\"/></w:tblGrid>"
            "</w:tbl>"
        )
        tr = parse_xml(f"<w:tr {nsdecls('w')}/>")
        for width, kind in ((w_side, "empty"), (w_mid, "math"), (w_side, "num")):
            tc = parse_xml(
                f"<w:tc {nsdecls('w')}><w:tcPr><w:tcW w:w=\"{width}\" w:type=\"dxa\"/>"
                "<w:vAlign w:val=\"center\"/></w:tcPr></w:tc>"
            )
            p = parse_xml(
                f"<w:p {nsdecls('w')}><w:pPr><w:spacing w:before=\"120\" w:after=\"120\"/>"
                "<w:ind w:left=\"0\" w:firstLine=\"0\"/>"
                f"<w:jc w:val=\"{'right' if kind == 'num' else 'center'}\"/></w:pPr></w:p>"
            )
            if kind == "math":
                para = parse_xml(f"<m:oMathPara {nsdecls('m')}/>")
                para.append(latex_to_omml(latex))
                p.append(para)
            elif kind == "num":
                for k, piece in enumerate(PLACEHOLDER_RE.split(f"({number})")):
                    if piece:
                        p.append(self._run(piece, highlight=(k % 2 == 1)))
            tc.append(p)
            tr.append(tc)
        tbl.append(tr)
        self._place(tbl)

    def table(self, label: str, title: str, header: Sequence[str], rows: Sequence[Sequence[str]],
              widths_cm: Sequence[float], source: str = "Fonte: Elaborado pelos autores (2026)") -> None:
        """Tabela no padrão ABNT/IBGE: título acima, traços só no topo, sob o cabeçalho e no fim."""
        cap = self._new_par("caption")
        for k, piece in enumerate(PLACEHOLDER_RE.split(label)):
            if piece:
                cap.append(self._run(piece, bold=True, highlight=(k % 2 == 1)))
        self._fill(cap, f" – {title}")
        self._place(cap)

        widths = [int(w * 567) for w in widths_cm]
        grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
        tbl = parse_xml(
            f"<w:tbl {nsdecls('w')}><w:tblPr><w:tblW w:w=\"{sum(widths)}\" w:type=\"dxa\"/>"
            "<w:jc w:val=\"center\"/><w:tblLayout w:type=\"fixed\"/>"
            "<w:tblCellMar><w:left w:w=\"80\" w:type=\"dxa\"/><w:right w:w=\"80\" w:type=\"dxa\"/></w:tblCellMar>"
            f"<w:tblLook w:val=\"0000\"/></w:tblPr><w:tblGrid>{grid}</w:tblGrid></w:tbl>"
        )
        line = '<w:{0} w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
        all_rows = [list(header)] + [list(r) for r in rows]
        for i, row in enumerate(all_rows):
            tr = parse_xml(f"<w:tr {nsdecls('w')}><w:trPr><w:cantSplit/></w:trPr></w:tr>")
            borders = ""
            if i == 0:
                borders = line.format("top") + line.format("bottom")
            elif i == len(all_rows) - 1:
                borders = line.format("bottom")
            for w, text in zip(widths, row):
                tc = parse_xml(
                    f"<w:tc {nsdecls('w')}><w:tcPr><w:tcW w:w=\"{w}\" w:type=\"dxa\"/>"
                    f"<w:tcBorders>{borders}</w:tcBorders><w:vAlign w:val=\"center\"/></w:tcPr></w:tc>"
                )
                p = parse_xml(
                    f"<w:p {nsdecls('w')}><w:pPr><w:spacing w:before=\"40\" w:after=\"40\" w:line=\"240\" "
                    "w:lineRule=\"auto\"/><w:ind w:left=\"0\" w:firstLine=\"0\"/><w:jc w:val=\"center\"/>"
                    "<w:rPr><w:sz w:val=\"22\"/></w:rPr></w:pPr></w:p>"
                )
                self._fill(p, text, bold_all=(i == 0))
                for r in p.findall(qn("w:r")):
                    r.find(qn("w:rPr")).append(parse_xml(f'<w:sz {nsdecls("w")} w:val="22"/>'))
                tc.append(p)
                tr.append(tc)
            tbl.append(tr)
        self._place(tbl)

        src = self._new_par("source")
        src.append(self._run(source, italic=True))
        self._place(src)

    def figure(self, image: Path, width_cm: float, label: str, title: str,
               source: str = "Fonte: Elaborado pelos autores (2026)") -> None:
        """Figura centralizada, seguida de legenda e fonte no padrão do documento."""
        tmp = self.doc.add_paragraph()
        tmp.add_run().add_picture(str(image), width=Cm(width_cm))
        drawing_run = tmp._p.findall(qn("w:r"))[0]
        p = self._new_par("figure")
        p.append(drawing_run)
        tmp._p.getparent().remove(tmp._p)
        self._place(p)

        cap = self._new_par("caption")
        for k, piece in enumerate(PLACEHOLDER_RE.split(label)):
            if piece:
                cap.append(self._run(piece, bold=True, highlight=(k % 2 == 1)))
        self._fill(cap, f" – {title}")
        self._place(cap)

        src = self._new_par("source")
        src.append(self._run(source, italic=True))
        self._place(src)


def find_paragraph(doc, text: str, start: int = 0, style_prefix: Optional[str] = None):
    """Retorna o índice do primeiro parágrafo cujo texto (sem espaços) é igual a `text`."""
    for i, p in enumerate(doc.paragraphs[start:], start):
        if p.text.strip() == text and (style_prefix is None or p.style.name.startswith(style_prefix)):
            return i
    raise ValueError(f"Parágrafo não encontrado: {text!r}")


# Texto novo ou alterado fora da seção de Métodos vai em vermelho, para revisão do grupo.
COR_FORA_METODOS = "FF0000"


_DEPOIS_DE_COLOR = {qn(f"w:{n}") for n in (
    "spacing", "w", "kern", "position", "sz", "szCs", "highlight", "u", "effect", "bdr", "shd", "fitText",
    "vertAlign", "rtl", "cs", "em", "lang", "eastAsianLayout", "specVanish", "oMath")}


def definir_cor(rpr, cor: str) -> None:
    """Coloca w:color no rPr na posição exigida pelo esquema do Word (antes de sz, highlight etc.)."""
    for c in rpr.findall(qn("w:color")):
        rpr.remove(c)
    novo = parse_xml(f'<w:color {nsdecls("w")} w:val="{cor}"/>')
    depois = next((ch for ch in rpr if ch.tag in _DEPOIS_DE_COLOR), None)
    if depois is not None:
        depois.addprevious(novo)
    else:
        rpr.append(novo)


def pintar(elementos: Sequence, cor: str = COR_FORA_METODOS) -> None:
    """Aplica a cor a todo o texto dos elementos (parágrafos, tabelas e equações OMML)."""
    m_r = "{http://schemas.openxmlformats.org/officeDocument/2006/math}r"
    for el in elementos:
        for r in list(el.iter(qn("w:r"))) + list(el.iter(m_r)):
            rpr = r.find(qn("w:rPr"))
            if rpr is None:
                rpr = parse_xml(f"<w:rPr {nsdecls('w')}/>")
                # em m:r, o w:rPr vem depois do m:rPr (se houver); em w:r, é o primeiro filho
                mrpr = r.find("{http://schemas.openxmlformats.org/officeDocument/2006/math}rPr")
                if mrpr is not None:
                    mrpr.addnext(rpr)
                else:
                    r.insert(0, rpr)
            definir_cor(rpr, cor)


def add_references(doc, entries: Sequence[str]) -> List[str]:
    """Insere referências em ordem alfabética na lista (formato copiado das existentes).

    As entradas novas ficam em vermelho (COR_FORA_METODOS), pois a lista de
    referências está fora da seção de Métodos.
    """
    ps = doc.paragraphs
    i0 = find_paragraph(doc, "REFERÊNCIAS BIBLIOGRÁFICAS")
    i1 = find_paragraph(doc, "APÊNDICES", start=i0)
    refs = [p for p in ps[i0 + 1:i1] if p.text.strip()]
    added = []
    for entry in entries:
        # Mesmo primeiro autor e mesmo ano = referência já presente (permite autores repetidos em anos diferentes)
        key = entry.split(".")[0][:25]
        anos = re.findall(r"\b(?:19|20)\d{2}\b", entry)
        ano = anos[-1] if anos else ""
        if any(p.text.strip().startswith(key) and ano in p.text for p in refs):
            continue
        target = next((p for p in refs if _chave_ref(p.text.strip()) > _chave_ref(entry)), refs[-1])
        new = copy.deepcopy(target._p)
        for r in new.findall(qn("w:r")):
            new.remove(r)
        new.append(SectionWriter._run(entry, color=COR_FORA_METODOS))
        if _chave_ref(target.text.strip()) > _chave_ref(entry):
            target._p.addprevious(new)
        else:
            target._p.addnext(new)
        added.append(entry)
        refs = [p for p in doc.paragraphs[i0 + 1:i1 + len(added)] if p.text.strip()]
    return added
