"""Gera a v19 a partir da v18 (sem alterá-la): proposta de enxugamento, marcada por cores.

Pedido do usuário em 12/11/2026:
1. Métodos do black-box (MLP pura): versão mais breve, apoiada na seção comum e na seção serial;
2. Apêndices A a D: tirar as explicações gerais (que passam a ser citadas na Revisão Bibliográfica) e as
   repetições da Seção 4.5, deixando o que foi feito e as tabelas de resultados;
3. Marcação: texto a RETIRAR em vermelho (FF0000) e tachado; texto a ADICIONAR em azul (0070C0).

Nada é apagado: o usuário decide bloco a bloco. O vermelho antigo dos apêndices (que estava lá só por
esquecimento) é removido antes, para que vermelho signifique apenas "retirar".
Figuras a retirar ficam com a legenda e a fonte em vermelho (a imagem não aceita cor).
Uso: python enxugar_apendices_v19.py
"""

from __future__ import annotations

import copy
import io
import sys
from pathlib import Path

import docx
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docx_utils import SectionWriter, _DEPOIS_DE_COLOR, pintar  # noqa: E402

DOC_DIR = Path(__file__).resolve().parents[1]
ORIGEM = DOC_DIR / "RELATÓRIO FINAL LOP_v18.docx"
DESTINO = DOC_DIR / "RELATÓRIO FINAL LOP_v19.docx"
VERMELHO, AZUL = "FF0000", "0070C0"
W_P, W_TBL, W_R, W_T = qn("w:p"), qn("w:tbl"), qn("w:r"), qn("w:t")
M_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
M_OMATH, M_T = M_NS + "oMath", M_NS + "t"
_DEPOIS_DE_STRIKE = _DEPOIS_DE_COLOR | {qn(f"w:{n}") for n in (
    "dstrike", "outline", "shadow", "emboss", "imprint", "noProof", "snapToGrid", "vanish", "webHidden", "color")}

stats = {"retirar": 0, "adicionar": 0}


def texto(el) -> str:
    return "".join(x.text or "" for x in el.iter() if x.tag in (W_T, M_T))


def tachar(el) -> None:
    for r in el.iter(W_R):
        rpr = r.find(qn("w:rPr"))
        if rpr.find(qn("w:strike")) is not None:
            continue
        novo = parse_xml(f'<w:strike {nsdecls("w")}/>')
        depois = next((ch for ch in rpr if ch.tag in _DEPOIS_DE_STRIKE), None)
        if depois is not None:
            depois.addprevious(novo)
        else:
            rpr.append(novo)


def retirar(*els) -> None:
    """Marca elementos inteiros (parágrafos ou tabelas) para retirada."""
    for el in els:
        stats["retirar"] += len(texto(el).split())
        pintar([el], VERMELHO)
        tachar(el)


def _dividir_run(r, k: int):
    """Divide o run no caractere k; devolve (esquerda, direita)."""
    ts = r.findall(W_T)
    assert len(ts) == 1 and len([c for c in r if c.tag != qn("w:rPr")]) == 1, "run complexo demais para dividir"
    novo = copy.deepcopy(r)
    t0, t1 = ts[0], novo.find(W_T)
    s = t0.text
    t0.text, t1.text = s[:k], s[k:]
    for t in (t0, t1):
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    r.addnext(novo)
    return r, novo


def retirar_trecho(p, inicio: str | None, fim: str | None):
    """Marca para retirada o trecho do parágrafo que vai do começo de `inicio` ao final de `fim`.

    inicio=None: desde o começo do parágrafo; fim=None: até o final. Devolve o último elemento marcado.
    """
    total = texto(p)
    a = 0 if inicio is None else total.find(inicio)
    assert a >= 0, f"trecho inicial não encontrado: {inicio!r}"
    if fim is None:
        b = len(total)
    else:
        b = total.find(fim, a)
        assert b >= 0, f"trecho final não encontrado: {fim!r}"
        b += len(fim)
    pos, marcados = 0, []
    for ch in list(p):
        if ch.tag not in (W_R, M_OMATH, M_NS + "oMathPara"):
            assert not texto(ch), f"elemento com texto não tratado: {ch.tag}"
            continue
        n = len(texto(ch))
        ini, end = pos, pos + n
        pos = end
        if n == 0 or end <= a or ini >= b:
            continue
        if ch.tag == W_R:
            alvo = ch
            if ini < a:
                _, alvo = _dividir_run(alvo, a - ini)
                ini = a
            if end > b:
                alvo, _ = _dividir_run(alvo, b - ini)
            marcados.append(alvo)
        else:
            marcados.append(ch)
    assert marcados
    for el in marcados:
        stats["retirar"] += len(texto(el).split())
        if el.tag == W_R:
            pintar_run(el, VERMELHO)
            tachar_run(el)
        else:
            pintar([el], VERMELHO)
    return marcados[-1]


def pintar_run(r, cor: str) -> None:
    from docx_utils import definir_cor
    rpr = r.find(qn("w:rPr"))
    if rpr is None:
        rpr = parse_xml(f"<w:rPr {nsdecls('w')}/>")
        r.insert(0, rpr)
    definir_cor(rpr, cor)


def tachar_run(r) -> None:
    rpr = r.find(qn("w:rPr"))
    if rpr.find(qn("w:strike")) is None:
        novo = parse_xml(f'<w:strike {nsdecls("w")}/>')
        depois = next((ch for ch in rpr if ch.tag in _DEPOIS_DE_STRIKE), None)
        if depois is not None:
            depois.addprevious(novo)
        else:
            rpr.append(novo)


def novo_paragrafo(depois_de, modelo, txt: str):
    """Insere, depois do elemento dado, um parágrafo azul com a formatação do parágrafo-modelo."""
    sw = SectionWriter(None, {"body": modelo}, None)
    p = sw._new_par("body")
    sw._fill(p, txt)
    pintar([p], AZUL)
    depois_de.addnext(p)
    stats["adicionar"] += len(texto(p).split())
    return p


def run_azul(depois_de, txt: str) -> None:
    r = SectionWriter._run(txt, color=AZUL)
    depois_de.addnext(r)
    stats["adicionar"] += len(txt.split())


def main() -> None:
    with open(ORIGEM, "rb") as f:
        doc = docx.Document(io.BytesIO(f.read()))
    P = [p._p for p in doc.paragraphs]
    T = [t._tbl for t in doc.tables]

    def p(i: int, comeco: str):
        assert texto(P[i]).strip().startswith(comeco), f"[{i}] esperado {comeco!r}, achei {texto(P[i])[:60]!r}"
        return P[i]

    def figura(i_legenda: int, comeco: str):
        """Imagem, legenda e fonte de uma figura (a legenda é o parágrafo i_legenda)."""
        assert P[i_legenda - 1].findall(".//" + qn("w:drawing")) and texto(P[i_legenda + 1]).startswith("Fonte")
        return [p(i_legenda, comeco), P[i_legenda + 1]]

    # ------------------------------------------------------------------ 0. apêndices: tirar o vermelho antigo
    ini = p(720, "APÊNDICE A")
    el, n_cor = ini, 0
    while el is not None:
        for c in list(el.iter(qn("w:color"))):
            if c.get(qn("w:val")) == VERMELHO:
                c.getparent().remove(c)
                n_cor += 1
        el = el.getnext()
    palavras_apendices = sum(len(texto(e).split()) for e in ini.itersiblings()) + len(texto(ini).split())
    palavras_ad = sum(len(texto(e).split()) for e in _ate(ini, p(986, "APÊNDICE E")))

    corpo_ap = P[721]      # modelo de formatação: corpo de texto dos apêndices
    corpo_rev = P[213]     # corpo de texto da revisão
    corpo_met = P[402]     # corpo de texto de Métodos (black-box)

    # ------------------------------------------------------------------ 1. Revisão: conceitos com as fontes
    novo_paragrafo(p(213, "As funções de ativação conferem"), corpo_rev,
        "Além dessas funções clássicas, redes voltadas à regressão têm empregado ativações suaves como a GELU "
        "(*Gaussian Error Linear Unit*), que se comporta como a ReLU longe da origem, mas é diferenciável em todos os "
        "pontos (Hendrycks; Gimpel, 2016), e a função *softplus*, $\\ln(1+e^{z})$, adotada na camada de saída quando a "
        "grandeza prevista deve ser positiva (Goodfellow; Bengio; Courville, 2016). Para facilitar o treinamento de "
        "redes com várias camadas, He et al. (2016) propuseram as conexões residuais, em que cada bloco soma à sua "
        "saída uma cópia ou uma projeção linear da própria entrada, de modo que as camadas aprendem apenas a correção "
        "sobre esse atalho. Já o *dropout* anula aleatoriamente uma fração dos neurônios a cada passo do treinamento, "
        "o que impede a rede de depender de combinações específicas entre eles e reduz o sobreajuste "
        "(Srivastava et al., 2014).")
    p(215, "O ajuste dos pesos")
    novo_paragrafo(P[215], corpo_rev,
        "Na prática, a perda é calculada em mini-lotes (*mini-batches*) dos dados de treino, e cada passagem completa "
        "pelo conjunto constitui uma época (Goodfellow; Bengio; Courville, 2016). Entre as variações do Adam, o AdamW "
        "separa a penalização dos pesos da atualização pelo gradiente (Loshchilov; Hutter, 2019), e é comum reduzir a "
        "taxa de aprendizado ao longo das épocas segundo uma curva cossenoidal, com passos grandes no início e "
        "pequenos no final (Loshchilov; Hutter, 2017). Como os pesos iniciais e a ordem dos lotes são sorteados, redes "
        "idênticas treinadas com sementes diferentes chegam a soluções distintas. Lakshminarayanan, Pritzel e Blundell "
        "(2017) mostraram que a média das previsões de um comitê dessas redes (*deep ensemble*) reduz o erro e que a "
        "dispersão entre os membros indica a incerteza da previsão.")
    p(237, "Sob o aspecto metodológico")
    novo_paragrafo(P[237], corpo_rev,
        "Quando há poucos dados, a partição única de validação é substituída pela validação cruzada em $k$ dobras: o "
        "conjunto de treino é dividido em $k$ partes, cada uma é usada uma vez como validação de um modelo ajustado "
        "com as demais, e o erro médio das $k$ rodadas estima a capacidade de generalização (Hastie; Tibshirani; "
        "Friedman, 2009). Se as observações formam grupos dependentes entre si, como os pontos de uma mesma curva "
        "cinética, as dobras devem ser formadas por grupos inteiros, sob pena de vazamento de informação (Kapoor; "
        "Narayanan, 2023). Os hiperparâmetros podem ser escolhidos por busca em grade, por busca aleatória ou por "
        "busca guiada por modelo, como o algoritmo TPE (*Tree-structured Parzen Estimator*), que utiliza as "
        "configurações já avaliadas para propor as seguintes (Bergstra et al., 2011) e está implementado na biblioteca "
        "Optuna (Akiba et al., 2019). Como a melhor entre muitas configurações tende a ter sido favorecida também pelo "
        "acaso, a sua nota é otimista e deve ser reestimada (Cawley; Talbot, 2010). Para a escolha final, Hastie, "
        "Tibshirani e Friedman (2009) recomendam a regra de um erro-padrão, que adota o modelo mais simples entre "
        "aqueles cujo erro não supera o do melhor em mais de um erro-padrão.")
    p(300, "A calibração do modelo serial pode ser realizada")
    novo_paragrafo(P[300], corpo_rev,
        "Na abordagem sequencial, a identificação da grandeza não medida a partir dos dados constitui um problema "
        "inverso, em geral mal-posto, pois várias soluções reproduzem as mesmas observações. A solução é estabilizada "
        "restringindo-se a forma da função procurada e acrescentando-se termos de regularização à função objetivo "
        "(Aster; Borchers; Thurber, 2018). Já a abordagem simultânea foi introduzida por Psichogios e Ungar (1992), "
        "que treinaram a rede neural através do próprio modelo de primeiros princípios.")

    # ------------------------------------------------------------------ 2. Métodos: black-box (MLP pura) mais breve
    retirar(p(402, "O modelo puramente orientado a dados (black-box) estima"), p(403, "Como a temperatura"),
            p(404, "Como as três entradas"))
    novo_paragrafo(P[404], corpo_met,
        "O modelo puramente orientado a dados (*black-box*) é uma rede neural que estima a conversão de zinco "
        "diretamente a partir dos parâmetros operacionais do ensaio, sem o balanço populacional, e serve de linha de "
        "base para as abordagens híbridas (Seção 4.2.4). As entradas são a concentração inicial de ácido sulfúrico "
        "($C_{A0}$), a razão molar estequiométrica ($\\eta$) e o tempo de reação, fornecido como $\\ln t$, e a saída é "
        "a conversão ($X_{Zn}$). A partição dos ensaios é a comum a todas as abordagens (Seção 4.2.1), com 13 ensaios "
        "de treino (91 pontos com $t>0$) e os Ensaios 7, 8 e 14 reservados para o teste cego (21 pontos), e as "
        "entradas foram padronizadas pelo escore Z, como no modelo híbrido serial (Equação 4.5.2.1), com a média e o "
        "desvio-padrão calculados apenas nos pontos de treino. A diferença em relação ao modelo serial está no alvo: a "
        "rede é treinada com as conversões medidas, e não com as taxas de retração do problema inverso.")
    retirar(p(406, "O modelo black-box é uma rede neural MLP"), p(407, "Na alimentação direta"),
            p(408, "A camada de saída é linear"))
    novo_paragrafo(P[408], corpo_met,
        "A rede é um perceptron multicamadas de alimentação direta (Seção 3.2.2), com três camadas ocultas de 90, 45 "
        "e 22 neurônios, as mesmas larguras da rede do modelo híbrido serial (Seção 4.5.3), função de ativação GELU "
        "(Hendrycks; Gimpel, 2016) e 5.490 parâmetros. Diferentemente da rede do modelo serial, não há blocos "
        "residuais nem *dropout*, e a camada de saída é linear. O modelo não tem, portanto, nenhuma restrição física: "
        "a conversão prevista não é obrigada a ficar entre 0 e 1, a respeitar o limite estequiométrico nem a crescer "
        "com o tempo (Seção 4.2.3), o que permite medir o que o aprendizado de máquina alcança sem informação do "
        "processo.")
    p(410, "O treinamento é guiado pelo erro quadrático médio")
    p(411, "Em que Nd")
    retirar(p(412, "Para esse ajuste, utiliza-se o algoritmo de backpropagation"),
            p(413, "Os parâmetros são atualizados"), p(414, "O modelo final é a média das previsões de dez redes"))
    novo_paragrafo(P[414], corpo_met,
        "O ajuste foi feito por retropropagação (Seção 3.2.2) com o otimizador AdamW (Loshchilov; Hutter, 2019), em "
        "mini-lotes de 16 pontos, como no modelo serial (Seção 4.5.4). Os hiperparâmetros foram escolhidos pela "
        "validação cruzada por ensaio, com as mesmas quatro dobras do modelo serial (Seção 4.5.2): entre 32 "
        "combinações de arquitetura, taxa de aprendizado, penalização dos pesos e número de épocas, adotou-se a de "
        "menor erro na conversão fora da dobra, com taxa de aprendizado de $10^{-2}$, penalização dos pesos de "
        "$10^{-4}$ e 900 épocas fixas, sem parada antecipada. O modelo final é a média das previsões de dez redes "
        "treinadas com essa configuração e sementes diferentes (42 a 51), e o seu desempenho é quantificado por "
        "$R^2$, RMSE e MAE (Seção 4.2.4).")

    # ------------------------------------------------------------------ 3. Apêndice A
    retirar(p(722, "Para treinar a rede neural"), p(723, "Problemas inversos desse formato"))
    retirar(p(725, "A taxa de retração de cada ensaio foi representada"), T[17], p(726, "Em que θ="))
    novo_paragrafo(P[726], corpo_ap,
        "A taxa de retração de cada ensaio foi representada pela Equação (4.5.1.1), cujos parâmetros, unidades e "
        "limites estão na Tabela A.2. A Figura A.1 ilustra a contribuição de cada termo e a retração acumulada "
        "resultante.")
    retirar(p(731, "Para cada vetor de parâmetros"), T[18], p(732, "Com δ1="))
    novo_paragrafo(P[732], corpo_ap,
        "A retração acumulada foi calculada pela Equação (4.5.1.2) na malha temporal de 0,25 min da Figura A.2, que "
        "contém todos os instantes experimentais.")
    retirar(p(737, "Como em t=0 a conversão é nula"), p(738, "Os parâmetros de cada ensaio foram determinados"), T[19],
            p(739, "O primeiro termo da Equação (A.3)"), p(740, "O  primeiro termo, com λ1"),
            p(741, "O segundo termo, com λ2"), p(742, "Os últimos termos, com λ3 e λ4"), p(743, "Os pesos adotados foram"))
    novo_paragrafo(P[743], corpo_ap,
        "A função objetivo, os termos de penalização e os pesos adotados são os das Equações (4.5.1.3) e (4.5.1.4), "
        "com $b_1^{ref}=4$ min⁻¹.")
    retirar_trecho(p(744, "Para verificar o efeito das penalizações"), "A penalização da taxa final, com", None)
    retirar(p(749, "A minimização foi realizada com o algoritmo L-BFGS-B"), p(750, "Como a função objetivo pode apresentar"))
    novo_paragrafo(P[750], corpo_ap,
        "A minimização (Seção 4.5.1) respeitou os limites da Tabela A.2 e partiu das seis estimativas iniciais da "
        "Tabela A.3, com as derivadas aproximadas por diferenças finitas e tolerância de convergência de $10^{-10}$.")
    retirar(p(755, "Ao final do ajuste"), p(756, "Foi escolhida da malha regular"), p(757, "Em ambas as bases"))

    # ------------------------------------------------------------------ 4. Apêndice B
    retirar(p(775, "A partir dos dados obtidos pelo problema inverso"))
    novo_paragrafo(P[775], corpo_ap,
        "A Figura B.1 resume a preparação dos dados para o treinamento, e a Tabela B.1 apresenta, como exemplo, alguns "
        "registros do Ensaio 9. Cada ensaio contribui com os 60 registros da malha de 0,25 a 15 min, num total de 960; "
        "apenas $C_{A0}$, $\\eta$ e $t$ são fornecidos à rede, e $\\nu$ é a variável que ela deve prever.")
    retirar(p(779, "Cada registro da base corresponde"), p(782, "Os registros da malha regular foram utilizados"),
            p(783, "Como variáveis de entrada"))
    retirar_trecho(p(785, "Para avaliar a capacidade de generalização"), "Os ensaios de teste não participaram", None)
    retirar(p(786, "A divisão foi feita por ensaios inteiros"))
    retirar_trecho(p(787, "A proporção adotada"), None, "não dependa de uma única condição. ")
    retirar(p(790, "A escolha dos ensaios de teste não foi aleatória"), p(791, "O primeiro critério"),
            p(792, "O segundo critério"), p(793, "O terceiro, e último, critério"))
    novo_paragrafo(P[793], corpo_ap,
        "A escolha dos ensaios de teste não foi aleatória e seguiu três critérios (Figura 4.5.4(a)). Os quatro "
        "vértices do planejamento ($C_{A0}$ de 0,10 e 1,50 mol/L com $\\eta$ de 0,5 e 3,1) foram mantidos no treino, "
        "de modo que o teste avalia a interpolação, e não a extrapolação (Sansana et al., 2024). Os ensaios de teste "
        "cobrem as três situações de disponibilidade de ácido: o Ensaio 8 é estequiométrico ($\\eta=1{,}0$), o Ensaio "
        "14 opera com excesso moderado ($\\eta=1{,}5$) e o Ensaio 7, com grande excesso ($\\eta=3{,}1$). Por fim, os "
        "quatro ensaios com deficiência de ácido ($\\eta=0{,}5$), em que a reação cessa pelo esgotamento do ácido, "
        "permaneceram no treino.")
    retirar(p(795, "Além do conjunto de teste"), p(796, "Para lidar com isso"), p(797, "Pelo mesmo motivo discutido"))
    retirar(p(802, "Quanto à transformação das variáveis"), T[28], p(803, "Em que xj"))
    novo_paragrafo(P[803], corpo_ap,
        "As entradas foram padronizadas pela Equação (4.5.2.1), com as médias e os desvios-padrão da Tabela B.4, "
        "calculados com os registros de treino e aplicados, sem recálculo, aos registros de teste. Os mesmos valores "
        "foram utilizados nas quatro dobras da validação cruzada, de modo que os ensaios de validação de cada dobra "
        "participaram do cálculo de $\\mu_j$ e $\\sigma_j$.")
    retirar(p(806, "Os parâmetros μj e σj foram calculados"))
    retirar_trecho(p(807, "A variável de saída exigiu"), "Isso ocorre porque a dissolução", None)
    retirar(p(808, "Se a rede fosse treinada diretamente"), T[30], p(809, "Com isso, a faixa da saída"))
    novo_paragrafo(P[809], corpo_ap,
        "Por isso, a saída foi transformada pela Equação (4.5.2.2), que comprime a faixa de 0 a 94 µm/min para 0 a "
        "4,55 (Figura B.2(b)).")

    # ------------------------------------------------------------------ 5. Apêndice C
    retirar(p(816, "A relação entre as condições do ensaio"), p(817, "A rede recebe as três entradas"), T[31],
            p(818, "Assim, mτ="), p(819, "A transformação do tempo"), p(820, "Com isso, a rede dispõe"))
    novo_paragrafo(P[820], corpo_ap,
        "A entrada temporal é a da Equação (4.5.3.1), com $m_\\tau=1{,}758$ e $s_\\tau=0{,}893$, média e "
        "desvio-padrão de $\\ln t$ nos 60 nós da malha temporal (Figura A.2). O uso de $t$ ou de $\\ln t$ foi uma das "
        "opções da busca de hiperparâmetros (Seção D.2).")
    p(821, "As camadas ocultas foram organizadas")
    p(822, "Em que Wl,1")
    retirar(p(823, "O vetor de saída de cada bloco"))
    retirar_trecho(p(824, "Conexões desse tipo foram propostas"), None, "à medida que se mostra necessária. ")
    retirar(p(825, "Como função de ativação ϕ"), T[33], p(826, "Em que Φ(z)"), p(827, "Durante o treinamento, foi utilizado o dropout"),
            p(828, "Por fim, a camada de saída"), T[34], p(829, "Em que y é a previsão"), T[35],
            p(830, "Essa combinação foi escolhida"), p(831, "Substituindo a Equação C.5"))
    novo_paragrafo(P[831], corpo_ap,
        "A função de ativação é a GELU (Hendrycks; Gimpel, 2016), e o *dropout* (Srivastava et al., 2014), com "
        "probabilidade $p=0{,}125$ definida pela busca de hiperparâmetros, é aplicado no ramo não linear de cada "
        "bloco, logo após a ativação, apenas durante o treinamento. A camada de saída é a das Equações (4.5.3.2) e "
        "(4.5.3.3), que, em conjunto, equivalem a $\\hat{\\nu}=e^{z}$, isto é, a saída linear da rede representa o "
        "logaritmo da taxa de retração. A Figura C.1 mostra as duas funções.")
    retirar(p(836, "O treinamento consiste em ajustar"), T[36], p(837, "Em que B é o número de registros"),
            p(838, "A minimização foi feita por descida de gradiente"))
    novo_paragrafo(P[838], corpo_ap,
        "A função de perda é a da Equação (4.5.4.1), e os parâmetros ajustados são os pesos, os vieses, as matrizes de "
        "projeção e os coeficientes $\\alpha_l$. O ciclo de treinamento, em mini-lotes de 16 registros (49 "
        "atualizações por época), está representado na Figura C.2(a).")
    p(842, "A atualização dos parâmetros seguiu o algoritmo AdamW")
    retirar_trecho(p(843, "Em que γ0="), "Conforme a Figura C.2(b)", None)
    retirar_trecho(p(844, "Outro ponto importante"), None, "em condições novas. ")
    retirar(p(845, "Por fim, o resultado do treinamento depende"), p(846, "Redes treinadas com sementes diferentes"))

    # ------------------------------------------------------------------ 6. Apêndice D
    retirar(p(854, "Os valores apresentados na Tabela"), p(855, "A primeira decisão foi a grandeza"),
            p(856, "Como a retração acumulada é a integral"), p(857, "Por tanto, para lidar com isso"),
            p(858, "Ao final das quatro dobras"), T[39], p(859, "Em que Vk reúne"))
    novo_paragrafo(P[859], corpo_ap,
        "O critério de avaliação de cada configuração é o erro na conversão de zinco fora da dobra, dado pela Equação "
        "(4.5.5.1) e calculado nas $13\\times 7=91$ previsões dos ensaios de treino, cada uma feita por uma rede que "
        "não utilizou o ensaio no ajuste.")
    retirar_trecho(p(860, "Um cuidado adicional foi necessário"), "Se os ensaios de validação fossem usados", None)
    p(861, "Por fim, como o resultado do treinamento varia")
    retirar(p(867, "Com o critério definido"), p(868, "O funcionamento do TPE"), T[41], p(869, "Em que 𝐱 representa"))
    novo_paragrafo(P[869], corpo_ap,
        "A busca foi feita com o algoritmo TPE (Bergstra et al., 2011), na versão multivariada implementada na "
        "biblioteca Optuna (Akiba et al., 2019), que considera a dependência entre os hiperparâmetros. Para "
        "economizar tempo de cálculo, uma tentativa era interrompida se, depois da segunda dobra, a sua nota parcial "
        "fosse pior que a mediana das tentativas anteriores no mesmo ponto, e as avaliações foram executadas em 24 "
        "processos paralelos (Figura D.2(a)).")
    p(870, "A busca foi realizada em dois estágios")
    retirar_trecho(p(873, "Encerrada cada busca"), "Essa etapa é necessária porque", "(Cawley; Talbot, 2010). ")
    retirar_trecho(p(875, "A ideia da regra"), None, "um modelo mais complexo. ")
    retirar_trecho(p(880, "Definida a configuração"), "Redes treinadas com sementes diferentes partem", None)
    retirar(p(890, "Esses conjuntos têm significados diferentes"))
    novo_paragrafo(P[890], corpo_ap,
        "As métricas dos ensaios de treino medem a reprodução das curvas usadas no ajuste. A capacidade de previsão é "
        "estimada pelo erro fora da dobra da validação cruzada (Equação 4.5.5.1) e pelo teste cego, que, por reunir "
        "apenas três ensaios, deve ser interpretado com cautela. De forma complementar, a taxa prevista para os "
        "ensaios de teste foi comparada com as taxas estimadas no problema inverso, na malha de 0,25 min, pelo "
        "$R^2$ nas escalas de $\\nu$ e de $\\ln(1+\\nu)$.")
    retirar(p(891, "Para situar o desempenho do modelo híbrido"), p(892, "Tabela D.2"), T[46])
    assert texto(P[893]).startswith("Fonte")
    retirar(P[893])
    novo_paragrafo(P[893], corpo_ap,
        "Para situar o desempenho do modelo híbrido, foram utilizadas duas referências, acopladas ao balanço "
        "populacional da mesma forma: o modelo fenomenológico puro, com a taxa de retração dada pela lei cinética de "
        "reação interfacial, sem o fator empírico $\\alpha$, e a configuração de referência da rede, que mostra o "
        "efeito do procedimento de seleção. A comparação com o modelo puramente orientado a dados é apresentada na "
        "Seção 5.")
    # D.8: perdas com informação física
    retirar_trecho(p(941, "Com a configuração final fixa"), "O peso de νi é a soma", "da escala logarítmica da perda. ")
    retirar_trecho(P[941], "Com γ=1, o peso em 0,25 min", "(Figura D.12). ")
    retirar(*figura(943, "Figura D.12"))
    retirar(*figura(949, "Figura D.13"))
    retirar_trecho(p(945, "A busca (101 tentativas"), " e Figura D.13", " e Figura D.13")
    retirar(p(952, "Tabela D.9"), T[53])
    assert texto(P[953]).startswith("Fonte")
    retirar(P[953], p(954, "Para verificar se um γ menor"))
    novo_paragrafo(P[954], corpo_ap,
        "Repetida com a taxa de aprendizado e as épocas da configuração final e $\\gamma$ de 0,5, 1,0 e 1,5, a D1 não "
        "colapsou em 120 treinos, mas o resultado não foi monotônico em $\\gamma$ e nenhum valor teve ganho confiável "
        "(Tabela D.11).")
    retirar_trecho(p(955, "A D2 (λ=0,1) foi neutra"), "Nos alvos, 126 dos 960 valores", None)
    # D.9: ajuste fino
    retirar(*figura(961, "Figura D.14"))
    # D.11: previsão a priori
    ult = retirar_trecho(p(975, "As previsões foram geradas"), "(Tabela D.13 e Figura D.16)", "(Tabela D.13 e Figura D.16)")
    run_azul(ult, "(Figura D.16 e Tabela E.3)")
    retirar(p(976, "Tabela D.13"), T[57])
    assert texto(P[977]).startswith("Fonte")
    retirar(P[977], p(981, "As relações esperadas são as seguintes"))
    retirar(*figura(983, "Figura D.17"))
    retirar_trecho(p(985, "Como referência de erro"), None, "não é intervalo de confiança. ")

    doc.save(DESTINO)
    print(f"cores vermelhas antigas removidas nos apêndices: {n_cor}")
    print(f"palavras nos apêndices A-E (v18): {palavras_apendices}; em A-D: {palavras_ad}")
    print(f"palavras marcadas para retirar: {stats['retirar']}; palavras a adicionar: {stats['adicionar']}")
    print(f"gravado: {DESTINO.name}")


def _ate(inicio, fim):
    el = inicio
    while el is not None and el is not fim:
        yield el
        el = el.getnext()


if __name__ == "__main__":
    main()
