"""Gera a v7 do relatório: Metodologia do híbrido serial enxuta e explicação completa em apêndices.

Parte do documento enviado ao orientador em 29/10 (RELATÓRIO PARCIAL-fab.docx, com as edições do
usuário), que não é alterado, e produz RELATÓRIO FINAL LOP_v7.docx.

Na seção "MODELAGEM HÍBRIDA SERIAL" (dentro de Métodos, cor normal):
- mantêm-se a abertura, os elementos do modelo fenomenológico e o acoplamento, que já eram curtos;
- as demais subseções são substituídas por versões condensadas, que conservam as equações e as
  figuras principais e remetem aos apêndices;
- acrescenta-se um parágrafo que responde ao comentário do orientador sobre o passo 1 usar só os 13
  ensaios de treino.

Em apêndices novos, fora de Métodos (texto em vermelho):
- B: problema inverso; C: base de dados e partição; D: arquitetura e treinamento; E: critério de
  avaliação, busca de hiperparâmetros, comitê de redes e métricas.
- Os parágrafos, equações, figuras e tabelas originais (já com as edições do usuário) são movidos
  para os apêndices sem alteração de conteúdo; só os marcadores de numeração e as referências
  cruzadas são ajustados (Figura B.1, Tabela C.3, Equação D.7 etc.).
- Equações que aparecem na Metodologia são copiadas, e não movidas, para que cada apêndice seja
  legível por si só.
- As subseções E.2 a E.4 (busca, comitê e avaliação) vêm do texto de escrever_hibrido_serial.py,
  que o usuário havia retirado do documento enviado ao orientador.
- O Apêndice B ganha uma verificação a posteriori dos pesos de penalização (resposta ao comentário
  "explicar melhor o processo empírico").

Uso: python reorganizar_apendices_hibrido_serial.py [--saida CAMINHO.docx]
"""

from __future__ import annotations

import ast
import copy
import re
import sys
from pathlib import Path

import docx
import pandas as pd
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

sys.path.insert(0, str(Path(__file__).parent))
from docx_utils import SectionWriter, pintar  # noqa: E402

RAIZ = Path(r"C:\us trem\Doc\UFMG\9\Lop")
ORIGEM = RAIZ / "RELATÓRIO PARCIAL-fab.docx"
DOC_DIR = RAIZ / "Codigo_v4" / "Documento"
DESTINO = DOC_DIR / "RELATÓRIO FINAL LOP_v7.docx"
FIG_DIR = DOC_DIR / "figuras_metodologia"
SCRIPT_LONGO = Path(__file__).parent / "escrever_hibrido_serial.py"
CSV_PENAL = RAIZ / "Codigo_v4" / "Código" / "outputs" / "etapa_2_1" / "tabela_contribuicao_penalidades.csv"

M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
W14 = "{http://schemas.microsoft.com/office/word/2010/wordml}"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

# Índices dos elementos do corpo do documento de origem (conferidos por texto em verificar_origem)
I_INI, I_FIM = 519, 695  # [519, 695): da seção até antes dos parágrafos vazios que a seguem

# --------------------------------------------------------------------------- numeração nos apêndices
FIG_APENDICE = {6: "B.1", 7: "B.2", 8: "C.1", 10: "C.2", 12: "D.1", 13: "D.2", 14: "E.1"}
TAB_APENDICE = {1: "B.2", 2: "B.3", 3: "C.1", 4: "C.2", 5: "C.3", 6: "C.4"}
EQ_APENDICE = {5: "B.1", 6: "B.2", 7: "B.3", 8: "B.4", 9: "C.1", 10: "C.2", 11: "D.1", 12: "D.2", 13: "D.3",
               14: "D.4", 15: "D.5", 16: "D.6", 17: "D.7", 21: "D.8", 22: "E.1", 23: "E.2"}
# O que fica na Metodologia mantém a numeração 4.XX.n; só as equações que existem apenas nos apêndices mudam
EQ_METODOLOGIA = {12: "D.2", 13: "D.3", 14: "D.4", 21: "D.8", 23: "E.2"}

TABELAS_EQUACAO = {545, 551, 558, 607, 615, 626, 631, 636, 640, 642, 651, 658, 673, 677, 691}

# Elementos que aparecem na Metodologia e no apêndice correspondente (cópia na Metodologia)
COPIAS = {545, 551, 558, 607, 615, 626, 640, 642, 651, 652, 673, 674}

# Referências cruzadas a seções que deixaram de existir na Metodologia (índice do parágrafo -> trocas)
TROCAS_TEXTO = {
    584: [("(Seção 4.XX)", "(Seção E.4)")],
    596: [("(Seção 4.XX)", "(Seção E.2)")],
    629: [("(Seção 4.XX)", "(Seção E.2)")],
    634: [("(Seção 4.XX)", "(Seção E.2)")],
    662: [("(Seção 4.XX)", "(Seção E.3)")],
    668: [("nas Tabelas 4.XX.7 e 4.XX.8", "na Tabela 4.XX.8 e na Figura 4.XX.11")],
    676: [("(Seção 4.XX)", "(Apêndice D)")],
}

# --------------------------------------------------------------------------- Metodologia (texto novo)
T_RESSALVA = (
    r"O problema inverso (etapa 1) foi resolvido separadamente para cada um dos 16 ensaios, utilizando "
    r"apenas as conversões medidas no próprio ensaio e, por isso, a sua solução para os três ensaios de teste "
    r"cego não transfere informação para o treinamento. As taxas desses três ensaios foram usadas somente "
    r"para verificar a taxa prevista pela rede, e a conversão prevista foi sempre comparada com a conversão "
    r"medida."
)

T_INV1 = (
    r"Para treinar a rede neural, é necessário dispor de pares formados pelas variáveis de entrada "
    r"($C_{A0}$, $\eta$ e $t$) e pelo valor correspondente da taxa de retração $\nu$. Como os ensaios de "
    r"Bortot Coelho (2017) fornecem apenas a conversão de zinco, medida em sete instantes (0,5; 1; 2; 3; 4; 5 "
    r"e 15 min), a curva $\nu(t)$ de cada um dos 16 ensaios foi estimada por um problema inverso (Aster; "
    r"Borchers; Thurber, 2018), isto é, buscou-se a curva que, inserida no balanço populacional (Seção "
    r"4.2.2), reproduz a conversão medida. Como infinitas curvas reproduzem sete pontos, a taxa foi restrita "
    r"a uma forma paramétrica e o ajuste foi regularizado por termos de penalização, conforme resumido na "
    r"Figura 4.XX.5 e detalhado no Apêndice B."
)
T_INV2 = r"A taxa de retração de cada ensaio foi representada pela soma de dois decaimentos exponenciais e de uma constante:"
T_INV3 = (
    r"Em que $\theta=(a_1,b_1,a_2,b_2,c)$ é o vetor de parâmetros do ensaio. A forma acompanha o "
    r"comportamento das curvas de conversão, com uma etapa inicial rápida, associada à dissolução das "
    r"partículas finas, e uma etapa lenta de aproximação ao patamar e, como todos os parâmetros são não "
    r"negativos, a taxa é positiva e decrescente."
)
T_INV4 = (
    r"Para cada vetor de parâmetros, a retração acumulada foi calculada em uma malha regular de 0,25 a 15 min, "
    r"com passo $\Delta t=0{,}25$ min (60 nós), que contém todos os instantes experimentais, partindo de "
    r"$\delta(0)=0$, com o primeiro intervalo integrado a taxa constante e os demais pela regra do trapézio:"
)
T_INV5 = (
    r"Com $\delta_1=\nu(t_1)\,t_1$ e $k=2,\dots,60$. A conversão em cada nó foi lida da curva "
    r"$X_{\mathrm{Zn}}(\delta)$ pré-calculada (Figura 4.X.4), procedimento idêntico ao do acoplamento com a "
    r"rede, de modo que a taxa estimada nesta etapa e a prevista pela rede são convertidas em conversão da "
    r"mesma forma. O instante $t=0$, em que $X_{\mathrm{Zn}}(0)=0$, $\delta(0)=0$ e $C_A(0)=C_{A0}$ por "
    r"definição, foi imposto como condição inicial e excluído do ajuste e das métricas, pois não traz "
    r"informação sobre a cinética e inflaria artificialmente os indicadores de desempenho."
)
T_INV6 = r"Os parâmetros de cada ensaio foram determinados pela minimização da função objetivo:"
T_INV7 = (
    r"O primeiro termo da Equação (4.XX.7) é a soma dos quadrados dos desvios entre a conversão medida e a "
    r"calculada nos sete instantes do ensaio, e os termos de $J_{\mathrm{reg}}$ são penalizações que conduzem "
    r"o ajuste a soluções fisicamente plausíveis onde os dados não determinam a curva: taxa elevada ao final "
    r"do ensaio ($\lambda_1$), retração acumulada acima de $\delta_{\mathrm{lim}}=140$ µm ($\lambda_2$) e "
    r"picos de $\nu$ antes da primeira medição ($\lambda_3$ e $\lambda_4$). Os pesos foram escolhidos por "
    r"tentativa e erro, adotando-se os valores que apresentaram os melhores resultados: "
    r"$\lambda_1=\lambda_2=10^{-4}$, $\lambda_3=10^{-7}$ e $\lambda_4=10^{-6}$. A contribuição de cada termo "
    r"ao resultado é discutida no Apêndice B."
)
T_INV8 = (
    r"A minimização foi feita com o algoritmo L-BFGS-B (Byrd et al., 1995), que admite limites para cada "
    r"parâmetro, a partir de seis estimativas iniciais, para reduzir o risco de mínimos locais, adotando-se a "
    r"solução de menor $J(\theta)$ (limites e estimativas no Apêndice B)."
)
T_INV9 = (
    r"Com os parâmetros ótimos, calcularam-se $\nu$, $\delta$ e $X_{\mathrm{Zn}}$ em duas bases: a primeira, "
    r"com os sete instantes experimentais de cada ensaio (112 registros), foi usada para verificar a "
    r"reconstrução das curvas, e a segunda, com os 60 nós da malha regular (960 registros), foi usada no "
    r"treinamento da rede. Os valores da malha regular não são medições adicionais, mas resultam da curva "
    r"ajustada, de modo que a informação experimental continua restrita aos sete pontos medidos. A qualidade "
    r"da reconstrução é apresentada na Seção 5.XX."
)

T_BD1 = (
    r"Os valores de $\nu(t)$ do problema inverso foram organizados em uma base de dados na qual cada registro "
    r"corresponde a um instante de um ensaio. Como entradas da rede, foram utilizadas a concentração inicial "
    r"de ácido ($C_{A0}$), a razão molar estequiométrica ($\eta$) e o tempo ($t$), e a saída é a taxa de "
    r"retração, $\nu=f(C_{A0},\eta,t)$, uma função direta das três entradas, já que o acúmulo da retração é "
    r"calculado fora da rede, pela integração da Equação (4.XX.6). A temperatura (40 °C) e a velocidade de "
    r"agitação (1000 rpm) não foram incluídas, pois foram mantidas constantes em todos os ensaios. A base com "
    r"960 registros (60 por ensaio) foi usada no treinamento, enquanto a avaliação final do modelo híbrido é "
    r"feita apenas nos instantes com medição experimental, porque os valores da malha resultam da curva "
    r"ajustada, e não do experimento."
)
T_BD2 = (
    r"Os 16 ensaios foram divididos em 13 para treino (81,25%) e 3 para teste cego (Ensaios 7, 8 e 14). A "
    r"divisão foi feita por ensaios inteiros, e não por registros, pois os registros de um mesmo ensaio "
    r"compartilham as condições operacionais e, separados por apenas 0,25 min, têm valores de $\nu$ muito "
    r"próximos. Com registros sorteados, quase todo ponto de teste teria um vizinho quase idêntico no treino, "
    r"e o resultado não mediria a capacidade de prever condições novas. A proporção buscou equilibrar o "
    r"aproveitamento dos dados, já que cada ensaio retirado do treino reduz em cerca de 6% a informação "
    r"disponível, e um teste que não dependa de uma única condição. Os ensaios de teste não participaram do "
    r"ajuste dos pesos, da escolha da configuração nem do cálculo da padronização, e foram consultados uma "
    r"única vez (Goodfellow; Bengio; Courville, 2016)."
)
T_BD2B = (
    r"A escolha desses três ensaios seguiu três critérios (Figura 4.XX.9(a)): (i) os quatro vértices do "
    r"planejamento foram mantidos no treino, de modo que o teste seja uma interpolação e não uma "
    r"extrapolação (Sansana et al., 2024); (ii) os ensaios cobrem três situações de disponibilidade de ácido, "
    r"com $\eta=1{,}0$ (Ensaio 8), $\eta=1{,}5$ (Ensaio 14) e $\eta=3{,}1$ (Ensaio 7); e (iii) os quatro "
    r"ensaios com $\eta=0{,}5$, nos quais a reação cessa pelo esgotamento do ácido, foram mantidos no treino. "
    r"Os mesmos três ensaios foram adotados como teste no modelo puramente orientado por dados e na PINN, de "
    r"modo que as abordagens sejam comparadas nas mesmas condições."
)
T_BD3 = (
    r"A escolha da configuração da rede e a decisão de quando interromper o treinamento não podem se basear "
    r"no teste, que deixaria de ser independente (Hastie; Tibshirani; Friedman, 2009). Por isso, foi "
    r"utilizada a validação cruzada em quatro dobras dentro do conjunto de treino, também formadas por "
    r"ensaios inteiros (*GroupKFold*), cada uma reservando três ou quatro ensaios para validação (Figura "
    r"4.XX.9(b)). Com quatro dobras, cada validação dispõe de ensaios suficientes para não depender de "
    r"condições particulares, sem reduzir demais os ensaios disponíveis para o ajuste. A composição das "
    r"dobras é apresentada na Tabela C.3 (Apêndice C)."
)
T_BD4A = (
    r"As entradas têm escalas muito diferentes e, em redes treinadas por gradiente, isso torna o "
    r"treinamento mais lento e instável (LeCun et al., 1998). Por isso, foram padronizadas pelo escore Z:"
)
T_BD4B = (
    r"Em que $\mu_j$ e $\sigma_j$ são a média e o desvio-padrão da variável $j$ nos registros de treino "
    r"(Tabela C.4), aplicados sem recálculo aos ensaios de teste."
)
T_BD5A = (
    r"A saída exigiu um tratamento diferente. A distribuição de $\nu$ nos registros de treino é fortemente "
    r"assimétrica, pois os valores variam de 0 a cerca de 94 µm/min, mas 64% dos registros estão abaixo de "
    r"0,1 µm/min. Com o erro quadrático médio como função de perda, os poucos registros de taxa elevada "
    r"dominariam o ajuste e a rede negligenciaria a etapa lenta, que define a aproximação ao patamar de "
    r"conversão. Para equilibrar a contribuição das duas etapas, a saída foi transformada por:"
)
T_BD5B = (
    r"Com isso, a faixa da saída foi comprimida de 0–94 µm/min para 0–4,55 (Apêndice C). A rede é treinada "
    r"para prever $y$, e a taxa é recuperada por $\nu=e^{y}-1$, aplicada na própria camada de saída."
)

T_AR1 = (
    r"A relação entre as condições do ensaio e a taxa de retração, $\nu=f(C_{A0},\eta,t)$, foi aproximada por "
    r"uma rede neural do tipo perceptron multicamadas (*multilayer perceptron*, MLP), que prevê apenas a "
    r"taxa de retração em cada instante, depois integrada e convertida em conversão pelo modelo "
    r"fenomenológico. A Figura 4.XX.11 apresenta a arquitetura adotada."
)
T_AR2A = (
    r"A rede recebe as três entradas padronizadas pela Equação 4.XX.9 mas, antes da primeira camada, o tempo é "
    r"convertido de volta em minutos e substituído pelo seu logaritmo, novamente padronizado:"
)
T_AR2B = (
    r"Em que $\mu_{\ln t}$ e $\sigma_{\ln t}$ são a média e o desvio-padrão de $\ln t$ nos 60 nós da malha "
    r"temporal. Como $\nu$ cai várias ordens de grandeza nos primeiros minutos de cada ensaio, a escala "
    r"logarítmica dá à rede mais resolução nesse trecho: o intervalo de 0,25 a 2 min, em que ocorre a maior "
    r"parte da conversão, ocupa 12% da faixa do tempo na escala linear e cerca de 51% na logarítmica."
)
T_AR3A = (
    r"As camadas ocultas são três blocos residuais (He et al., 2016), com 90, 45 e 22 neurônios, função de "
    r"ativação GELU (*Gaussian Error Linear Unit*; Hendrycks; Gimpel, 2016) e *dropout* no ramo não linear de "
    r"cada bloco (Srivastava et al., 2014). Cada bloco soma uma projeção linear da sua entrada, o atalho, a "
    r"uma correção não linear, o que facilita o treinamento de redes com várias camadas. Por fim, a camada de "
    r"saída combina linearmente os 22 valores do último bloco em um número $z$, transformado pela função "
    r"softplus:"
)
T_AR3B = (
    r"Em que $\hat{y}$ é a previsão da rede para a variável transformada $y$ da Equação 4.XX.10. A taxa de "
    r"retração é recuperada por:"
)
T_AR4 = (
    r"Como a função softplus só assume valores positivos, tem-se $\hat{y}\geq 0$ e $\hat{\nu}\geq 0$ para "
    r"qualquer combinação de entradas, inclusive em condições fora das ensaiadas, o que impede taxas "
    r"negativas, que corresponderiam ao crescimento das partículas. Os detalhes dos blocos e das funções de "
    r"ativação e de saída estão no Apêndice D."
)

T_TR1 = (
    r"O treinamento consiste em ajustar o conjunto $\Theta$ de parâmetros da rede de modo que as previsões se "
    r"aproximem dos valores-alvo do problema inverso, minimizando o erro quadrático médio na escala "
    r"transformada:"
)
T_TR2 = (
    r"A minimização foi feita por descida de gradiente em mini-lotes de 16 registros (49 por época), com as "
    r"derivadas obtidas por retropropagação, utilizando o algoritmo AdamW (Loshchilov; Hutter, 2019), "
    r"variação do Adam (Kingma; Ba, 2017). A taxa de aprendizado foi reduzida ao longo das épocas, de "
    r"$4{,}08\times10^{-3}$ a $10^{-5}$, segundo uma curva cossenoidal (Loshchilov; Hutter, 2017). A rede foi "
    r"treinada por 928 épocas fixas, número definido pela busca de hiperparâmetros (Apêndice E), sem parada "
    r"antecipada, e os sorteios foram controlados por sementes fixas. A Tabela 4.XX.8 reúne os valores "
    r"adotados."
)

T_CR1 = (
    r"Os valores apresentados na Tabela 4.XX.8 e na Figura 4.XX.11 não são ajustados durante o treinamento, "
    r"mas definidos antes dele, e são chamados de hiperparâmetros. Para escolher entre configurações, foi "
    r"utilizado como critério o erro na própria conversão de zinco, e não em $\nu$, pois um erro em $\nu$ "
    r"nos primeiros instantes se acumula em $\delta$ e permanece na conversão até o fim do ensaio, enquanto um "
    r"erro da mesma ordem na etapa final tem efeito pequeno. Para cada configuração e cada dobra $k$, a rede é "
    r"treinada com os ensaios de ajuste, a taxa prevista para os ensaios de validação é acoplada ao modelo "
    r"fenomenológico, como no uso final do modelo (Seção 4.XX), e a conversão resultante é comparada com a "
    r"medida nos sete instantes experimentais:"
)
T_CR3 = (
    r"A nota de cada configuração é a média desse erro em várias sementes (Apêndice E). A busca foi feita com "
    r"o algoritmo TPE (Bergstra et al., 2011), implementado no Optuna (Akiba et al., 2019), em dois estágios "
    r"(423 e 523 tentativas, com três sementes cada). As cinco melhores configurações de cada estágio foram "
    r"reavaliadas com dez sementes e, pela regra de um erro-padrão (Hastie; Tibshirani; Friedman, 2009), "
    r"escolheu-se a mais simples entre as equivalentes à melhor. O modelo final é a média das taxas previstas "
    r"por dez redes treinadas com essa configuração e sementes diferentes (Lakshminarayanan; Pritzel; "
    r"Blundell, 2017), e a dispersão entre elas indica a incerteza do modelo. O teste cego foi consultado uma "
    r"única vez, depois de salvo o modelo final."
)

# --------------------------------------------------------------------------- Apêndice B (texto novo)
T_B_PESOS1 = (
    r"Para verificar o efeito das penalizações, calculou-se, com os parâmetros ótimos de cada ensaio, a "
    r"contribuição de cada termo de $J_{\mathrm{reg}}$ em relação ao termo de ajuste (Tabela B.1). A "
    r"penalização da amplitude da etapa rápida, com $\lambda_3$, foi a mais influente, com mediana de 16% do "
    r"termo de ajuste e máximo de 38% (Ensaio 5), o que indica que ela atua como uma regularização suave em "
    r"todos os ensaios, sem se sobrepor ao ajuste aos dados. A penalização da taxa final, com $\lambda_1$, só "
    r"foi relevante nos Ensaios 2, 7 e 11, em que a taxa em 15 min ficou em 0,52, 0,60 e 0,76 µm/min "
    r"(18%, 9% e 1% do termo de ajuste, respectivamente), e a do afastamento de $b_1$, com $\lambda_4$, teve "
    r"mediana de apenas 0,3%. A penalização da retração acumulada, com $\lambda_2$, só atua acima de 140 µm e "
    r"foi praticamente nula: o único ensaio que atinge esse valor é o Ensaio 12, com 140,0 µm."
)
T_B_PESOS2 = (
    r"Assim, com os pesos adotados, as penalizações têm efeito secundário em relação ao ajuste aos dados e "
    r"atuam principalmente quando o termo de ajuste não é capaz de discriminar entre soluções, que é o "
    r"comportamento pretendido. Vale registrar, porém, que os valores dos pesos foram definidos por "
    r"tentativa e erro, e não por um procedimento sistemático de otimização, de modo que a sua escolha "
    r"criteriosa é uma possível melhoria do método."
)

APENDICES = {
    "B": "APÊNDICE B - OBTENÇÃO DA TAXA DE RETRAÇÃO POR PROBLEMA INVERSO",
    "C": "APÊNDICE C - CONSTRUÇÃO DA BASE DE DADOS E PARTIÇÃO DOS ENSAIOS",
    "D": "APÊNDICE D - ARQUITETURA DA REDE NEURAL E ALGORITMO DE TREINAMENTO",
    "E": "APÊNDICE E - SELEÇÃO DA CONFIGURAÇÃO, MODELO FINAL E AVALIAÇÃO",
}
INTRO = {
    "B": "Este apêndice detalha a obtenção da taxa de retração de cada ensaio por problema inverso, resumida na "
         "Seção 4.XX (Modelagem híbrida serial).",
    "C": "Este apêndice detalha a construção da base de dados, a partição dos ensaios entre treino, teste cego e "
         "validação cruzada e a transformação das variáveis, resumidas na Seção 4.XX.",
    "D": "Este apêndice detalha a arquitetura da rede neural e o algoritmo de treinamento, resumidos na Seção 4.XX.",
    "E": "Este apêndice detalha o critério de avaliação das configurações da rede, a busca de hiperparâmetros, o "
         "modelo final em comitê e as métricas de avaliação, resumidos na Seção 4.XX.",
}

# Trocas aplicadas ao texto das subseções E.2 a E.4 (escrever_hibrido_serial.py) ao portá-las
TROCAS_PORTE = [
    ("Figura 4.X.15", "Figura E.2"), ("Figura 4.X.16", "Figura E.3"),
    ("Tabela 4.X.9", "Tabela E.1"), ("Tabela 4.X.10", "Tabela E.2"),
    ("Equação 4.X.22", "Equação E.1"),
    ("nas Tabelas 4.X.7 e 4.X.8", "na Tabela 4.XX.8 e na Figura 4.XX.11"),
    ("(Eqs. 4.X.1 a 4.X.3)", "(Seção 4.2.2)"),
    ("(Seção 5.X)", "(Seção 5.XX)"),
    ("as duas estratégias de parada descritas anteriormente", "as duas estratégias de parada (Seção E.1)"),
]
NUMEROS_EQ_PORTE = {"4.X.24": "E.3", "4.X.25": "E.4", "4.X.26": "E.5", "4.X.27": "E.6"}
SUBTITULOS_PORTE = {
    "Busca de hiperparâmetros": "E.2 Busca de hiperparâmetros",
    "Modelo final: comitê de redes": "E.3 Modelo final: comitê de redes",
    "Avaliação do modelo híbrido": "E.4 Avaliação do modelo híbrido",
}


# --------------------------------------------------------------------------- utilitários de XML
def texto(e) -> str:
    return "".join(t.text or "" for t in e.iter(qn("w:t")))


def clonar(e):
    """Cópia independente de um elemento, sem identificadores únicos, marcadores nem âncoras de comentário."""
    c = copy.deepcopy(e)
    for x in c.iter():
        for a in list(x.attrib):
            if a in (W14 + "paraId", W14 + "textId"):
                del x.attrib[a]
    for tag in ("bookmarkStart", "bookmarkEnd", "commentRangeStart", "commentRangeEnd"):
        for b in list(c.iter(qn("w:" + tag))):
            b.getparent().remove(b)
    for ref in list(c.iter(qn("w:commentReference"))):
        run = ref.getparent()
        run.getparent().remove(run)
    return c


def _runs_com_texto(p):
    return [r for r in p.iter(qn("w:r")) if r.find(qn("w:t")) is not None]


def _texto_run(r) -> str:
    return "".join(t.text or "" for t in r.findall(qn("w:t")))


def _definir_texto_run(r, novo: str) -> None:
    ts = r.findall(qn("w:t"))
    ts[0].text = novo
    ts[0].set(XML_SPACE, "preserve")
    for x in ts[1:]:
        r.remove(x)


def _tirar_destaque(r) -> None:
    rpr = r.find(qn("w:rPr"))
    h = rpr.find(qn("w:highlight")) if rpr is not None else None
    if h is not None:
        rpr.remove(h)


def trocar_no_paragrafo(p, antigo: str, novo: str) -> bool:
    """Troca um trecho de texto, mesmo que ele se estenda por vários runs."""
    runs = _runs_com_texto(p)
    textos = [_texto_run(r) for r in runs]
    cheio = "".join(textos)
    i = cheio.find(antigo)
    if i < 0:
        return False
    j, pos, colocado = i + len(antigo), 0, False
    for r, t in zip(runs, textos):
        s, e = pos, pos + len(t)
        pos = e
        if e <= i or s >= j:
            continue
        a, b = max(i, s) - s, min(j, e) - s
        _definir_texto_run(r, t[:a] + (novo if not colocado else "") + t[b:])
        colocado = True
        if "XX" not in novo:
            _tirar_destaque(r)
    return True


def _paragrafos(e):
    return [e] if e.tag == qn("w:p") else list(e.iter(qn("w:p")))


KW = re.compile(r"(Figuras?|Tabelas?|Equaç(?:ão|ões)|Eqs?\.)|(4\.XX?\.(\d+))")


def renumerar(elementos, figs, tabs, eqs, equacao_por_padrao=()):
    """Troca os marcadores 4.XX.n pelos números definitivos dos apêndices, conforme o tipo citado."""
    mapas = {"fig": figs, "tab": tabs, "eq": eqs}
    avisos = []
    for idx, e in elementos:
        for p in _paragrafos(e):
            runs = _runs_com_texto(p)
            textos = [_texto_run(r) for r in runs]
            cheio = "".join(textos)
            ctx = "eq" if idx in equacao_por_padrao else None
            trocas = []
            for m in KW.finditer(cheio):
                if m.group(1):
                    kw = m.group(1)
                    ctx = "fig" if kw.startswith("Figura") else "tab" if kw.startswith("Tabela") else "eq"
                else:
                    novo = mapas[ctx].get(int(m.group(3))) if ctx else None
                    if novo:
                        trocas.append((m.start(2), m.end(2), novo))
                    elif ctx is None:
                        avisos.append((idx, cheio[max(0, m.start() - 30):m.end() + 10]))
            for s, e_, novo in reversed(trocas):
                pos = 0
                for r, t in zip(runs, textos):
                    if pos <= s < pos + len(t):
                        a = s - pos
                        _definir_texto_run(r, t[:a] + novo + t[a + (e_ - s):])
                        _tirar_destaque(r)
                        break
                    pos += len(t)
    return avisos


def sem_numeracao(ppr):
    for n in ppr.findall(qn("w:numPr")):
        ppr.remove(n)
    return ppr


# --------------------------------------------------------------------------- porte das subseções E.2 a E.4
class Porte:
    """Intermediário que aplica as trocas de rótulos às chamadas de escrever_hibrido_serial.py."""

    def __init__(self, w: SectionWriter, subtitulo) -> None:
        self.w, self.subtitulo = w, subtitulo

    @staticmethod
    def _t(s: str) -> str:
        for a, b in TROCAS_PORTE:
            s = s.replace(a, b)
        return re.sub(r"Seção 4\.X(?!X)", "Seção 4.XX", s)

    def subheading(self, texto_: str) -> None:
        self.subtitulo(SUBTITULOS_PORTE[texto_])

    def paragraph(self, t: str) -> None:
        self.w.paragraph(self._t(t))

    def equation(self, latex: str, numero: str) -> None:
        self.w.equation(latex, NUMEROS_EQ_PORTE.get(numero, numero))

    def table(self, label, title, header, rows, widths_cm, **kw) -> None:
        self.w.table(self._t(label), self._t(title), [self._t(h) for h in header],
                     [[self._t(c) for c in r] for r in rows], widths_cm, **kw)

    def figure(self, image, width_cm, label, title, **kw) -> None:
        self.w.figure(image, width_cm, self._t(label), self._t(title), **kw)


def comandos_portados():
    """Instruções de conteudo() de escrever_hibrido_serial.py que viram as subseções E.2 a E.4."""
    arv = ast.parse(SCRIPT_LONGO.read_text(encoding="utf-8"))
    fn = next(n for n in arv.body if isinstance(n, ast.FunctionDef) and n.name == "conteudo")
    sub = lambda st: (isinstance(st, ast.Expr) and isinstance(st.value, ast.Call)  # noqa: E731
                      and isinstance(st.value.func, ast.Attribute) and st.value.func.attr == "subheading"
                      and isinstance(st.value.args[0], ast.Constant))
    corpo, dentro = [], False
    for st in fn.body:
        if sub(st):
            dentro = st.value.args[0].value in SUBTITULOS_PORTE
        if dentro:
            corpo.append(st)
    mod = ast.Module(body=corpo, type_ignores=[])
    ast.fix_missing_locations(mod)
    return compile(mod, str(SCRIPT_LONGO), "exec")


# --------------------------------------------------------------------------- tabela do Apêndice B
def linhas_tabela_penalidades():
    df = pd.read_csv(CSV_PENAL, index_col="ensaio")
    r = {c: df[c] / df["fit"] * 100 for c in ("cauda", "delta", "a1", "b1")}
    fmt = lambda v: f"{v:.2f}".replace(".", ",") if v >= 0.005 else "< 0,01"  # noqa: E731
    fmt2 = lambda s: f"{fmt(s.median())}"  # noqa: E731

    def maximo(s):
        return f"{fmt(s.max())} (Ensaio {int(s.idxmax())})"

    return [
        [r"$\lambda_1\,\nu(t_{60})^2$", "taxa ao final do ensaio (15 min)", r"$10^{-4}$", fmt2(r["cauda"]), maximo(r["cauda"])],
        [r"$\lambda_2[\max(0,\delta(t_{60})-\delta_{lim})]^2$", "retração acima de 140 µm", r"$10^{-4}$",
         fmt2(r["delta"]), maximo(r["delta"])],
        [r"$\lambda_3\,a_1^2$", "amplitude da etapa rápida", r"$10^{-7}$", fmt2(r["a1"]), maximo(r["a1"])],
        [r"$\lambda_4(b_1-b_{1,ref})^2$", r"afastamento de $b_1$ em relação a 4 min$^{-1}$", r"$10^{-6}$",
         fmt2(r["b1"]), maximo(r["b1"])],
    ]


# --------------------------------------------------------------------------- principal
def verificar_origem(els) -> None:
    esperado = {519: "MODELAGEM HÍBRIDA SERIAL", 531: "Elementos do modelo", 538: "Obtenção da taxa",
                575: "Construção da base", 620: "Arquitetura da rede", 649: "Função de perda",
                667: "Critério de avaliação", 683: "Acoplamento da rede"}
    for i, ini in esperado.items():
        assert texto(els[i]).strip().startswith(ini), (i, texto(els[i])[:60])
    nxt = next(e for e in els[I_FIM:] if texto(e).strip())
    assert texto(nxt).startswith("RESULTADOS E DISCUSS"), texto(nxt)[:60]
    for i in (648, 666, 682, *range(695, 701)):
        assert not texto(els[i]).strip() and els[i].find(".//" + qn("w:sectPr")) is None, i


def main() -> None:
    saida = Path(sys.argv[sys.argv.index("--saida") + 1]) if "--saida" in sys.argv else DESTINO
    doc = docx.Document(str(ORIGEM))
    body = doc.element.body
    els = list(body)
    verificar_origem(els)

    # 1. cópias das equações e parágrafos que ficam nos dois lugares (antes de renumerar)
    copias = {i: clonar(els[i]) for i in COPIAS}

    # 2. ajustes de texto e numeração nos elementos que vão para os apêndices
    for i, trocas in TROCAS_TEXTO.items():
        for a, b in trocas:
            assert any(trocar_no_paragrafo(p, a, b) for p in _paragrafos(els[i])), (i, a)

    def indices(*faixas):
        return [i for f in faixas for i in (range(f[0], f[1] + 1) if isinstance(f, tuple) else [f])]

    B = indices((539, 540), (544, 574))
    C = indices((576, 602), (606, 619))
    D = indices(621, (625, 647), (650, 662))
    E1 = indices((668, 681))
    ap_orig = [(i, els[i]) for i in B + C + D + E1]
    avisos = renumerar(ap_orig, FIG_APENDICE, TAB_APENDICE, EQ_APENDICE, TABELAS_EQUACAO)

    mantidos = indices((519, 537), 538, (541, 543), (575, 575), (603, 605), 620, (622, 624), 649, (663, 665), 667,
                       (683, 694))
    avisos += renumerar([(i, els[i]) for i in mantidos], FIG_APENDICE, TAB_APENDICE, EQ_METODOLOGIA)
    if avisos:
        print("Marcadores sem tipo identificado:", avisos)

    # 3. destacar os parágrafos e tabelas de origem e abrir espaço
    contidos = set(B + C + D + E1 + mantidos)
    todos = set(range(I_INI, I_FIM))
    vazios = {i for i in todos - contidos if not texto(els[i]).strip() and els[i].find(".//" + qn("w:drawing")) is None}
    sobras = sorted(todos - contidos - vazios)
    assert not sobras, f"elementos de origem sem destino: {sobras}"

    marca_met = parse_xml(f"<w:p {nsdecls('w')}/>")
    els[I_FIM].addprevious(marca_met)
    for e in els[I_INI:I_FIM]:
        body.remove(e)

    # âncora dos apêndices: depois do parágrafo com quebra de página que segue o Apêndice A
    i_apend = next(i for i, e in enumerate(els) if texto(e).strip() == "APÊNDICES")
    i_quebra = next(i for i in range(i_apend, len(els)) if els[i].find(".//" + qn("w:br")) is not None)
    marca_ap = parse_xml(f"<w:p {nsdecls('w')}/>")
    els[i_quebra + 1].addprevious(marca_ap)

    refs = {"body": els[521], "figure": els[524], "caption": els[525], "source": els[526],
            "heading": els[519], "subheading": els[521]}
    w_met = SectionWriter(doc, refs, marca_met)
    w_ap = SectionWriter(doc, refs, marca_ap)

    def pôr(w, i):
        w._place(els[i])

    def pôr_copia(w, i):
        w._place(copias[i])

    # ---------------------------------------------------------------- Metodologia
    for i in range(519, 531):
        pôr(w_met, i)
    w_met.paragraph(T_RESSALVA)
    for i in range(531, 538):
        pôr(w_met, i)
    pôr(w_met, 538)
    w_met.paragraph(T_INV1)
    for i in (541, 542, 543):
        pôr(w_met, i)
    w_met.paragraph(T_INV2)
    pôr_copia(w_met, 545)
    w_met.paragraph(T_INV3)
    w_met.paragraph(T_INV4)
    pôr_copia(w_met, 551)
    w_met.paragraph(T_INV5)
    w_met.paragraph(T_INV6)
    pôr_copia(w_met, 558)
    for t in (T_INV7, T_INV8, T_INV9):
        w_met.paragraph(t)

    pôr(w_met, 575)
    for t in (T_BD1, T_BD2, T_BD2B, T_BD3):
        w_met.paragraph(t)
    for i in (603, 604, 605):
        pôr(w_met, i)
    w_met.paragraph(T_BD4A)
    pôr_copia(w_met, 607)
    w_met.paragraph(T_BD4B)
    w_met.paragraph(T_BD5A)
    pôr_copia(w_met, 615)
    w_met.paragraph(T_BD5B)

    pôr(w_met, 620)
    w_met.paragraph(T_AR1)
    for i in (622, 623, 624):
        pôr(w_met, i)
    w_met.paragraph(T_AR2A)
    pôr_copia(w_met, 626)
    w_met.paragraph(T_AR2B)
    w_met.paragraph(T_AR3A)
    pôr_copia(w_met, 640)
    w_met.paragraph(T_AR3B)
    pôr_copia(w_met, 642)
    w_met.paragraph(T_AR4)

    pôr(w_met, 649)
    w_met.paragraph(T_TR1)
    pôr_copia(w_met, 651)
    pôr_copia(w_met, 652)
    w_met.paragraph(T_TR2)
    for i in (663, 664, 665):
        pôr(w_met, i)

    pôr(w_met, 667)
    w_met.paragraph(T_CR1)
    pôr_copia(w_met, 673)
    pôr_copia(w_met, 674)
    w_met.paragraph(T_CR3)

    for i in range(683, 695):
        pôr(w_met, i)

    # ---------------------------------------------------------------- Apêndices (fora de Métodos: vermelho)
    ap_a = next(e for e in els if texto(e).startswith("APÊNDICE A"))
    primeiro = {"B": True}

    def titulo(letra: str) -> None:
        p = parse_xml(f"<w:p {nsdecls('w')}/>")
        ppr = copy.deepcopy(ap_a.find(qn("w:pPr")))
        sem_numeracao(ppr)
        if not primeiro.get(letra):
            ppr.insert(1, parse_xml(f"<w:pageBreakBefore {nsdecls('w')}/>"))
        p.append(ppr)
        p.append(SectionWriter._run(APENDICES[letra]))
        w_ap._place(p)
        w_ap.paragraph(INTRO[letra])

    def subtitulo(txt: str) -> None:
        p = parse_xml(f"<w:p {nsdecls('w')}/>")
        ppr = sem_numeracao(copy.deepcopy(els[519].find(qn("w:pPr"))))
        p.append(ppr)
        p.append(SectionWriter._run(txt))
        w_ap._place(p)

    def bloco(faixa):
        for i in faixa:
            pôr(w_ap, i)

    # B
    titulo("B")
    bloco([539, 540])
    subtitulo("B.1 Parametrização da taxa de retração")
    bloco([544, 545, 546, 547, 548, 549])
    subtitulo("B.2 Integração da retração acumulada e malha temporal")
    bloco(range(550, 556))
    subtitulo("B.3 Função objetivo e penalizações")
    bloco(range(556, 564))
    w_ap.paragraph(T_B_PESOS1)
    w_ap.table("Tabela B.1", "Contribuição de cada termo de penalização ao valor final da função objetivo, em "
               "relação ao termo de ajuste, nos 16 ensaios",
               ["Termo", "Penaliza", "Peso", "Mediana (% do ajuste)", "Máximo (% do ajuste)"],
               linhas_tabela_penalidades(), [3.8, 4.2, 1.6, 2.7, 3.7],
               source="Fonte: Elaborado pelos autores (2026)")
    w_ap.paragraph(T_B_PESOS2)
    subtitulo("B.4 Otimização e bases de dados geradas")
    bloco(range(564, 575))

    # C
    titulo("C")
    subtitulo("C.1 Organização da base de dados e variáveis")
    bloco(range(576, 586))
    subtitulo("C.2 Divisão entre treino e teste cego")
    bloco(range(586, 596))
    subtitulo("C.3 Validação cruzada por ensaio")
    bloco(range(596, 603))
    subtitulo("C.4 Transformação das variáveis")
    bloco(range(606, 620))

    # D
    titulo("D")
    subtitulo("D.1 Arquitetura da rede neural")
    bloco([621] + list(range(625, 648)))
    subtitulo("D.2 Função de perda e algoritmo de treinamento")
    bloco(range(650, 663))

    # E
    titulo("E")
    subtitulo("E.1 Critério de avaliação das configurações da rede")
    bloco(range(668, 682))
    porte = Porte(w_ap, subtitulo)
    exec(comandos_portados(), {"w": porte, "FIG_DIR": FIG_DIR})

    # 4. cor vermelha em tudo que foi para os apêndices
    pintar(list(w_ap.inserted))
    marca_met.getparent().remove(marca_met)
    marca_ap.getparent().remove(marca_ap)

    saida.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(saida))
    print(f"Documento salvo em: {saida}")


if __name__ == "__main__":
    main()
