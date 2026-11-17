"""Gera a v14 a partir da v13 (sem alterá-la): os apêndices sobem uma letra, porque o Apêndice A não existe.

Decisão do usuário em 10/11/2026: B -> A, C -> B, D -> C, E -> D, F -> E. A troca é só de rótulos e remissões
(títulos de apêndice e de subseção, figuras, tabelas, equações, "Seção X.n", "Apêndice X"), no documento inteiro;
nenhuma frase é reescrita. O título vazio "APÊNDICE A - XX" e o seu conteúdo de marcação são retirados.

Não são tocados: as referências bibliográficas, os nomes das fases da busca (Fase B, B2, C, D, E), as variantes D1 e
D2 e o "Apêndice A1" da dissertação de Bortot Coelho (2017), que não casam com os padrões abaixo.

Uso: python renomear_apendices_v14.py            (grava a v14)
     python renomear_apendices_v14.py --listar   (só lista as trocas, sem gravar)
"""

from __future__ import annotations

import io
import re
import sys
from collections import Counter
from pathlib import Path

import docx
from docx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reescrever_serial_v11 import _trocar_trecho  # noqa: E402

DOC_DIR = Path(__file__).resolve().parents[1]
ORIGEM = DOC_DIR / "RELATÓRIO FINAL LOP_v13.docx"
DESTINO = DOC_DIR / "RELATÓRIO FINAL LOP_v14.docx"
MAPA = {"B": "A", "C": "B", "D": "C", "E": "D", "F": "E"}
W_P, W_T = qn("w:p"), qn("w:t")
M_OMATH = "{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath"

# rótulo numerado de apêndice: "B.5", "E.11" (figura, tabela, equação, seção ou título de subseção)
RE_ROTULO = re.compile(r"(?<![A-Za-z0-9.])([B-F])\.(\d{1,2})(?![0-9A-Za-z])")
# "Apêndice B", "Apêndices B a E", "APÊNDICE B -"
RE_APENDICE = re.compile(r"(Ap[êe]ndices?|AP[ÊE]NDICES?)(\s+)([B-F])(?![A-Za-z0-9])((?:\s*,\s*|\s+(?:a|e)\s+)([B-F])(?![A-Za-z0-9]))?")


def texto(el) -> str:
    return "".join(t.text or "" for t in el.iter(W_T))


def estilo(el) -> str:
    ppr = el.find(qn("w:pPr"))
    if ppr is None or ppr.find(qn("w:pStyle")) is None:
        return ""
    return ppr.find(qn("w:pStyle")).get(qn("w:val"))


def segmentos(p):
    """Listas de w:t consecutivos do parágrafo (inclui hyperlinks e campos), quebradas onde há equação."""
    segs, atual = [], []
    for node in p.iter():
        if node.tag == M_OMATH:
            if atual:
                segs.append(atual)
            atual = []
        elif node.tag == W_T:
            atual.append(node)
    if atual:
        segs.append(atual)
    return segs


def trocas_do_texto(flat: str):
    """Lista (início, fim, novo) das trocas num texto corrido, sem sobreposição."""
    achados = []
    for m in RE_ROTULO.finditer(flat):
        achados.append((m.start(1), m.end(1), MAPA[m.group(1)]))
    for m in RE_APENDICE.finditer(flat):
        achados.append((m.start(3), m.end(3), MAPA[m.group(3)]))
        if m.group(5):
            achados.append((m.start(5), m.end(5), MAPA[m.group(5)]))
    return sorted(set(achados))


def main() -> None:
    listar = "--listar" in sys.argv
    with open(ORIGEM, "rb") as f:
        doc = docx.Document(io.BytesIO(f.read()))
    body = doc.element.body
    els = list(body.iterchildren())

    def achar(pred, inicio=0):
        return next(i for i, e in enumerate(els) if i >= inicio and e.tag == W_P and pred(e))

    i_ref = achar(lambda e: estilo(e) == "Heading2" and texto(e).strip().startswith("REFERÊNCIAS"))
    i_aps = achar(lambda e: estilo(e) == "Heading2" and texto(e).strip() == "APÊNDICES", i_ref)
    i_a = achar(lambda e: texto(e).strip().startswith("APÊNDICE A"), i_aps)
    i_b = achar(lambda e: texto(e).strip().startswith("APÊNDICE B"), i_a)
    i_serial = achar(lambda e: estilo(e) == "Heading3" and texto(e).strip() == "MODELAGEM HÍBRIDA SERIAL")

    # Apêndice A vazio: título e marcações até o título do antigo Apêndice B
    vazio = els[i_a:i_b]
    resto = " ".join(texto(e).strip() for e in vazio[1:]).strip()
    assert len(vazio) <= 5 and len(resto) < 60 and not any(e.tag != W_P for e in vazio), f"o Apêndice A não está vazio: {resto!r}"
    if listar:
        print("Apêndice A (será retirado):", [texto(e).strip() for e in vazio])

    total, fora, por_tipo = 0, [], Counter()
    for i, el in enumerate(els):
        if i_ref <= i < i_aps or i_a <= i < i_b:   # referências bibliográficas e o apêndice vazio
            continue
        for p in el.iter(W_P):
            for ts in segmentos(p):
                flat = "".join(t.text or "" for t in ts)
                trocas = trocas_do_texto(flat)
                if not trocas:
                    continue
                if i < i_serial:   # trecho de outros integrantes: listar para conferência
                    fora.append((i, flat[max(0, trocas[0][0] - 50):trocas[-1][1] + 20]))
                for ini, fim, novo in reversed(trocas):
                    por_tipo[flat[ini:fim] + "→" + novo] += 1
                    if listar:
                        print(f"{i:5d}  …{flat[max(0, ini - 28):fim + 12]!r}")
                    _trocar_trecho(ts, ini, fim, novo)
                total += len(trocas)
    for e in vazio:
        body.remove(e)

    # conferências
    atuais = list(body.iterchildren())
    titulos = [texto(e).strip() for e in atuais if e.tag == W_P and estilo(e) == "Heading1" and texto(e).strip().startswith("APÊNDICE")]
    assert [t.split(" - ")[0] for t in titulos] == [f"APÊNDICE {x}" for x in "ABCDE"], titulos
    subs = [texto(e).strip() for e in atuais if e.tag == W_P and estilo(e) == "Heading3" and re.match(r"^[A-F]\.\d+ ", texto(e).strip())]
    assert not any(s.startswith("F.") for s in subs) and Counter(s[0] for s in subs) == Counter({"A": 5, "B": 4, "C": 3, "D": 11, "E": 2}), Counter(s[0] for s in subs)
    corpo = "\n".join(texto(e) for k, e in enumerate(atuais) if not (i_ref <= k < i_aps))
    assert not re.search(r"Ap[êe]ndices?\s+F(?![A-Za-z0-9])", corpo, re.I), "sobrou remissão ao Apêndice F"
    assert not re.search(r"(?<![A-Za-z0-9.])F\.\d{1,2}(?![0-9A-Za-z])", corpo), "sobrou rótulo F.n"

    print(f"{total} rótulos trocados: " + ", ".join(f"{k} ({n})" for k, n in sorted(por_tipo.items())))
    print(f"fora das partes da serial (antes da seção 4.5): {len(fora)}")
    for i, trecho in fora:
        print(f"   {i:5d}  {trecho!r}")
    print("apêndices:", " | ".join(titulos))
    if not listar:
        doc.save(str(DESTINO))
        print(f"{DESTINO.name} gravada a partir da {ORIGEM.name}")


if __name__ == "__main__":
    main()
