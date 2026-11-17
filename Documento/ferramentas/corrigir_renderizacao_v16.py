"""Gera a v16 a partir da v15 (sem alterá-la): corrige defeitos de renderização vistos no PDF exportado pelo Word.

Conferência de 10/11/2026 (PDF do Word das seções 4.5, 5.4, 5.X e dos Apêndices A a E). Nenhuma frase muda.

A. Recuo direito nas células: o documento tem recuo padrão de 0,72 cm à direita em todo parágrafo, e as células das
   tabelas e das equações zeravam só o recuo esquerdo. Resultado: colunas estreitas, palavras e números quebrados
   ("En/sai/os", "0,9/95") e números de equação em várias linhas. Agora o recuo direito também é zero.
B. A equação (4.5.4.1), recriada na v11, ganha a mesma coluna de numeração das demais.
C. Somatórios: operadores sem o termo somado dentro do operador (o Word mostra um quadrado pontilhado) passam a
   conter o termo seguinte; limite superior vazio é ocultado; em equações destacadas, os limites ficam acima e
   abaixo do símbolo.
D. Tabelas mais largas que o bloco de texto (15,15 cm) são reduzidas proporcionalmente e alinhadas ao texto.
E. Expoentes escritos como equação sem base ("min" + equação com base vazia e expoente −1): o Word mostra um quadrado
   pontilhado antes do expoente. Viram texto sobrescrito comum.

Regiões tratadas: seção 4.5 de Métodos, Resultados e Apêndices A a E. O restante do documento não é tocado.
Uso: python corrigir_renderizacao_v16.py
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import docx
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reescrever_resultados_v13 import estilo, texto  # noqa: E402

DOC_DIR = Path(__file__).resolve().parents[1]
ORIGEM = DOC_DIR / "RELATÓRIO FINAL LOP_v15.docx"
DESTINO = DOC_DIR / "RELATÓRIO FINAL LOP_v16.docx"
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
W_P, W_TBL = qn("w:p"), qn("w:tbl")
LARGURA_TEXTO = 8590   # 16 cm menos os recuos padrão do documento (75 + 407 twips)
RECUO_ESQ = 75


def recuo_direito_zero(tbl) -> int:
    n = 0
    for ind in tbl.iter(qn("w:ind")):
        if ind.get(qn("w:right")) is None and ind.get(qn("w:end")) is None:
            ind.set(qn("w:right"), "0")
            n += 1
    return n


def definir_larguras(tbl, larguras) -> None:
    cols = tbl.find(qn("w:tblGrid")).findall(qn("w:gridCol"))
    assert len(cols) == len(larguras)
    for c, w in zip(cols, larguras):
        c.set(qn("w:w"), str(w))
    for tr in tbl.findall(qn("w:tr")):
        tcs = tr.findall(qn("w:tc"))
        assert len(tcs) == len(larguras)
        for tc, w in zip(tcs, larguras):
            tcw = tc.find(qn("w:tcPr")).find(qn("w:tcW"))
            tcw.set(qn("w:w"), str(w))
            tcw.set(qn("w:type"), "dxa")


def ajustar_ao_texto(tbl) -> bool:
    """Tabela do docx_utils (largura fixa, centralizada) mais larga que o bloco de texto: reduz e alinha ao texto."""
    pr = tbl.find(qn("w:tblPr"))
    tblw, lay = pr.find(qn("w:tblW")), pr.find(qn("w:tblLayout"))
    if tblw is None or tblw.get(qn("w:type")) != "dxa" or lay is None or lay.get(qn("w:type")) != "fixed":
        return False
    total = int(tblw.get(qn("w:w")))
    cols = [int(c.get(qn("w:w"))) for c in tbl.find(qn("w:tblGrid")).findall(qn("w:gridCol"))]
    if total <= LARGURA_TEXTO or sum(cols) != total or tbl.findall(".//" + qn("w:gridSpan")):
        return False
    novas = [int(c * LARGURA_TEXTO / total) for c in cols]
    novas[-1] += LARGURA_TEXTO - sum(novas)
    definir_larguras(tbl, novas)
    tblw.set(qn("w:w"), str(LARGURA_TEXTO))
    jc = pr.find(qn("w:jc"))
    jc.set(qn("w:val"), "left")
    for velho in pr.findall(qn("w:tblInd")):
        pr.remove(velho)
    jc.addnext(parse_xml(f'<w:tblInd {nsdecls("w")} w:w="{RECUO_ESQ}" w:type="dxa"/>'))
    return True


def consertar_somatorios(el) -> dict:
    cont = {"termo": 0, "limite": 0, "posicao": 0}
    for nary in reversed(list(el.iter(M + "nary"))):   # de trás para frente: o somatório interno primeiro
        pr = nary.find(M + "naryPr")
        if pr is None:
            pr = parse_xml(f'<m:naryPr {nsdecls("m")}/>')
            nary.insert(0, pr)
        e = nary.find(M + "e")
        if e is None:
            e = parse_xml(f'<m:e {nsdecls("m")}/>')
            nary.append(e)
        if len(e) == 0:
            prox = nary.getnext()
            assert prox is not None and prox.tag in {M + t for t in ("sSup", "sSub", "sSubSup", "nary", "d", "f", "rad")}, \
                f"somatório sem termo seguinte reconhecível: {None if prox is None else prox.tag}"
            e.append(prox)   # move o termo somado para dentro do operador
            cont["termo"] += 1
        for nome, oculta in (("sup", "supHide"), ("sub", "subHide")):
            lim = nary.find(M + nome)
            if lim is not None and len(lim) == 0 and pr.find(M + oculta) is None:
                pr.append(parse_xml(f'<m:{oculta} {nsdecls("m")} m:val="1"/>'))
                cont["limite"] += 1
        if any(a.tag == M + "oMathPara" for a in nary.iterancestors()):
            loc = pr.find(M + "limLoc")
            if loc is None:
                loc = parse_xml(f'<m:limLoc {nsdecls("m")} m:val="undOvr"/>')
                ch = pr.find(M + "chr")
                (ch.addnext(loc) if ch is not None else pr.insert(0, loc))
            elif loc.get(M + "val") != "undOvr":
                loc.set(M + "val", "undOvr")
                cont["posicao"] += 1
    # ordem dos filhos de naryPr exigida pelo esquema: chr, limLoc, grow, subHide, supHide, ctrlPr
    ordem = {M + t: k for k, t in enumerate(("chr", "limLoc", "grow", "subHide", "supHide", "ctrlPr"))}
    for pr in el.iter(M + "naryPr"):
        filhos = sorted(list(pr), key=lambda c: ordem.get(c.tag, 99))
        for c in filhos:
            pr.remove(c)
        for c in filhos:
            pr.append(c)
    return cont


def expoentes_sem_base(el) -> int:
    """Troca a equação "base vazia elevada a x", logo depois de um trecho de texto, por texto sobrescrito."""
    n = 0
    depois = {qn(f"w:{t}") for t in ("rtl", "cs", "em", "lang", "eastAsianLayout", "specVanish", "oMath")}
    for om in list(el.iter(M + "oMath")):
        filhos = [c for c in om if c.tag != M + "ctrlPr"]
        if len(filhos) != 1 or filhos[0].tag != M + "sSup":
            continue
        base, sup = filhos[0].find(M + "e"), filhos[0].find(M + "sup")
        txt = lambda x: "".join(t.text or "" for t in x.iter(M + "t"))
        ant = om.getprevious()
        if base is None or sup is None or txt(base).strip() or not txt(sup).strip() or ant is None or ant.tag != qn("w:r"):
            continue
        novo = parse_xml(f'<w:r {nsdecls("w")}><w:t xml:space="preserve"/></w:r>')
        rpr = ant.find(qn("w:rPr"))
        rpr = parse_xml(f'<w:rPr {nsdecls("w")}/>') if rpr is None else __import__("copy").deepcopy(rpr)
        for velho in rpr.findall(qn("w:vertAlign")):
            rpr.remove(velho)
        va = parse_xml(f'<w:vertAlign {nsdecls("w")} w:val="superscript"/>')
        ref = next((c for c in rpr if c.tag in depois), None)
        (ref.addprevious(va) if ref is not None else rpr.append(va))
        novo.insert(0, rpr)
        novo.find(qn("w:t")).text = txt(sup)
        om.addprevious(novo)
        om.getparent().remove(om)
        n += 1
    return n


def main() -> None:
    with open(ORIGEM, "rb") as f:
        doc = docx.Document(io.BytesIO(f.read()))
    els = list(doc.element.body.iterchildren())

    def achar(pred, inicio=0):
        return next(i for i, e in enumerate(els) if i >= inicio and e.tag == W_P and pred(e))

    i_met = achar(lambda e: estilo(e) == "Heading3" and texto(e).strip() == "MODELAGEM HÍBRIDA SERIAL")
    i_res = achar(lambda e: estilo(e) == "Heading2" and texto(e).strip() == "RESULTADOS E DISCUSSÃO")
    i_conc = achar(lambda e: estilo(e) == "Heading2" and texto(e).strip().startswith("CONCLUS"), i_res)
    i_ap = achar(lambda e: estilo(e) == "Heading2" and texto(e).strip() == "APÊNDICES", i_conc)
    regiao = list(range(i_met, i_conc)) + list(range(i_ap, len(els)))

    n_ind = n_larg = n_tab = n_exp = 0
    soma = {"termo": 0, "limite": 0, "posicao": 0}
    for i in regiao:
        el = els[i]
        for k, val in consertar_somatorios(el).items():
            soma[k] += val
        n_exp += expoentes_sem_base(el)
        if el.tag != W_TBL:
            continue
        n_tab += 1
        n_ind += recuo_direito_zero(el)
        eh_equacao = bool(el.findall(".//" + M + "oMathPara")) and texto(el).strip().startswith("(")
        if eh_equacao and texto(el).strip() == "(4.5.4.1)":
            definir_larguras(el, [900, 6670, 1520])
        elif not eh_equacao and ajustar_ao_texto(el):
            n_larg += 1

    # conferências
    for i in regiao:
        for nary in els[i].iter(M + "nary"):
            assert len(nary.find(M + "e")) > 0, "sobrou somatório sem termo"
        if els[i].tag == W_TBL:
            # todo recuo de célula tem agora o lado direito explícito (zero, ou o valor que já vinha definido)
            assert all(ind.get(qn("w:right")) is not None or ind.get(qn("w:end")) is not None for ind in els[i].iter(qn("w:ind")))
    doc.save(str(DESTINO))
    print(f"{DESTINO.name} gravada a partir da {ORIGEM.name}")
    print(f"tabelas tratadas: {n_tab}; recuos direitos zerados: {n_ind}; tabelas reduzidas à largura do texto: {n_larg}")
    print(f"expoentes sem base convertidos em sobrescrito: {n_exp}")
    print(f"somatórios: {soma['termo']} termos movidos para dentro do operador, {soma['limite']} limites vazios ocultados, "
          f"{soma['posicao']} com limites reposicionados")


if __name__ == "__main__":
    main()
