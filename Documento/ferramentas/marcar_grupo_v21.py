"""Gera a v21: as propostas da v20 transportadas para a versão oficial do grupo.

Base: `RELATÓRIO FINAL LOP - GRUPO.docx` (exportação do Google Docs; não é alterada).
Saída: `RELATÓRIO FINAL LOP_v21.docx`, com a mesma marcação da v20:
RETIRAR em vermelho (FF0000) e tachado; ADICIONAR em azul (0070C0).

A versão do grupo difere da v18 (base da v19/v20) na Revisão, na seção do black-box de Métodos e na
numeração; os apêndices são praticamente iguais. Por isso:
- os apêndices reaproveitam as operações da v19 (o trecho do código-fonte é executado aqui, com os
  parágrafos e as tabelas da v18 mapeados para os da versão do grupo) e as da v20 (fusão em dois);
- Revisão, Métodos (black-box e serial), Resultados e Referências têm operações próprias, ancoradas
  pelo começo do texto de cada parágrafo.
Uso: python marcar_grupo_v21.py
"""

from __future__ import annotations

import difflib
import io
import re
import sys
import textwrap
from pathlib import Path

import docx
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import enxugar_apendices_v19 as v19  # noqa: E402
import enxugar_apendices_v20 as v20  # noqa: E402
from docx_utils import add_references, pintar  # noqa: E402

DOC_DIR = v19.DOC_DIR
GRUPO = DOC_DIR / "RELATÓRIO FINAL LOP - GRUPO.docx"
V18 = DOC_DIR / "RELATÓRIO FINAL LOP_v18.docx"
DESTINO = DOC_DIR / "RELATÓRIO FINAL LOP_v21.docx"
AZUL, VERMELHO = v19.AZUL, v19.VERMELHO
W_P, W_TBL, W_R = v19.W_P, v19.W_TBL, v19.W_R
texto = v19.texto

# Remissões do texto novo, trocadas pelos rótulos que a versão do grupo usa hoje
TRADUCAO = [
    ("das Equações (4.5.1.3) e (4.5.1.4)", "da Equação (4.XX.7)"),
    ("4.5.1.1", "4.XX.5"), ("4.5.1.2", "4.XX.6"), ("4.5.2.1", "4.XX.9"), ("4.5.2.2", "4.XX.10"),
    ("4.5.3.1", "4.XX.11"), ("4.5.3.2", "4.XX.15"), ("4.5.3.3", "4.XX.16"), ("4.5.4.1", "4.XX.17"),
    ("4.5.5.1", "4.XX.22"), ("Figura 4.5.4(a)", "Figura 4.XX.9(a)"), ("Seções 5.4 e 5.X", "Seções 5.2 e 5.5"),
]

REF_PSICHOGIOS = ("PSICHOGIOS, D. C.; UNGAR, L. H. A hybrid neural network-first principles approach to process "
                  "modeling. AIChE Journal, v. 38, n. 10, p. 1499–1511, 1992.")


def traduzir(txt: str) -> str:
    for a, b in TRADUCAO:
        txt = txt.replace(a, b)
    txt = re.sub(r"Seção 4\.5\.\d", "Seção 4.5", txt)
    assert not re.search(r"4\.5\.\d", txt), txt
    return txt


def sem_espaco(s: str) -> str:
    return re.sub(r"\s+", "", s)


def abrir(caminho: Path):
    with open(caminho, "rb") as f:
        return docx.Document(io.BytesIO(f.read()))


def desembrulhar(body) -> int:
    """Tira os w:sdt do Google Docs (em volta de tabelas e de marcas de comentário); o sumário fica."""
    n = 0
    for sdt in list(body.iter(qn("w:sdt"))):
        pr = sdt.find(qn("w:sdtPr"))
        if pr is not None and pr.find(qn("w:docPartObj")) is not None:
            continue
        if any(a.tag == qn("w:sdt") and a.find(qn("w:sdtPr")) is not None
               and a.find(qn("w:sdtPr")).find(qn("w:docPartObj")) is not None for a in sdt.iterancestors()):
            continue
        conteudo = sdt.find(qn("w:sdtContent"))
        for ch in (list(conteudo) if conteudo is not None else []):
            sdt.addprevious(ch)
        sdt.getparent().remove(sdt)
        n += 1
    return n


def garantir_rpr(body) -> None:
    for r in body.iter(W_R):
        if r.find(qn("w:rPr")) is None:
            r.insert(0, parse_xml(f"<w:rPr {nsdecls('w')}/>"))


def trecho_real(total: str, trecho: str | None, a_partir: int = 0) -> str | None:
    """Devolve o trecho como aparece no parágrafo, tolerando diferenças de espaços."""
    if trecho is None or total.find(trecho, a_partir) >= 0:
        return trecho
    alvo = sem_espaco(trecho)
    pos = [i for i, c in enumerate(total) if not c.isspace()]
    compacto = "".join(total[i] for i in pos)
    k = compacto.find(alvo, sum(1 for i in pos if i < a_partir))
    assert k >= 0, f"trecho não encontrado: {trecho!r} em {total[:80]!r}"
    return total[pos[k]:pos[k + len(alvo) - 1] + 1]


def retirar_trecho(p, inicio, fim):
    total = texto(p)
    ini = trecho_real(total, inicio)
    a = 0 if ini is None else total.find(ini)
    fim_real = trecho_real(total, fim, a)
    if fim is not None and fim.endswith(" ") and total[total.find(fim_real, a) + len(fim_real):][:1] == " ":
        fim_real += " "
    return v19.retirar_trecho(p, ini, fim_real)


def novo_paragrafo(depois_de, modelo, txt: str, antes: bool = False):
    p = v19.novo_paragrafo(depois_de, modelo, traduzir(txt))
    if antes:
        depois_de.addprevious(p)
    return p


def trocar(p, antigo: str, novo: str) -> None:
    """Marca `antigo` para retirada e escreve `novo`, em azul, logo depois."""
    ult = retirar_trecho(p, antigo, antigo)
    v19.run_azul(ult, novo)


def main() -> None:
    doc = abrir(GRUPO)
    body = doc.element.body
    print("sdt removidos:", desembrulhar(body))
    garantir_rpr(body)
    G = [x._p for x in doc.paragraphs]
    Gt = [texto(x).strip() for x in G]

    def g(comeco: str, depois_de=None):
        """Parágrafo da versão do grupo que começa com o texto dado (único)."""
        alvo = sem_espaco(comeco)
        i0 = G.index(depois_de) + 1 if depois_de is not None else 0
        achados = [G[i] for i in range(i0, len(G)) if sem_espaco(Gt[i]).startswith(alvo)]
        assert len(achados) == 1, f"{len(achados)} parágrafos começam com {comeco!r}"
        return achados[0]

    # ------------------------------------------------------------------ mapa v18 -> grupo
    d18 = abrir(V18)
    A = [x._p for x in d18.paragraphs]
    At = [texto(x).strip() for x in A]
    mapa: dict[int, object] = {}
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, At, Gt, autojunk=False).get_opcodes():
        if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
            for k in range(i2 - i1):
                mapa[i1 + k] = G[j1 + k]

    class Mapa:
        def __init__(self, d, nome):
            self.d, self.nome = d, nome

        def __getitem__(self, i):
            assert i in self.d, f"{self.nome}[{i}] da v18 sem correspondente na versão do grupo"
            return self.d[i]

    # tabelas: a n-ésima tabela depois do parágrafo i da v18 é a n-ésima depois do correspondente
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
    print(f"parágrafos mapeados: {len(mapa)}/{len(A)}; tabelas mapeadas: {len(mapa_t)}/{k}")
    P, T = Mapa(mapa, "P"), Mapa(mapa_t, "T")

    def p(i: int, comeco: str):
        el = mapa.get(i)
        if el is not None and sem_espaco(texto(el)).startswith(sem_espaco(comeco)):
            return el
        el = g(comeco, depois_de=ap_a)
        print(f"  [aviso] P[{i}] localizado pelo texto: {comeco!r}")
        mapa[i] = el
        return el

    def figura(i_legenda: int, comeco: str):
        assert P[i_legenda - 1].findall(".//" + qn("w:drawing")) and texto(P[i_legenda + 1]).startswith("Fonte")
        return [p(i_legenda, comeco), P[i_legenda + 1]]

    # ------------------------------------------------------------------ 0. apêndices: tirar o vermelho antigo
    ap_a = g("APÊNDICE A -")
    el, n_cor = ap_a, 0
    while el is not None:
        for c in list(el.iter(qn("w:color"))):
            if (c.get(qn("w:val")) or "").upper() == VERMELHO:
                c.getparent().remove(c)
                n_cor += 1
        el = el.getnext()
    print("cores vermelhas antigas removidas nos apêndices:", n_cor)

    # ------------------------------------------------------------------ 1. Revisão
    corpo_rev = g("As funções de ativação conferem")
    if not any(sem_espaco(t).startswith(sem_espaco("Além dessas funções")) for t in Gt):
        novo_paragrafo(corpo_rev, corpo_rev, v20.REVISAO["Além dessas funções clássicas"][0])
    else:
        print("  parágrafo das ativações (GELU, SiLU, softplus) já está na versão do grupo; mantido")
    novo_paragrafo(g("Associada à escolha da função de ativação"), corpo_rev,
        "No treinamento, os pesos são ajustados pela retropropagação do erro (Rumelhart; Hinton; Williams, 1986), "
        "com a perda calculada em mini-lotes (*mini-batches*) dos dados de treino; cada passagem completa pelo "
        "conjunto constitui uma época (Goodfellow; Bengio; Courville, 2016), e os gradientes são obtidos por "
        "diferenciação automática em bibliotecas como o PyTorch (Paszke et al., 2019). Entre os otimizadores, o Adam "
        "adapta o passo de cada parâmetro (Kingma; Ba, 2017), e a sua variação AdamW separa a penalização dos pesos "
        "da atualização pelo gradiente (Loshchilov; Hutter, 2019). É comum reduzir a taxa de aprendizado ao longo "
        "das épocas segundo uma curva cossenoidal, com passos grandes no início e pequenos no final (Loshchilov; "
        "Hutter, 2017). Como os pesos iniciais e a ordem dos lotes são sorteados, redes idênticas treinadas com "
        "sementes diferentes chegam a soluções distintas. Lakshminarayanan, Pritzel e Blundell (2017) mostraram que "
        "a média das previsões de um comitê dessas redes (*deep ensemble*) reduz o erro e que a dispersão entre os "
        "membros indica a incerteza da previsão.")
    ultimo_run = [r for r in g("Dessa maneira, com o intuito de uniformizar") if r.tag == W_R][-1]
    v19.run_azul(ultimo_run, " Para redes treinadas por gradiente, LeCun et al. (1998) recomendam entradas de média "
                             "nula e variância unitária (escore Z), que aceleram a convergência.")
    ult = g("Sob o aspecto metodológico")
    for t in v20.REVISAO["Quando há poucos dados"]:
        ult = novo_paragrafo(ult, corpo_rev, t)
    novo_paragrafo(g("A calibração do modelo serial pode ser realizada"), corpo_rev,
                   v20.REVISAO["Na abordagem sequencial"][0])

    # ------------------------------------------------------------------ 2. Métodos: black-box (MLP pura)
    titulo = g("DESENVOLVIMENTO DO MODELO HÍBRIDO E APRENDIZADO DE MÁQUINA")
    corpo_met = g("Antes de iniciar o treinamento do black box")
    v19.retirar(titulo)
    novo = novo_paragrafo(titulo, titulo, "MODELO PURAMENTE ORIENTADO A DADOS (BLACK-BOX)")
    novo_paragrafo(novo, corpo_met,
        "O modelo puramente orientado a dados, chamado neste trabalho de MLP pura ou *black-box* puro, é uma rede "
        "neural do tipo perceptron multicamadas que estima a conversão de zinco "
        "diretamente a partir dos parâmetros operacionais do ensaio, sem o balanço populacional e sem restrições "
        "físicas, e serve de linha de base para as abordagens híbridas.")
    # pré-processamento e partição
    par = g("Para que essas diferentes grandezas")
    ult = retirar_trecho(par, None, "serão abordados mais adiante. ")
    v19.run_azul(ult, "As três entradas foram padronizadas pelo escore Z (Seção 3.2.3), com a média e o "
                      "desvio-padrão calculados apenas nos pontos de treino, e o tempo foi fornecido à rede como ln t, "
                      "pois a maior parte da conversão ocorre nos primeiros minutos; por isso, o instante t = 0, em "
                      "que a conversão é nula por definição, não participa do treinamento. ")
    trocar(par, "104 pontos", "91 pontos com t > 0")
    trocar(par, "totalizando 24 pontos", "totalizando 21 pontos")
    # arquitetura
    par = g("Tanto para a construção do modelo black-box")
    v19.retirar(par)
    novo_paragrafo(par, corpo_met,
        "O modelo *black-box* é um perceptron multicamadas de alimentação direta (Seção 3.2.2), com 3 neurônios de "
        "entrada ($C_{A0}$, $\\eta$ e $\\ln t$ padronizados), três camadas ocultas de 90, 45 e 22 neurônios, as "
        "mesmas larguras da rede do modelo híbrido serial (Seção 4.5), e 1 neurônio de saída, que fornece a conversão "
        "de zinco ($X_{Zn}$), num total de 5.490 parâmetros.")
    retirar_trecho(g("Na etapa de alimentação direta, os dados recebidos"), "Sendo assim, para que o treinamento comece",
                   None)
    par = g("Por fim, na camada de saída da rede neural, escolheu-se")
    v19.retirar(g("Logo após a soma ponderada em cada camada oculta"), par)
    novo_paragrafo(par, corpo_met,
        "Nas camadas ocultas, adotou-se a função de ativação GELU (Hendrycks; Gimpel, 2016), e a camada de saída é "
        "linear, sem blocos residuais nem *dropout*. O modelo não tem, portanto, nenhuma restrição física: a "
        "conversão prevista não é obrigada a ficar entre 0 e 1, a respeitar o limite estequiométrico nem a crescer "
        "com o tempo, o que permite medir o que o aprendizado de máquina alcança sem informação do processo.")
    # treinamento
    trocar(g("Em síntese, a Equação (4.XX.X) quantifica"), "104", "91")
    retirar_trecho(g("Para realizar esse ajuste, utiliza-se o algoritmo de backpropagation"),
                   ", sigmoidal na camada de saída", "abordadas na seção anterior,")
    par = g("Por fim, com as informações do gradiente fornecidas pelo backpropagation")
    v19.retirar(par)
    novo_paragrafo(par, corpo_met,
        "Com o gradiente fornecido pelo *backpropagation*, os pesos e os vieses foram atualizados pelo otimizador "
        "AdamW (Loshchilov; Hutter, 2019), variação do Adam (Kingma; Ba, 2017), em mini-lotes de 16 pontos. Os "
        "hiperparâmetros foram escolhidos pela validação cruzada por ensaio, com as mesmas quatro dobras do modelo "
        "híbrido serial (Seção 4.5): entre 32 combinações de arquitetura, taxa de aprendizado, penalização dos pesos "
        "e número de épocas, adotou-se a de menor erro na conversão fora da dobra, com taxa de aprendizado de "
        "$10^{-2}$, penalização dos pesos de $10^{-4}$ e 900 épocas fixas, sem parada antecipada. O modelo final é a "
        "média das previsões de dez redes treinadas com essa configuração e sementes diferentes (42 a 51).")
    # a figura mostra a rede de 4 camadas de 64 neurônios (tanh, sigmoide, Adam): passa para a seção da PINN
    chamada = g("A Figura 4.XX.X ilustra esquematicamente a arquitetura da rede MLP")
    legenda = g("Figura 4.XX.X – Representação esquemática da arquitetura da rede neural MLP")
    fonte = legenda.getnext()
    assert texto(fonte).startswith("Fonte")
    v19.retirar(chamada, legenda, fonte)
    retirar_trecho(g("Após o encerramento das 3.000 épocas"), "encerramento das 3.000 épocas de ",
                   "encerramento das 3.000 épocas de ")
    # PINN: a descrição da rede que estava na seção do black-box
    novo_paragrafo(g("MODELAGEM HÍBRIDA: REDES NEURAIS INFORMADAS PELA FÍSICA"), corpo_met,
        "A PINN utiliza uma rede própria, também do tipo MLP de alimentação direta, com 3 neurônios de entrada "
        "($t$, $C_{A0}$ e $\\eta$, convertidos para o intervalo de −1 a 1 pela normalização Min-Max; Jayalakshmi; "
        "Santhakumaran, 2011), quatro camadas ocultas com 64 neurônios cada e 1 neurônio de saída. Antes do "
        "treinamento, os vieses são inicializados em zero e os pesos são sorteados pela inicialização de Xavier "
        "(Datta, 2020). Nas camadas ocultas, adotou-se a tangente hiperbólica (tanh), contínua e diferenciável em "
        "todos os pontos, requisito para que a saída da rede seja derivada em relação ao tempo por diferenciação "
        "automática (Raissi et al., 2019); na camada de saída, a função sigmoide restringe o valor ao intervalo "
        "(0, 1). A Figura 4.XX.X ilustra essa arquitetura e o ciclo de treinamento, cujo mecanismo é o descrito na "
        "Seção 4.2.3.")
    retirar_trecho(g("Por fim, em adição ao algoritmo Adam"), " utilizado no treinamento do modelo black-box",
                   " utilizado no treinamento do modelo black-box")

    # ------------------------------------------------------------------ 3. Métodos: serial (cortes da v20)
    par = g("As entradas têm escalas muito diferentes")
    v19.retirar(par)
    novo_paragrafo(par, par, "As entradas foram padronizadas pelo escore Z (Seção 3.2.3):")
    retirar_trecho(g("A escolha da configuração da rede e a decisão"), "Com quatro dobras, cada validação dispõe",
                   "disponíveis para o ajuste. ")
    retirar_trecho(g("As camadas ocultas são três blocos residuais"), "Cada bloco soma uma projeção linear",
                   "redes com várias camadas. ")

    # ------------------------------------------------------------------ 4. Resultados: remissão do black-box
    trocar(g("Esta seção apresenta os resultados do modelo puramente orientado a dados"), "Seções 4.1.4 a 4.1.7",
           "Seção 4.2")

    # ------------------------------------------------------------------ 5. Apêndices: operações da v19
    corpo_ap = P[721]
    fonte_v19 = Path(v19.__file__).read_text(encoding="utf-8")
    a = fonte_v19.index("    # ------------------------------------------------------------------ 3. Apêndice A")
    b = fonte_v19.index("    doc.save(DESTINO)")
    exec(compile(textwrap.dedent(fonte_v19[a:b]), "v19:apendices", "exec"),
         {"p": p, "P": P, "T": T, "figura": figura, "retirar": v19.retirar, "retirar_trecho": retirar_trecho,
          "novo_paragrafo": novo_paragrafo, "run_azul": v19.run_azul, "corpo_ap": corpo_ap, "texto": texto})

    # ------------------------------------------------------------------ 6. Apêndices: cinco viram dois (v20)
    v19.retirar(ap_a)
    novo_paragrafo(ap_a, ap_a, "APÊNDICE A - DETALHAMENTO DO MODELO HÍBRIDO SERIAL")
    v19.retirar(p(721, "Este apêndice detalha a obtenção"))
    novo_paragrafo(P[721], corpo_ap,
        "Este apêndice detalha as etapas de desenvolvimento do modelo híbrido serial resumidas na Seção 4.5: o "
        "problema inverso, a base de dados, a rede neural e a seleção da configuração.")
    d5 = p(894, "D.5")
    novo_paragrafo(d5, ap_a, "APÊNDICE B - RESULTADOS COMPLEMENTARES DOS MODELOS HÍBRIDO SERIAL E BLACK-BOX", antes=True)
    novo_paragrafo(d5, corpo_ap,
        "Este apêndice reúne os resultados da seleção da configuração do modelo híbrido serial, das variantes "
        "testadas e da previsão dos ensaios novos (Seções B.1 a B.4) e os resultados completos dos modelos híbrido "
        "serial e *black-box*, resumidos nas Seções 5.4 e 5.X (Seções B.5 a B.8): as curvas, as métricas e a "
        "conversão de zinco medida e prevista em cada instante, nos 16 ensaios de Bortot Coelho (2017) e nos quatro "
        "ensaios novos. Nas Seções B.5 a B.8, os erros estão em pontos percentuais (p.p.) de conversão.", antes=True)
    for i, comeco, novo_titulo in v20.TITULOS:
        old = p(i, comeco)
        v19.retirar(old)
        if novo_titulo:
            novo_paragrafo(old, old, novo_titulo)
    for i, comeco in v20.INTRODUCOES_ANTIGAS:
        v19.retirar(p(i, comeco))

    # ------------------------------------------------------------------ 7. Referências novas, em azul
    novas = add_references(doc, v20.REFERENCIAS + [REF_PSICHOGIOS])
    for par in doc.paragraphs:
        if par.text.strip() in novas:
            pintar([par._p], AZUL)
    v19.stats["adicionar"] += sum(len(x.split()) for x in novas)
    print("referências novas:", len(novas))

    doc.save(DESTINO)
    print(f"palavras marcadas para retirar: {v19.stats['retirar']}; palavras a adicionar: {v19.stats['adicionar']}")
    print(f"gravado: {DESTINO.name}")


if __name__ == "__main__":
    main()
