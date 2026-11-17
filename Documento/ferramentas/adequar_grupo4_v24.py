"""Gera a v24 a partir da versão 4 do grupo (`RELATÓRIO FINAL LOP - GRUPO-4.docx`, que não é alterada).

Pedido de 15/11/2026. A versão 4 do grupo ainda traz as Seções 5.2 (black-box) e 5.5 (serial) e o Apêndice B na
forma antiga (a v23 não tinha sido passada para o Google Docs). O que este script faz:

0. Aceita as marcas que já estavam no arquivo do grupo, no documento inteiro: o vermelho tachado é apagado e o
   azul vira preto. Daí em diante, as cores marcam só o que é novo: VERMELHO TACHADO = sai; AZUL = entra.
1. Resultados 5.2 e 5.5 reescritos (comentário do Rodrigo de 14/11: menos números no texto e mais discussão
   física): por que o black-box não serve sozinho, se a serial dialogou com a física, se superou o white-box e
   onde é incompleta. Os parágrafos antigos ficam em vermelho e os novos, em azul.
2. Erros sem "p.p.", na escala da conversão (0 a 1), com três casas, como na Seção 5.1: tabelas 5.2.n, 5.5.n e
   B.10, B.13, B.14 e B.17 (valores brutos dos CSV), texto das Seções B.5 a B.8 e a frase da Seção 4.1.4.
3. A métrica "inconsistência física" sai de tudo: definição na Seção 4.1.4, coluna da Tabela 5.5.1, colunas das
   Tabelas B.14 e B.17, legendas e texto. A discussão passa a ser qualitativa, com exemplos tirados das curvas.
4. Tabelas dos ensaios novos só com Ensaio, RMSE, MAE e erro máximo (a antiga fica em vermelho, a nova em azul).
5. Figuras de Resultados e as malhas 4x4 do Apêndice B no visual atual (as de `figuras_v23/`).
6. Duas figuras novas da MLP pura (`figuras_metodologia/gerar_figuras_mlp_pura.py`): a genérica na Revisão
   (Seção 3.2.2), com subtítulos que separam MLP e PINN, e a detalhada na Seção 4.3, no lugar da imagem antiga.
7. Numeração 5.2.n e 5.5.n e remissões no esquema atual (4.1 comum, 4.2 white-box, 4.3 black-box, 4.6 serial).

Saídas: `RELATÓRIO FINAL LOP_v24.docx` (com as marcas) e `RELATÓRIO FINAL LOP_v24_limpo.docx` (as mesmas
mudanças já aceitas, para copiar e colar). O η dos ensaios novos continua o nominal (decisão de 15/11).
Uso: python ../figuras_metodologia/gerar_figuras_mlp_pura.py && python adequar_grupo4_v24.py
"""

from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adequar_resultados_v23 as v23  # noqa: E402
import enxugar_apendices_v19 as v19  # noqa: E402
import marcar_grupo_v21 as m  # noqa: E402
from docx_utils import SectionWriter, pintar  # noqa: E402

DOC_DIR = v19.DOC_DIR
GRUPO = DOC_DIR / "RELATÓRIO FINAL LOP - GRUPO-4.docx"
DESTINO = DOC_DIR / "RELATÓRIO FINAL LOP_v24.docx"
LIMPO = DOC_DIR / "RELATÓRIO FINAL LOP_v24_limpo.docx"
FIG_RES = DOC_DIR / "figuras_v23"
FIG_MET = DOC_DIR / "figuras_metodologia"
RESULTADOS = v23.RESULTADOS
AZUL, VERMELHO = v19.AZUL, v19.VERMELHO
W_P, W_TBL, W_R, W_T, M_T, M_OMATH = v19.W_P, v19.W_TBL, v19.W_R, v19.W_T, v19.M_T, v19.M_OMATH
M_R, M_PARA = v19.M_NS + "r", v19.M_NS + "oMathPara"
XML_SPACE = v23.XML_SPACE
A_BLIP, R_EMBED = v23.A_BLIP, v23.R_EMBED
WP_EXTENT = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}extent"
WP_DOCPR = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr"
A_EXT = "{http://schemas.openxmlformats.org/drawingml/2006/main}ext"
texto, cor_de, isolar, tres = v19.texto, v23.cor_de, v23.isolar, v23.tres
feito: list[str] = []
ESCALA = "na mesma escala da conversão de zinco, adimensional e entre 0 e 1"
FONTE = "Fonte: Elaborado pelos autores (2026)"


# ---------------------------------------------------------------------------------------------- aceitar marcas
def runs_com_texto(el):
    return [r for r in el.iter() if r.tag in (W_R, M_R) and any((x.text or "") for x in r if x.tag in (W_T, M_T))]


def todo_vermelho(el) -> bool:
    rs = runs_com_texto(el)
    return bool(rs) and all(cor_de(r) == VERMELHO for r in rs)


def tem_figura(el) -> bool:
    return el.find(".//" + qn("w:drawing")) is not None


MARCAS = ("commentRangeStart", "commentRangeEnd", "commentReference")


def ids_de_comentario(body) -> dict:
    return {nome: sorted(x.get(qn("w:id")) for x in body.iter(qn(f"w:{nome}"))) for nome in MARCAS}


def guardar_marcas(el) -> None:
    """Antes de apagar um parágrafo ou tabela, passa as marcas de comentário para o parágrafo vizinho."""
    marcas = []
    for x in el.iter():
        if x.tag in (qn("w:commentRangeStart"), qn("w:commentRangeEnd")):
            marcas.append(x)
        elif x.tag == W_R and x.find(qn("w:commentReference")) is not None:
            marcas.append(x)
    if not marcas:
        return
    destino = next((v for v in el.itersiblings() if v.tag == W_P), None)
    if destino is None:
        destino = next(v for v in el.itersiblings(preceding=True) if v.tag == W_P)
    ppr = destino.find(qn("w:pPr"))
    k = 0 if ppr is None else list(destino).index(ppr) + 1
    for i, x in enumerate(marcas):
        destino.insert(k + i, x)


def aceitar(body) -> dict:
    """Aceita as marcas: apaga o que está em vermelho (parágrafos, tabelas, colunas, trechos) e põe o azul em preto."""
    n = {"tabelas": 0, "colunas": 0, "parágrafos": 0, "trechos": 0, "azul": 0}
    for tbl in list(body.iter(W_TBL)):
        if tbl.getparent() is None:
            continue
        if todo_vermelho(tbl) and not tem_figura(tbl):
            guardar_marcas(tbl)
            tbl.getparent().remove(tbl)
            n["tabelas"] += 1
            continue
        linhas = tbl.findall(qn("w:tr"))
        ncol = {len(tr.findall(qn("w:tc"))) for tr in linhas}
        if len(ncol) != 1 or tbl.find(".//" + qn("w:gridSpan")) is not None:
            continue
        grade = tbl.find(qn("w:tblGrid"))
        for j in reversed(range(ncol.pop())):
            celulas = [tr.findall(qn("w:tc"))[j] for tr in linhas]
            if not all(todo_vermelho(tc) for tc in celulas):
                continue
            for tc in celulas:
                tc.getparent().remove(tc)
            cols = grade.findall(qn("w:gridCol"))
            grade.remove(cols[j])
            tblw = tbl.find(qn("w:tblPr")).find(qn("w:tblW"))
            if tblw is not None and tblw.get(qn("w:type")) == "dxa":
                tblw.set(qn("w:w"), str(sum(int(c.get(qn("w:w"))) for c in grade.findall(qn("w:gridCol")))))
            n["colunas"] += 1
    for p in list(body.iter(W_P)):
        if p.getparent() is None:
            continue
        tinha = bool(runs_com_texto(p))
        for r in runs_com_texto(p):
            if cor_de(r) != VERMELHO:
                continue
            if r.tag == W_R:
                r.getparent().remove(r)
                n["trechos"] += 1
            else:
                om = next(a for a in r.iterancestors() if a.tag == M_OMATH)
                if om.getparent() is not None and all(cor_de(x) == VERMELHO for x in om.iter(M_R)):
                    pai = om.getparent()
                    pai.remove(om)
                    if pai.tag == M_PARA and len(pai) == 0:
                        pai.getparent().remove(pai)
        if tinha and not texto(p).strip() and not tem_figura(p) and p.getparent().tag == qn("w:body"):
            guardar_marcas(p)
            p.getparent().remove(p)
            n["parágrafos"] += 1
    for c in list(body.iter(qn("w:color"))):
        if (c.get(qn("w:val")) or "").upper() == AZUL:
            c.getparent().remove(c)
            n["azul"] += 1
    return n


# ---------------------------------------------------------------------------------------------- marcar
def marcar_run(r, novo: str | None):
    """O run fica vermelho tachado; se `novo` for dado, entra depois dele uma cópia azul com o texto novo."""
    if novo is not None:
        n = copy.deepcopy(r)
        for h in n.find(qn("w:rPr")).findall(qn("w:highlight")):
            h.getparent().remove(h)
        n.find(W_T).text = novo
        n.find(W_T).set(XML_SPACE, "preserve")
        v19.pintar_run(n, AZUL)
        r.addnext(n)
    v19.pintar_run(r, VERMELHO)
    v19.tachar_run(r)


def troca(p, antigo: str, novo: str, vezes: int = 1) -> None:
    """Troca marcada de um trecho curto (dentro de um run), mantendo a formatação: antigo em vermelho, novo em azul."""
    for _ in range(vezes):
        total, ini = texto(p), 0
        while True:
            a = total.find(antigo, ini)
            assert a >= 0, f"não encontrado: {antigo!r} em {total[:70]!r}"
            r = isolar(p, a, a + len(antigo))
            if cor_de(r) != VERMELHO:
                break
            ini = a + 1
        marcar_run(r, novo)
    feito.append(f"{antigo} -> {novo}")


def troca_longa(p, antigo: str, novo: str) -> None:
    """Troca marcada de um trecho que pode atravessar vários runs (o texto novo aceita *itálico*)."""
    ult = m.retirar_trecho(p, antigo, antigo)
    tmp = SectionWriter(None, {"body": p}, None)._new_par("body")
    SectionWriter(None, {}, None)._fill(tmp, novo)
    pintar([tmp], AZUL)
    for el in reversed([ch for ch in tmp if ch.tag != qn("w:pPr")]):
        ult.addnext(el)
    feito.append(f"{antigo[:50]} -> {novo[:50]}")


def sai(*els) -> None:
    v19.retirar(*els)
    for el in els:
        feito.append(f"− {texto(el).strip()[:80]}")


def sai_trecho(p, trecho: str) -> None:
    m.retirar_trecho(p, trecho, trecho)
    feito.append(f"− {trecho[:80]}")


def novo_par(depois_de, modelo, txt: str, italico: bool = False, negrito_ate: str | None = None):
    """Parágrafo azul depois de `depois_de`, com a formatação de parágrafo de `modelo`."""
    sw = SectionWriter(None, {"body": modelo}, None)
    p = sw._new_par("body")
    if negrito_ate:
        k = txt.index(negrito_ate) + len(negrito_ate)
        sw._fill(p, txt[:k], bold_all=True)
        sw._fill(p, txt[k:])
    else:
        sw._fill(p, txt, italic_all=italico)
    for h in list(p.iter(qn("w:highlight"))):   # numeração nova já é a definitiva
        if "XX" not in txt:
            h.getparent().remove(h)
    pintar([p], AZUL)
    depois_de.addnext(p)
    feito.append(f"+ {texto(p).strip()[:80]}")
    return p


def acrescentar(p, txt: str) -> None:
    """Frase azul no fim do parágrafo."""
    if texto(p).endswith(" "):
        txt = txt.lstrip()
    tmp = SectionWriter(None, {"body": p}, None)._new_par("body")
    SectionWriter(None, {}, None)._fill(tmp, txt)
    pintar([tmp], AZUL)
    for el in [ch for ch in tmp if ch.tag != qn("w:pPr")]:
        p.append(el)
    feito.append(f"+ {txt.strip()[:80]}")


def inserir(p, depois_de: str, novo: str) -> None:
    v23.inserir(p, depois_de, novo)
    feito.append(f"+ {novo.strip()[:80]}")


def sem_pp(p, fontes=()) -> None:
    """Converte, com marcas, todo 'N p.p.' do parágrafo para a escala da conversão (três casas)."""
    total = texto(p)
    for k in reversed(list(v23.SEQUENCIA_PP.finditer(total))):
        depois = total[k.end():]
        fim_de_frase = not depois.strip() or re.match(r" [A-ZÀ-Ý]", depois) is not None
        novo = re.sub(v23.NUMERO, lambda x: v23.fracao(x.group(0), fontes), k.group(1)) + ("." if fim_de_frase else "")
        marcar_run(isolar(p, k.start(), k.end()), novo)
        feito.append(f"{k.group(0)} -> {novo}")


def coluna_sai(tbl, cabecalho: str) -> None:
    linhas = tbl.findall(qn("w:tr"))
    assert cabecalho in texto(linhas[0].findall(qn("w:tc"))[-1]), texto(linhas[0])
    for tr in linhas:
        v19.retirar(tr.findall(qn("w:tc"))[-1])
    feito.append(f"− coluna: {cabecalho}")


def _escrever_celula_azul(tc, txt: str) -> None:
    _escrever_celula_original(tc, txt)
    pintar([tc], AZUL)


_escrever_celula_original = v23.escrever_celula
v23.escrever_celula = _escrever_celula_azul   # as funções de tabela da v23 passam a marcar em azul o que reescrevem


# ---------------------------------------------------------------------------------------------- figuras
def por_imagem(doc, p, arquivo: Path, largura_cm: float) -> None:
    """Põe `arquivo` na figura do parágrafo (parte nova no pacote) com a largura dada."""
    blips = list(p.iter(A_BLIP))
    assert len(blips) == 1
    antigo = blips[0].get(R_EMBED)
    rid, _ = doc.part.get_or_add_image(str(arquivo))
    blips[0].set(R_EMBED, rid)
    w, h = Image.open(arquivo).size
    cx = int(largura_cm * 360000)
    cy = int(cx * h / w)
    for ext in list(p.iter(WP_EXTENT)) + list(p.iter(A_EXT)):
        ext.set("cx", str(cx))
        ext.set("cy", str(cy))
    ids = [int(d.get("id")) for d in doc.element.body.iter(WP_DOCPR)]
    for d in p.iter(WP_DOCPR):
        d.set("id", str(max(ids) + 1))
        d.set("name", arquivo.name)
    if antigo != rid and not any(b.get(R_EMBED) == antigo for b in doc.element.body.iter(A_BLIP)):
        doc.part.drop_rel(antigo)
    feito.append(f"figura: {arquivo.name}")


# ---------------------------------------------------------------------------------------------- fatos das curvas
def fatos() -> dict:
    """Números citados nos textos novos, calculados dos CSV congelados (as frases são conferidas contra eles)."""
    N = v23.numeros()
    S, B = N["serial"], N["mlp_pura"]
    f = {"N": N}
    ds = pd.read_csv(RESULTADOS / "serial" / "dados_plotados.csv")
    dm = pd.read_csv(RESULTADOS / "mlp_pura" / "dados_plotados.csv")
    d = ds.merge(dm[["ensaio", "t_min", "XZn_mlp_pura"]], on=["ensaio", "t_min"])
    d = d[d["t_min"] > 0]

    def rmse(a, b):
        return float(np.sqrt(np.mean((a - b) ** 2)))
    por_eta = {eta: (rmse(g["XZn_exp"], g["XZn_whitebox_novo"]), rmse(g["XZn_exp"], g["XZn_serial"])) for eta, g in d.groupby("eta")}
    f["wb_eta"] = (tres(min(v[0] for v in por_eta.values())), tres(max(v[0] for v in por_eta.values())))
    f["ser_eta"] = (tres(min(v[1] for v in por_eta.values())), tres(max(v[1] for v in por_eta.values())))
    # MLP pura: curvas finas (passo de 0,01 min) dos 16 ensaios
    cm = pd.read_csv(RESULTADOS / "mlp_pura" / "curvas_mlp_pura.csv")
    lim = dm.groupby("ensaio")["limite_estequiometrico"].first()
    quedas = {e: float((np.maximum.accumulate(g["XZn"].values) - g["XZn"].values).max()) for e, g in cm.groupby("ensaio")}
    f["n_queda"] = sum(q > 0.005 for q in quedas.values())   # quedas menores (Ensaio 15: 0,002) não são contadas
    f["queda_max"] = max(quedas.values())
    f["excesso_e4_treino"] = float(cm[cm["ensaio"] == 4]["XZn"].max() - lim[4])
    cn = pd.read_csv(RESULTADOS / "mlp_pura" / "ensaios_novos" / "curvas_mlp_pura_ensaios_novos.csv")
    e4 = cn[cn["ensaio"] == "E4"]["XZn"]
    f["e4_bb"] = (float(e4.min()), float(e4.max()))
    # serial: patamar no Ensaio 8 e nos ensaios novos
    cs = pd.read_csv(RESULTADOS / "serial" / "curvas_serial.csv")
    g8 = cs[cs["ensaio"] == 8]
    f["e8_serial"] = [float(np.interp(t, g8["t_min"], g8["XZn"])) for t in (2, 15)]
    sn = pd.read_csv(RESULTADOS / "serial" / "ensaios_novos" / "dados_plotados_ensaios_novos.csv")
    f["novos_serial"] = sn
    f["cv_bb"] = pd.read_csv(v23.CV_MLP_PURA / "cv_mlp_pura_10_sementes.csv")["RMSE_mlp_pura"]
    f["faixa_bb"] = pd.read_csv(RESULTADOS / "mlp_pura" / "faixa_entre_membros_112_pontos.csv")["faixa_entre_membros"].mean()
    return f


# ---------------------------------------------------------------------------------------------- principal
def main() -> None:
    doc = m.abrir(GRUPO)
    body = doc.element.body
    print("sdt removidos:", m.desembrulhar(body))
    print("marcas de comentário repetidas retiradas:", v23.consertar_comentarios(body))
    m.garantir_rpr(body)
    comentarios = ids_de_comentario(body)
    assert comentarios["commentRangeStart"] == comentarios["commentRangeEnd"] == comentarios["commentReference"]
    print("marcas do arquivo do grupo aceitas:", aceitar(body))
    assert ids_de_comentario(body) == comentarios, "marca de comentário perdida"
    assert not any(cor_de(r) in (VERMELHO, AZUL) for r in body.iter(W_R)), "sobrou cor antiga"
    G = [el for el in body if el.tag in (W_P, W_TBL)]

    def pos(comeco: str, a: int = 0, b: int | None = None, exato: bool = False) -> int:
        alvo = m.sem_espaco(comeco)
        for i in range(a, len(G) if b is None else b):
            t = m.sem_espaco(texto(G[i]))
            if G[i].tag == W_P and (t == alvo if exato else t.startswith(alvo)):
                return i
        raise AssertionError(f"parágrafo não encontrado: {comeco!r}")

    def figura_depois(i: int):
        return next(el for el in G[i:] if el.tag == W_P and el.find(".//" + A_BLIP) is not None)

    i_rev = pos("REVISÃO BIBLIOGRÁFICA", exato=True)
    i_met = pos("MATERIAIS E MÉTODOS", exato=True)
    i_res = pos("RESULTADOS E DISCUSSÃO", exato=True)
    i_fim = pos("CONCLUSÕES", i_res, exato=True)
    i_bb = pos("MODELO PURAMENTE ORIENTADO A DADOS (BLACK-BOX)", i_res, i_fim, exato=True)
    i_pinn = pos("MODELAGEM HÍBRIDA VIA REDES NEURAIS", i_bb, i_fim)
    i_ser = pos("MODELAGEM HÍBRIDA SERIAL", i_res, i_fim, exato=True)
    i_comp = pos("Comparação final", i_ser, i_fim, exato=True)
    F = fatos()
    S, B = F["N"]["serial"], F["N"]["mlp_pura"]

    def t3(tabela, linha, col="RMSE_pp"):
        return tres(tabela.loc[linha, col] / 100)

    # -------------------------------------------------------------- conferência dos números das frases novas
    wbn = {e: t3(S["nov_wb"], e) for e in ("E1", "E2", "E3", "E4")}
    assert (t3(S["res_wb"], "Teste cego"), f'{S["res_wb"].loc["Teste cego", "R2"]:.3f}') == ("0,078", "-0.675")
    assert wbn == {"E1": "0,081", "E2": "0,117", "E3": "0,072", "E4": "0,036"}, wbn
    assert (t3(B["res"], "Teste cego"), f'{B["res"].loc["Teste cego", "R2"]:.3f}', t3(B["res"], "Treino")) == ("0,018", "0.907", "0,006")
    assert (tres(F["cv_bb"].mean()), tres(F["cv_bb"].std(ddof=1))) == ("0,044", "0,004")
    assert 7.5 < F["cv_bb"].mean() / (B["res"].loc["Treino", "RMSE_pp"] / 100) < 8.5
    assert tres(F["faixa_bb"]) == "0,039"
    assert (F["n_queda"], tres(F["queda_max"])) == (13, "0,025"), (F["n_queda"], F["queda_max"])
    assert F["excesso_e4_treino"] > 0.01
    assert (f'{F["e4_bb"][0]:.2f}', f'{F["e4_bb"][1]:.2f}') == ("0.45", "0.51"), F["e4_bb"]
    assert (t3(S["res"], "Teste cego"), f'{S["res"].loc["Teste cego", "R2"]:.3f}', t3(S["res"], "Treino")) == ("0,020", "0.888", "0,014")
    assert round(S["reducao"]) == 74 and round(B["reducao"]) == 76
    assert (F["wb_eta"], F["ser_eta"]) == (("0,025", "0,123"), ("0,014", "0,018")), (F["wb_eta"], F["ser_eta"])
    assert all(f"{x:.2f}" == "0.84" for x in F["e8_serial"]), F["e8_serial"]
    sn = F["novos_serial"]
    col_s = next(c for c in sn.columns if "serial" in c.lower())
    quinze = sn[sn["t_min"] == 15].set_index("ensaio")
    assert f'{quinze.loc["E1", col_s]:.2f}' == "0.71"
    assert all(abs(quinze.loc[e, col_s] - quinze.loc[e, "XZn_exp"]) < 0.02 for e in ("E2", "E3"))
    dif_s = S["nov"].loc[["E1", "E2", "E3", "E4"], "RMSE_pp"] - S["nov_wb"].loc[["E1", "E2", "E3", "E4"], "RMSE_pp"]
    assert (dif_s[["E2", "E3"]] < 0).all() and (dif_s[["E1", "E4"]] > 0).all()

    # ------------------------------------------------------------------ Revisão 3.2.2: MLP separado da PINN
    sub = next(el for el in G[i_rev:i_met] if el.tag == W_P and el.find(qn("w:pPr")) is not None
               and el.find(qn("w:pPr")).find(qn("w:pStyle")) is not None
               and el.find(qn("w:pPr")).find(qn("w:pStyle")).get(qn("w:val")) == "Heading6")
    p_mlp = G[pos("Dessa maneira, primeiramente, é interessante comentar sobre as redes neurais artificiais", i_rev, i_met)]
    p_treino = G[pos("No treinamento, os pesos são ajustados pela retropropagação do erro", i_rev, i_met)]
    p_pinn = G[pos("Outra arquitetura de redes neurais fundamental de ser citada", i_rev, i_met)]
    i_leg = pos("Figura 3.XX: Representação visual da arquitetura de uma PINN", i_rev, i_met)
    fig_modelo, leg_modelo, fonte_modelo = G[i_leg - 1], G[i_leg], G[i_leg + 1]
    assert fig_modelo.find(".//" + A_BLIP) is not None and texto(fonte_modelo).startswith("Fonte")
    novo_par(p_mlp.getprevious(), sub, "Perceptron multicamadas (MLP)")
    novo_par(p_pinn.getprevious(), sub, "Redes neurais informadas pela física (PINN)")
    p = novo_par(p_treino, p_treino,
                 "A Figura 3.XX resume o funcionamento de um MLP e o seu ciclo de treinamento. Quando a função de perda é "
                 "calculada apenas com os dados medidos, como na figura, a rede é um modelo puramente orientado a dados "
                 "(*black-box*): nenhuma equação do processo participa do ajuste, e o que a rede sabe sobre o fenômeno é "
                 "somente o que os dados contêm.")
    fig = copy.deepcopy(fig_modelo)
    p.addnext(fig)
    por_imagem(doc, fig, FIG_MET / "fig_mlp_01_generica_fluxo.png", 15.5)
    leg = novo_par(fig, leg_modelo, "Figura 3.XX: Representação esquemática de um perceptron multicamadas (MLP) e do ciclo de treinamento")
    novo_par(leg, fonte_modelo, FONTE, italico=True)
    acrescentar(p_pinn, " A rede, em si, pode ser o mesmo MLP da Figura 3.XX: o que distingue a PINN é a função de perda, que passa "
                        "a incluir, além do erro em relação aos dados, os resíduos das equações físicas.")

    # ------------------------------------------------------------------ 4.1.4: unidade dos erros e métrica retirada
    troca_longa(G[pos("O desempenho de todos os modelos é quantificado", i_met, i_res)],
                "em pontos percentuais (p.p.) de conversão", ESCALA)
    sai(G[pos("A consistência física das previsões é quantificada pela fração dos nós", i_met, i_res)])

    # ------------------------------------------------------------------ 4.3: remissões e figura detalhada
    i_bbm = pos("MODELO PURAMENTE ORIENTADO A DADOS (BLACK-BOX)", i_met, i_res, exato=True)
    i_pinnm = pos("MODELAGEM HÍBRIDA: REDES NEURAIS INFORMADAS PELA FÍSICA", i_bbm, i_res)
    troca(G[pos("O modelo black-box é um perceptron multicamadas de alimentação direta", i_bbm, i_pinnm)], "(Seção 4.5)", "(Seção 4.6)")
    i_opt = pos("Com o gradiente fornecido pelo backpropagation", i_bbm, i_pinnm)
    troca(G[i_opt], "(Seção 4.5)", "(Seção 4.6)")
    fig = figura_depois(i_opt)
    assert G.index(fig) == i_opt + 1, "a imagem antiga do black-box não está onde se esperava"
    novo_par(G[i_opt], G[i_opt], "A Figura 4.3.1 resume a arquitetura da rede, o treinamento de cada uma das dez redes e a "
                                 "formação do modelo final.")
    por_imagem(doc, fig, FIG_MET / "fig_mlp_02_arquitetura_mlp_pura.png", 16.0)
    i_ser_m = pos("MODELAGEM HÍBRIDA SERIAL", i_met, i_res, exato=True)
    i_leg = pos("Figura 4.XX.1 – Representação esquemática da arquitetura híbrida serial", i_ser_m, i_res)
    leg = novo_par(fig, G[i_leg], "Figura 4.3.1 – Arquitetura do modelo *black-box* (MLP pura), treinamento de cada rede e "
                                  "formação do comitê de dez redes")
    novo_par(leg, G[i_leg + 1], FONTE)

    # ------------------------------------------------------------------ 5.2 black-box
    ERROS = {"RMSE (p.p.)": "RMSE_pp", "MAE (p.p.)": "MAE_pp", "Erro máximo (p.p.)": "Emax_pp"}

    def colunas(tabela, extras=None) -> dict:
        return {cab: tabela[col] for cab, col in ERROS.items()} | (extras or {})

    def por_ensaio(rotulo: str) -> int:
        return int(rotulo.rstrip("*"))

    def bb(comeco: str):
        return G[pos(comeco, i_bb, i_pinn)]

    def ser(comeco: str):
        return G[pos(comeco, i_ser, i_comp)]

    def legenda_sem_inconsistencia(p) -> None:
        k = re.search(r", erro máximo e inconsistência física \(.*\)\s*$", texto(p))
        assert k and "(MAE)" in texto(p)[:k.start()]
        troca_longa(p, texto(p)[k.start():].rstrip(), " e erro máximo")

    def legenda_ensaios_novos(p, modelo: str) -> None:
        troca_longa(p, f"Ensaios novos: condições, limite estequiométrico, conversão de zinco medida e prevista pelo modelo {modelo} "
                       "em 15 min e erros da previsão nos seis instantes de amostragem",
                    f"Desempenho do modelo {'*black-box*' if modelo == 'black-box' else modelo} nos ensaios novos: RMSE, erro absoluto médio (MAE) e erro máximo nos seis "
                    "instantes de amostragem")

    def cabecalho_como_5_1(tbl) -> None:
        """Cabeçalho das tabelas de Resultados como o da Seção 5.1: RMSE, MAE e erro máximo sem unidade."""
        for tc in tbl.find(qn("w:tr")).findall(qn("w:tc")):
            t = texto(tc).strip()
            if t in ("RMSE (–)", "MAE (–)", "Erro máximo (–)"):
                _escrever_celula_azul(tc, t[:-4])
            elif t.endswith("(–)"):   # R2 (–): a equação fica e a unidade sai
                r = next(r for r in tc.iter(W_R) if "(–)" in texto(r))
                assert texto(r).strip() == "(–)", texto(r)
                marcar_run(r, None)
        assert "(–)" not in "".join(texto(r) for r in tbl.find(qn("w:tr")).iter(W_R) if cor_de(r) != VERMELHO)

    def tabela_nova_ensaios(p_legenda, metricas) -> None:
        """A tabela antiga, em vermelho, vai para antes da legenda (duas tabelas seguidas seriam unidas pelo Word)."""
        antiga = G[G.index(p_legenda) + 1]
        assert antiga.tag == W_TBL
        nova = copy.deepcopy(antiga)
        antiga.addnext(nova)
        v23.tabela_ensaios_novos(nova, metricas)
        cabecalho_como_5_1(nova)
        pr = nova.find(qn("w:tblPr"))
        for jc in pr.findall(qn("w:jc")):
            pr.remove(jc)
        pr.find(qn("w:tblW")).addnext(parse_xml(f'<w:jc {nsdecls("w")} w:val="center"/>'))
        pintar([nova], AZUL)
        sai(antiga)
        p_legenda.addprevious(antiga)

    p = bb("Esta seção apresenta os resultados do modelo puramente orientado a dados")
    sai(p)
    novo_par(p, p,
             "Esta seção apresenta os resultados do modelo puramente orientado a dados (*black-box*), descrito na Seção 4.3 e "
             "adotado como linha de base das abordagens híbridas (Seção 4.1.4). O modelo é a média de dez redes MLP que estimam "
             "a conversão de zinco diretamente a partir de $C_{A0}$, $\\eta$ e $\\ln t$, sem o balanço populacional e sem "
             f"restrições físicas. Como na Seção 5.1, os erros são expressos {ESCALA}.")
    p1, p2 = bb("Nos 13 ensaios de treino, o RMSE foi de"), bb("Nos Ensaios 7, 8 e 14, reservados para o teste cego")
    sai(p1, p2)
    novo_par(p2, p1,
             "Em termos de erro, o modelo *black-box* ficou bem abaixo do *white-box* (Tabela 5.2.1). Nos Ensaios 7, 8 e 14, "
             "reservados para o teste cego, o RMSE foi de 0,018 e o $R^2$, de 0,907, frente a 0,078 e −0,675 do modelo "
             "*white-box* nos mesmos 21 pontos. Nos 13 ensaios de treino, o RMSE foi de 0,006, valor que mede apenas o ajuste "
             "aos pontos usados no treinamento.")
    p = bb("Tabela 5.X.1")
    troca(p, "5.X.1", "5.2.1")
    legenda_sem_inconsistencia(p)
    tbl = G[G.index(p) + 1]
    assert tbl.tag == W_TBL and len(tbl.find(qn("w:tr")).findall(qn("w:tc"))) == 7
    assert v23.tabela_de_csv(tbl, colunas(B["res"])) == 9
    cabecalho_como_5_1(tbl)
    p = bb("A Figura 5.X.1 compara as curvas previstas")
    sai(p)
    v23.trocar_imagem(doc, figura_depois(G.index(p)), FIG_RES / "fig_mlp_pura_2x2_texto_ensaios_01_07_08_14.png")
    novo_par(p, p,
             "A Figura 5.2.1 compara as curvas previstas com as medições no Ensaio 1, de treino, e nos três ensaios de teste "
             "cego, ao lado do modelo *white-box* da Seção 4.2. As curvas começam em 0,5 min, primeiro instante com medição, "
             "pois a rede não recebe a condição inicial. No Ensaio 8 ($\\eta = 1,0$), em que o *white-box* tende à conversão "
             "completa, a rede acompanha de perto o patamar medido, de cerca de 0,87: os dados contêm a informação que falta "
             "à lei cinética do modelo fenomenológico, e a rede a reproduz mesmo sem conhecer o processo. As curvas e os "
             "valores dos 16 ensaios estão na Seção B.7.")
    troca(bb("Figura 5.X.1 – Conversão de zinco medida e prevista"), "5.X.1", "5.2.1")
    p1, p2 = bb("Na validação cruzada por ensaio, com as mesmas quatro dobras"), bb("Entre as dez redes, a diferença entre a maior e a menor")
    sai(p1, p2)
    q = novo_par(p2, p1,
                 "Esses resultados, porém, não bastam para que o modelo seja usado sozinho na previsão do processo. O primeiro "
                 "motivo é que o erro pequeno depende de a condição prevista estar cercada por ensaios de treino. Na validação "
                 "cruzada por ensaio, com as mesmas quatro dobras do modelo serial (Seção 4.6.3) e dez sementes, o RMSE fora da "
                 "dobra foi de 0,044 ± 0,004, cerca de oito vezes o erro de ajuste, e os maiores erros ocorreram nos Ensaios 5, "
                 "2 e 6, todos com $C_{A0}$ de 0,1 ou 1,5 mol/L, extremos da faixa ensaiada. Além disso, as dez redes, "
                 "treinadas com os mesmos dados, divergem entre si: a diferença entre a maior e a menor conversão prevista "
                 "foi, em média, de 0,039 nos 112 pontos, o que indica que os 91 pontos de treino não determinam uma única "
                 "curva.")
    novo_par(q, p1,
             "O segundo motivo, e o principal, é que nada obriga a curva prevista a obedecer à física da lixiviação. A rede "
             "não recebe a condição inicial $X(0)=0$ e não descreve o trecho anterior a 0,5 min, em que ocorre a maior parte "
             "da dissolução. Em 13 dos 16 ensaios, a conversão prevista recua mais de 0,005 em algum trecho, chegando a 0,025, o que "
             "corresponderia à reprecipitação do zinco com regeneração de ácido, fenômeno que não ocorre nesse sistema. Essas "
             "oscilações acompanham a dispersão das próprias medições: no Ensaio 4 ($\\eta = 0,5$), por exemplo, a rede "
             "reproduz o sobe e desce dos pontos medidos entre 0,47 e 0,53 e ultrapassa o limite estequiométrico de 0,50, "
             "isto é, prevê mais zinco dissolvido do que o ácido disponível permite. A rede, portanto, ajusta também o erro "
             "experimental, e não apenas a cinética.")
    p = bb("Nos quatro ensaios novos, descritos na Seção 5.4")
    sai(p)
    novo_par(p, p,
             "Nos quatro ensaios novos, descritos na Seção 4.1.2, as previsões foram calculadas com as mesmas dez redes, sem "
             "novo ajuste, e com os rótulos de E2 e E3 trocados (Tabela 5.2.2 e Figura 5.2.2). Em E2 e E3, condições com "
             f"excesso de ácido e dentro da faixa de treino, o erro foi inferior ao do modelo *white-box* ({wbn['E2']} e "
             f"{wbn['E3']}). O Ensaio E4 expõe a limitação mais séria: com razão molar de 0,40, abaixo da faixa de treino, a "
             "rede previu conversões entre 0,45 e 0,51 ao longo de toda a curva, acima do limite estequiométrico de 0,40. Em "
             "vez de reconhecer que o ácido se esgota mais cedo, a rede praticamente repetiu o patamar dos ensaios de treino "
             "com $\\eta = 0,5$, o que sugere que esse patamar foi aprendido como um valor, e não como consequência do balanço "
             "de ácido. As medições desse ensaio também superam o limite, o que a Seção 5.1 atribui a erro experimental, mas "
             "a previsão da rede fica acima das próprias medições. O *white-box*, que impõe o balanço de ácido, atinge "
             f"exatamente o limite em E4 e em E1 e teve erro menor nos dois ensaios ({wbn['E4']} e {wbn['E1']}).")
    p = bb("Tabela 5.X.2")
    troca(p, "5.X.2", "5.2.2")
    legenda_ensaios_novos(p, "black-box")
    tabela_nova_ensaios(p, B["nov"])
    p = bb("Figura 5.X.2")
    troca(p, "5.X.2", "5.2.2")
    v23.trocar_imagem(doc, G[G.index(p) - 1], FIG_RES / "fig_mlp_pura_2x2_ensaios_novos.png")
    fonte = G[G.index(p) + 1]
    assert texto(fonte).startswith("Fonte")
    novo_par(fonte, p1,
             "Em síntese, o modelo *black-box* mostra que os dados disponíveis são suficientes para corrigir os desvios do "
             "*white-box* dentro da faixa ensaiada, mas não constitui, sozinho, um modelo do processo. Ele fornece apenas a "
             "conversão, em instantes e condições próximos aos do treino, não calcula a concentração de ácido nem a retração "
             "das partículas, não garante os balanços de massa e não dá nenhuma indicação de quando deixa de valer. É essa "
             "lacuna que as abordagens híbridas das Seções 5.3 a 5.5 procuram preencher, ao manter a estrutura física do "
             "modelo fenomenológico e deixar para os dados apenas a parcela que a teoria não descreve bem.")

    # ------------------------------------------------------------------ 5.5 serial
    p = ser("Esta seção apresenta os resultados do modelo híbrido serial")
    sai(p)
    novo_par(p, p,
             "Esta seção apresenta os resultados do modelo híbrido serial (Seção 4.6), em que a rede neural estima apenas a "
             "taxa de retração das partículas, $\\nu(t)$, e a conversão é calculada pelos balanços populacional e de ácido. A "
             f"versão final é a média de dez redes treinadas com os 13 ensaios de treino. Os erros são expressos {ESCALA}, e "
             "calculados nos instantes com medição e $t>0$ (Seção 4.1.4).")
    p1, p2 = ser("Nos 13 ensaios de treino, o modelo reproduziu a conversão medida"), ser("Nos Ensaios 7, 8 e 14, reservados para o teste cego")
    sai(p1, p2)
    novo_par(p2, p1,
             "Nos Ensaios 7, 8 e 14, reservados para o teste cego, o RMSE foi de 0,020 e o $R^2$, de 0,888 (Tabela 5.5.1), "
             "frente a 0,078 e −0,675 do modelo *white-box* nos mesmos 21 pontos, o que representa um erro cerca de 74% menor. "
             "Nos 13 ensaios de treino, o RMSE foi de 0,014, praticamente o mesmo da conversão calculada diretamente com as "
             "taxas do problema inverso (Tabela B.1), que são o alvo do treinamento. A rede, portanto, reproduz as taxas que "
             "lhe foram fornecidas, e esse valor mede o ajuste, não a capacidade de previsão.")
    p = ser("Tabela 5.4.1")
    troca(p, "5.4.1", "5.5.1")
    legenda_sem_inconsistencia(p)
    tbl = G[G.index(p) + 1]
    assert tbl.tag == W_TBL
    coluna_sai(tbl, "Inconsistência física")
    assert v23.tabela_de_csv(tbl, colunas(S["res"])) == 9
    cabecalho_como_5_1(tbl)
    p = ser("A Figura 5.4.1 compara as curvas previstas")
    sai(p)
    v23.trocar_imagem(doc, figura_depois(G.index(p)), FIG_RES / "fig_serial_2x2_texto_ensaios_01_07_08_14.png")
    novo_par(p, p,
             "A Figura 5.5.1 compara as curvas previstas com as medições no Ensaio 1, de treino, e nos três ensaios de teste "
             "cego, ao lado do modelo *white-box* da Seção 4.2; as curvas e os valores dos 16 ensaios estão na Seção B.5. O "
             "ganho em relação ao *white-box* concentra-se onde a lei cinética de primeira ordem falha. Nos ensaios com "
             "$\\eta = 1,0$, o *white-box* tende à conversão completa, enquanto a dissolução medida cessa entre 0,85 e 0,87, "
             "com parte do ácido ainda livre (Seção 5.1). O modelo serial reproduz esse comportamento: no Ensaio 8, a taxa de "
             "retração prevista pela rede cai praticamente a zero em cerca de 2 min, e a conversão se estabiliza em 0,84, "
             "frente a 0,87 medida. Nos ensaios limitados pelo ácido ($\\eta = 0,5$), em que o balanço estequiométrico já "
             "determina o patamar, os dois modelos chegam praticamente ao mesmo valor. Com isso, o erro do modelo serial é "
             f"semelhante nas quatro razões molares, entre {F['ser_eta'][0]} e {F['ser_eta'][1]}, ao passo que o do "
             f"*white-box* varia de {F['wb_eta'][0]} a {F['wb_eta'][1]}.")
    troca(ser("Figura 5.4.1 – Conversão de zinco medida e prevista"), "5.4.1", "5.5.1")
    p1, p2 = ser("Como o teste cego reúne apenas três ensaios"), ser("As dez redes do comitê forneceram previsões próximas entre si")
    sai(p1, p2)
    q = novo_par(p2, p1,
                 "Quanto à coerência com a física do processo, as restrições da Seção 4.1.3 são satisfeitas por construção, e "
                 "não por penalização: a curva parte de $X(0)=0$, a taxa prevista é sempre positiva, de modo que a conversão "
                 "nunca diminui, e o balanço de ácido limita a conversão a $\\min(1,\\eta)$ (Tabela 4.1.3). Em nenhum dos 16 "
                 "ensaios, nem nos ensaios novos, a curva prevista violou essas condições, e o modelo fornece, além da "
                 "conversão, a retração das partículas e a concentração de ácido ao longo do tempo.")
    novo_par(q, p1,
             "Como o teste cego reúne apenas três ensaios, a capacidade de previsão foi avaliada também pela validação "
             "cruzada por ensaio (Seções 4.6.3 e 4.6.6), em que cada ensaio de treino é previsto por redes treinadas sem ele. "
             "Com dez sementes, o RMSE fora da dobra foi de 0,033 ± 0,005, contra 0,044 ± 0,004 do *black-box* nas mesmas "
             "dobras, e os maiores erros ocorreram nos Ensaios 15, 10 e 6, todos com $C_{A0}$ de 0,1 ou 1,5 mol/L, extremos "
             "da faixa ensaiada (Tabela B.10). Entre as dez redes do comitê, a diferença entre a maior e a menor conversão "
             "prevista foi, em média, de 0,004, cerca de um décimo da observada no *black-box*; essa faixa expressa apenas a "
             "variabilidade do treinamento e não inclui o erro experimental nem as simplificações do modelo fenomenológico. "
             "Assim, com os mesmos dados e redes de mesma largura, os dois modelos têm erro semelhante no teste cego, mas a "
             "estrutura física reduz o erro fora dos ensaios de treino e a dependência do sorteio inicial dos pesos.")
    troca(ser("O modelo foi confrontado também com quatro ensaios novos"), "Tabela 5.4.2", "Tabela 4.1.2")
    p = ser("Tabela 5.4.2 – Ensaios novos")
    troca(p, "5.4.2", "5.5.2")
    legenda_ensaios_novos(p, "híbrido serial")
    tabela_nova_ensaios(p, S["nov"])
    p = ser("Com essa correção, o RMSE foi de")
    sai(p)
    novo_par(p, p,
             "Com os rótulos de E2 e E3 trocados (Seção 4.1.2), o erro em E2 e E3 foi inferior ao do modelo *white-box* "
             f"({wbn['E2']} e {wbn['E3']}; Tabela 5.5.2 e Figura 5.5.2), e a conversão prevista em 15 min diferiu da medida "
             "em menos de 0,02. Em E1 e E4, nos quais o ácido é o reagente limitante, as medições superam o limite "
             "estequiométrico em todos os instantes e, em E1, diminuem de 0,87 em 1 min para 0,81 em 15 min, o que indica "
             "erro experimental (Seção 5.1). Nessas condições, um modelo que respeita o balanço de ácido não pode reproduzir "
             f"os valores medidos, e o *white-box*, que atinge exatamente o limite, teve erro menor ({wbn['E1']} e "
             f"{wbn['E4']}). Em E1 ($\\eta = 0,75$), além disso, a conversão prevista pelo modelo serial se estabilizou em "
             "0,71, abaixo do limite de 0,75: essa razão molar fica entre as de treino mais próximas (0,5 e 1,0), que "
             "pertencem a regimes diferentes, e a taxa interpolada pela rede praticamente se anula antes do esgotamento do "
             "ácido.")
    p = ser("Figura 5.4.2 – Conversão de zinco medida e prevista")
    troca(p, "5.4.2", "5.5.2")
    v23.trocar_imagem(doc, G[G.index(p) - 1], FIG_RES / "fig_serial_2x2_ensaios_novos.png")
    fonte = G[G.index(p) + 1]
    assert texto(fonte).startswith("Fonte")
    novo_par(fonte, p1,
             "Em síntese, o modelo híbrido serial superou o *white-box* nas condições em que este apresenta desvio "
             "sistemático e manteve a coerência física que falta ao *black-box*. As suas limitações decorrem do que a rede "
             "aprende: a taxa de retração é estimada como função de $C_{A0}$, $\\eta$ e $t$, e não da concentração de ácido em "
             "cada instante, de modo que o modelo reproduz a desaceleração da dissolução, mas não explica a sua causa, como "
             "a ordem aparente de reação inferior a um ou o consumo de ácido pelo ferro (Seção 5.1). Por isso, a previsão é "
             "confiável apenas na faixa de condições coberta pelos 13 ensaios de treino, como indicam os erros maiores nos "
             "extremos de $C_{A0}$ e o resultado do Ensaio E1.")

    # ------------------------------------------------------------------ Apêndice B
    i_apb = pos("APÊNDICE B - RESULTADOS COMPLEMENTARES", i_fim)
    troca_longa(G[pos("Este apêndice reúne os resultados da seleção da configuração", i_apb)],
                "Nas Seções B.5 a B.8, os erros estão em pontos percentuais (p.p.) de conversão.", "Os erros estão " + ESCALA + ".")
    v23.trocar_imagem(doc, G[pos("Figura B.11 – Conversão de zinco medida e prevista pelo modelo híbrido serial", i_apb) - 1],
                      FIG_RES / "fig_serial_4x4_todos.png")
    v23.trocar_imagem(doc, G[pos("Figura B.12 – Conversão de zinco medida e prevista pelo modelo black-box", i_apb) - 1],
                      FIG_RES / "fig_mlp_pura_4x4_todos.png")

    def tabela_apos(legenda: str):
        tbl = G[pos(legenda, i_apb) + 1]
        assert tbl.tag == W_TBL
        return tbl

    sai_trecho(G[pos("A Figura B.12 apresenta as curvas previstas pelo modelo black-box nos 16 ensaios", i_apb)],
               " e a fração dos nós da curva fisicamente inconsistentes")
    sai_trecho(G[pos("Tabela B.17 – Métricas do modelo black-box nos ensaios novos", i_apb)],
               " e inconsistência física das curvas previstas")
    coluna_sai(tabela_apos("Tabela B.14 – Métricas do modelo black-box"), "Inconsistência física")
    coluna_sai(tabela_apos("Tabela B.17 – Métricas do modelo black-box nos ensaios novos"), "Inconsistência física")
    n_cel = v23.tabela_de_csv(tabela_apos("Tabela B.10 – Métricas do modelo híbrido serial"), colunas(S["por"], {
        "RMSE na validação cruzada (p.p.)": S["vc"], "RMSE do white-box (p.p.)": S["por_wb"]["RMSE_pp"]}), por_ensaio)
    n_cel += v23.tabela_de_csv(tabela_apos("Tabela B.13 – Métricas do modelo híbrido serial nos ensaios novos"), colunas(S["nov"], {
        "Desvio médio (p.p.)": S["nov"]["vies_pp"], "RMSE do white-box (p.p.)": S["nov_wb"]["RMSE_pp"]}))
    n_cel += v23.tabela_de_csv(tabela_apos("Tabela B.14 – Métricas do modelo black-box"), colunas(B["por"], {
        "RMSE na validação cruzada (p.p.)": B["vc"]}), por_ensaio)
    n_cel += v23.tabela_de_csv(tabela_apos("Tabela B.17 – Métricas do modelo black-box nos ensaios novos"), colunas(B["nov"], {
        "Desvio médio (p.p.)": B["nov"]["vies_pp"]}))
    assert n_cel == (16 * 5 - 3) + 6 * 5 + (16 * 4 - 3) + 6 * 4, n_cel
    for el in G[pos("B.5 Modelo híbrido serial: ensaios do planejamento original", i_apb):]:
        if el.tag == W_P and el.getparent() is not None:
            sem_pp(el, S["fontes"] + B["fontes"])
    feito.append(f"Apêndice B: {n_cel} valores de tabela na escala da conversão")

    # ------------------------------------------------------------------ conferência final e gravação
    def vivo(el) -> str:
        return "".join((x.text or "") for r in el.iter() if r.tag in (W_R, M_R) and cor_de(r) != VERMELHO
                       for x in r if x.tag in (W_T, M_T))
    atual = [el for el in body if el.tag in (W_P, W_TBL)]
    a, b, c, d2 = (atual.index(G[i]) for i in (i_bb, i_pinn, i_ser, i_comp))
    for nome, trecho in (("5.2", atual[a:b]), ("5.5", atual[c:d2]), ("Apêndice B", atual[atual.index(G[i_apb]):])):
        resto = "".join(vivo(el) for el in trecho)
        assert not re.search(r"5\.X|5\.4\.\d|p\.p\.|percentuais|[Ii]nconsist|Apêndice E|Seção 4\.5\)", resto), f"sobra em {nome}"
    doc.save(DESTINO)
    print(f"{len(feito)} alterações; gravado: {DESTINO.name}")
    for linha in feito:
        print("  ", linha)
    assert ids_de_comentario(body) == comentarios, "marca de comentário perdida"
    print("versão limpa:", aceitar(body))
    assert ids_de_comentario(body) == comentarios, "marca de comentário perdida na versão limpa"
    doc.save(LIMPO)
    print("gravado:", LIMPO.name)


if __name__ == "__main__":
    main()
