"""Gera a v11 do relatório a partir da v10 (sem alterá-la).

Bloco 1 (10/11/2026): seção de Métodos "MODELAGEM HÍBRIDA SERIAL" na forma final combinada com o grupo
(documento "revisao e metodologia claude": azul = entra, vermelho = sai):

- o que passou para a nova Seção 4.2 (estrutura comum às modelagens híbridas) sai daqui e vira remissão:
  núcleo fenomenológico e curva X_Zn(delta) (4.2.2), partição 13 + 3 e critérios de escolha (4.2.1),
  restrições físicas (4.2.3);
- o subtítulo "Elementos do modelo fenomenológico utilizados no acoplamento" é retirado, e a seção passa a
  ter seis subseções (4.5.1 a 4.5.6);
- numeração definitiva de equações (4.5.s.n), figuras (4.5.n) e tabela (4.5.1), no padrão das demais seções;
- símbolos e equações sempre como equações nativas do Word; correção de símbolos e remissões incoerentes.

Texto de Métodos fica em cor normal (preto). Uso: python reescrever_serial_v11.py
"""

from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

import docx
from docx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docx_utils import SectionWriter  # noqa: E402

DOC_DIR = Path(__file__).resolve().parents[1]
SRC = DOC_DIR / "RELATÓRIO FINAL LOP_v10.docx"
DST = DOC_DIR / "RELATÓRIO FINAL LOP_v11.docx"

W_T, W_R, W_P, W_TBL = qn("w:t"), qn("w:r"), qn("w:p"), qn("w:tbl")
M_OMATH = "{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath"
M_OMATHPARA = "{http://schemas.openxmlformats.org/officeDocument/2006/math}oMathPara"

# ---------------------------------------------------------------- numeração definitiva
FIG = {"1": "4.5.1", "2": "4.5.2", "4": "4.2.1", "5": "4.5.3", "9": "4.5.4", "11": "4.5.5", "17": "4.5.6"}
TAB = {"8": "4.5.1"}
EQ = {"5": "4.5.1.1", "6": "4.5.1.2", "7": "4.5.1.3", "8": "4.5.1.4", "9": "4.5.2.1", "10": "4.5.2.2",
      "11": "4.5.3.1", "15": "4.5.3.2", "16": "4.5.3.3", "17": "4.5.4.1", "22": "4.5.5.1", "28": "4.5.6.1"}


# ---------------------------------------------------------------- utilitários de XML
def texto(el) -> str:
    return "".join(t.text or "" for t in el.iter(W_T))


def estilo(el) -> str:
    ppr = el.find(qn("w:pPr"))
    if ppr is None or ppr.find(qn("w:pStyle")) is None:
        return ""
    return ppr.find(qn("w:pStyle")).get(qn("w:val"))


def segmentos(p):
    """Listas de w:t consecutivos (runs vizinhos, sem equação no meio) de um parágrafo."""
    segs, atual = [], []
    for ch in p:
        if ch.tag == W_R and ch.find(W_T) is not None:
            atual.extend(ch.findall(W_T))
        elif ch.tag == qn("w:pPr") or (ch.tag == W_R and ch.find(W_T) is None and not len(ch.findall(qn("w:drawing")))):
            continue
        else:
            if atual:
                segs.append(atual)
            atual = []
    if atual:
        segs.append(atual)
    return segs


def _trocar_trecho(ts, ini: int, fim: int, novo: str) -> None:
    """Substitui os caracteres [ini, fim) do texto concatenado de `ts` por `novo`."""
    pos = 0
    primeiro = True
    for t in ts:
        s = t.text or ""
        a, b = pos, pos + len(s)
        pos = b
        if b <= ini or a >= fim:
            if not (a == b == ini and primeiro and ini == fim):
                continue
        li, lf = max(ini, a) - a, min(fim, b) - a
        t.text = s[:li] + (novo if primeiro else "") + s[lf:]
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        primeiro = False
    assert not primeiro, "trecho fora do segmento"


def trocar(p, antigo: str, novo: str) -> None:
    """Troca `antigo` por `novo` dentro de um parágrafo, mesmo que o trecho esteja dividido em vários runs."""
    for ts in segmentos(p):
        flat = "".join(t.text or "" for t in ts)
        i = flat.find(antigo)
        if i >= 0:
            _trocar_trecho(ts, i, i + len(antigo), novo)
            return
    raise ValueError(f"Trecho não encontrado: {antigo!r} em {texto(p)[:80]!r}")


_RE_ROTULO = re.compile(r"(Figuras?|Tabelas?|Equaç(?:ão|ões)|Eq\.)(\s+)(\(?)4\.X+\.(\d+)(\)?)")
_RE_NUM_EQ = re.compile(r"^\(4\.X+\.(\d+)\)$")


def renumerar(el) -> int:
    """Troca os marcadores provisórios 4.X.n / 4.XX.n pela numeração definitiva. Retorna quantas trocas fez."""
    n = 0
    for p in el.iter(W_P):
        for ts in segmentos(p):
            flat = "".join(t.text or "" for t in ts)
            m = _RE_NUM_EQ.match(flat.strip())
            if m:
                ini = flat.index("(")
                _trocar_trecho(ts, ini, ini + len(flat.strip()), f"({EQ[m.group(1)]})")
                n += 1
                continue
            for m in reversed(list(_RE_ROTULO.finditer(flat))):
                tipo, esp, num = m.group(1), m.group(2), m.group(4)
                if tipo.startswith("Fig"):
                    novo = f"{tipo}{esp}{FIG[num]}"
                    fim = m.end(4)
                elif tipo.startswith("Tab"):
                    novo = f"{tipo}{esp}{TAB[num]}"
                    fim = m.end(4)
                elif tipo == "Eq.":
                    novo = f"{tipo}{esp}{EQ[num]}"
                    fim = m.end(4)
                else:  # Equação -> sempre entre parênteses, como nas demais seções
                    novo = f"{tipo}{esp}({EQ[num]})"
                    fim = m.end(5) if m.group(3) else m.end(4)
                _trocar_trecho(ts, m.start(), fim, novo)
                n += 1
    return n


def main() -> None:
    doc = docx.Document(str(SRC))
    body = doc.element.body
    els = list(body.iterchildren())

    i0 = next(i for i, e in enumerate(els) if e.tag == W_P and estilo(e) == "Heading3"
              and texto(e).strip() == "MODELAGEM HÍBRIDA SERIAL")
    i1 = next(i for i, e in enumerate(els) if i > i0 and e.tag == W_P and estilo(e) == "Heading2"
              and texto(e).strip() == "RESULTADOS E DISCUSSÃO")
    sec = els[i0:i1]
    n_antes = len(sec)

    def achar(prefixo: str):
        achados = [e for e in sec if e.tag == W_P and texto(e).strip().startswith(prefixo) and e.getparent() is not None]
        assert len(achados) == 1, f"{len(achados)} parágrafos começam com {prefixo!r}"
        return achados[0]

    corpo_ref = achar("Com essa escolha, a rede neural fica responsável")
    w = SectionWriter(doc, {"body": corpo_ref}, None)

    def refazer(p, novo_texto: str) -> None:
        """Reescreve o parágrafo inteiro ($...$ vira equação nativa), mantendo a formatação do parágrafo."""
        for ch in list(p):
            if ch.tag != qn("w:pPr"):
                p.remove(ch)
        w._fill(p, novo_texto)

    def remover(el) -> None:
        el.getparent().remove(el)

    # -------------------------------------------------------- abertura da seção
    p = achar("A principal decisão na construção do modelo")
    trocar(p, "Na formulação original,", "Na formulação de Bortot Coelho (2017),")  # há um w:sdt logo depois
    trocar(p, " foi introduzido para compensar esses desvios por meio de um único valor ajustado para o conjunto de "
              "ensaios, porém, na abordagem híbrida, essa correção",
           " foi introduzido para representar a desaceleração da dissolução que a lei cinética não descreve "
           "(Seção 3.1.5), por meio de um único valor ajustado para o conjunto de ensaios. Na abordagem híbrida, "
           "essa correção")

    # -------------------------------------------------------- antigo 4.5.1 -> um parágrafo na abertura (remete à 4.2.2)
    h_elem = next(e for e in sec if e.tag == W_P and estilo(e) == "Heading3"
                  and texto(e).strip() == "Elementos do modelo fenomenológico utilizados no acoplamento")
    p_ini = achar("Para que a taxa estimada pela rede seja convertida")
    p_fim = achar("No modelo fenomenológico, essa função é dada pela lei cinética")
    a, b = sec.index(p_ini), sec.index(p_fim)
    assert sec.index(h_elem) == a - 1 and b - a == 5, "estrutura do antigo 4.5.1 mudou"
    for e in sec[a:b]:  # dois parágrafos, a figura X(delta), legenda e fonte: agora na Seção 4.2.2
        remover(e)
    remover(h_elem)
    refazer(p_fim,
            r"Para converter a taxa estimada pela rede em conversão de zinco, utiliza-se o núcleo fenomenológico "
            r"comum descrito na Seção 4.2.2: a taxa é integrada para fornecer $\delta(t)$, a conversão é lida na "
            r"curva $X_{\mathrm{Zn}}(\delta)$ e o balanço de ácido fornece $C_A(t)$. No modelo fenomenológico, a "
            r"taxa $\nu(t)$ é dada pela lei cinética de reação interfacial, com a constante $k_s$; no modelo "
            r"híbrido, ela passa a ser estimada pela rede neural. O problema de modelagem, portanto, resume-se a "
            r"obter uma boa estimativa de $\nu(t)$ para cada condição operacional, o que é tratado nas seções "
            r"seguintes.")

    # -------------------------------------------------------- 4.5.1 problema inverso
    trocar(achar("Para treinar a rede neural, é necessário dispor"), "(Seção 4.2.2)", "(Seção 4.1.2)")
    trocar(achar("Com os parâmetros ótimos, calcularam-se"), "é apresentada na Seção 5.XX.", "é apresentada na Seção B.5.")

    # -------------------------------------------------------- 4.5.2 base de dados e partição
    trocar(achar("Os valores de"),
           "A temperatura (40 °C) e a velocidade de agitação (1000 rpm) não foram incluídas, pois foram mantidas "
           "constantes em todos os ensaios. ", "")
    refazer(achar("Os 16 ensaios foram divididos em 13 para treino (81,25%)"),
            r"A partição dos ensaios segue a Seção 4.2.1: 13 ensaios para treino, que fornecem 780 registros, e 3 "
            r"para teste cego (Ensaios 7, 8 e 14), com 180 registros (Figura 4.5.4(a)). No modelo serial, a divisão "
            r"por ensaios inteiros é ainda mais necessária, pois os registros de um mesmo ensaio, separados por "
            r"apenas 0,25 min, têm valores de $\nu$ muito próximos.")
    remover(achar("A escolha desses três ensaios seguiu três critérios"))

    # -------------------------------------------------------- 4.5.3 arquitetura
    refazer(achar("Em que  e  são a média e o desvio-padrão de  nos 60 nós"),
            r"Em que $m_{\tau}$ e $s_{\tau}$ são a média e o desvio-padrão de $\ln t$ nos 60 nós da malha temporal. "
            r"Como $\nu$ cai várias ordens de grandeza nos primeiros minutos de cada ensaio, a escala logarítmica dá "
            r"à rede mais resolução nesse trecho: o intervalo de 0,25 a 2 min, em que ocorre a maior parte da "
            r"conversão, ocupa 12% da faixa do tempo na escala linear e cerca de 51% na logarítmica.")
    trocar(achar("A positividade da taxa é a única restrição física"),
           "Ela decorre da irreversibilidade da dissolução:", "Ela decorre da irreversibilidade da dissolução (Seção 4.2.3):")

    # -------------------------------------------------------- 4.5.4 perda: Theta maiúsculo também na equação
    p_perda = achar("O treinamento consiste em ajustar o conjunto")
    tbl_antiga = p_perda.getnext()
    assert tbl_antiga.tag == W_TBL and "4.XX.17" in texto(tbl_antiga)
    w.anchor = tbl_antiga
    w.equation(r"L(\Theta)=\frac{1}{B}\sum_{i=1}^{B}{\left[\hat{y}_i(\Theta)-y_i\right]^2}", "4.5.4.1")
    remover(tbl_antiga)

    # -------------------------------------------------------- 4.5.5 critério
    trocar(achar("Os valores apresentados na Tabela"), "(Seção 4.XX)", "(Seção 4.5.6)")

    # -------------------------------------------------------- 4.5.6 acoplamento e simulação
    refazer(achar("O acoplamento descrito nesta seção"),
            r"Esta seção descreve o funcionamento final do modelo híbrido serial. Dadas as condições de um ensaio, "
            r"$C_{A0}$ e $\eta$, e os instantes em que se deseja a previsão, o algoritmo segue as sete etapas da "
            r"Figura 4.5.6.")
    refazer(achar("Como discutido anteriormente, a rede só é avaliada"),
            r"A rede só é avaliada a partir de $t=0,25$ min, início do domínio coberto pelos dados de treino. Em "
            r"seguida, a conversão em cada nó é lida da curva $X_{\mathrm{Zn}}(\delta)$ pré-calculada (Figura 4.2.1). "
            r"Como a integração e a leitura da conversão são idênticas às do problema inverso, a taxa prevista pela "
            r"rede e a taxa estimada a partir dos dados são convertidas em conversão exatamente da mesma forma.")
    refazer(achar("Antes do cálculo da concentração de ácido, a conversão é submetida a duas"),
            r"Antes do cálculo da concentração de ácido, a conversão é submetida às restrições de irreversibilidade "
            r"e de limite estequiométrico da Seção 4.2.3:")
    refazer(achar("A primeira operação garante que a conversão não diminua"),
            r"O máximo acumulado garante que a conversão não diminua ao longo do tempo. Como $\hat{\nu}$ é sempre "
            r"positiva e a curva $X_{\mathrm{Zn}}(\delta)$ é crescente, essa condição já é satisfeita por "
            r"construção, e a operação funciona apenas como salvaguarda numérica.")
    refazer(achar("A segunda operação reforça que relação"),
            r"O truncamento em $\min(1,\eta)$ é necessário porque a curva $X_{\mathrm{Zn}}(\delta)$ decorre apenas "
            r"da granulometria e não considera o ácido disponível. Quando $\eta<1$ e a conversão atinge o limite, o "
            r"ácido está esgotado e a dissolução cessa, de modo que a retração acumulada é mantida constante. A "
            r"concentração de ácido livre é então calculada pela Equação (3.1.6.5).")

    # -------------------------------------------------------- parágrafos e título vazios no fim da seção
    vazios = 0
    for e in reversed(sec):
        if e.getparent() is None:
            continue
        if e.tag == W_P and not texto(e).strip() and not e.findall(".//" + qn("w:drawing")) \
                and not e.findall(".//" + M_OMATH) and not e.findall(".//" + qn("w:sectPr")):
            remover(e)
            vazios += 1
        else:
            break

    # -------------------------------------------------------- numeração definitiva e fim dos destaques amarelos
    atuais = list(body.iterchildren())
    vivos = atuais[i0:atuais.index(els[i1])]  # inclui a equação recriada
    trocas = sum(renumerar(e) for e in vivos)
    for e in vivos:
        for h in list(e.iter(qn("w:highlight"))):
            h.getparent().remove(h)

    # -------------------------------------------------------- conferências
    txt = "\n".join(texto(e) for e in vivos)
    restos = re.findall(r".{0,40}\d\.X+.{0,20}", txt)
    assert not restos, f"marcadores provisórios restantes: {restos}"
    assert list(body.iterchildren())[i0 + len(vivos)].tag == W_P and \
        texto(list(body.iterchildren())[i0 + len(vivos)]).strip() == "RESULTADOS E DISCUSSÃO"
    titulos = [texto(e).strip() for e in vivos if e.tag == W_P and estilo(e) == "Heading3"]
    assert len(titulos) == 7, titulos  # título da seção + 6 subseções
    for num in EQ.values():  # as 12 equações numeradas estão presentes, uma vez cada, como rótulo
        assert txt.count(f"({num})\n") + txt.endswith(f"({num})") >= 1 or f"({num})" in txt, num

    doc.save(str(DST))
    print(f"v11 gravada: {DST.name}")
    print(f"seção serial: {n_antes} -> {len(vivos)} blocos; {trocas} rótulos renumerados; {vazios} vazios removidos")
    print("subseções:", " | ".join(titulos[1:]))
    print("palavras na seção:", len(txt.split()))


if __name__ == "__main__":
    main()
