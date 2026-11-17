"""Gera a v20 a partir da v18 (sem alterá-la): tudo o que a v19 propunha e mais três pedidos de 12/11/2026 (tarde).

1. Revisão mais completa: os conceitos usados na metodologia são citados com a fonte, sem explicação longa;
2. Cinco apêndices viram dois. Aqui só os títulos mudam; a renumeração de figuras, tabelas, equações e remissões
   fica para a versão limpa, depois de o usuário aprovar a estrutura;
3. Mais alguns cortes na Seção 4.5, apoiados na revisão.

As operações da v19 são reaproveitadas (o módulo `enxugar_apendices_v19` é executado com outro destino e com os
parágrafos da revisão substituídos), e as novas entram antes de salvar.
Marcação: RETIRAR em vermelho (FF0000) e tachado; ADICIONAR em azul (0070C0).
Uso: python enxugar_apendices_v20.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import enxugar_apendices_v19 as v19  # noqa: E402
from docx_utils import add_references, pintar  # noqa: E402

DESTINO = v19.DOC_DIR / "RELATÓRIO FINAL LOP_v20.docx"
AZUL = v19.AZUL
W_R = v19.W_R

# Parágrafos da revisão que substituem os da v19 (chave = começo do texto da v19)
REVISAO = {
    "Além dessas funções clássicas": [
        "Além dessas funções clássicas, redes voltadas à regressão têm empregado ativações suaves, como a GELU "
        "(*Gaussian Error Linear Unit*; Hendrycks; Gimpel, 2016) e a SiLU (*Sigmoid Linear Unit*; Elfwing; Uchibe; "
        "Doya, 2018), que se comportam como a ReLU longe da origem, mas são diferenciáveis em todos os pontos. Na "
        "camada de saída, a função *softplus*, $\\ln(1+e^{z})$, é adotada quando a grandeza prevista deve ser "
        "positiva (Goodfellow; Bengio; Courville, 2016), o que permite impor uma restrição física pela própria "
        "arquitetura da rede, e não por penalização na função de perda. Para facilitar o treinamento de redes com "
        "várias camadas, He et al. (2016) propuseram as conexões residuais, em que cada bloco soma à sua saída uma "
        "cópia ou uma projeção linear da própria entrada, e Ba, Kiros e Hinton (2016), a normalização de camada, que "
        "padroniza as ativações de cada camada. Já o *dropout* anula aleatoriamente uma fração dos neurônios a cada "
        "passo do treinamento, o que reduz o sobreajuste (Srivastava et al., 2014).",
    ],
    "Na prática, a perda é calculada": [
        "Na prática, a perda é calculada em mini-lotes (*mini-batches*) dos dados de treino, e cada passagem completa "
        "pelo conjunto constitui uma época (Goodfellow; Bengio; Courville, 2016), com os gradientes obtidos por "
        "diferenciação automática em bibliotecas como o PyTorch (Paszke et al., 2019). Entre as variações do Adam, o "
        "AdamW separa a penalização dos pesos da atualização pelo gradiente (Loshchilov; Hutter, 2019), e é comum "
        "reduzir a taxa de aprendizado ao longo das épocas segundo uma curva cossenoidal, com passos grandes no início "
        "e pequenos no final (Loshchilov; Hutter, 2017). Como os pesos iniciais e a ordem dos lotes são sorteados, "
        "redes idênticas treinadas com sementes diferentes chegam a soluções distintas. Lakshminarayanan, Pritzel e "
        "Blundell (2017) mostraram que a média das previsões de um comitê dessas redes (*deep ensemble*) reduz o erro "
        "e que a dispersão entre os membros indica a incerteza da previsão.",
    ],
    "Quando há poucos dados": [
        "Os valores que definem a rede e o seu treinamento, como o número de camadas e de neurônios, a taxa de "
        "aprendizado e o número de épocas, não são ajustados pelo gradiente e são chamados de hiperparâmetros. Quando "
        "há poucos dados, a sua escolha se apoia na validação cruzada em $k$ dobras: o conjunto de treino é dividido "
        "em $k$ partes, cada uma é usada uma vez como validação de um modelo ajustado com as demais, e o erro médio "
        "das $k$ rodadas estima a capacidade de generalização (Hastie; Tibshirani; Friedman, 2009). Se as observações "
        "formam grupos dependentes entre si, como os pontos de uma mesma curva cinética, as dobras devem ser formadas "
        "por grupos inteiros (Roberts et al., 2017), procedimento disponível na biblioteca scikit-learn (Pedregosa et "
        "al., 2011), sob pena de vazamento de informação (Kapoor; Narayanan, 2023).",
        "A busca dos hiperparâmetros pode ser feita em grade, por sorteio aleatório, mais eficiente quando poucos "
        "deles são de fato importantes (Bergstra; Bengio, 2012), ou guiada por modelo, como no algoritmo TPE "
        "(*Tree-structured Parzen Estimator*), que utiliza as configurações já avaliadas para propor as seguintes "
        "(Bergstra et al., 2011). O algoritmo está implementado na biblioteca Optuna, que também interrompe "
        "antecipadamente as tentativas pouco promissoras (Akiba et al., 2019). Como a melhor entre muitas "
        "configurações tende a ter sido favorecida também pelo acaso, a sua nota é otimista e deve ser reestimada "
        "(Cawley; Talbot, 2010). Para a escolha final, Hastie, Tibshirani e Friedman (2009) recomendam a regra de um "
        "erro-padrão, que adota o modelo mais simples entre aqueles cujo erro não supera o do melhor em mais de um "
        "erro-padrão, e a diferença entre duas configurações avaliadas nas mesmas condições pode ser verificada por "
        "testes pareados, como o teste $t$ e o de postos sinalizados (Wilcoxon, 1945).",
    ],
    "Na abordagem sequencial": [
        "Na abordagem sequencial, a identificação da grandeza não medida a partir dos dados constitui um problema "
        "inverso, em geral mal-posto, pois várias soluções reproduzem as mesmas observações. A solução é estabilizada "
        "restringindo-se a forma da função procurada e acrescentando-se termos de regularização à função objetivo "
        "(Aster; Borchers; Thurber, 2018), e os parâmetros são obtidos por métodos de otimização que admitem limites, "
        "como o L-BFGS-B (Byrd et al., 1995). Já a abordagem simultânea foi introduzida por Psichogios e Ungar (1992), "
        "que treinaram a rede neural através do próprio modelo de primeiros princípios.",
    ],
}

REFERENCIAS = [
    "BA, J. L.; KIROS, J. R.; HINTON, G. E. Layer normalization. arXiv, 1607.06450, 2016. Disponível em: "
    "https://arxiv.org/abs/1607.06450. Acesso em: 12 nov. 2026.",
    "BERGSTRA, J.; BENGIO, Y. Random search for hyper-parameter optimization. Journal of Machine Learning "
    "Research, v. 13, p. 281-305, 2012.",
    "ELFWING, S.; UCHIBE, E.; DOYA, K. Sigmoid-weighted linear units for neural network function approximation "
    "in reinforcement learning. Neural Networks, v. 107, p. 3-11, 2018.",
    "PEDREGOSA, F. et al. Scikit-learn: machine learning in Python. Journal of Machine Learning Research, v. 12, "
    "p. 2825-2830, 2011.",
    "ROBERTS, D. R. et al. Cross-validation strategies for data with temporal, spatial, hierarchical, or "
    "phylogenetic structure. Ecography, v. 40, n. 8, p. 913-929, 2017.",
]

# (índice na v18, começo do título antigo, título novo ou None para apenas retirar)
TITULOS = [
    (724, "A.1", "A.1 Problema inverso: parametrização, função objetivo e otimização"),
    (730, "A.2", None), (736, "A.3", None), (748, "A.4", None),
    (758, "A.5", "A.2 Reconstrução das curvas de conversão"),
    (772, "APÊNDICE B", None),
    (774, "B.1", "A.3 Base de dados e partição dos ensaios"),
    (784, "B.2", None), (794, "B.3", None),
    (801, "B.4", "A.4 Transformação das variáveis"),
    (813, "APÊNDICE C", None),
    (815, "C.1", "A.5 Arquitetura e treinamento da rede neural"),
    (835, "C.2", None),
    (847, "C.3", "A.6 Treinamento do comitê"),
    (851, "APÊNDICE D", None),
    (853, "D.1", "A.7 Critério de avaliação e busca de hiperparâmetros"),
    (866, "D.2", None),
    (879, "D.3", "A.8 Modelo final e avaliação"),
    (888, "D.4", None),
    (894, "D.5", "B.1 Seleção da configuração da rede"),
    (902, "D.6", None),
    (926, "D.7", "B.2 Desempenho do modelo final no teste cego"),
    (940, "D.8", "B.3 Variantes testadas depois da seleção"),
    (956, "D.9", None), (967, "D.10", None),
    (971, "D.11", "B.4 Previsão a priori de quatro ensaios novos de laboratório"),
    (986, "APÊNDICE E", None),
    (988, "E.1", "B.5 Modelo híbrido serial: ensaios do planejamento original"),
    (997, "E.2", "B.6 Modelo híbrido serial: ensaios novos"),
    (1004, "E.3", "B.7 Modelo black-box: ensaios do planejamento original"),
    (1013, "E.4", "B.8 Modelo black-box: ensaios novos"),
]
INTRODUCOES_ANTIGAS = [(773, "Este apêndice detalha a construção"), (814, "Este apêndice detalha a arquitetura"),
                       (852, "Este apêndice detalha o critério"), (987, "Este apêndice reúne os resultados completos")]


def main() -> None:
    estado: dict = {}
    novo_paragrafo_v19 = v19.novo_paragrafo
    usados = set()

    def novo_paragrafo(depois_de, modelo, txt: str, antes: bool = False):
        """Como o da v19, mas troca os parágrafos da revisão pelos desta versão e aceita inserir antes."""
        chave = next((k for k in REVISAO if txt.startswith(k)), None)
        textos = [txt]
        if chave and chave not in usados:
            usados.add(chave)
            textos = REVISAO[chave]
        ultimo = depois_de
        for t in textos:
            if antes:
                p = novo_paragrafo_v19(depois_de, modelo, t)
                depois_de.addprevious(p)
            else:
                p = novo_paragrafo_v19(ultimo, modelo, t)
                ultimo = p
        return p

    class _Doc:
        """Intercepta o save da v19 para aplicar as operações novas antes de gravar."""

    doc_save = v19.docx.document.Document.save

    def salvar(self, destino):
        extras(self)
        doc_save(self, DESTINO)

    def extras(doc) -> None:
        P, T = estado["P"], estado["T"]

        def p(i: int, comeco: str):
            assert v19.texto(P[i]).strip().startswith(comeco), f"[{i}] esperado {comeco!r}, achei {v19.texto(P[i])[:60]!r}"
            return P[i]

        corpo_ap = P[721]
        # revisão: frase sobre a padronização
        ultimo = [r for r in p(235, "Dessa maneira, com o intuito de uniformizar") if r.tag == W_R][-1]
        v19.run_azul(ultimo, " Para redes treinadas por gradiente, LeCun et al. (1998) recomendam entradas de média nula "
                             "e variância unitária, que aceleram a convergência.")
        # Seção 4.5: cortes apoiados na revisão
        v19.retirar(p(545, "As entradas têm escalas muito diferentes"))
        novo_paragrafo(P[545], P[545], "As entradas foram padronizadas pelo escore Z (Seção 3.2.3):")
        v19.retirar_trecho(p(541, "A escolha da configuração da rede"), "Com quatro dobras, cada validação dispõe",
                           "disponíveis para o ajuste. ")
        v19.retirar_trecho(p(556, "As camadas ocultas são três blocos residuais"), "Cada bloco soma uma projeção linear",
                           "redes com várias camadas. ")
        # cinco apêndices -> dois
        a = p(720, "APÊNDICE A")
        v19.retirar(a)
        novo_paragrafo(a, a, "APÊNDICE A - DETALHAMENTO DO MODELO HÍBRIDO SERIAL")
        v19.retirar(p(721, "Este apêndice detalha a obtenção"))
        novo_paragrafo(P[721], corpo_ap,
            "Este apêndice detalha as etapas de desenvolvimento do modelo híbrido serial resumidas na Seção 4.5: o "
            "problema inverso, a base de dados, a rede neural e a seleção da configuração.")
        d5 = p(894, "D.5")
        novo_paragrafo(d5, a, "APÊNDICE B - RESULTADOS COMPLEMENTARES DOS MODELOS HÍBRIDO SERIAL E BLACK-BOX", antes=True)
        novo_paragrafo(d5, corpo_ap,
            "Este apêndice reúne os resultados da seleção da configuração do modelo híbrido serial, das variantes "
            "testadas e da previsão dos ensaios novos (Seções B.1 a B.4) e os resultados completos dos modelos híbrido "
            "serial e *black-box*, resumidos nas Seções 5.4 e 5.X (Seções B.5 a B.8): as curvas, as métricas e a "
            "conversão de zinco medida e prevista em cada instante, nos 16 ensaios de Bortot Coelho (2017) e nos quatro "
            "ensaios novos. Nas Seções B.5 a B.8, os erros estão em pontos percentuais (p.p.) de conversão.", antes=True)
        for i, comeco, novo in TITULOS:
            old = p(i, comeco)
            v19.retirar(old)
            if novo:
                novo_paragrafo(old, old, novo)
        for i, comeco in INTRODUCOES_ANTIGAS:
            v19.retirar(p(i, comeco))
        # referências novas, em azul
        novas = add_references(doc, REFERENCIAS)
        for par in doc.paragraphs:
            if par.text.strip() in novas:
                pintar([par._p], AZUL)
        v19.stats["adicionar"] += sum(len(x.split()) for x in novas)
        print("referências novas:", len(novas))

    # captura P e T no momento em que a v19 os monta (antes de qualquer alteração)
    docx_Document = v19.docx.Document

    def abrir(arg):
        doc = docx_Document(arg)
        estado["P"] = [x._p for x in doc.paragraphs]
        estado["T"] = [x._tbl for x in doc.tables]
        return doc

    v19.novo_paragrafo = novo_paragrafo
    v19.docx.Document = abrir
    v19.docx.document.Document.save = salvar
    try:
        v19.main()
    finally:
        v19.novo_paragrafo = novo_paragrafo_v19
        v19.docx.Document = docx_Document
        v19.docx.document.Document.save = doc_save
    assert usados == set(REVISAO), f"parágrafos da revisão não substituídos: {set(REVISAO) - usados}"
    print(f"gravado de fato: {DESTINO.name}")


if __name__ == "__main__":
    main()
