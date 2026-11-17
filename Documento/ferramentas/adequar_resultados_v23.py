"""Gera a v23 a partir da versão 3 do grupo (`RELATÓRIO FINAL LOP - GRUPO-3.docx`, que não é alterada).

Pedido de 14/11/2026: adequar os Resultados da serial (5.5) e do black-box (5.2), e o apêndice, às seções novas dos
colegas. A referência de formato é a do white-box (5.1), que é o que o grupo combinou em 12 e 13/11 (comentários
do Google Docs exportados no próprio arquivo: tirar a inconsistência física da tabela, tirar o "p.p.", tabela dos
ensaios novos só com identificação e métricas, eixos em todos os quadros). A paralela (5.4) ainda estava em p.p.
O que muda:

1. Erros na escala da conversão (adimensional, 0 a 1), sem "p.p." e com TRÊS casas, como na tabela do white-box
   (decisão do usuário em 14/11): texto, tabelas e figuras das Seções 5.2 e 5.5 e as Seções B.5 a B.8 do apêndice.
   As tabelas são reescritas a partir dos valores brutos dos CSV (conferindo antes que a célula antiga era a da
   fonte), e os números do texto terminados em 5 são resolvidos pela fonte, para não arredondar duas vezes
   (1,45 p.p. era 1,449 e vira 0,014). As Seções B.1 a B.4 e o Apêndice A continuam com quatro casas: ali as
   comparações entre configurações estão na quarta casa. A frase da Seção 4.1.4 que definia a unidade comum
   também passa para a escala nova;
2. Tabela de desempenho com as mesmas sete colunas das dos colegas (Conjunto, Ensaios, Pontos, R2, RMSE, MAE e
   erro máximo). A coluna de inconsistência física sai da tabela da serial (na do black-box já tinha saído) e das
   duas legendas; a informação continua no texto e nas Tabelas B.14 e B.17 do apêndice;
3. Tabela dos ensaios novos só com Ensaio, RMSE, MAE e erro máximo, como a do white-box. As condições ficam na
   Tabela 4.1.2 e a conversão medida e prevista em cada instante, nas Tabelas B.12 e B.16;
4. Figuras no visual atual: números dos eixos x e y em todos os quadros, traço em t = 0, o white-box na legenda só
   como "White-box" e o RMSE de cada quadro sem "p.p.", como na figura da Seção 5.1. Trocam-se as quatro figuras
   do texto e as duas malhas 4x4 do Apêndice B (Figuras B.11 e B.12). Geradas antes por `figuras_resultados_v23.py`;
5. Comparação com o white-box nos mesmos pontos, como nos textos dos colegas (teste cego e ensaios novos);
6. Numeração definitiva (Tabelas e Figuras 5.2.n e 5.5.n) e remissões no esquema atual do documento: seção comum
   4.1, white-box 4.2, black-box 4.3, serial 4.6, apêndices A e B. As marcas da v22 que ficaram no parágrafo dos
   ensaios novos da serial são aceitas;
7. Conserto do arquivo: a exportação do Google Docs traz uma marca de comentário repetida na tabela dos ensaios
   novos do white-box, e o Word recusa o arquivo do grupo como corrompido. A marca repetida é retirada (o texto
   dos colegas não muda), e a v23 abre normalmente.

Cores: o que é frase NOVA fica em azul (0070C0), para o grupo localizar; renumeração, remissões e a troca de
unidade ficam em preto.
Uso: python figuras_resultados_v23.py && python adequar_resultados_v23.py
"""

from __future__ import annotations

import copy
import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pandas as pd
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import enxugar_apendices_v19 as v19  # noqa: E402
import marcar_grupo_v21 as m  # noqa: E402
from docx_utils import SectionWriter, pintar  # noqa: E402

DOC_DIR = v19.DOC_DIR
GRUPO = DOC_DIR / "RELATÓRIO FINAL LOP - GRUPO-3.docx"
DESTINO = DOC_DIR / "RELATÓRIO FINAL LOP_v23.docx"
FIGURAS = DOC_DIR / "figuras_v23"
RESULTADOS = DOC_DIR.parent / "Código" / "outputs" / "resultados_por_modelagem"
AZUL, VERMELHO = v19.AZUL, v19.VERMELHO
W_P, W_TBL, W_R, W_T, M_T, M_OMATH = v19.W_P, v19.W_TBL, v19.W_R, v19.W_T, v19.M_T, v19.M_OMATH
M_R = v19.M_NS + "r"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
A_BLIP = "{http://schemas.openxmlformats.org/drawingml/2006/main}blip"
R_EMBED = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
texto = v19.texto
feito: list[str] = []


# ---------------------------------------------------------------------------------------------- utilitários
def cor_de(r) -> str:
    rpr = r.find(qn("w:rPr"))
    c = rpr.find(qn("w:color")) if rpr is not None else None
    return (c.get(qn("w:val")) or "").upper() if c is not None else ""


def isolar(p, a: int, b: int, sem_amarelo: bool = False):
    """Devolve o run que contém exatamente os caracteres [a, b) do parágrafo (dividindo o run, se preciso).

    sem_amarelo: tira o realce amarelo do run de origem (ele marcava numeração provisória, 5.X.n).
    """
    pos = 0
    for ch in list(p):
        if ch.tag not in (W_R, M_OMATH, v19.M_NS + "oMathPara"):
            continue
        n = len(texto(ch))
        ini, fim = pos, pos + n
        pos = fim
        if n == 0 or fim <= a or ini >= b:
            continue
        assert ch.tag == W_R and ini <= a and b <= fim, f"trecho fora de um único run: {texto(p)[a:b]!r}"
        if sem_amarelo:   # antes de dividir, para os pedaços vizinhos (um ")" colado ao número) também perderem o realce
            for h in ch.find(qn("w:rPr")).findall(qn("w:highlight")):
                h.getparent().remove(h)
        alvo = ch
        if ini < a:
            _, alvo = v19._dividir_run(alvo, a - ini)
        if fim > b:
            alvo, _ = v19._dividir_run(alvo, b - a)
        return alvo
    raise AssertionError(f"posição {a}-{b} não encontrada em {texto(p)[:60]!r}")


def troca(p, antigo: str, novo: str, azul: bool = False, vezes: int = 1) -> None:
    """Troca `antigo` por `novo` (texto corrido, fora de equações), mantendo a formatação do trecho."""
    for _ in range(vezes):
        a = texto(p).find(antigo)
        assert a >= 0, f"não encontrado: {antigo!r} em {texto(p)[:70]!r}"
        r = isolar(p, a, a + len(antigo), sem_amarelo=True)
        t = r.find(W_T)
        t.text = novo
        t.set(XML_SPACE, "preserve")
        if azul:
            v19.pintar_run(r, AZUL)
    assert antigo not in texto(p) or antigo in novo, f"sobrou {antigo!r} em {texto(p)[:70]!r}"
    feito.append(f"{antigo} -> {novo}")


def inserir(p, depois_de: str, novo: str) -> None:
    """Insere `novo` em azul logo depois do trecho `depois_de` (aceita *itálico* e $equação$)."""
    a = texto(p).find(depois_de)
    assert a >= 0, f"não encontrado: {depois_de!r} em {texto(p)[:70]!r}"
    ancora = isolar(p, a + len(depois_de) - 1, a + len(depois_de))
    tmp = SectionWriter(None, {"body": p}, None)._new_par("body")
    SectionWriter(None, {}, None)._fill(tmp, novo)
    pintar([tmp], AZUL)
    for el in reversed([ch for ch in tmp if ch.tag != qn("w:pPr")]):
        ancora.addnext(el)
    feito.append(f"+ {novo.strip()[:90]}")


def aceitar_marcas(p) -> None:
    """Num parágrafo com as marcas da v22: apaga o vermelho tachado e deixa o azul em preto."""
    for ch in list(p):
        if ch.tag == W_R and cor_de(ch) == VERMELHO:
            p.remove(ch)
        elif ch.tag == M_OMATH and all(cor_de(r) == VERMELHO for r in ch.iter(M_R)):
            p.remove(ch)
    for c in list(p.iter(qn("w:color"))):
        if (c.get(qn("w:val")) or "").upper() == AZUL:
            c.getparent().remove(c)
    ult = [t for t in p.iter(W_T) if t.text]
    ult[-1].text = ult[-1].text.rstrip()
    assert not any(cor_de(r) for r in p.iter(W_R)), "sobrou cor no parágrafo"


def trocar_imagem(doc, p, arquivo: Path) -> None:
    """Substitui os bytes da imagem do parágrafo (mesma proporção: o tamanho no Word não muda)."""
    from PIL import Image

    blips = list(p.iter(A_BLIP))
    assert len(blips) == 1, "esperava uma imagem no parágrafo"
    parte = doc.part.related_parts[blips[0].get(R_EMBED)]
    import io
    antiga, nova = Image.open(io.BytesIO(parte.blob)).size, Image.open(arquivo).size
    assert abs(antiga[0] / antiga[1] - nova[0] / nova[1]) < 0.005, f"proporção diferente: {antiga} x {nova}"
    usos = sum(1 for b in doc.element.body.iter(A_BLIP) if doc.part.related_parts[b.get(R_EMBED)] is parte)
    assert usos == 1, "imagem usada em mais de um lugar"
    parte._blob = arquivo.read_bytes()
    feito.append(f"figura trocada: {arquivo.name}")


def tirar_ultima_coluna(tbl, cabecalho: str) -> None:
    linhas = tbl.findall(qn("w:tr"))
    assert cabecalho in texto(linhas[0].findall(qn("w:tc"))[-1]), texto(linhas[0])
    for tr in linhas:
        tr.remove(tr.findall(qn("w:tc"))[-1])
    grade = tbl.find(qn("w:tblGrid"))
    for alt in grade.findall(qn("w:tblGridChange")):
        grade.remove(alt)
    cols = grade.findall(qn("w:gridCol"))
    grade.remove(cols[-1])
    tbl.find(qn("w:tblPr")).find(qn("w:tblW")).set(qn("w:w"), str(sum(int(c.get(qn("w:w"))) for c in cols[:-1])))
    feito.append(f"coluna retirada da tabela: {cabecalho}")


def consertar_comentarios(body) -> int:
    """Tira marcas de comentário repetidas (mesmo id), que fazem o Word recusar o arquivo como corrompido.

    A exportação do Google Docs de 13/11 repete o fim e a referência do comentário 139 dentro da tabela dos ensaios
    novos do white-box (Seção 5.1). Fica a primeira ocorrência de cada marca; o texto não muda.
    """
    n = 0
    for nome in ("commentRangeStart", "commentRangeEnd", "commentReference"):
        vistos = set()
        for x in list(body.iter(qn(f"w:{nome}"))):
            ident = x.get(qn("w:id"))
            if ident not in vistos:
                vistos.add(ident)
                continue
            pai = x.getparent()
            pai.remove(x)
            if pai.tag == W_R and all(ch.tag == qn("w:rPr") for ch in pai):   # run que só tinha a referência
                pai.getparent().remove(pai)
            n += 1
    return n


def num(x: float, casas: int = 1) -> str:
    return f"{x:.{casas}f}".replace(".", ",")


# ---------------------------------------------------------------------------------------------- sem "p.p.", 3 casas
NUMERO = r"[−-]?\d+,\d+"
SEQUENCIA_PP = re.compile(rf"((?:{NUMERO}(?:; | e | ± | a ))*{NUMERO}) p\.p\.")
MILESIMO = Decimal("0.001")
convertidos: list[str] = []


def tres(x: float) -> str:
    """Erro na escala da conversão (0 a 1) com três casas, a partir do valor bruto: 0.016457 -> '0,016'."""
    d = Decimal(repr(abs(float(x)))).quantize(MILESIMO, rounding=ROUND_HALF_UP)
    return ("−" if x < 0 and d != 0 else "") + f"{d:.3f}".replace(".", ",")


def duas(x: float) -> str:
    """Valor em p.p. com duas casas, como estava escrito nas versões anteriores (serve para conferir a fonte)."""
    d = Decimal(repr(abs(float(x)))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return ("−" if x < 0 and d != 0 else "") + f"{d:.2f}".replace(".", ",")


def fracao(s: str, fontes=()) -> str:
    """'4,87' (p.p.) -> '0,049' (escala da conversão, três casas).

    Com uma casa em p.p. a conversão é exata. Com duas, o arredondamento só é ambíguo quando o número termina em 5
    ('1,45' pode ser 1,449 ou 1,451): nesse caso o valor bruto é procurado em `fontes` (valores em p.p. dos CSV),
    para não arredondar duas vezes.
    """
    negativo = s[0] in "−-"
    d = Decimal(s.lstrip("−-").replace(",", "."))
    if -d.as_tuple().exponent == 2 and s[-1] == "5":
        achados = {tres(v / 100) for v in fontes if duas(abs(v)) == s.lstrip("−-")}
        assert len(achados) == 1, f"valor bruto de {s} p.p. não encontrado ou ambíguo nas fontes: {achados}"
        return ("−" if negativo else "") + achados.pop().lstrip("−")
    return ("−" if negativo else "") + f"{(d / 100).quantize(MILESIMO, rounding=ROUND_HALF_UP):.3f}".replace(".", ",")


def sem_pp(p, fontes=()) -> None:
    """Converte todo 'N p.p.' do parágrafo (inclusive listas como '5,9; 5,7 e 4,5 p.p.') para a escala da conversão."""
    while True:
        k = SEQUENCIA_PP.search(texto(p))
        if k is None:
            break
        depois = texto(p)[k.end():]
        fim_de_frase = not depois.strip() or re.match(r" [A-ZÀ-Ý]", depois) is not None   # o ponto de "p.p." fechava a frase
        novo = re.sub(NUMERO, lambda x: fracao(x.group(0), fontes), k.group(1)) + ("." if fim_de_frase else "")
        a = k.start()
        r = isolar(p, a, k.end())
        r.find(W_T).text = novo
        r.find(W_T).set(XML_SPACE, "preserve")
        convertidos.append(f"{k.group(0)} -> {novo}")
    assert "p.p." not in texto(p), texto(p)


def escrever_celula(tc, txt: str) -> None:
    ts = list(tc.iter(W_T))
    assert ts and not list(tc.iter(M_T)), f"célula com equação ou vazia: {texto(tc)!r}"
    ts[0].text = txt
    ts[0].set(XML_SPACE, "preserve")
    for t in ts[1:]:
        t.text = ""


def tabela_de_csv(tbl, colunas: dict, chave=lambda s: s) -> int:
    """Reescreve as colunas de erro de uma tabela na escala da conversão, com três casas, a partir dos CSV.

    colunas: {cabeçalho atual, com '(p.p.)': série em p.p. indexada pelo rótulo da primeira coluna}. Antes de
    escrever, confere que o valor que estava na célula (p.p., duas casas) é o da fonte: garante a correspondência
    entre linhas, colunas e CSV. Devolve o número de células reescritas.
    """
    linhas = tbl.findall(qn("w:tr"))
    cab = [texto(tc).strip() for tc in linhas[0].findall(qn("w:tc"))]
    assert {c for c in cab if "(p.p.)" in c} == set(colunas), (cab, list(colunas))
    n = 0
    for nome, serie in colunas.items():
        j = cab.index(nome)
        escrever_celula(linhas[0].findall(qn("w:tc"))[j], nome.replace("(p.p.)", "(–)"))
        for tr in linhas[1:]:
            tcs = tr.findall(qn("w:tc"))
            rotulo, antigo = chave(texto(tcs[0]).strip()), texto(tcs[j]).strip()
            if antigo == "–":
                assert rotulo not in serie.index or pd.isna(serie.loc[rotulo]), (nome, rotulo)
                continue
            bruto = float(serie.loc[rotulo])
            assert antigo == duas(bruto), f"{nome}, linha {rotulo}: a tabela tinha {antigo} e a fonte dá {duas(bruto)}"
            escrever_celula(tcs[j], tres(bruto / 100))
            n += 1
    assert "p.p." not in texto(tbl)
    return n


def tabela_ensaios_novos(tbl, metricas) -> None:
    """Tabela dos ensaios novos só com identificação e métricas, como a do white-box (Seção 5.1).

    Saem as colunas que repetem a Tabela 4.1.2 (C_A0, η e limite) e a conversão em 15 min, que está no Apêndice B;
    entra o MAE. `metricas`: tabela dos CSV congelados, por ensaio, com RMSE_pp, MAE_pp e Emax_pp.
    """
    linhas = tbl.findall(qn("w:tr"))
    cab = [texto(tc).strip() for tc in linhas[0].findall(qn("w:tc"))]
    assert len(cab) == 8 and cab[0] == "Ensaio" and cab[6] == "RMSE (p.p.)" and cab[7] == "Erro máximo (p.p.)", cab
    for i, tr in enumerate(linhas):
        tcs = tr.findall(qn("w:tc"))
        for tc in tcs[1:6]:
            tr.remove(tc)
        ensaio, rmse, emax = tcs[0], tcs[6], tcs[7]
        mae = copy.deepcopy(rmse)
        rmse.addnext(mae)
        if i == 0:
            for tc, t in ((rmse, "RMSE (–)"), (mae, "MAE (–)"), (emax, "Erro máximo (–)")):
                escrever_celula(tc, t)
        else:
            r, a, x = (float(metricas.loc[texto(ensaio).strip(), c]) for c in ("RMSE_pp", "MAE_pp", "Emax_pp"))
            assert (texto(rmse).strip(), texto(emax).strip()) == (duas(r), duas(x)), (texto(rmse), r, texto(emax), x)   # a tabela antiga confere com o CSV
            for tc, v in ((rmse, r), (mae, a), (emax, x)):
                escrever_celula(tc, tres(v / 100))
    grade = tbl.find(qn("w:tblGrid"))
    for ch in list(grade):
        grade.remove(ch)
    larguras = (1300, 1500, 1500, 1900)
    for w in larguras:
        grade.append(parse_xml(f'<w:gridCol {nsdecls("w")} w:w="{w}"/>'))
    tbl.find(qn("w:tblPr")).find(qn("w:tblW")).set(qn("w:w"), str(sum(larguras)))
    for tcw in tbl.iter(qn("w:tcW")):   # se houver largura por célula, vale a da grade
        tcw.getparent().remove(tcw)
    feito.append("tabela dos ensaios novos: Ensaio, RMSE, MAE e erro máximo")


# ---------------------------------------------------------------------------------------------- números
SAIDAS = DOC_DIR.parent / "Código" / "outputs"
OTIMIZACAO = SAIDAS / "etapa_3_2" / "subetapa_3_2_6_mlp_otimizacao"
CV_MLP_PURA = SAIDAS / "etapa_4_5_auditoria_serial" / "item_3_mlp_pura_10_sementes"
WB_NOME = "White-box (novo)"


def numeros() -> dict:
    """Tabelas dos CSV congelados (erros em p.p.) e, por modelo, todos os valores citados no texto (`fontes`)."""
    out = {}
    for nome, rotulo in (("serial", "Híbrido serial"), ("mlp_pura", "MLP pura")):
        res = pd.read_csv(RESULTADOS / nome / "metricas_resumo.csv")
        por = pd.read_csv(RESULTADOS / nome / "metricas_por_ensaio.csv")
        nov = pd.read_csv(RESULTADOS / nome / "ensaios_novos" / "metricas_ensaios_novos.csv").replace({"ensaio": {"Sem E1": "Sem o E1"}})
        d = {"res": res[res["modelo"] == rotulo].set_index("particao"), "res_wb": res[res["modelo"] == WB_NOME].set_index("particao"),
             "por": por[por["modelo"] == rotulo].set_index("ensaio"), "por_wb": por[por["modelo"] == WB_NOME].set_index("ensaio"),
             "nov": nov[nov["modelo"] == rotulo].set_index("ensaio"), "nov_wb": nov[nov["modelo"] == WB_NOME].set_index("ensaio")}
        if nome == "serial":
            erro = pd.read_csv(SAIDAS / "etapa_4_4_resultados_hibrido_serial" / "tabela_erro_por_ensaio.csv").set_index("ensaio")
            d["vc"] = 100 * erro["RMSE_v2_fora_da_dobra"]
            fin = pd.read_csv(OTIMIZACAO / "fase_b2" / "tabela_fase_b2_finalistas.csv").set_index("config").loc["B2 – tentativa 511"]
            dob = pd.read_csv(OTIMIZACAO / "fase_b2" / "finalistas_por_dobra.csv")
            dob = dob[dob["config"] == "B2 – tentativa 511"].groupby("fold")["RMSE_X"].mean()
            mem = pd.read_csv(OTIMIZACAO / "fase_e" / "tabela_fase_e_membros_teste_cego.csv")["RMSE_teste_cego"]
            pred = pd.read_csv(SAIDAS / "etapa_4_2_avaliacao_indomain" / "tabela_predicoes_detalhadas_16_ensaios.csv")
            pred = pred[pred["t_min"] > 0]
            faixa = pred["XZn_Hibrido_MLP_v2_max"] - pred["XZn_Hibrido_MLP_v2_min"]
            teto = float(pd.read_csv(OTIMIZACAO / "fase_a" / "tabela_fase_a_resumo.csv").set_index("referencia")["valor"]["teto"])
            soltos = [fin["RMSE_X_media"], fin["RMSE_X_dp"], *dob, mem.mean(), mem.std(ddof=1), faixa.mean(), faixa.max(), teto]
        else:
            d["vc"] = 100 * pd.read_csv(CV_MLP_PURA / "tabela_v2_vs_mlp_pura_por_ensaio.csv").set_index("ensaio")["RMSE_mlp_pura"]
            cv = pd.read_csv(CV_MLP_PURA / "cv_mlp_pura_10_sementes.csv")["RMSE_mlp_pura"]
            mem = pd.read_csv(RESULTADOS / nome / "membros_teste_cego.csv")["RMSE_teste_cego"]
            faixa = pd.read_csv(RESULTADOS / nome / "faixa_entre_membros_112_pontos.csv")["faixa_entre_membros"]
            soltos = [cv.mean(), cv.std(ddof=1), mem.mean(), mem.std(ddof=1), mem.min(), mem.max(), faixa.mean(), faixa.max()]
        colunas = ["RMSE_pp", "MAE_pp", "Emax_pp"]
        # só o que o texto cita com duas casas: resumo por conjunto, RMSE dos três ensaios de teste e valores avulsos
        # (as tabelas por ensaio são reescritas célula a célula, direto da fonte, por `tabela_de_csv`)
        d["fontes"] = [float(v) for t in (d["res"], d["res_wb"]) for v in t[colunas].to_numpy().ravel()]
        d["fontes"] += [float(v) for v in d["por"].loc[[7, 8, 14], "RMSE_pp"]] + [100 * float(v) for v in soltos]
        d["reducao"] = 100 * (1 - d["res"].loc["Teste cego", "RMSE_pp"] / d["res_wb"].loc["Teste cego", "RMSE_pp"])
        novos = ["E1", "E2", "E3", "E4"]   # o que as frases afirmam: melhor que o white-box em E2 e E3, pior em E1 e E4
        dif = d["nov"].loc[novos, "RMSE_pp"] - d["nov_wb"].loc[novos, "RMSE_pp"]
        assert (dif[["E2", "E3"]] < 0).all() and (dif[["E1", "E4"]] > 0).all()
        out[nome] = d
    assert out["serial"]["nov_wb"]["RMSE_pp"].equals(out["mlp_pura"]["nov_wb"]["RMSE_pp"])
    return out


# ---------------------------------------------------------------------------------------------- principal
def main() -> None:
    doc = m.abrir(GRUPO)
    body = doc.element.body
    print("sdt removidos:", m.desembrulhar(body))
    print("marcas de comentário repetidas retiradas:", consertar_comentarios(body))
    m.garantir_rpr(body)
    G = [el for el in body if el.tag in (W_P, W_TBL)]

    def pos(comeco: str, a: int = 0, b: int | None = None, exato: bool = False) -> int:
        alvo = m.sem_espaco(comeco)
        for i in range(a, len(G) if b is None else b):
            t = m.sem_espaco(texto(G[i]))
            if G[i].tag == W_P and (t == alvo if exato else t.startswith(alvo)):
                return i
        raise AssertionError(f"parágrafo não encontrado: {comeco!r}")

    i_res = pos("RESULTADOS E DISCUSSÃO", exato=True)
    i_fim = pos("CONCLUSÕES", i_res, exato=True)
    i_bb = pos("MODELO PURAMENTE ORIENTADO A DADOS (BLACK-BOX)", i_res, i_fim, exato=True)
    i_pinn = pos("MODELAGEM HÍBRIDA VIA REDES NEURAIS", i_bb, i_fim)
    i_ser = pos("MODELAGEM HÍBRIDA SERIAL", i_res, i_fim, exato=True)
    i_comp = pos("Comparação final", i_ser, i_fim, exato=True)
    N = numeros()
    S, B = N["serial"], N["mlp_pura"]
    wb_teste = tres(S["res_wb"].loc["Teste cego", "RMSE_pp"] / 100)
    wbn = {e: tres(S["nov_wb"].loc[e, "RMSE_pp"] / 100) for e in ("E1", "E2", "E3", "E4")}
    assert (wb_teste, wbn) == ("0,078", {"E1": "0,081", "E2": "0,117", "E3": "0,072", "E4": "0,036"}), (wb_teste, wbn)
    ERROS = {"RMSE (p.p.)": "RMSE_pp", "MAE (p.p.)": "MAE_pp", "Erro máximo (p.p.)": "Emax_pp"}

    def colunas(tabela, extras=None) -> dict:
        return {cab: tabela[col] for cab, col in ERROS.items()} | (extras or {})

    def por_ensaio(rotulo: str) -> int:
        return int(rotulo.rstrip("*"))
    ESCALA = "na mesma escala da conversão de zinco, adimensional e entre 0 e 1"

    def bb(comeco: str):
        return G[pos(comeco, i_bb, i_pinn)]

    def ser(comeco: str):
        return G[pos(comeco, i_ser, i_comp)]

    def figura_depois(i: int):
        return next(el for el in G[i:] if el.tag == W_P and el.find(".//" + A_BLIP) is not None)

    def legenda_sem_inconsistencia(p) -> None:
        k = re.search(r", erro máximo e inconsistência física \(.*\)\s*$", texto(p))
        assert k and "(MAE)" in texto(p)[:k.start()]
        troca(p, texto(p)[k.start():], " e erro máximo")

    def legenda_ensaios_novos(p) -> None:
        troca(p, " – Ensaios novos: condições, limite estequiométrico, conversão de zinco medida e prevista pelo modelo ",
              " – Desempenho do modelo ")
        troca(p, " em 15 min e erros da previsão nos seis instantes de amostragem",
              " nos ensaios novos: RMSE, erro absoluto médio (MAE) e erro máximo nos seis instantes de amostragem")

    # ------------------------------------------------------------------ 4.1.4: a unidade dos erros, comum a todos
    i_met = pos("MATERIAIS E MÉTODOS", exato=True)
    troca(G[pos("O desempenho de todos os modelos é quantificado", i_met, i_res)],
          "em pontos percentuais (p.p.) de conversão", ESCALA)

    # ------------------------------------------------------------------ 5.2 black-box
    # primeiro a unidade (os trechos usados como âncora mais abaixo já estão na escala nova)
    p = bb("Esta seção apresenta os resultados do modelo puramente orientado a dados")
    troca(p, "em pontos percentuais (p.p.) de conversão", ESCALA)
    for el in G[i_bb:i_pinn]:
        if el.tag == W_P:
            sem_pp(el, B["fontes"])
    troca(p, "nas Seções 4.1.4 a 4.1.7", "na Seção 4.3")
    troca(p, "Seção 4.2.4", "Seção 4.1.4")
    troca(bb("Nos 13 ensaios de treino, o RMSE foi de"), "5.X.1", "5.2.1")
    p = bb("Nos Ensaios 7, 8 e 14, reservados para o teste cego")
    troca(p, "Seção 4.2.3", "Seção 4.1.3")
    assert round(B["reducao"]) == 76
    inserir(p, "e 0,018 no Ensaio 14.", f" Frente ao RMSE de {wb_teste} do modelo *white-box* nos mesmos 21 pontos, "
                                         f"o erro foi cerca de {B['reducao']:.0f}% menor.")
    inserir(p, "conversão decrescente ou acima do limite estequiométrico", " (Tabela B.14)")
    p = bb("Tabela 5.X.1")
    troca(p, "5.X.1", "5.2.1")
    legenda_sem_inconsistencia(p)
    tbl = G[G.index(p) + 1]
    assert tbl.tag == W_TBL and len(tbl.find(qn("w:tr")).findall(qn("w:tc"))) == 7   # a coluna já tinha saído
    assert tabela_de_csv(tbl, colunas(B["res"])) == 9
    p = bb("A Figura 5.X.1 compara as curvas previstas")
    troca(p, "5.X.1", "5.2.1")
    troca(p, " da Seção 4.1.", " da Seção 4.2.")
    troca(p, "estão no Apêndice E", "estão na Seção B.7")
    trocar_imagem(doc, figura_depois(G.index(p)), FIGURAS / "fig_mlp_pura_2x2_texto_ensaios_01_07_08_14.png")
    troca(bb("Figura 5.X.1 – Conversão de zinco medida e prevista"), "5.X.1", "5.2.1")
    troca(bb("Na validação cruzada por ensaio, com as mesmas quatro dobras"), "Seção 4.5.2", "Seção 4.6.3")
    p = bb("Nos quatro ensaios novos, descritos na Seção 5.4")
    troca(p, "descritos na Seção 5.4", "descritos na Seção 4.1.2")
    troca(p, "5.X.2", "5.2.2", vezes=2)
    inserir(p, "dos nós das curvas apresentaram conversão decrescente.",
            f" O erro foi inferior ao do modelo *white-box* em E2 e E3 ({wbn['E2']} e {wbn['E3']}) e superior em E1 e E4 "
            f"({wbn['E1']} e {wbn['E4']}), ensaios em que o *white-box* atinge exatamente o limite estequiométrico.")
    p = bb("Tabela 5.X.2")
    troca(p, "5.X.2", "5.2.2")
    legenda_ensaios_novos(p)
    tabela_ensaios_novos(G[G.index(p) + 1], B["nov"])
    p = bb("Figura 5.X.2")
    troca(p, "5.X.2", "5.2.2")
    trocar_imagem(doc, G[G.index(p) - 1], FIGURAS / "fig_mlp_pura_2x2_ensaios_novos.png")
    resto = "".join(texto(el) for el in G[i_bb:i_pinn])
    assert not re.search(r"5\.X|p\.p\.|percentuais", resto), "sobrou numeração provisória ou p.p. no black-box"

    # ------------------------------------------------------------------ 5.5 serial
    p = ser("Esta seção apresenta os resultados do modelo híbrido serial")
    troca(p, "em pontos percentuais (p.p.) de conversão de zinco e calculados", ESCALA + ", e calculados")
    for el in G[i_ser:i_comp]:
        if el.tag == W_P and not any(cor_de(r) == VERMELHO for r in el.iter(W_R)):   # o parágrafo com marcas da v22 não tem p.p.
            sem_pp(el, S["fontes"])
    troca(p, "(Seção 4.5)", "(Seção 4.6)")
    troca(p, "Seção 4.2.4", "Seção 4.1.4")
    p = ser("Nos 13 ensaios de treino, o modelo reproduziu a conversão medida")
    troca(p, "Tabela 5.4.1", "Tabela 5.5.1")
    troca(p, "(Seção A.5)", "(Tabela B.1)")
    p = ser("Nos Ensaios 7, 8 e 14, reservados para o teste cego")
    assert round(S["reducao"]) == 74
    inserir(p, "e 0,011 no Ensaio 14.", f" Frente ao RMSE de {wb_teste} do modelo *white-box* nos mesmos 21 pontos, "
                                         f"o erro foi cerca de {S['reducao']:.0f}% menor.")
    troca(p, "Tabela 4.2.2", "Tabela 4.1.3")
    p = ser("Tabela 5.4.1")
    troca(p, "Tabela 5.4.1", "Tabela 5.5.1")
    legenda_sem_inconsistencia(p)
    tbl = G[G.index(p) + 1]
    assert tbl.tag == W_TBL
    tirar_ultima_coluna(tbl, "Inconsistência física")
    assert tabela_de_csv(tbl, colunas(S["res"])) == 9
    p = ser("A Figura 5.4.1 compara as curvas previstas")
    troca(p, "Figura 5.4.1", "Figura 5.5.1")
    troca(p, " da Seção 4.1;", " da Seção 4.2;")
    troca(p, "estão no Apêndice E", "estão na Seção B.5")
    trocar_imagem(doc, figura_depois(G.index(p)), FIGURAS / "fig_serial_2x2_texto_ensaios_01_07_08_14.png")
    troca(ser("Figura 5.4.1 – Conversão de zinco medida e prevista"), "Figura 5.4.1", "Figura 5.5.1")
    p = ser("Como o teste cego reúne apenas três ensaios")
    troca(p, "Seções 4.5.2 e 4.5.5", "Seções 4.6.3 e 4.6.6")
    troca(p, "(Seção D.6)", "(Tabela B.10)")
    p = ser("O modelo foi confrontado também com quatro ensaios novos")
    aceitar_marcas(p)
    troca(p, "Tabela 5.4.2", "Tabela 4.1.2")   # as condições dos ensaios novos ficam só na seção comum
    assert texto(p) == ("O modelo foi confrontado também com quatro ensaios novos (E1 a E4), descritos na Seção 4.1.2 (Tabela 4.1.2). "
                        "As previsões foram geradas com o modelo já definido, sem novo ajuste, e registradas antes de as medições "
                        "estarem disponíveis (Seção B.4)."), texto(p)
    p = ser("Tabela 5.4.2 – Ensaios novos")
    troca(p, "Tabela 5.4.2", "Tabela 5.5.2")
    legenda_ensaios_novos(p)
    tabela_ensaios_novos(G[G.index(p) + 1], S["nov"])
    p = ser("Com essa correção, o RMSE foi de")
    troca(p, "Com essa correção", "Com os rótulos de E2 e E3 trocados (Seção 4.1.2)", azul=True)
    troca(p, "(Figura 5.4.2)", "(Tabela 5.5.2 e Figura 5.5.2)")
    inserir(p, "diferiu da medida em 0,007 e 0,018", " (Tabela B.12)")
    inserir(p, "e os maiores desvios ocorreram até 3 min",
            f"; nesses dois ensaios, o erro foi inferior ao do modelo *white-box* ({wbn['E2']} e {wbn['E3']})")
    inserir(p, "não pode reproduzir os valores medidos",
            f", e o modelo *white-box*, que atinge exatamente o limite estequiométrico, teve erro menor ({wbn['E1']} e {wbn['E4']})")
    p = ser("Figura 5.4.2 – Conversão de zinco medida e prevista")
    troca(p, "Figura 5.4.2", "Figura 5.5.2")
    trocar_imagem(doc, G[G.index(p) - 1], FIGURAS / "fig_serial_2x2_ensaios_novos.png")
    resto = "".join(texto(el) for el in G[i_ser:i_comp])
    assert not re.search(r"5\.4\.\d|Seção 4\.5|4\.2\.[234]|Apêndice E|D\.\d|p\.p\.|percentuais", resto), "sobrou remissão antiga ou p.p. na serial"

    # ------------------------------------------------------------------ Apêndice B: malhas 4x4 e escala dos erros
    i_apb = pos("APÊNDICE B - RESULTADOS COMPLEMENTARES", i_fim)
    troca(G[pos("Este apêndice reúne os resultados da seleção da configuração", i_apb)],
          "Nas Seções B.5 a B.8, os erros estão em pontos percentuais (p.p.) de conversão.",
          "Os erros estão " + ESCALA + ".")
    trocar_imagem(doc, G[pos("Figura B.11 – Conversão de zinco medida e prevista pelo modelo híbrido serial", i_apb) - 1],
                  FIGURAS / "fig_serial_4x4_todos.png")
    trocar_imagem(doc, G[pos("Figura B.12 – Conversão de zinco medida e prevista pelo modelo black-box", i_apb) - 1],
                  FIGURAS / "fig_mlp_pura_4x4_todos.png")
    def tabela_apos(legenda: str):
        tbl = G[pos(legenda, i_apb) + 1]
        assert tbl.tag == W_TBL
        return tbl

    n_cel = tabela_de_csv(tabela_apos("Tabela B.10 – Métricas do modelo híbrido serial"), colunas(S["por"], {
        "RMSE na validação cruzada (p.p.)": S["vc"], "RMSE do white-box (p.p.)": S["por_wb"]["RMSE_pp"]}), por_ensaio)
    n_cel += tabela_de_csv(tabela_apos("Tabela B.13 – Métricas do modelo híbrido serial nos ensaios novos"), colunas(S["nov"], {
        "Desvio médio (p.p.)": S["nov"]["vies_pp"], "RMSE do white-box (p.p.)": S["nov_wb"]["RMSE_pp"]}))
    n_cel += tabela_de_csv(tabela_apos("Tabela B.14 – Métricas do modelo black-box"), colunas(B["por"], {
        "RMSE na validação cruzada (p.p.)": B["vc"]}), por_ensaio)
    n_cel += tabela_de_csv(tabela_apos("Tabela B.17 – Métricas do modelo black-box nos ensaios novos"), colunas(B["nov"], {
        "Desvio médio (p.p.)": B["nov"]["vies_pp"]}))
    for el in G[pos("B.5 Modelo híbrido serial: ensaios do planejamento original", i_apb):]:
        if el.tag == W_P:
            sem_pp(el, S["fontes"] + B["fontes"])
    # Tabelas B.10 (16 x 5), B.13 (6 x 5), B.14 (16 x 4) e B.17 (6 x 4); os 3 ensaios de teste não têm validação cruzada
    assert n_cel == (16 * 5 - 3) + 6 * 5 + (16 * 4 - 3) + 6 * 4, n_cel
    assert not re.search(r"p\.p\.|percentuais", "".join(texto(el) for el in G[i_apb:])), "sobrou p.p. no Apêndice B"
    feito.append(f"Apêndice B: {n_cel} valores de tabela convertidos para a escala da conversão")

    doc.save(DESTINO)
    for linha in feito:
        print("  ", linha)
    print("conversões de p.p. no texto:")
    for linha in convertidos:
        print("    ", linha)
    print(f"{len(feito)} alterações e {len(convertidos)} conversões de unidade no texto; gravado: {DESTINO.name}")


if __name__ == "__main__":
    main()
