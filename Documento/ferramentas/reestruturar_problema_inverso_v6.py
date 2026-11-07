"""Gera a v6 do relatório a partir da v5, retirando do híbrido serial o que já está na seção do white box.

O que é feito (apenas na seção "Modelagem híbrida serial", dentro de Métodos):
- remove a subseção "Elementos do modelo fenomenológico utilizados no acoplamento", cujo conteúdo
  (retração uniforme, MOC, X(δ) e balanço de ácido) já está nas Seções 4.2.1 e 4.2.2 do colega;
- insere no início de "Obtenção da taxa de retração por problema inverso" um parágrafo de ligação
  com a Seção 4.2.2 (e a distinção entre v, da lei cinética, e ν, aprendida pela rede);
- leva para o problema inverso o cálculo tabelado de X(δ) (600 valores de δ, regra do trapézio em
  5000 diâmetros, PCHIP), junto com a figura da curva;
- ajusta as referências cruzadas que apontavam para a subseção removida e renumera os marcadores
  provisórios de figuras (4.X.n) e equações (4.X.n) da seção.

A v5 não é alterada; o resultado é salvo como RELATÓRIO FINAL LOP_v6.docx.
"""

from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

import docx
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

sys.path.insert(0, str(Path(__file__).parent))
from docx_utils import PLACEHOLDER_RE, SectionWriter  # noqa: E402

DOC_DIR = Path(__file__).resolve().parents[1]
ORIGEM = DOC_DIR / "RELATÓRIO FINAL LOP_v5.docx"
DESTINO = DOC_DIR / "RELATÓRIO FINAL LOP_v6.docx"

TITULO_SERIAL = "MODELAGEM HÍBRIDA SERIAL: APRENDIZADO DA TAXA DE RETRAÇÃO DAS PARTÍCULAS"
SUB_REMOVIDA = "Elementos do modelo fenomenológico utilizados no acoplamento"
SUB_INVERSO = "Obtenção da taxa de retração por problema inverso"

# Numeração antiga -> nova. A figura 4.X.3 (retração uniforme) e as equações 4.X.1 a 4.X.4 saem;
# a curva X(δ), antiga 4.X.4, passa a vir depois das figuras do problema inverso.
FIGURAS = {1: 1, 2: 2, 5: 3, 6: 4, 7: 5, 4: 6}
for n in range(8, 18):
    FIGURAS[n] = n - 1
EQUACOES = {n: n - 4 for n in range(5, 29)}

TEXTO_LIGACAO = (
    "Conforme apresentado na Seção 4.2.2, quando a reação química na interface controla o processo, "
    "todas as partículas sofrem a mesma retração diametral acumulada, $\\delta(t)$, e a conversão de "
    "zinco passa a depender apenas desse valor e da distribuição granulométrica inicial. Com isso, o "
    "comportamento da população de partículas e, por meio do balanço de ácido, o da fase líquida "
    "ficam determinados por uma única função do tempo, a taxa de retração diametral. No modelo "
    "fenomenológico, essa taxa corresponde à velocidade de retração $v$ dada pela lei cinética de "
    "reação interfacial, com a constante $k_s$; no modelo híbrido, ela é estimada pela rede neural e, "
    "para distinguir as duas, é representada nesta seção por $\\nu(t)=-dD/dt$. As demais relações, "
    "isto é, a translação da distribuição, a conversão em função de $\\delta$ e o balanço de ácido, "
    "são as mesmas do modelo fenomenológico e foram utilizadas com as mesmas hipóteses: partículas "
    "esféricas, ausência de quebra ou aglomeração e proporção estequiométrica unitária entre o ácido "
    "sulfúrico e o óxido de zinco."
)

TEXTO_TABELA_X = (
    "Na relação $X_{\\mathrm{Zn}}(\\delta)$, dada pela razão entre o terceiro momento da distribuição "
    "remanescente e o seu valor inicial, a distribuição inicial em número de partículas foi integrada "
    "até $D_{\\mathrm{max}}=297$ µm, que corresponde à maior abertura de peneira empregada na "
    "caracterização granulométrica. Como a função objetivo descrita a seguir é avaliada repetidas "
    "vezes ao longo da otimização de cada ensaio, e como a conversão depende apenas de $\\delta$, e "
    "não do caminho percorrido até atingi-lo, essa relação foi calculada uma única vez, antes das "
    "simulações, e armazenada na forma de tabela. Para isso, tomaram-se 600 valores de $\\delta$ "
    "igualmente espaçados entre 0 e $D_{\\mathrm{max}}$, o que corresponde a um intervalo de "
    "aproximadamente 0,5 µm, e, para cada um deles, as integrais do numerador e do denominador foram "
    "avaliadas pela regra do trapézio em uma malha de 5000 diâmetros igualmente espaçados entre 0,01 "
    "e 297 µm."
)

TEXTO_PCHIP = (
    "Durante as simulações, a conversão correspondente a valores intermediários de $\\delta$ foi "
    "obtida por interpolação cúbica monótona (PCHIP, do inglês *Piecewise Cubic Hermite Interpolating "
    "Polynomial*), que preserva o caráter crescente da curva e evita oscilações sem significado físico "
    "entre os pontos tabelados (Fritsch; Carlson, 1980). A mesma tabela é utilizada na simulação do "
    "modelo fenomenológico puro, o que torna as comparações entre os modelos independentes da forma "
    "de cálculo da conversão. A curva resultante é apresentada na Figura 4.X.4."
)

TEXTO_LEITURA_CURVA = (
    "Observa-se que a conversão cresce rapidamente nos primeiros micrômetros de retração: metade do "
    "ZnO é convertida com $\\delta$ de aproximadamente 5 µm e 90% com cerca de 27 µm, reflexo da "
    "parcela expressiva da massa inicial associada às partículas finas. A partir de cerca de 72 µm, "
    "a conversão supera 99% e a curva torna-se praticamente plana, de modo que diferenças na taxa de "
    "retração nessa região têm efeito pequeno sobre a conversão calculada."
)

# (início do parágrafo, trecho antigo, trecho novo). Referências novas escritas na numeração antiga,
# para que a renumeração final as converta junto com as demais.
SUBSTITUICOES = [
    ("Para treinar a rede neural, é necessário",
     "ao ser inserida nas Equações (4.X.1) a (4.X.3), reproduz",
     "ao ser integrada no tempo e convertida pela relação entre a retração acumulada e a conversão "
     "(Seção 4.2.2), reproduz"),
    ("Com ",
     " pré-calculada (Figura 4.X.4) e esse",
     " deduzida na Seção 4.2.2, e esse"),
    ("A taxa de retração foi tratada como uma função direta",
     "pela integração da Equação (4.X.1)",
     "pela integração numérica da Equação (4.X.6)"),
    ("A primeira decisão foi a grandeza a ser avaliada",
     "(Equação 4.X.1)",
     "(Seção 4.2.2)"),
    ("A primeira operação garante que a conversão não diminua",
     "calculada pela Equação 4.X.4.",
     "calculada pelo balanço de ácido da Seção 4.2.2 (Equação 3.XX)."),
    ("balanço populacional (Eqs.",
     "balanço populacional (Eqs. 4.X.1 a 4.X.3)",
     "balanço populacional (Seção 4.2.2)"),
]


def texto(el) -> str:
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def novo_run(base_rpr, trecho: str, destacar: bool):
    r = parse_xml(f"<w:r {nsdecls('w')}/>")
    rpr = copy.deepcopy(base_rpr) if base_rpr is not None else parse_xml(f"<w:rPr {nsdecls('w')}/>")
    for h in rpr.findall(qn("w:highlight")):
        rpr.remove(h)
    if destacar:
        rpr.append(parse_xml(f'<w:highlight {nsdecls("w")} w:val="yellow"/>'))
    r.append(rpr)
    t = parse_xml(f"<w:t {nsdecls('w')} xml:space=\"preserve\"/>")
    t.text = trecho
    r.append(t)
    return r


def substituir_no_paragrafo(p, antigo: str, novo: str) -> None:
    """Troca um trecho que pode estar dividido em vários runs de texto consecutivos (sem equações)."""
    # grupos de runs de texto consecutivos, interrompidos por equações ou outros elementos
    grupos, atual = [], []
    for filho in p:
        if filho.tag == qn("w:r") and filho.find(qn("w:t")) is not None:
            atual.append(filho)
        elif filho.tag in (qn("w:pPr"),):
            continue
        else:
            if atual:
                grupos.append(atual)
            atual = []
    if atual:
        grupos.append(atual)

    for runs in grupos:
        textos = [texto(r) for r in runs]
        junto = "".join(textos)
        i = junto.find(antigo)
        if i < 0:
            continue
        fim = i + len(antigo)
        # localiza runs de início e fim do trecho
        pos, ini_run, fim_run = 0, None, None
        for k, tx in enumerate(textos):
            if ini_run is None and i < pos + len(tx):
                ini_run, off_ini = k, i - pos
            if fim <= pos + len(tx):
                fim_run, off_fim = k, fim - pos
                break
            pos += len(tx)
        r0, r1 = runs[ini_run], runs[fim_run]
        prefixo = textos[ini_run][:off_ini]
        sufixo = textos[fim_run][off_fim:]
        base = r0.find(qn("w:rPr"))
        novos = [novo_run(base, prefixo, r0.find(qn("w:rPr") + "/" + qn("w:highlight")) is not None)] if prefixo else []
        for k, pedaco in enumerate(PLACEHOLDER_RE.split(novo)):
            if pedaco:
                novos.append(novo_run(base, pedaco, k % 2 == 1))
        if sufixo:
            novos.append(novo_run(r1.find(qn("w:rPr")), sufixo,
                                  r1.find(qn("w:rPr") + "/" + qn("w:highlight")) is not None))
        for n in novos:
            r0.addprevious(n)
        for r in runs[ini_run:fim_run + 1]:
            p.remove(r)
        return
    raise ValueError(f"Trecho não encontrado: {antigo!r}")


CHAVE_RE = re.compile(r"(Figuras?|Equaç(?:ão|ões)|Eqs?\.|Tabelas?)")


def renumerar(p) -> list:
    """Aplica os mapas FIGURAS/EQUACOES aos marcadores 4.X.n de um parágrafo."""
    completo = texto(p).strip()
    eh_numero_eq = re.fullmatch(r"\(4\.X\.\d+\)", completo) is not None
    anterior, trocas = "", []
    for t in p.iter(qn("w:t")):
        original = t.text or ""

        def troca(m):
            contexto = anterior + original[:m.start()]
            chaves = CHAVE_RE.findall(contexto)
            tipo = chaves[-1] if chaves else ("Equação" if eh_numero_eq else None)
            n = int(m.group(1))
            if tipo is None:
                raise ValueError(f"Marcador sem contexto: {completo[:80]!r}")
            if tipo.startswith("Tabela"):
                return m.group(0)
            mapa = FIGURAS if tipo.startswith("Figura") else EQUACOES
            if n not in mapa:
                raise ValueError(f"{tipo} 4.X.{n} removida ainda citada: {completo[:120]!r}")
            trocas.append((tipo, n, mapa[n]))
            return f"4.X.{mapa[n]}"

        t.text = re.sub(r"4\.X\.(\d+)", troca, original)
        anterior += original
    return trocas


def main() -> None:
    doc = docx.Document(str(ORIGEM))
    body = doc.element.body
    filhos = list(body)

    def indice(txt: str, inicio: int = 0) -> int:
        return next(i for i, el in enumerate(filhos[inicio:], inicio) if texto(el).strip() == txt)

    i_serial = indice(TITULO_SERIAL)
    i_res = next(i for i, el in enumerate(filhos[i_serial:], i_serial)
                 if texto(el).strip() == "RESULTADOS E DISCUSSÃO")
    i_rem = indice(SUB_REMOVIDA, i_serial)
    i_inv = indice(SUB_INVERSO, i_rem)

    # figura da curva X(δ): parágrafo da imagem, legenda e fonte (são movidos, não recriados)
    i_cap = next(i for i in range(i_rem, i_inv) if texto(filhos[i]).startswith("Figura 4.X.4"))
    figura_xd = filhos[i_cap - 1:i_cap + 2]
    assert figura_xd[0].find(".//" + qn("w:drawing")) is not None
    # o vermelho era só a marcação do colega para "manter na parte do híbrido"; em Métodos volta ao normal
    for el in figura_xd:
        for cor in el.iter(qn("w:color")):
            if cor.get(qn("w:val"), "").lower() == "ff0000":
                cor.getparent().remove(cor)

    # 1) referências cruzadas (antes de mexer na estrutura)
    for inicio, antigo, novo in SUBSTITUICOES:
        alvos = [p for el in filhos[i_inv:i_res] for p in ([el] if el.tag == qn("w:p") else el.iter(qn("w:p")))
                 if texto(p).startswith(inicio) and antigo in texto(p)]
        if len(alvos) != 1:
            raise ValueError(f"Esperado 1 parágrafo para {antigo!r}, achados {len(alvos)}")
        substituir_no_paragrafo(alvos[0], antigo, novo)

    # 2) parágrafo de ligação no início do problema inverso
    p_ref = filhos[i_inv + 1]
    assert texto(p_ref).startswith("Para treinar a rede neural")
    refs = {"body": p_ref}
    w = SectionWriter(doc, refs, p_ref)
    w.paragraph(TEXTO_LIGACAO)

    # 3) tabela de X(δ) logo após a figura das malhas temporais
    i_malha = next(i for i in range(i_inv, i_res) if texto(filhos[i]).startswith("Figura 4.X.7"))
    ancora = filhos[i_malha + 2]  # parágrafo seguinte à fonte da figura
    w = SectionWriter(doc, refs, ancora)
    w.paragraph(TEXTO_TABELA_X)
    w.paragraph(TEXTO_PCHIP)
    for el in figura_xd:
        ancora.addprevious(el)
    w.paragraph(TEXTO_LEITURA_CURVA)

    # 4) remove a subseção (a figura já foi movida para fora do intervalo)
    for el in filhos[i_rem:i_inv]:
        if el.getparent() is body and el not in figura_xd:
            body.remove(el)

    # 5) renumeração dos marcadores da seção
    filhos = list(body)
    i_serial = indice(TITULO_SERIAL)
    i_res = next(i for i, el in enumerate(filhos[i_serial:], i_serial)
                 if texto(el).strip() == "RESULTADOS E DISCUSSÃO")
    trocas = []
    for el in filhos[i_serial:i_res]:
        for p in ([el] if el.tag == qn("w:p") else el.iter(qn("w:p"))):
            trocas += renumerar(p)
    doc.save(str(DESTINO))
    print(f"Salvo: {DESTINO.name}")
    print(f"Marcadores renumerados: {sum(a != b for _, a, b in trocas)} de {len(trocas)}")


if __name__ == "__main__":
    main()
