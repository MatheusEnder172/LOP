"""Gera a v22 a partir da versão 2 do grupo (`RELATÓRIO FINAL LOP - GRUPO-2.docx`, que não é alterada).

Pedido de 12/11/2026 (tarde):
1. Seção comum a todas as modelagens, no início de Materiais e Métodos (4.1): base de dados e partição dos
   ensaios, ensaios novos de laboratório e tratamento das leituras de absorção atômica, restrições físicas e
   avaliação de desempenho. O texto parte da seção comum do documento de sugestões do grupo. O que passa
   para lá é marcado para sair das seções do black-box, da serial e dos Resultados;
2. Apêndices na forma final, SEM cores: cortes da v19/v20 aplicados, cinco apêndices fundidos em dois e
   figuras, tabelas, equações e remissões renumeradas;
3. No restante do documento, a marcação continua: RETIRAR em vermelho tachado, ADICIONAR em azul.
A versão 2 já tem a Revisão e o black-box da v21 colados (com as cores); essas partes não são refeitas.
Uso: python secao_comum_v22.py
"""

from __future__ import annotations

import difflib
import re
import sys
import textwrap
from pathlib import Path

from docx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import enxugar_apendices_v19 as v19  # noqa: E402
import enxugar_apendices_v20 as v20  # noqa: E402
import marcar_grupo_v21 as m  # noqa: E402
from docx_utils import SectionWriter, add_references, pintar  # noqa: E402

DOC_DIR = v19.DOC_DIR
GRUPO = DOC_DIR / "RELATÓRIO FINAL LOP - GRUPO-2.docx"
DESTINO = DOC_DIR / "RELATÓRIO FINAL LOP_v22.docx"
AZUL, VERMELHO = v19.AZUL, v19.VERMELHO
W_P, W_TBL, W_R, W_T, M_T = v19.W_P, v19.W_TBL, v19.W_R, v19.W_T, v19.M_T
M_R, M_OMATH, M_PARA = v19.M_NS + "r", v19.M_OMATH, v19.M_NS + "oMathPara"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
texto, sem_espaco = v19.texto, m.sem_espaco

# seção nova de cada seção antiga dos apêndices (letras atuais, A a E)
SECOES = {"A.1": "A.1", "A.2": "A.1", "A.3": "A.1", "A.4": "A.1", "A.5": "A.2", "B.1": "A.3", "B.2": "A.3",
          "B.3": "A.3", "B.4": "A.4", "C.1": "A.5", "C.2": "A.5", "C.3": "A.6", "D.1": "A.7", "D.2": "A.7",
          "D.3": "A.8", "D.4": "A.8", "D.5": "B.1", "D.6": "B.1", "D.7": "B.2", "D.8": "B.3", "D.9": "B.3",
          "D.10": "B.3", "D.11": "B.4", "E.1": "B.5", "E.2": "B.6", "E.3": "B.7", "E.4": "B.8"}
APENDICE = {"A": "A", "B": "A", "C": "A", "E": "B"}      # "Apêndice D" depende do contexto
LETRA_ANTERIOR = {"B": "A", "C": "B", "D": "C", "E": "D", "F": "E"}   # Métodos da serial usa as letras antigas
PALAVRA = re.compile(r"Figuras?|Tabelas?|Equaç(?:ão|ões)|[Ss]eç(?:ão|ões)|Apêndices?")
ROTULO = re.compile(r"(?<![A-Za-z0-9.])([A-F])\.(\d{1,2})(?![\d])")
AP_SOLTO = re.compile(r"Apêndices? ([A-F])(?!\w|\.\d)")
AJUSTES_APENDICE = [
    ("nas seções B.1 a B.2", "nas Seções B.1 e B.2"),
    ("A Partir da busca de hiperparâmetros, o modelo foi treinado com épocas",
     "A partir da busca de hiperparâmetros, o modelo foi treinado com 928 épocas"),
    ("varia com a semente (Apêndice A)", "varia com a semente (Seção A.6)"),
    ("descrita na próxima seção e o procedimento", "descrita a seguir, e o procedimento"),
    ("o primeiro mostrou (Seção 5.XX)", "o primeiro mostrou (Seção B.1)"),
    ("discutido na Seção 4.XX", "discutido na Seção 4.1.4"),
    ("apresentada na Seção 5.4 e no Apêndice B.", "apresentada nas Seções 5.5 e B.6."),
]
log: list[str] = []


# ---------------------------------------------------------------------------------------------- utilitários
def cor_de(r) -> str:
    rpr = r.find(qn("w:rPr"))
    c = rpr.find(qn("w:color")) if rpr is not None else None
    return (c.get(qn("w:val")) or "").upper() if c is not None else ""


def runs_com_texto(el):
    return [r for r in el.iter() if r.tag in (W_R, M_R) and any((x.text or "") for x in r if x.tag in (W_T, M_T))]


def todo_vermelho(el) -> bool:
    rs = runs_com_texto(el)
    return bool(rs) and all(cor_de(r) == VERMELHO for r in rs)


def vazio(el) -> bool:
    return (el.tag == W_P and not texto(el).strip() and not el.findall(".//" + qn("w:drawing"))
            and not el.findall(".//" + qn("w:br")) and not el.findall(".//" + qn("w:sectPr")))


def aceitar_marcas(inicio, remover_tambem) -> None:
    """Na região dos apêndices: apaga o que está em vermelho e deixa o azul em preto."""
    for el in remover_tambem:
        el.getparent().remove(el)
    for el in [inicio] + list(inicio.itersiblings()):
        if el.tag not in (W_P, W_TBL):
            continue
        if todo_vermelho(el) and not el.findall(".//" + qn("w:drawing")):
            el.getparent().remove(el)
            continue
        for r in runs_com_texto(el):
            if cor_de(r) != VERMELHO:
                continue
            if r.tag == W_R:
                r.getparent().remove(r)
            else:
                om = next(a for a in r.iterancestors() if a.tag == M_OMATH)
                if om.getparent() is not None and all(cor_de(x) == VERMELHO for x in om.iter(M_R)):
                    pai = om.getparent()
                    pai.remove(om)
                    if pai.tag == M_PARA and len(pai) == 0:
                        pai.getparent().remove(pai)
        for c in list(el.iter(qn("w:color"))):
            if (c.get(qn("w:val")) or "").upper() == AZUL:
                c.getparent().remove(c)
    for el in list(inicio.itersiblings()):
        ant = el.getprevious()
        if vazio(el) and ant is not None and vazio(ant):
            el.getparent().remove(el)


def substituir(p, a: int, b: int, novo: str) -> None:
    """Troca os caracteres [a, b) do texto do parágrafo, preservando os runs."""
    pos, primeiro = 0, True
    for n in [x for x in p.iter() if x.tag in (W_T, M_T)]:
        s = n.text or ""
        ini, fim = pos, pos + len(s)
        pos = fim
        if fim <= a or ini >= b:
            continue
        assert n.tag == W_T, f"rótulo dentro de equação: {texto(p)[:80]!r}"
        i, j = max(a, ini) - ini, min(b, fim) - ini
        n.text = s[:i] + (novo if primeiro else "") + s[j:]
        n.set(XML_SPACE, "preserve")
        primeiro = False


def marcar_troca(p, a: int, b: int, novo: str) -> None:
    """Como `substituir`, mas marcando: o trecho antigo fica vermelho tachado e o novo, azul, logo depois."""
    pos, marcados = 0, []
    for ch in list(p):
        if ch.tag not in (W_R, M_OMATH, M_PARA):
            continue
        n = len(texto(ch))
        ini, fim = pos, pos + n
        pos = fim
        if n == 0 or fim <= a or ini >= b:
            continue
        assert ch.tag == W_R
        alvo = ch
        if ini < a:
            _, alvo = v19._dividir_run(alvo, a - ini)
            ini = a
        if fim > b:
            alvo, _ = v19._dividir_run(alvo, b - ini)
        marcados.append(alvo)
    assert marcados
    for r in marcados:
        v19.stats["retirar"] += len(texto(r).split())
        v19.pintar_run(r, VERMELHO)
        v19.tachar_run(r)
    v19.run_azul(marcados[-1], novo)


def remissoes(p, mapas, letras_antigas: bool, contexto_d: str | None = None):
    """Lista (a, b, antigo, novo) das remissões a rótulos dos apêndices no parágrafo."""
    t = texto(p)
    palavras = [(k.end(), k.group()[0].upper()) for k in PALAVRA.finditer(t)]
    trocas = []
    for k in ROTULO.finditer(t):
        letra, num = k.group(1), k.group(2)
        if letras_antigas:
            if letra not in LETRA_ANTERIOR:
                continue
            letra = LETRA_ANTERIOR[letra]
        elif letra == "F":
            continue
        antes = [tipo for fim, tipo in palavras if fim <= k.start()]
        tipo = antes[-1] if antes else ("E" if t.strip() == f"({k.group()})" else None)
        if tipo == "A":
            tipo = "S"
        if tipo is None:
            log.append(f"SEM TIPO  {k.group()}: {t[max(0, k.start() - 60):k.end() + 20]!r}")
            continue
        novo = mapas[tipo].get(f"{letra}.{num}")
        if novo is None:
            log.append(f"SEM DESTINO  {tipo} {k.group()}: {t[max(0, k.start() - 70):k.end() + 20]!r}")
            continue
        if novo != k.group():
            trocas.append((k.start(), k.end(), k.group(), novo))
    for k in AP_SOLTO.finditer(t):
        letra = k.group(1)
        if letras_antigas:
            letra = LETRA_ANTERIOR.get(letra, letra)
        novo = APENDICE.get(letra) or contexto_d
        if novo is None:
            log.append(f"APÊNDICE D sem contexto: {t[max(0, k.start() - 70):k.end() + 30]!r}")
            continue
        if novo != k.group(1):
            trocas.append((k.start(1), k.end(1), k.group(1), novo))
            log.append(f"apêndice {k.group(1)} -> {novo}: {t[max(0, k.start() - 60):k.end() + 25]!r}")
    return sorted(trocas, reverse=True)


# ---------------------------------------------------------------------------------------------- seção comum
def secao_comum(doc, g) -> list:
    ancora = g("IMPLEMENTAÇÃO DO MODELO WHITE BOX")
    legenda = g("Tabela 4.XX.8 – Parâmetros do treinamento")
    fonte = next(e for e in legenda.itersiblings() if e.tag == W_P and texto(e).startswith("Fonte"))
    sw = SectionWriter(doc, {"heading": ancora, "subheading": g("Condição inicial em base numérica de distribuição"),
                             "body": g("As equações que governam a lixiviação em batelada"),
                             "caption": legenda, "source": fonte}, ancora)
    sw.heading("BASE DE DADOS E CRITÉRIOS COMUNS ÀS MODELAGENS")
    sw.paragraph(
        "As modelagens desenvolvidas neste trabalho, isto é, o modelo *white-box* (Seção 4.2), o modelo *black-box* "
        "(Seção 4.3), a rede neural informada pela física (Seção 4.4), a arquitetura paralela cooperativa (Seção 4.5) "
        "e a arquitetura serial (Seção 4.6), utilizam a mesma base de dados, a mesma partição dos ensaios, as mesmas "
        "restrições físicas e o mesmo protocolo de avaliação. Para evitar repetições e garantir que as abordagens "
        "sejam comparadas nas mesmas condições, esses elementos são reunidos nesta seção, e as seções seguintes "
        "descrevem apenas o que é próprio de cada modelo. As três arquiteturas híbridas diferem na grandeza atribuída "
        "ao componente orientado por dados e na forma como o conhecimento físico é incorporado, conforme a Tabela "
        "4.1.1.")
    sw.table("Tabela 4.1.1", "Papel do componente orientado por dados em cada arquitetura híbrida",
             ["Arquitetura", "Grandeza estimada pelo componente de dados", "Entradas",
              "Forma de incorporação da física"],
             [["PINN", "Retração diametral acumulada, $\\delta(t)$", "$t$, $C_{A0}$ e $\\eta$",
               "Lei de retração e restrições físicas como parcelas da função de perda; $k_s$ e $\\alpha$ estimados "
               "no treinamento"],
              ["Paralela cooperativa", "Resíduo da conversão, $\\Delta X = X_{exp} - X_{PBM}$",
               "$t$, $C_{A0}$, $\\eta_{real}$ e $X_{PBM}$",
               "Modelo *white-box* completo em paralelo, com acoplador físico sobre a saída"],
              ["Serial", "Taxa de retração diametral, $\\nu(t)$", "$t$, $C_{A0}$ e $\\eta$",
               "Integração de $\\nu(t)$ e balanços populacional e de ácido em série com a rede"]],
             [2.6, 4.2, 3.2, 6.0])

    sw.subheading("Ensaios de lixiviação e partição em treino e teste")
    sw.paragraph(
        "Os dados utilizados foram extraídos das Tabelas A1.1 e A1.4 (Apêndice A1) da dissertação de Bortot Coelho "
        "(2017), que reúnem 16 ensaios em batelada, conduzidos a 40 °C e 1000 rpm e monitorados em oito instantes "
        "(0; 0,5; 1; 2; 3; 4; 5 e 15 min), num total de 128 observações. Como a temperatura e a agitação foram "
        "mantidas constantes, nenhuma delas é variável de entrada dos modelos, que recebem a concentração inicial de "
        "ácido sulfúrico ($C_{A0}$), a razão molar estequiométrica ($\\eta$) e o tempo de reação ($t$). A única "
        "diferença está no modelo paralelo, que emprega a razão molar real ($\\eta_{real}$), calculada pelas massas e "
        "volumes efetivos (Seção 4.5). Em todos os casos, a referência final de comparação é a conversão de zinco "
        "medida ($X_{Zn}$).")
    sw.paragraph(
        "Os ensaios foram divididos em 13 para treino e 3 para teste cego (Ensaios 7, 8 e 14). A divisão foi feita "
        "por ensaios inteiros, e não por pontos sorteados, pois os pontos de um mesmo ensaio compartilham as "
        "condições operacionais e são fortemente correlacionados: com pontos sorteados, quase todo ponto de teste "
        "teria um vizinho quase idêntico no treino, e o resultado não mediria a capacidade de prever condições novas "
        "(Kapoor; Narayanan, 2023). A proporção adotada buscou equilibrar o aproveitamento dos dados, já que cada "
        "ensaio retirado do treino reduz em cerca de 6% a informação disponível, e um teste que não dependa de uma "
        "única condição.")
    sw.paragraph(
        "A escolha desses três ensaios seguiu três critérios (Figura 4.XX.9(a)): (i) os quatro vértices do "
        "planejamento foram mantidos no treino, de modo que o teste seja uma interpolação e não uma extrapolação "
        "(Sansana et al., 2024); (ii) os ensaios cobrem três situações de disponibilidade de ácido, com "
        "$\\eta=1{,}0$ (Ensaio 8), $\\eta=1{,}5$ (Ensaio 14) e $\\eta=3{,}1$ (Ensaio 7); e (iii) os quatro ensaios "
        "com $\\eta=0{,}5$, nos quais a reação cessa pelo esgotamento do ácido, foram mantidos no treino. Os mesmos "
        "três ensaios são adotados como teste no modelo *black-box*, na PINN e no modelo serial, de modo que essas "
        "abordagens sejam comparadas nas mesmas condições.")
    sw.paragraph(
        "Para que o teste permaneça independente, os Ensaios 7, 8 e 14 não participam de nenhuma etapa do "
        "desenvolvimento: não são usados no ajuste dos pesos nem na escolha dos hiperparâmetros, não recebem pontos "
        "de colocação na PINN e não entram no cálculo das estatísticas de normalização das entradas, que são obtidas "
        "apenas com os ensaios de treino e aplicadas sem recálculo ao teste. O conjunto de teste é consultado uma "
        "única vez, após a definição do modelo final (Goodfellow; Bengio; Courville, 2016). Quando é necessário "
        "comparar configurações dentro do treino, emprega-se a validação cruzada também agrupada por ensaios "
        "inteiros, como as quatro dobras dos modelos serial e *black-box* (Seção 4.6). O modelo paralelo, por sua "
        "vez, é avaliado por protocolos de validação que retiram ensaios inteiros em rodízio (Seção 4.5).")

    sw.subheading("Ensaios novos de laboratório")
    sw.paragraph(
        "Além dos ensaios de Bortot Coelho (2017), o grupo realizou quatro ensaios novos (E1 a E4), em condições "
        "intermediárias às do planejamento original (Tabela 4.1.2), para verificar a capacidade de previsão dos "
        "modelos em condições que não participaram de nenhuma etapa do desenvolvimento. Os ensaios foram conduzidos "
        "nas mesmas condições de temperatura (40 °C) e de agitação (1000 rpm), com volume de solução de 200 mL em "
        "vez de 400 mL, e amostrados em seis instantes (0,5; 1; 2; 3; 5 e 15 min). O Ensaio E4 ($\\eta=0{,}40$) está "
        "abaixo da menor razão molar dos ensaios originais (0,5) e constitui uma pequena extrapolação; os demais "
        "estão dentro da faixa do planejamento.")
    sw.table("Tabela 4.1.2", "Condições dos ensaios novos e limite estequiométrico da conversão",
             ["Ensaio", "$C_{A0}$ (mol/L)", "$\\eta$ (–)", "Massa de ustulado (g)", "Volume de solução (mL)",
              "$\\min(1,\\eta)$"],
             [["E1", "0,25", "0,75", "6,7", "200", "0,75"], ["E2", "0,75", "1,25", "12,1", "200", "1,00"],
              ["E3", "0,75", "2,25", "6,7", "200", "1,00"], ["E4", "0,25", "0,40", "12,6", "200", "0,40"]],
             [2.0, 2.6, 2.2, 3.4, 3.4, 2.4])
    sw.paragraph(
        "A concentração de zinco no licor foi determinada por espectrometria de absorção atômica. Como a leitura é "
        "feita em solução diluída, cada alíquota foi diluída por pesagem, e o fator de diluição ($FD$) foi calculado "
        "pela razão entre a massa da solução diluída ($M_2$) e a massa da alíquota ($M_1$), de modo que a "
        "concentração de zinco é o produto da leitura do equipamento ($L$) pelo fator de diluição:")
    sw.equation("C_{Zn}=L\\cdot FD=L\\,\\frac{M_2}{M_1}", "4.1.2.1")
    sw.paragraph("A concentração foi convertida em conversão de zinco pela mesma relação dos ensaios originais:")
    sw.equation("X_{Zn}=\\frac{C_{Zn}\\,V}{m\\,w}", "4.1.2.2")
    sw.paragraph(
        "Em que $V=0{,}200$ L é o volume de solução, $m$ é a massa de ustulado e $w$ é o teor de zinco do sólido, de "
        "0,611 g/g, valor que reproduz a conversão final dos 16 ensaios originais. A conversão em $t=0$ é nula por "
        "definição.")
    sw.paragraph(
        "Duas hipóteses foram adotadas nesse tratamento e aguardam confirmação do laboratório. A primeira é que os "
        "valores de concentração da planilha correspondem a g/L, única leitura que fornece conversões da ordem de "
        "grandeza esperada. A segunda é que os rótulos dos Ensaios E2 e E3 estão trocados entre si na planilha, pois "
        "as concentrações registradas em cada um só são compatíveis com a massa de sólido do outro: como "
        "registrados, a conversão do E3 chegaria a 1,69, acima de 1.")
    sw.paragraph(
        "Esses ensaios não foram usados no ajuste nem na escolha de nenhum modelo. As previsões são calculadas com "
        "os modelos já definidos, sem novo ajuste, e comparadas com as conversões medidas nos seis instantes de "
        "amostragem pelas métricas da Seção 4.1.4; os resultados são apresentados no Capítulo 5.")

    sw.subheading("Restrições físicas")
    sw.paragraph(
        "Independentemente da arquitetura, a conversão prevista deve satisfazer três restrições, decorrentes da "
        "definição do problema e dos balanços de massa:")
    sw.paragraph(
        "(i) condição inicial: $X(0)=0$, $\\delta(0)=0$ e $C_A(0)=C_{A0}$, pois não há dissolução antes do contato "
        "entre o sólido e a solução;")
    sw.paragraph(
        "(ii) irreversibilidade: $dX/dt\\geq 0$, pois a dissolução do ZnO é irreversível, e uma conversão "
        "decrescente implicaria a reprecipitação do zinco com regeneração de ácido livre no reator. De forma "
        "equivalente, a taxa de retração é não negativa, pois uma taxa negativa corresponderia ao crescimento das "
        "partículas;")
    sw.paragraph(
        "(iii) limite estequiométrico: como cada mol de ZnO dissolvido consome $\\nu$ mol de H₂SO₄, a conversão não "
        "pode exceder nem a totalidade do sólido nem a disponibilidade de ácido:")
    sw.equation("X_{max}=\\min\\left(1,\\ \\frac{\\eta}{\\nu}\\right)", "4.1.3.1")
    sw.paragraph(
        "Com $\\nu=1$ neste trabalho. Nos ensaios com deficiência de ácido ($\\eta=0{,}5$), a conversão máxima é, "
        "portanto, de 50%; ao atingi-la, o ácido se esgota e a dissolução cessa. Qualquer conversão superior a "
        "$\\eta$ tornaria negativa a concentração de ácido residual calculada pela Equação (3.1.6.5).")
    sw.paragraph(
        "Os modelos diferem na forma como essas restrições são impostas (Tabela 4.1.3). Na PINN, elas são "
        "incorporadas de forma branda, como penalizações na função de perda, e podem ser violadas em pequena "
        "magnitude; nos modelos paralelo e serial, são impostas de forma rígida, por construção da rede ou por "
        "projeção da saída, e são satisfeitas exatamente; o modelo *black-box* não impõe nenhuma delas. Essa "
        "distinção é retomada na comparação da consistência física das previsões (Capítulo 5).")
    sw.table("Tabela 4.1.3", "Forma de imposição das restrições físicas em cada modelo",
             ["Restrição", "*Black-box*", "PINN", "Paralelo cooperativo", "Serial"],
             [["$X(0)=0$", "Não imposta", "Penalização na perda ($L_{ic}$)", "Imposição direta pelo acoplador físico",
               "Imposição direta como condição inicial"],
              ["$dX/dt\\geq 0$", "Não imposta", "Penalização na perda ($L_{mono}$)",
               "Regressão isotônica no acoplador físico",
               "Saída *softplus* ($\\nu\\geq 0$) e máximo acumulado como salvaguarda"],
              ["$X\\leq\\min(1,\\eta)$", "Não imposta", "Penalização na perda ($L_{acid}$)",
               "Truncamento em $X_{max}$ no acoplador físico",
               "Truncamento em $\\min(1,\\eta)$ e $\\delta$ constante após o esgotamento do ácido"]],
             [2.6, 2.2, 3.2, 3.6, 4.4])

    sw.subheading("Avaliação de desempenho e linhas de base")
    sw.paragraph(
        "O desempenho de todos os modelos é quantificado pelo coeficiente de determinação ($R^2$), pela raiz do erro "
        "quadrático médio (RMSE) e pelo erro absoluto médio (MAE), calculados conforme as Equações (3.25), (3.26) e "
        "(3.27) (Chicco; Warrens; Jurman, 2021), além do erro máximo. As métricas são calculadas sempre em relação à "
        "conversão medida e apenas nos instantes com medição experimental e $t>0$, uma vez que o ponto $t=0$ é "
        "conhecido por definição em todos os ensaios e inflaria artificialmente os indicadores, e os erros são "
        "expressos em pontos percentuais (p.p.) de conversão. Os valores calculados em malhas temporais mais finas, "
        "como os pontos de colocação da PINN e a malha de 0,25 min do modelo serial, não entram nessas métricas, "
        "pois não correspondem a medições.")
    sw.paragraph(
        "A consistência física das previsões é quantificada pela fração dos nós da curva prevista, em malha de "
        "0,25 min, com conversão decrescente ou acima do limite estequiométrico (Equação 4.1.3.1), denominada "
        "inconsistência física.")
    sw.paragraph(
        "Para quantificar o ganho de cada arquitetura híbrida, duas linhas de base são adotadas em comum: o modelo "
        "puramente fenomenológico (*white-box*, Seção 4.2), que indica o erro da física sem correção, e o modelo "
        "puramente orientado a dados (*black-box*, Seção 4.3), que indica o que o aprendizado de máquina alcança sem "
        "informação física. No modelo paralelo, adota-se ainda uma terceira referência, construída diretamente a "
        "partir da tabela experimental organizada por $\\eta$ e $t$.")
    pintar(sw.inserted, AZUL)
    v19.stats["adicionar"] += sum(len(texto(e).split()) for e in sw.inserted)
    return sw.inserted


# ---------------------------------------------------------------------------------------------- principal
def main() -> None:
    doc = m.abrir(GRUPO)
    body = doc.element.body
    print("sdt removidos:", m.desembrulhar(body))
    m.garantir_rpr(body)
    G = [x._p for x in doc.paragraphs]
    Gt = [texto(x).strip() for x in G]

    def g(comeco: str, depois_de=None, antes_de=None):
        alvo = sem_espaco(comeco)
        i0 = G.index(depois_de) + 1 if depois_de is not None else 0
        i1 = G.index(antes_de) if antes_de is not None else len(G)
        achados = [G[i] for i in range(i0, i1) if sem_espaco(Gt[i]).startswith(alvo)]
        assert len(achados) == 1, f"{len(achados)} parágrafos começam com {comeco!r}"
        return achados[0]

    # ------------------------------------------------------------------ mapa v18 -> versão 2 do grupo
    v18 = m.V18 if m.V18.exists() else DOC_DIR / "old" / m.V18.name   # as versões antigas foram para old/
    d18 = m.abrir(v18)
    A = [x._p for x in d18.paragraphs]
    At = [texto(x).strip() for x in A]
    mapa: dict[int, object] = {}
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, At, Gt, autojunk=False).get_opcodes():
        if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
            for k in range(i2 - i1):
                mapa[i1 + k] = G[j1 + k]
    mapa_t: dict[int, object] = {}
    idx_p = {id(el): i for i, el in enumerate(A)}
    ultimo, ordem, k = None, 0, 0
    for el in d18.element.body:
        if el.tag == W_P:
            ultimo, ordem = idx_p[id(el)], 0
        elif el.tag == W_TBL:
            ordem += 1
            if ultimo in mapa:
                alvo, n = mapa[ultimo].getnext(), 0
                while alvo is not None and alvo.tag != W_P:
                    if alvo.tag == W_TBL:
                        n += 1
                        if n == ordem:
                            if difflib.SequenceMatcher(None, texto(el), texto(alvo)).ratio() > 0.8:
                                mapa_t[k] = alvo
                            break
                    alvo = alvo.getnext()
            k += 1

    class Mapa:
        def __init__(self, d, nome):
            self.d, self.nome = d, nome

        def __getitem__(self, i):
            assert i in self.d, f"{self.nome}[{i}] da v18 sem correspondente na versão do grupo"
            return self.d[i]

    P, T = Mapa(mapa, "P"), Mapa(mapa_t, "T")
    ap_a = g("APÊNDICE A -")
    imagens = []

    def p(i: int, comeco: str):
        el = mapa.get(i)
        if el is not None and sem_espaco(texto(el)).startswith(sem_espaco(comeco)):
            return el
        el = g(comeco, depois_de=ap_a)
        mapa[i] = el
        return el

    def figura(i_legenda: int, comeco: str):
        assert P[i_legenda - 1].findall(".//" + qn("w:drawing")) and texto(P[i_legenda + 1]).startswith("Fonte")
        imagens.append(P[i_legenda - 1])
        return [p(i_legenda, comeco), P[i_legenda + 1]]

    def np_ap(depois_de, modelo, txt: str, antes: bool = False):
        par = v19.novo_paragrafo(depois_de, modelo, m.traduzir(txt).replace("Seção 4.5", "Seção 4.6"))
        if antes:
            depois_de.addprevious(par)
        return par

    # ------------------------------------------------------------------ 1. apêndices: cortes da v19 e fusão da v20
    el = ap_a
    while el is not None:
        for c in list(el.iter(qn("w:color"))):
            if (c.get(qn("w:val")) or "").upper() == VERMELHO:
                c.getparent().remove(c)
        el = el.getnext()
    corpo_ap = P[721]
    fonte_v19 = Path(v19.__file__).read_text(encoding="utf-8")
    a = fonte_v19.index("    # ------------------------------------------------------------------ 3. Apêndice A")
    b = fonte_v19.index("    doc.save(DESTINO)")
    exec(compile(textwrap.dedent(fonte_v19[a:b]), "v19:apendices", "exec"),
         {"p": p, "P": P, "T": T, "figura": figura, "retirar": v19.retirar, "retirar_trecho": m.retirar_trecho,
          "novo_paragrafo": np_ap, "run_azul": v19.run_azul, "corpo_ap": corpo_ap, "texto": texto})
    v19.retirar(ap_a)
    novo_a = np_ap(ap_a, ap_a, "APÊNDICE A - DETALHAMENTO DO MODELO HÍBRIDO SERIAL")
    v19.retirar(p(721, "Este apêndice detalha a obtenção"))
    intro_a = np_ap(P[721], corpo_ap,
        "Este apêndice detalha as etapas de desenvolvimento do modelo híbrido serial resumidas na Seção 4.6: o "
        "problema inverso, a base de dados, a rede neural e a seleção da configuração.")
    d5 = p(894, "D.5")
    novo_b = np_ap(d5, ap_a, "APÊNDICE B - RESULTADOS COMPLEMENTARES DOS MODELOS HÍBRIDO SERIAL E BLACK-BOX", antes=True)
    intro_b = np_ap(d5, corpo_ap,
        "Este apêndice reúne os resultados da seleção da configuração do modelo híbrido serial, das variantes "
        "testadas e da previsão dos ensaios novos (Seções B.1 a B.4) e os resultados completos dos modelos híbrido "
        "serial e *black-box*, resumidos nas Seções 5.4 e 5.X (Seções B.5 a B.8): as curvas, as métricas e a "
        "conversão de zinco medida e prevista em cada instante, nos 16 ensaios de Bortot Coelho (2017) e nos quatro "
        "ensaios novos. Nas Seções B.5 a B.8, os erros estão em pontos percentuais (p.p.) de conversão.", antes=True)
    ja_novos = [intro_a, intro_b]      # guardar os elementos (e não id()), para o lxml manter os mesmos objetos
    for i, comeco, novo_titulo in v20.TITULOS:
        old = p(i, comeco)
        v19.retirar(old)
        if novo_titulo:
            ja_novos.append(np_ap(old, old, novo_titulo))
    for i, comeco in v20.INTRODUCOES_ANTIGAS:
        v19.retirar(p(i, comeco))
    # a conversão das medições dos ensaios novos passa para a seção comum
    par = g("As medições dos quatro ensaios novos (condições na Tabela D.12)", depois_de=ap_a)
    v19.retirar(par)
    np_ap(par, corpo_ap,
        "As medições dos quatro ensaios novos (condições na Tabela D.12) foram convertidas em conversão de zinco "
        "conforme a Seção 4.1.2, com os rótulos dos Ensaios E2 e E3 trocados em relação à planilha do laboratório. "
        "Não há medição em 4 min.")
    palavras_antes = sum(len(texto(e).split()) for e in [ap_a] + list(ap_a.itersiblings()))

    # ------------------------------------------------------------------ 2. apêndices: forma final, sem cores
    retirado, adicionado = v19.stats["retirar"], v19.stats["adicionar"]
    aceitar_marcas(ap_a, imagens)
    v19.stats["retirar"], v19.stats["adicionar"] = 0, 0      # daqui em diante, só o que fica marcado no documento
    regiao = [novo_a] + list(novo_a.itersiblings())
    regiao = [e for e in regiao if e.tag in (W_P, W_TBL)]
    palavras_depois = sum(len(texto(e).split()) for e in regiao)

    # ------------------------------------------------------------------ 3. apêndices: renumeração
    mapas = {"F": {}, "T": {}, "E": {}, "S": SECOES}
    cont = {}
    ap = "A"
    for el in regiao:
        if el is novo_b:
            ap = "B"
        achados = []
        if el.tag == W_P:
            k = re.match(r"(Figura|Tabela)\s+([A-E]\.\d+)\b", texto(el).strip())
            if k:
                achados.append((k.group(1)[0], k.group(2)))
        elif el.findall(".//" + M_OMATH):
            for tr in el.findall(qn("w:tr")):       # tabela de equação: uma equação por linha
                k = re.search(r"\(([A-E]\.\d+)\)$", texto(tr).strip())
                if k:
                    achados.append(("E", k.group(1)))
        for tipo, antigo in achados:
            cont[(ap, tipo)] = cont.get((ap, tipo), 0) + 1
            assert antigo not in mapas[tipo], f"rótulo repetido: {tipo} {antigo}"
            mapas[tipo][antigo] = f"{ap}.{cont[(ap, tipo)]}"
    mapas["E"].setdefault("A.1", "4.XX.5")      # equação que saiu do apêndice: vale a da Seção 4.6
    for tipo_ in "FTE":
        log.append(f"mapa {tipo_}: " + ", ".join(f"{k_}>{v_}" for k_, v_ in mapas[tipo_].items()))
    for el in regiao:
        if el.tag == W_TBL and "(C.2)" in texto(el):
            log.append(f"tabela C.2: linhas={len(el.findall(qn('w:tr')))} omath={len(el.findall('.//' + M_OMATH))} texto={texto(el)[-80:]!r}")
    print("rótulos nos apêndices:", {f"{a_}{t_}": n for (a_, t_), n in sorted(cont.items())})
    n_trocas = 0
    ap = "A"
    for el in regiao:
        if el is novo_b:
            ap = "B"
        for par in ([el] if el.tag == W_P else list(el.iter(W_P))):
            estilo = par.find(qn("w:pPr") + "/" + qn("w:pStyle"))
            if any(par is x for x in ja_novos) or (estilo is not None and estilo.get(qn("w:val"), "").startswith("Heading")):
                continue
            for a_, b_, antigo, novo in remissoes(par, mapas, letras_antigas=False, contexto_d=ap):
                substituir(par, a_, b_, novo)
                n_trocas += 1
    for el in regiao:        # "Seções B.3 a B.3" -> "Seção B.3"
        if el.tag == W_P:
            for k in reversed(list(re.finditer(r"Seções ([AB]\.\d+) (?:a|e) \1(?!\d)", texto(el)))):
                substituir(el, k.start(), k.end(), f"Seção {k.group(1)}")
    print("remissões trocadas nos apêndices:", n_trocas)
    # ajustes pontuais que a fusão das seções pede (e duas lacunas que já vinham do texto original)
    for antigo, novo in AJUSTES_APENDICE:
        alvos = [e for e in regiao if e.tag == W_P and antigo in texto(e)]
        assert len(alvos) == 1, f"{len(alvos)} parágrafos com {antigo!r}"
        i_ = texto(alvos[0]).index(antigo)
        substituir(alvos[0], i_, i_ + len(antigo), novo)

    # ------------------------------------------------------------------ 4. seção comum (azul)
    secao_comum(doc, g)

    # ------------------------------------------------------------------ 5. black-box: o que passa para a seção comum
    corpo_met = g("Antes de iniciar o treinamento do black box")
    sub = g("Pré-processamento e partição dos dados")
    v19.retirar(corpo_met, g("Dessa forma, como a temperatura (40°C) e a agitação"))
    v19.novo_paragrafo(sub, corpo_met,
        "Os dados, as variáveis de entrada e de saída e a partição dos ensaios em treino e teste cego são os "
        "descritos na Seção 4.1.1.")
    m.retirar_trecho(g("Para que essas diferentes grandezas"), "Por fim, com o intuito de avaliar a capacidade", None)
    for comeco in ("O modelo black-box é um perceptron multicamadas", "Com o gradiente fornecido pelo backpropagation"):
        m.trocar(g(comeco), "(Seção 4.5)", "(Seção 4.6)")

    # ------------------------------------------------------------------ 6. serial: partição e cortes da v21
    resultados = g("RESULTADOS E DISCUSSÃO")
    met_serial = g("MODELAGEM HÍBRIDA SERIAL", antes_de=resultados)
    m.retirar_trecho(g("Os valores de ν(t) do problema inverso foram organizados"),
                     "A temperatura (40 °C) e a velocidade de agitação", "em todos os ensaios. ")
    par = g("A escolha desses três ensaios seguiu três critérios", depois_de=met_serial)
    v19.retirar(g("Os 16 ensaios foram divididos em 13 para treino (81,25%)"), par)
    v19.novo_paragrafo(par, par,
        "A partição dos ensaios é a comum a todas as abordagens (Seção 4.1.1): 13 ensaios de treino e os Ensaios 7, "
        "8 e 14 reservados para o teste cego (Figura 4.XX.9(a)). Na base de 960 registros, a divisão por ensaios "
        "inteiros é ainda mais necessária, pois os registros de um mesmo ensaio, separados por apenas 0,25 min, têm "
        "valores de $\\nu$ muito próximos.")
    par = g("As entradas têm escalas muito diferentes")
    v19.retirar(par)
    v19.novo_paragrafo(par, par, "As entradas foram padronizadas pelo escore Z (Seção 3.2.3):")
    m.retirar_trecho(g("A escolha da configuração da rede e a decisão"), "Com quatro dobras, cada validação dispõe",
                     "disponíveis para o ajuste. ")
    m.retirar_trecho(g("As camadas ocultas são três blocos residuais"), "Cada bloco soma uma projeção linear",
                     "redes com várias camadas. ")

    # ------------------------------------------------------------------ 7. Resultados: ensaios novos e remissões
    m.trocar(g("Nos quatro ensaios novos, descritos na Seção 5.4"), "descritos na Seção 5.4", "descritos na Seção 4.1.2")
    par = g("O modelo foi confrontado também com quatro ensaios novos")
    ult = m.retirar_trecho(par, ", realizados pelo grupo em condições intermediárias",
                           "e amostragem em 0,5; 1; 2; 3; 5 e 15 min")
    v19.run_azul(ult, ", descritos na Seção 4.1.2 (Tabela 5.4.2)")
    ult = m.retirar_trecho(par, "O Ensaio E4 (", None)
    v19.run_azul(ult, "As medições foram tratadas com os rótulos de E2 e E3 trocados (Seção 4.1.2).")
    n_res = 0
    i_res, i_fim = G.index(resultados), G.index(g("REFERÊNCIAS BIBLIOGRÁFICAS"))
    TROCAS_RES = [(r"Seções 4\.1\.4 a 4\.1\.7", "Seção 4.3"), (r"Seção 4\.2\.4", "Seção 4.1.4"),
                  (r"Seção 4\.2\.3", "Seção 4.1.3"), (r"Tabela 4\.2\.2", "Tabela 4.1.3"),
                  (r"Seções 4\.5\.2 e 4\.5\.5", "Seções 4.6.3 e 4.6.6"), (r"Seção 4\.5\.2", "Seção 4.6.3"),
                  (r"Seção 4\.5(?![.\d])", "Seção 4.6"), (r"white-box da Seção 4\.1(?![.\d])", "white-box da Seção 4.2")]
    for par in G[i_res:i_fim]:
        if par.getparent() is None:
            continue
        achados = []
        for padrao, novo in TROCAS_RES:
            for k in re.finditer(padrao, texto(par)):
                if not any(a_ < k.end() and k.start() < b_ for a_, b_, _ in achados):
                    achados.append((k.start(), k.end(), novo))
        for a_, b_, novo in sorted(achados, reverse=True):
            marcar_troca(par, a_, b_, novo)
            n_res += 1
    print("remissões marcadas nos Resultados (seções):", n_res)

    # ------------------------------------------------------------------ 8. remissões aos apêndices no corpo do texto
    n_corpo = 0
    i_met, i_ser = G.index(g("MATERIAIS E MÉTODOS")), G.index(met_serial)
    for i in range(i_met, i_fim):
        par = G[i]
        if par.getparent() is None or cor_todo(par) == VERMELHO:
            continue
        antigas = i_ser < i < i_res
        ctx = None
        t = texto(par)
        if "Apêndice D" in t or "Apêndice E" in t:
            ctx = "A" if antigas else ("B" if "E2 e E3" in t or "ensaios estão no" in t else None)
        for a_, b_, antigo, novo in remissoes(par, mapas, letras_antigas=antigas, contexto_d=ctx):
            if any(cor_de(r) == VERMELHO for r in runs_no_trecho(par, a_, b_)):
                continue
            marcar_troca(par, a_, b_, novo)
            n_corpo += 1
            log.append(f"corpo: {antigo} -> {novo}: {t[max(0, a_ - 50):b_ + 15]!r}")
    print("remissões aos apêndices marcadas no corpo:", n_corpo)

    # ------------------------------------------------------------------ 9. referências novas, em azul
    novas = add_references(doc, v20.REFERENCIAS + [m.REF_PSICHOGIOS])
    for par in doc.paragraphs:
        if par.text.strip() in novas:
            pintar([par._p], AZUL)
    v19.stats["adicionar"] += sum(len(x.split()) for x in novas)

    doc.save(DESTINO)
    for linha in log:
        print("  ", linha)
    print(f"apêndices: {palavras_antes - adicionado} palavras na versão do grupo -> {palavras_depois} na forma final")
    print(f"corpo do texto: {v19.stats['retirar']} palavras marcadas para retirar; {v19.stats['adicionar']} a adicionar")
    print(f"referências novas: {len(novas)}; gravado: {DESTINO.name}")


def cor_todo(par) -> str:
    return VERMELHO if todo_vermelho(par) else ""


def runs_no_trecho(par, a: int, b: int):
    pos, out = 0, []
    for ch in par:
        if ch.tag not in (W_R, M_OMATH, M_PARA):
            continue
        n = len(texto(ch))
        if n and pos < b and a < pos + n and ch.tag == W_R:
            out.append(ch)
        pos += n
    return out


if __name__ == "__main__":
    main()
