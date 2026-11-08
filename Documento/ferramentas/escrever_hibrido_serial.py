"""Escreve no relatório a seção de Materiais e Métodos do modelo híbrido serial.

A seção é inserida ao final de MATERIAIS E MÉTODOS (antes de RESULTADOS E DISCUSSÃO),
depois das partes já escritas pelo grupo. Antes de qualquer alteração, uma cópia do
relatório é salva em Documento/old/.

Uso:
    python escrever_hibrido_serial.py               # insere a seção (falha se já existir)
    python escrever_hibrido_serial.py --substituir  # reescreve a seção já inserida
"""

from __future__ import annotations

import sys
from pathlib import Path

import docx
from docx.oxml.ns import qn

from docx_utils import SectionWriter, add_references, backup, find_paragraph

DOC_DIR = Path(__file__).resolve().parents[1]
DOC_PATH = DOC_DIR / "RELATÓRIO FINAL LOP.docx"
FIG_DIR = DOC_DIR / "figuras_metodologia"

TITULO_SECAO = "Modelagem Híbrida Serial: Aprendizado da Taxa de Retração das Partículas"

REFERENCIAS_NOVAS = [
    "ASTER, R. C.; BORCHERS, B.; THURBER, C. H. Parameter Estimation and Inverse Problems. 3. ed. "
    "Amsterdam: Elsevier, 2018.",
    "BYRD, R. H.; LU, P.; NOCEDAL, J.; ZHU, C. A limited memory algorithm for bound constrained "
    "optimization. SIAM Journal on Scientific Computing, v. 16, n. 5, p. 1190–1208, 1995.",
    "BOX, G. E. P.; COX, D. R. An analysis of transformations. Journal of the Royal Statistical "
    "Society: Series B (Methodological), v. 26, n. 2, p. 211–252, 1964.",
    "LECUN, Y.; BOTTOU, L.; ORR, G. B.; MÜLLER, K.-R. Efficient BackProp. In: ORR, G. B.; MÜLLER, "
    "K.-R. (Eds.). Neural Networks: Tricks of the Trade. Berlin: Springer, 1998. p. 9–50.",
    "ROBERTS, D. R. et al. Cross-validation strategies for data with temporal, spatial, "
    "hierarchical, or phylogenetic structure. Ecography, v. 40, n. 8, p. 913–929, 2017.",
    "KAPOOR, S.; NARAYANAN, A. Leakage and the reproducibility crisis in machine-learning-based "
    "science. Patterns, v. 4, n. 9, p. 100804, 2023.",
    "FRITSCH, F. N.; CARLSON, R. E. Monotone piecewise cubic interpolation. SIAM Journal on "
    "Numerical Analysis, v. 17, n. 2, p. 238–246, 1980.",
    "RANDOLPH, A. D.; LARSON, M. A. Theory of Particulate Processes: analysis and techniques of "
    "continuous crystallization. 2. ed. San Diego: Academic Press, 1988.",
    "HE, K.; ZHANG, X.; REN, S.; SUN, J. Deep residual learning for image recognition. In: IEEE "
    "Conference on Computer Vision and Pattern Recognition (CVPR), 2016, Las Vegas. Proceedings [...]. "
    "Las Vegas: IEEE, 2016. p. 770–778.",
    "HENDRYCKS, D.; GIMPEL, K. Gaussian Error Linear Units (GELUs). arXiv preprint arXiv:1606.08415, 2016.",
    "SRIVASTAVA, N.; HINTON, G.; KRIZHEVSKY, A.; SUTSKEVER, I.; SALAKHUTDINOV, R. Dropout: a simple way "
    "to prevent neural networks from overfitting. Journal of Machine Learning Research, v. 15, n. 56, "
    "p. 1929–1958, 2014.",
    "LOSHCHILOV, I.; HUTTER, F. SGDR: Stochastic gradient descent with warm restarts. In: International "
    "Conference on Learning Representations (ICLR), 2017, Toulon. Proceedings [...]. Toulon, 2017.",
    "LOSHCHILOV, I.; HUTTER, F. Decoupled weight decay regularization. In: International Conference on "
    "Learning Representations (ICLR), 2019, New Orleans. Proceedings [...]. New Orleans, 2019.",
    "PASZKE, A. et al. PyTorch: an imperative style, high-performance deep learning library. In: Advances "
    "in Neural Information Processing Systems 32 (NeurIPS 2019). Vancouver: Curran Associates, 2019. "
    "p. 8024–8035.",
    "CAWLEY, G. C.; TALBOT, N. L. C. On over-fitting in model selection and subsequent selection bias in "
    "performance evaluation. Journal of Machine Learning Research, v. 11, p. 2079–2107, 2010.",
    "BERGSTRA, J.; BARDENET, R.; BENGIO, Y.; KÉGL, B. Algorithms for hyper-parameter optimization. In: "
    "Advances in Neural Information Processing Systems 24 (NIPS 2011). Granada: Curran Associates, 2011. "
    "p. 2546–2554.",
    "AKIBA, T.; SANO, S.; YANASE, T.; OHTA, T.; KOYAMA, M. Optuna: a next-generation hyperparameter "
    "optimization framework. In: ACM SIGKDD International Conference on Knowledge Discovery & Data Mining, "
    "25., 2019, Anchorage. Proceedings [...]. New York: ACM, 2019. p. 2623–2631.",
    "LAKSHMINARAYANAN, B.; PRITZEL, A.; BLUNDELL, C. Simple and scalable predictive uncertainty estimation "
    "using deep ensembles. In: Advances in Neural Information Processing Systems 30 (NIPS 2017). Long "
    "Beach: Curran Associates, 2017. p. 6402–6413.",
    "WILCOXON, F. Individual comparisons by ranking methods. Biometrics Bulletin, v. 1, n. 6, p. 80–83, 1945.",
    "GLOROT, X.; BENGIO, Y. Understanding the difficulty of training deep feedforward neural networks. In: "
    "International Conference on Artificial Intelligence and Statistics (AISTATS), 13., 2010, Sardinia. "
    "Proceedings [...]. Sardinia: PMLR, 2010. p. 249–256.",
    "CHICCO, D.; WARRENS, M. J.; JURMAN, G. The coefficient of determination R-squared is more informative "
    "than SMAPE, MAE, MAPE, MSE and RMSE in regression analysis evaluation. PeerJ Computer Science, v. 7, "
    "e623, 2021.",
]


def conteudo(w: SectionWriter) -> None:
    """Texto da seção, na ordem em que aparece no relatório."""
    w.heading(TITULO_SECAO)

    # ---------------------------------------------------------------- abertura
    w.paragraph(
        "Conforme discutido na revisão bibliográfica (Seção 3.X), na arquitetura híbrida serial o "
        "modelo orientado por dados não substitui o modelo fenomenológico, mas atua como um estimador "
        "de grandezas internas que não podem ser determinadas diretamente a partir de primeiros "
        "princípios. Os valores estimados são, então, inseridos nas equações de conservação, de modo "
        "que as variáveis de interesse continuam sendo calculadas pelos balanços de massa e "
        "populacional (Sansana et al., 2024). Nesta etapa do trabalho, essa estrutura foi aplicada à "
        "lixiviação do ustulado de zinco em batelada, combinando o balanço populacional descrito na "
        "Seção 3.1.4.1 a uma rede neural do tipo MLP (*Multilayer Perceptron*)."
    )
    w.paragraph(
        "A principal decisão na construção do modelo foi a escolha da grandeza a ser aprendida pela "
        "rede neural. Em vez de estimar diretamente a conversão de zinco, como ocorre no modelo "
        "puramente orientado por dados apresentado na Seção 4.X, a rede foi treinada para estimar a "
        "taxa de retração diametral das partículas, $\\nu(t)=-dD/dt$. No modelo fenomenológico, essa "
        "taxa é obtida pela lei cinética de reação interfacial, e é justamente nela que se concentram "
        "as principais simplificações do modelo: a existência de um único mecanismo controlador, o uso "
        "da densidade molar do ZnO puro, um teor de zinco fixo no sólido alimentado e uma constante "
        "cinética $k_s$ invariável ao longo da reação (Bortot Coelho, 2017). Na formulação original, "
        "o parâmetro empírico $\\alpha$ foi introduzido para compensar esses desvios por meio de um "
        "único valor ajustado para o conjunto de ensaios. Na abordagem híbrida, essa correção deixa de "
        "ser representada por uma constante e passa a ser incorporada à própria taxa $\\nu$, aprendida "
        "pela rede como uma função contínua das condições operacionais e do tempo de reação."
    )
    w.paragraph(
        "Com essa escolha, a rede neural fica responsável apenas pela parcela do processo cuja "
        "descrição teórica é mais incerta, enquanto a relação entre a retração das partículas, a "
        "conversão de zinco e o consumo de ácido continua sendo descrita pelos balanços populacional "
        "e estequiométrico. Isso traz duas vantagens práticas. A primeira é que as previsões de "
        "conversão herdam as restrições físicas do modelo fenomenológico, permanecendo entre 0 e 1 e "
        "limitadas pela quantidade de ácido disponível no reator. A segunda é que a saída da rede "
        "possui significado físico, podendo ser comparada com a ordem de grandeza esperada para a "
        "velocidade de dissolução das partículas."
    )
    w.paragraph(
        "A Figura 4.X.1 resume a arquitetura adotada. As condições operacionais de cada ensaio, isto "
        "é, a concentração inicial de ácido sulfúrico ($C_{A0}$) e a razão molar estequiométrica "
        "($\\eta$), juntamente com o tempo de reação ($t$), são fornecidas à rede neural, que estima a "
        "taxa $\\nu(t)$. Essa taxa é integrada no tempo para obter a retração acumulada do diâmetro "
        "das partículas, $\\delta(t)$, a partir da qual o balanço populacional calcula a conversão de "
        "zinco, $X_{\\mathrm{Zn}}(t)$, e o balanço de ácido fornece a concentração de ácido livre na "
        "solução, $C_A(t)$."
    )
    w.figure(FIG_DIR / "fig_hs_01_arquitetura_serial.png", 16.0, "Figura 4.X.1",
             "Representação esquemática da arquitetura híbrida serial adotada neste trabalho")
    w.paragraph(
        "O desenvolvimento dessa abordagem foi organizado nas sete etapas apresentadas na Figura "
        "4.X.2. Partindo das curvas experimentais de conversão obtidas por Bortot Coelho (2017), a "
        "primeira dificuldade a ser contornada é que a taxa $\\nu(t)$, que a rede deve aprender, não é "
        "medida diretamente nos ensaios. Por isso, antes do treinamento, os valores de $\\nu(t)$ de "
        "cada ensaio foram estimados por meio de um problema inverso, isto é, buscando a curva de "
        "$\\nu(t)$ que, ao ser inserida no balanço populacional, reproduz a conversão medida. Os "
        "valores obtidos compõem a base de dados utilizada no treinamento da rede, que, depois de "
        "treinada, é acoplada ao balanço populacional e avaliada frente aos dados experimentais. Cada "
        "uma dessas etapas é detalhada nas seções seguintes."
    )
    w.figure(FIG_DIR / "fig_hs_02_fluxograma_etapas.png", 15.0, "Figura 4.X.2",
             "Etapas de desenvolvimento do modelo híbrido serial")

    # ------------------------------------------- elementos do modelo fenomenológico
    w.subheading("Elementos do modelo fenomenológico utilizados no acoplamento")
    w.paragraph(
        "Para que a taxa estimada pela rede pudesse ser convertida em conversão de zinco, foram "
        "aproveitados três elementos do modelo fenomenológico de Bortot Coelho (2017), apresentado na "
        "Seção 3.1.4: a hipótese de retração uniforme das partículas, a relação entre a retração "
        "acumulada e a conversão e o balanço de ácido. As considerações adotadas foram as mesmas do "
        "modelo original, ou seja, partículas esféricas, reação química na interface como etapa "
        "controladora, conforme estabelecido por Balarini et al. (2025), ausência de quebra ou "
        "aglomeração de partículas e proporção estequiométrica unitária entre o ácido sulfúrico e o "
        "óxido de zinco."
    )
    w.paragraph(
        "Quando a reação química na superfície controla o processo, a velocidade com que o diâmetro "
        "das partículas diminui não depende do seu tamanho, mas apenas das condições do meio "
        "reacional, como a concentração de ácido livre (Levenspiel, 2000). Assim, em um mesmo "
        "instante, todas as partículas da suspensão perdem a mesma espessura, independentemente do seu "
        "diâmetro inicial. Essa propriedade permite descrever o estado de toda a população por uma "
        "única variável, a retração diametral acumulada, $\\delta(t)$, definida como a redução de "
        "diâmetro sofrida por qualquer partícula desde o início da reação:"
    )
    w.equation(r"\delta(t)=\int_{0}^{t}{\nu(\tau)\,d\tau}", "4.X.1")
    w.paragraph(
        "Em que $\\nu(t)=-dD/dt\\geq 0$ é a taxa de retração diametral, positiva enquanto houver "
        "dissolução. Dessa forma, uma partícula que entrou no reator com diâmetro $D_0$ apresenta, no instante $t$, "
        "diâmetro igual a $D_0-\\delta(t)$, enquanto as partículas com $D_0\\leq\\delta(t)$ já foram "
        "completamente dissolvidas. Em termos do balanço populacional, isso corresponde à solução da "
        "Equação 3.XX pelo método das características: como a taxa de retração é a mesma para todos os "
        "tamanhos, a distribuição em número de partículas apenas se desloca ao longo do eixo dos "
        "diâmetros, sem mudar de forma (Randolph; Larson, 1988):"
    )
    w.equation(r"\bar{\psi}(D,t)=\bar{\psi}_{0}\left(D+\delta(t)\right)", "4.X.2")
    w.paragraph(
        "Em que $\\bar{\\psi}_0$ é a distribuição inicial em número de partículas. A Figura 4.X.3 "
        "ilustra esse comportamento. No painel (a), partículas de tamanhos diferentes perdem a mesma "
        "espessura, de modo que as menores desaparecem primeiro. No painel (b), observa-se a "
        "consequência sobre a massa de sólido remanescente em cada faixa de diâmetro: como as "
        "partículas finas concentram uma parcela importante da massa inicial e são as primeiras a se "
        "dissolver, pequenas retrações já resultam em uma redução expressiva da massa de ZnO não "
        "reagida."
    )
    w.figure(FIG_DIR / "fig_hs_03_retracao_uniforme.png", 16.0, "Figura 4.X.3",
             "Efeito da retração uniforme sobre a população de partículas: (a) partículas de "
             "diferentes tamanhos submetidas à mesma retração; (b) massa remanescente por faixa de "
             "diâmetro para diferentes valores de δ")
    w.paragraph(
        "Como o volume de cada partícula é proporcional ao cubo do seu diâmetro, a fração de ZnO que "
        "permanece sem reagir é dada pela razão entre o terceiro momento da distribuição no instante "
        "$t$ e o seu valor inicial (Randolph; Larson, 1988). Substituindo a Equação (4.X.2) na "
        "expressão da conversão apresentada na revisão bibliográfica (Equação 3.XX) e realizando a "
        "mudança de variável $D_0=D+\\delta$, obtém-se a conversão de zinco exclusivamente em função "
        "da retração acumulada:"
    )
    w.equation(
        r"X_{\mathrm{Zn}}(\delta)=1-\frac{\int_{\delta}^{D_{\mathrm{max}}}{\left(D_{0}-\delta\right)^{3}"
        r"\bar{\psi}_{0}(D_{0})\,dD_{0}}}{\int_{0}^{D_{\mathrm{max}}}{D_{0}^{3}\,\bar{\psi}_{0}(D_{0})\,dD_{0}}}",
        "4.X.3",
    )
    w.paragraph(
        "Nessa expressão, $\\bar{\\psi}_0$ corresponde à distribuição inicial em número de partículas, "
        "obtida a partir do ajuste do modelo RRB em base mássica, conforme descrito na Seção 4.X, e "
        "$D_{\\mathrm{max}}=297$ µm corresponde à maior abertura de peneira empregada na "
        "caracterização granulométrica. O limite inferior da integral do numerador indica que apenas "
        "as partículas com diâmetro inicial maior que $\\delta$ ainda contribuem para o sólido não "
        "reagido."
    )
    w.paragraph(
        "A Equação (4.X.3) mostra que, uma vez conhecida a distribuição granulométrica inicial, a "
        "conversão depende apenas de $\\delta$, e não do caminho percorrido até atingi-lo. Por esse "
        "motivo, a relação $X_{\\mathrm{Zn}}(\\delta)$ foi calculada uma única vez, antes das "
        "simulações, em 600 valores de $\\delta$ igualmente espaçados entre 0 e $D_{\\mathrm{max}}$, "
        "com as integrais avaliadas numericamente pela regra do trapézio em uma malha de 5000 "
        "diâmetros entre 0,01 e 297 µm. Durante as simulações, os valores intermediários foram obtidos "
        "por interpolação cúbica monótona (PCHIP, do inglês *Piecewise Cubic Hermite Interpolating "
        "Polynomial*), que preserva o caráter crescente da curva e evita oscilações sem significado "
        "físico (Fritsch; Carlson, 1980). A curva resultante é apresentada na Figura 4.X.4."
    )
    w.figure(FIG_DIR / "fig_hs_04_curva_conversao_delta.png", 11.0, "Figura 4.X.4",
             "Relação entre a conversão de zinco e a retração diametral acumulada, calculada a partir "
             "da distribuição granulométrica inicial")
    w.paragraph(
        "Por fim, a concentração de ácido livre na solução é obtida pelo balanço estequiométrico em "
        "batelada apresentado na revisão bibliográfica (Equação 3.XX), que relaciona o consumo de "
        "ácido ao avanço da conversão:"
    )
    w.equation(r"C_{A}(t)=C_{A0}\left[1-\frac{X_{\mathrm{Zn}}(t)}{\eta}\right]", "4.X.4")
    w.paragraph(
        "Como cada mol de ZnO dissolvido consome um mol de H₂SO₄, a conversão não pode ultrapassar a "
        "razão molar $\\eta$ nos ensaios com deficiência de ácido ($\\eta<1$), o que impõe o limite "
        "$X_{\\mathrm{Zn}}\\leq\\min(1,\\eta)$. Essa restrição é utilizada na etapa de acoplamento "
        "(Seção 4.X) para garantir que as previsões do modelo híbrido respeitem a conservação de massa."
    )
    w.paragraph(
        "Em síntese, por meio das Equações (4.X.1) a (4.X.4), o comportamento de toda a população de "
        "partículas e da fase líquida fica determinado a partir de uma única função do tempo, $\\nu(t)$. "
        "No modelo fenomenológico, essa função é dada pela lei cinética de reação interfacial, com a "
        "constante $k_s$; no modelo híbrido, ela passa a ser estimada pela rede neural. O problema de "
        "modelagem, portanto, resume-se a obter uma boa estimativa de $\\nu(t)$ para cada condição "
        "operacional, o que é tratado nas seções seguintes."
    )

    # ------------------------------------------------------------ problema inverso
    w.subheading("Obtenção da taxa de retração por problema inverso")
    w.paragraph(
        "Para treinar a rede neural de forma supervisionada, é necessário dispor de pares formados "
        "pelas variáveis de entrada ($C_{A0}$, $\\eta$ e $t$) e pelo valor correspondente da taxa de "
        "retração $\\nu$. No entanto, os ensaios de Bortot Coelho (2017) fornecem apenas a conversão de "
        "zinco ao longo do tempo, medida em sete instantes após o início da reação (0,5; 1; 2; 3; 4; 5 "
        "e 15 min), e não a velocidade com que o diâmetro das partículas diminui. Assim, antes do "
        "treinamento, foi necessário estimar, para cada um dos 16 ensaios, a curva $\\nu(t)$ que, ao "
        "ser inserida nas Equações (4.X.1) a (4.X.3), reproduz a conversão medida. Esse tipo de "
        "situação, em que se conhece o efeito (a conversão) e se deseja determinar a causa (a taxa de "
        "retração), caracteriza um problema inverso (Aster; Borchers; Thurber, 2018)."
    )
    w.paragraph(
        "Problemas inversos dessa natureza costumam ser mal-postos, pois existem infinitas curvas "
        "$\\nu(t)$ capazes de reproduzir sete pontos experimentais, inclusive curvas com oscilações sem "
        "significado físico. Para contornar essa dificuldade, foram adotadas duas estratégias "
        "complementares: a representação de $\\nu(t)$ por uma função com poucos parâmetros e forma "
        "fisicamente coerente e a inclusão de termos de penalização na função objetivo, que restringem "
        "o comportamento da curva nos intervalos em que não há medições (Aster; Borchers; Thurber, "
        "2018). A Figura 4.X.5 resume o procedimento adotado para cada ensaio, detalhado a seguir."
    )
    w.figure(FIG_DIR / "fig_hs_05_problema_inverso.png", 16.0, "Figura 4.X.5",
             "Procedimento de solução do problema inverso para a estimativa da taxa de retração de "
             "cada ensaio")
    w.paragraph("A taxa de retração de cada ensaio foi representada pela soma de dois decaimentos "
                "exponenciais e de uma constante:")
    w.equation(r"\nu(t;\theta)=a_{1}e^{-b_{1}t}+a_{2}e^{-b_{2}t}+c", "4.X.5")
    w.paragraph(
        "Em que $\\theta=(a_1,b_1,a_2,b_2,c)$ é o vetor de parâmetros do ensaio, com $a_1$, $a_2$ e "
        "$c$ em µm/min e $b_1$ e $b_2$ em min⁻¹. A escolha dessa forma baseou-se no comportamento das "
        "curvas de conversão, que apresentam uma etapa inicial muito rápida, na qual uma parcela "
        "expressiva do zinco é dissolvida, seguida de uma etapa lenta de aproximação ao patamar final. "
        "O primeiro termo representa a etapa rápida, associada à elevada concentração inicial de ácido "
        "e à dissolução das partículas finas; o segundo, a etapa lenta, em que a acidez já foi "
        "parcialmente consumida e restam apenas as partículas maiores; e a constante $c$ permite uma "
        "pequena taxa residual ao final do ensaio. Como todos os parâmetros são não negativos, a função "
        "é positiva e decrescente em todo o intervalo, o que é coerente com o consumo progressivo do "
        "agente lixiviante. A Figura 4.X.6 ilustra a contribuição de cada termo e a retração acumulada "
        "resultante."
    )
    w.figure(FIG_DIR / "fig_hs_06_parametrizacao_biexponencial.png", 16.0, "Figura 4.X.6",
             "Forma da parametrização adotada para a taxa de retração, com valores ilustrativos dos "
             "parâmetros: (a) contribuição de cada termo da Equação (4.X.5), em escala logarítmica; "
             "(b) retração acumulada correspondente")
    w.paragraph(
        "Para cada vetor de parâmetros, a retração acumulada foi calculada em uma malha temporal "
        "regular com passo $\\Delta t=0,25$ min, de 0,25 a 15 min (60 nós), que contém todos os "
        "instantes experimentais (Figura 4.X.7). Partindo da condição inicial $\\delta(0)=0$, o "
        "primeiro intervalo foi integrado considerando a taxa constante e igual a $\\nu(t_1)$, e os "
        "demais pela regra do trapézio:"
    )
    w.equation(r"\delta_{k}=\delta_{k-1}+\frac{\Delta t}{2}\left[\nu(t_{k})+\nu(t_{k-1})\right]", "4.X.6")
    w.paragraph(
        "Com $\\delta_1=\\nu(t_1)\\,t_1$ e $k=2,\\ldots,60$. A conversão em cada nó foi então obtida "
        "diretamente da curva $X_{\\mathrm{Zn}}(\\delta)$ pré-calculada (Figura 4.X.4). Esse mesmo "
        "procedimento de integração é utilizado posteriormente no acoplamento entre a rede neural e o "
        "balanço populacional, o que garante que a taxa estimada nesta etapa e a taxa prevista pela "
        "rede sejam convertidas em conversão exatamente da mesma forma."
    )
    w.figure(FIG_DIR / "fig_hs_07_malhas_temporais.png", 16.0, "Figura 4.X.7",
             "Instantes de medição experimental e malha temporal utilizada na integração da retração "
             "acumulada e na construção da base de treinamento")
    w.paragraph(
        "O instante inicial não foi incluído no ajuste. Em $t=0$, a conversão é nula por definição e "
        "foi imposta diretamente como condição inicial, isto é, $X_{\\mathrm{Zn}}(0)=0$, $\\delta(0)=0$ "
        "e $C_A(0)=C_{A0}$. Incluir esse ponto no ajuste, ou posteriormente no cálculo das métricas, não "
        "acrescentaria informação sobre a cinética e tenderia a inflar artificialmente os indicadores de "
        "desempenho, uma vez que qualquer modelo o reproduz exatamente. Por esse motivo, todo o "
        "tratamento descrito a seguir considera apenas os instantes com $t>0$."
    )
    w.paragraph("Os parâmetros de cada ensaio foram determinados pela minimização da seguinte função "
                "objetivo:")
    w.equation(
        r"J(\theta)=\sum_{i=1}^{7}{\left[X_{\mathrm{Zn}}^{\mathrm{exp}}(t_{i})-X_{\mathrm{Zn}}(t_{i};\theta)\right]^{2}}"
        r"+J_{\mathrm{reg}}(\theta)",
        "4.X.7",
    )
    w.equation(
        r"J_{\mathrm{reg}}(\theta)=\lambda_{1}\,\nu(t_{60})^{2}+\lambda_{2}\left[\max\left(0,\delta(t_{60})"
        r"-\delta_{\mathrm{lim}}\right)\right]^{2}+\lambda_{3}\,a_{1}^{2}+\lambda_{4}\left(b_{1}-b_{1}^{\mathrm{ref}}\right)^{2}",
        "4.X.8",
    )
    w.paragraph(
        "O primeiro termo da Equação (4.X.7) é a soma dos quadrados dos desvios entre a conversão "
        "medida e a calculada nos sete instantes experimentais do ensaio. Os termos de "
        "$J_{\\mathrm{reg}}$ atuam como regularização e foram incluídos para conduzir o ajuste a "
        "soluções fisicamente plausíveis nas regiões em que os dados não são suficientes para "
        "determinar a curva: (i) o termo com $\\lambda_1$ penaliza taxas de retração elevadas ao final "
        "do ensaio ($t_{60}=15$ min), evitando que a curva continue dissolvendo o sólido no longo "
        "intervalo entre 5 e 15 min, no qual existe apenas uma medição; (ii) o termo com $\\lambda_2$ "
        "penaliza retrações acumuladas superiores a $\\delta_{\\mathrm{lim}}=140$ µm, valor a partir do "
        "qual praticamente todo o sólido já estaria dissolvido (Figura 4.X.4), impedindo soluções sem "
        "sentido físico; e (iii) os termos com $\\lambda_3$ e $\\lambda_4$ suavizam a etapa rápida, "
        "evitando picos excessivos de $\\nu$ nos primeiros 30 segundos, intervalo que antecede a "
        "primeira medição, e mantendo $b_1$ próximo de $b_1^{\\mathrm{ref}}=4$ min⁻¹ quando os dados "
        "não indicam outro valor. Os pesos adotados foram $\\lambda_1=\\lambda_2=10^{-4}$, "
        "$\\lambda_3=10^{-7}$ e $\\lambda_4=10^{-6}$, definidos empiricamente de modo que as "
        "penalizações atuassem principalmente quando o termo de ajuste não fosse capaz de discriminar "
        "entre soluções."
    )
    w.paragraph(
        "A minimização foi realizada com o algoritmo L-BFGS-B (Byrd et al., 1995), um método "
        "quase-Newton de memória limitada que admite limites inferiores e superiores para cada "
        "parâmetro. Os limites, apresentados na Tabela 4.X.1, restringem os parâmetros a valores não "
        "negativos e a ordens de grandeza compatíveis com a escala de tempo dos ensaios. Como a função "
        "objetivo pode apresentar mínimos locais, o problema foi resolvido a partir de seis estimativas "
        "iniciais distintas (Tabela 4.X.2), mantendo-se, ao final, a solução com o menor valor de "
        "$J(\\theta)$. As derivadas da função objetivo foram aproximadas numericamente por diferenças "
        "finitas, e a tolerância de convergência adotada foi de $10^{-10}$."
    )
    w.table(
        "Tabela 4.X.1", "Parâmetros da taxa de retração e limites adotados na otimização",
        ["Parâmetro", "Significado", "Unidade", "Limite inferior", "Limite superior"],
        [
            ["$a_1$", "Amplitude da etapa rápida", "µm/min", "0", "250"],
            ["$b_1$", "Constante de decaimento da etapa rápida", "min⁻¹", "0,2", "8"],
            ["$a_2$", "Amplitude da etapa lenta", "µm/min", "0", "80"],
            ["$b_2$", "Constante de decaimento da etapa lenta", "min⁻¹", "0,02", "4"],
            ["$c$", "Taxa residual", "µm/min", "0", "0,03"],
        ],
        [2.2, 6.2, 2.2, 2.6, 2.6],
    )
    w.table(
        "Tabela 4.X.2", "Estimativas iniciais utilizadas na otimização de cada ensaio",
        ["Estimativa", "$a_1$ (µm/min)", "$b_1$ (min⁻¹)", "$a_2$ (µm/min)", "$b_2$ (min⁻¹)", "$c$ (µm/min)"],
        [
            ["1", "20", "3,0", "4", "0,4", "0"],
            ["2", "50", "5,0", "10", "0,8", "0"],
            ["3", "10", "1,5", "2", "0,2", "0"],
            ["4", "100", "6,0", "15", "1,0", "0"],
            ["5", "35", "4,0", "6", "0,5", "0"],
            ["6", "150", "7,5", "8", "0,3", "0"],
        ],
        [2.4, 2.6, 2.6, 2.6, 2.6, 2.6],
    )
    w.paragraph(
        "Ao final do ajuste, os parâmetros ótimos de cada ensaio foram utilizados para calcular $\\nu$, "
        "$\\delta$ e $X_{\\mathrm{Zn}}$ em dois conjuntos de instantes, que deram origem a duas bases de "
        "dados. A primeira contém apenas os sete instantes experimentais de cada ensaio (112 registros "
        "no total) e foi utilizada para verificar a qualidade da reconstrução das curvas de conversão. "
        "A segunda contém os 60 nós da malha regular (960 registros) e foi utilizada no treinamento da "
        "rede neural. A opção pela malha regular deve-se ao fato de que os instantes experimentais são "
        "poucos e concentrados nos primeiros cinco minutos; com a malha de 0,25 min, a rede recebe "
        "informação sobre a forma completa da curva de $\\nu(t)$, inclusive entre 5 e 15 min. "
        "Ressalta-se, entretanto, que os valores da malha regular não são medições adicionais, mas "
        "resultam da curva ajustada a cada ensaio, de modo que a informação experimental continua "
        "restrita aos sete pontos medidos."
    )
    w.paragraph(
        "Em ambas as bases, cada registro contém a identificação do ensaio, as condições operacionais "
        "($C_{A0}$ e $\\eta$), o tempo, a taxa de retração, a retração acumulada e a conversão "
        "reconstruída, além da conversão experimental, quando disponível. A qualidade da reconstrução "
        "obtida com esse procedimento é apresentada na Seção 5.X."
    )

    # ------------------------------------------------------- base de dados e partição
    w.subheading("Construção da base de dados e partição dos ensaios")
    w.paragraph(
        r"Concluído o problema inverso, os valores estimados de $\nu(t)$ precisaram ser organizados em "
        r"uma base de dados adequada ao treinamento supervisionado da rede neural. Essa etapa envolveu três "
        r"decisões principais: (i) a definição das variáveis de entrada e de saída e da estrutura de cada "
        r"registro; (ii) a divisão dos ensaios entre os conjuntos de treino e de teste, incluindo a "
        r"estratégia de validação cruzada utilizada na escolha da configuração da rede; e (iii) a "
        r"transformação numérica das variáveis antes do treinamento. A Figura 4.X.8 resume a sequência "
        r"adotada, que é detalhada a seguir."
    )
    w.figure(FIG_DIR / "fig_hs_10_fluxo_preparacao.png", 15.0, "Figura 4.X.8",
             "Fluxo de preparação dos dados para o treinamento da rede neural, com destaque para o "
             "isolamento do conjunto de teste cego")
    w.paragraph(
        r"Cada registro da base corresponde a um instante de um ensaio e reúne as condições operacionais "
        r"do ensaio, o tempo de reação e os valores calculados no problema inverso para aquele instante. "
        r"Como a malha regular possui 60 instantes entre 0,25 e 15 min, cada ensaio contribui com 60 "
        r"registros, totalizando 960 registros para os 16 ensaios. A Tabela 4.X.3 apresenta, como "
        r"exemplo, alguns registros do Ensaio 9. Das variáveis armazenadas, apenas $C_{A0}$, $\eta$ e $t$ "
        r"são fornecidas à rede, e $\nu$ é a variável que ela deve aprender a prever; a retração acumulada "
        r"e as conversões são mantidas na base apenas para conferência e para as etapas de avaliação."
    )
    w.table(
        "Tabela 4.X.3", r"Exemplo de registros da base de dados (Ensaio 9, $C_{A0}=1,00$ mol/L e $\eta=1,0$)",
        [r"$t$ (min)", r"$\nu$ (µm/min)", r"$\delta$ (µm)", r"$X_{\mathrm{Zn}}$ reconstruída (–)",
         r"$X_{\mathrm{Zn}}$ experimental (–)"],
        [
            ["0,25", "39,58", "9,89", "0,684", "–"],
            ["0,50", "13,41", "16,52", "0,808", "0,83"],
            ["1,00", "1,633", "19,56", "0,844", "0,84"],
            ["2,00", "0,028", "19,98", "0,848", "0,85"],
            ["5,00", "0,000", "19,99", "0,848", "0,84"],
            ["15,00", "0,000", "19,99", "0,848", "0,85"],
        ],
        [2.4, 3.0, 2.6, 4.0, 4.0],
        source="Fonte: Elaborado pelos autores (2026) a partir de dados de Bortot Coelho (2017)",
    )
    w.paragraph(
        r"Os registros da malha regular foram utilizados no treinamento da rede, enquanto a avaliação "
        r"final do modelo híbrido foi feita apenas nos instantes em que houve medição experimental "
        r"(Seção 4.X). Essa distinção é importante porque os valores da malha regular resultam do ajuste "
        r"do problema inverso: avaliar o modelo sobre eles mediria apenas a concordância com a curva "
        r"ajustada, e não com o experimento."
    )
    w.paragraph(
        r"Como variáveis de entrada, foram adotados a concentração inicial de ácido sulfúrico ($C_{A0}$), "
        r"a razão molar estequiométrica ($\eta$) e o tempo de reação ($t$). As duas primeiras definem as "
        r"condições iniciais de cada ensaio: $C_{A0}$ determina a acidez disponível no início da reação, e "
        r"$\eta$ indica se há ácido suficiente para dissolver todo o ZnO alimentado ($\eta\geq1$) ou se a "
        r"reação será interrompida pelo esgotamento do ácido ($\eta<1$). O tempo, por sua vez, posiciona o "
        r"registro ao longo da curva de cada ensaio. Nota-se que $C_{A0}$ e $\eta$ são constantes dentro de "
        r"um mesmo ensaio, de modo que, embora a base contenha 960 registros, a rede tem acesso a apenas 16 "
        r"combinações distintas de condições operacionais, das quais 13 são usadas no treinamento. Essa "
        r"característica, comum em dados experimentais de processos em batelada, orienta várias das "
        r"decisões descritas a seguir."
    )
    w.paragraph(
        r"A taxa de retração foi tratada como uma função direta das três entradas, "
        r"$\nu=f(C_{A0},\eta,t)$, sem que a rede precisasse acompanhar a evolução do sistema de um instante "
        r"para o outro. Essa formulação é possível porque o acúmulo da retração ao longo do tempo é "
        r"calculado fora da rede, pela integração da Equação (4.X.1), o que dispensa arquiteturas "
        r"recorrentes, que normalmente demandam um volume de dados maior do que o disponível."
    )
    w.paragraph(
        r"A temperatura (40 °C) e a velocidade de agitação (1000 rpm) não foram incluídas como entradas "
        r"porque foram mantidas constantes em todos os ensaios de bancada. Uma variável sem variação não "
        r"carrega informação que permita diferenciar o comportamento dos ensaios e, além disso, teria "
        r"desvio-padrão nulo, o que inviabilizaria a padronização descrita mais adiante. Incluí-las também "
        r"poderia sugerir que o modelo é capaz de representar o efeito dessas variáveis, o que não é "
        r"verdade, já que modelos orientados por dados só são confiáveis dentro da faixa coberta pelos "
        r"dados de treinamento (Venkatasubramanian, 2019). As mesmas três entradas foram utilizadas no "
        r"modelo puramente orientado por dados (Seção 4.X), cuja saída, entretanto, é a própria conversão "
        r"de zinco, e não a taxa de retração."
    )
    w.paragraph(
        r"Para avaliar a capacidade de generalização do modelo, os 16 ensaios foram divididos em um "
        r"conjunto de treino, com 13 ensaios, e um conjunto de teste cego, com 3 ensaios (Ensaios 7, 8 e "
        r"14). Os ensaios de teste não participaram de nenhuma etapa do desenvolvimento: não foram usados no "
        r"ajuste dos pesos, na escolha da configuração da rede nem no cálculo dos parâmetros de "
        r"padronização, sendo consultados uma única vez, ao final, para medir o desempenho do modelo "
        r"treinado (Goodfellow; Bengio; Courville, 2016)."
    )
    w.paragraph(
        r"A divisão foi feita por ensaios inteiros, e não por registros sorteados individualmente. Os "
        r"registros de um mesmo ensaio são fortemente dependentes entre si: compartilham exatamente as "
        r"mesmas condições operacionais e, por estarem separados por apenas 0,25 min, apresentam valores de "
        r"$\nu$ muito próximos. Se os registros fossem sorteados, praticamente todo instante do conjunto de "
        r"teste teria um vizinho quase idêntico no treino, e a rede poderia obter bons resultados apenas "
        r"interpolando entre pontos da mesma curva, sem ter aprendido como $\nu$ varia com as condições "
        r"operacionais. Esse tipo de dependência entre treino e teste é apontado por Kapoor e Narayanan "
        r"(2023) como uma das formas mais frequentes de vazamento de dados (*data leakage*) em aplicações "
        r"de aprendizado de máquina, levando a estimativas de desempenho excessivamente otimistas. Roberts "
        r"et al. (2017) mostram que, em dados com estrutura agrupada, como medições repetidas de uma mesma "
        r"unidade experimental, a separação entre os conjuntos deve respeitar esses grupos. No presente "
        r"caso, o ensaio é a unidade experimental, e a pergunta que o teste deve responder é se o modelo "
        r"consegue prever um ensaio que não viu durante o treinamento."
    )
    w.paragraph(
        r"A proporção adotada, de 13 ensaios para treino e 3 para teste (81,25% e 18,75%), buscou "
        r"equilibrar dois interesses conflitantes. Por um lado, com apenas 16 condições operacionais "
        r"disponíveis, cada ensaio retirado do treino reduz em cerca de 6% a informação disponível para a "
        r"rede aprender a influência de $C_{A0}$ e $\eta$. Por outro, o conjunto de teste precisa conter "
        r"ensaios suficientes para que a avaliação não dependa de uma única condição. A Tabela 4.X.4 "
        r"apresenta a composição final dos conjuntos."
    )
    w.table(
        "Tabela 4.X.4", "Composição dos conjuntos de treino e de teste cego",
        ["Conjunto", "Ensaios", "Proporção dos ensaios", "Registros na malha regular",
         r"Instantes experimentais ($t>0$)"],
        [
            ["Treino", "1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 15 e 16", "81,25%", "780", "91"],
            ["Teste cego", "7, 8 e 14", "18,75%", "180", "21"],
            ["Total", "16 ensaios", "100%", "960", "112"],
        ],
        [2.3, 5.4, 2.6, 2.9, 2.8],
    )
    w.paragraph(
        r"A escolha dos ensaios de teste não foi aleatória. Com um número tão reduzido de ensaios, um "
        r"sorteio poderia, por exemplo, reservar para o teste ensaios de uma mesma região do planejamento ou "
        r"retirar do treino as condições extremas, comprometendo tanto o aprendizado quanto a avaliação. Por "
        r"isso, a seleção seguiu três critérios, ilustrados na Figura 4.X.9(a)."
    )
    w.paragraph(
        r"O primeiro critério foi garantir que a avaliação correspondesse a uma interpolação. Para isso, os "
        r"quatro vértices do planejamento experimental, isto é, as combinações de $C_{A0}$ igual a 0,10 e "
        r"1,50 mol/L com $\eta$ igual a 0,5 e 3,1, foram mantidos no treino. Assim, os ensaios de teste "
        r"estão contidos no domínio coberto pelos dados de treinamento, e a avaliação mede a capacidade do "
        r"modelo de prever condições intermediárias. A capacidade de extrapolação para fora desse domínio é "
        r"uma questão distinta (Sansana et al., 2024), que exigiria retirar do treino justamente as "
        r"condições extremas e que, com apenas 16 ensaios, comprometeria a representatividade do conjunto "
        r"de treino."
    )
    w.paragraph(
        r"O segundo critério foi a diversidade de condições. Os ensaios de teste cobrem três situações "
        r"diferentes de disponibilidade de ácido: o Ensaio 8 é estequiométrico ($\eta=1,0$), o Ensaio 14 "
        r"opera com excesso moderado de ácido ($\eta=1,5$) e o Ensaio 7, com grande excesso ($\eta=3,1$), "
        r"distribuídos entre as concentrações de 0,50 e 1,00 mol/L. Dessa forma, a avaliação não fica "
        r"concentrada em um único regime de operação."
    )
    w.paragraph(
        r"O terceiro critério foi a preservação, no treino, dos quatro ensaios com deficiência de ácido "
        r"($\eta=0,5$). Nesses ensaios, a reação é interrompida pelo esgotamento do ácido quando metade do "
        r"ZnO foi dissolvida, comportamento que não ocorre nos demais. Caso algum deles fosse retirado do "
        r"treino, a rede teria menos exemplos dessa situação para aprender. Por fim, os mesmos três ensaios "
        r"foram adotados como teste no modelo puramente orientado por dados e na PINN, de modo que as "
        r"diferentes abordagens deste trabalho são comparadas exatamente nas mesmas condições."
    )
    w.paragraph(
        r"Além do conjunto de teste, foi necessário um mecanismo para escolher a configuração da rede, "
        r"como o número de camadas e de neurônios (Seção 4.X), e para decidir quando interromper o "
        r"treinamento. Essas escolhas não podem ser feitas com base no conjunto de teste, pois, nesse caso, o "
        r"teste deixaria de ser independente e passaria a influenciar o próprio modelo que deveria avaliar "
        r"(Hastie; Tibshirani; Friedman, 2009). Por isso, utilizou-se a validação cruzada em $k$ dobras "
        r"dentro do conjunto de treino. Nesse procedimento, os dados de treino são divididos em $k$ partes; "
        r"em cada rodada, uma delas é reservada para validação e as demais são usadas no ajuste, "
        r"repetindo-se o processo até que todas as partes tenham sido usadas uma vez como validação. O "
        r"desempenho médio nas $k$ rodadas fornece uma estimativa mais estável do que a obtida com uma "
        r"única divisão, o que é particularmente importante quando há poucos dados (Hastie; Tibshirani; "
        r"Friedman, 2009)."
    )
    w.paragraph(
        r"Pelo mesmo motivo discutido para o conjunto de teste, as dobras também foram formadas por ensaios "
        r"inteiros (validação cruzada agrupada, ou *GroupKFold*). Adotaram-se quatro dobras, de modo que "
        r"cada uma reserva três ou quatro ensaios para validação, o que corresponde a cerca de 25% dos dados "
        r"de treino. Um número maior de dobras deixaria cada validação com apenas um ou dois ensaios, "
        r"tornando-a muito dependente de condições particulares, enquanto um número menor reduziria a "
        r"quantidade de ensaios disponíveis para o ajuste em cada rodada. A composição das dobras, definida "
        r"automaticamente pelo algoritmo, é apresentada na Tabela 4.X.5 e na Figura 4.X.9(b). Observa-se que "
        r"a primeira dobra reúne três vértices do planejamento (Ensaios 1, 5 e 16), de modo que sua "
        r"validação envolve condições na borda do domínio; isso tende a tornar a estimativa obtida na "
        r"validação cruzada mais conservadora do que a do teste cego, que avalia apenas condições internas."
    )
    w.table(
        "Tabela 4.X.5", "Composição das dobras da validação cruzada por ensaio",
        ["Dobra", "Ensaios de validação", "Ensaios de ajuste", "Registros de ajuste", "Registros de validação"],
        [
            ["1", "1, 5, 11 e 16", "9", "540", "240"],
            ["2", "4, 10 e 15", "10", "600", "180"],
            ["3", "3, 9 e 13", "10", "600", "180"],
            ["4", "2, 6 e 12", "10", "600", "180"],
        ],
        [2.0, 4.6, 3.0, 3.2, 3.2],
    )
    w.figure(FIG_DIR / "fig_hs_08_particao_dobras.png", 16.0, "Figura 4.X.9",
             "Partição dos ensaios: (a) ensaios de treino e de teste cego no planejamento experimental; "
             "(b) composição das dobras da validação cruzada por ensaio")
    w.paragraph(
        r"Quanto à transformação das variáveis, as três entradas possuem escalas bastante diferentes: "
        r"$C_{A0}$ varia entre 0,10 e 1,50 mol/L, $\eta$ entre 0,5 e 3,1 e o tempo entre 0,25 e 15 min. Em "
        r"redes neurais treinadas por gradiente, entradas com escalas muito diferentes fazem com que os pesos "
        r"associados a cada variável sejam ajustados em ritmos distintos, o que torna o treinamento mais "
        r"lento e instável (LeCun et al., 1998; Hastie; Tibshirani; Friedman, 2009). Por isso, as entradas "
        r"foram padronizadas pelo escore Z:"
    )
    w.equation(r"\tilde{x}_{j}=\frac{x_{j}-\mu_{j}}{\sigma_{j}}", "4.X.9")
    w.paragraph(
        r"Em que $x_j$ é o valor original da variável de entrada $j$, $\tilde{x}_j$ é o valor padronizado "
        r"e $\mu_j$ e $\sigma_j$ são a média e o desvio-padrão dessa variável no conjunto de treino. Após a "
        r"transformação, as três entradas passam a ter média nula e desvio-padrão unitário no treino. Os "
        r"valores utilizados são apresentados na Tabela 4.X.6."
    )
    w.table(
        "Tabela 4.X.6", "Parâmetros da padronização das entradas, calculados com os 13 ensaios de treino",
        ["Variável", "Faixa no planejamento", r"Média, $\mu_j$", r"Desvio-padrão, $\sigma_j$"],
        [
            [r"$C_{A0}$ (mol/L)", "0,10 a 1,50", "0,800", "0,570"],
            [r"$\eta$ (–)", "0,5 a 3,1", "1,446", "0,976"],
            [r"$t$ (min)", "0,25 a 15,0", "7,625", "4,330"],
        ],
        [3.6, 4.2, 3.6, 3.6],
    )
    w.paragraph(
        r"Optou-se pela padronização, e não pela normalização Min-Max empregada no modelo puramente "
        r"orientado por dados (Seção 4.X), porque as funções de ativação adotadas nas camadas ocultas da "
        r"rede (Seção 4.X) concentram seu comportamento não linear em torno de zero; entradas centradas em "
        r"zero e com dispersão unitária mantêm os neurônios nessa faixa no início do treinamento (LeCun et "
        r"al., 1998). Ambas as técnicas, no entanto, cumprem o mesmo papel de equilibrar a influência das "
        r"variáveis sobre o ajuste (Bishop, 2006)."
    )
    w.paragraph(
        r"Os parâmetros $\mu_j$ e $\sigma_j$ foram calculados apenas com os registros de treino e aplicados, "
        r"sem recálculo, aos registros de teste. Se o conjunto de teste participasse desse cálculo, "
        r"informações sobre as condições de teste seriam incorporadas ao pré-processamento antes mesmo do "
        r"treinamento, constituindo outra forma de vazamento de dados (Kapoor; Narayanan, 2023; Hastie; "
        r"Tibshirani; Friedman, 2009). Por simplicidade, os mesmos valores foram utilizados nas quatro dobras "
        r"da validação cruzada, de modo que os ensaios de validação de cada dobra participaram do cálculo de "
        r"$\mu_j$ e $\sigma_j$. Trata-se de uma simplificação em relação ao procedimento ideal, que envolve "
        r"apenas as estatísticas das entradas, e não a variável de saída, e que não afeta o conjunto de teste "
        r"cego, mantido completamente isolado."
    )
    w.paragraph(
        r"A variável de saída exigiu um tratamento diferente. A Figura 4.X.10(a) mostra que a distribuição de "
        r"$\nu$ nos registros de treino é fortemente assimétrica: os valores variam de 0 a cerca de 94 "
        r"µm/min, mas 64% dos registros apresentam $\nu$ inferior a 0,1 µm/min e apenas 44 registros (5,6%) "
        r"superam 10 µm/min. Isso ocorre porque a dissolução se concentra nos primeiros instantes de cada "
        r"ensaio, enquanto a maior parte da malha temporal corresponde à etapa final, em que a conversão já "
        r"está próxima do patamar e a taxa de retração é praticamente nula."
    )
    w.paragraph(
        r"Se a rede fosse treinada diretamente com esses valores, utilizando o erro quadrático médio como "
        r"função de perda, os poucos registros com taxa elevada dominariam o ajuste: um erro de 10% em "
        r"$\nu=90$ µm/min equivale a 9 µm/min, enquanto um erro de 100% em $\nu=0,05$ µm/min corresponde a "
        r"apenas 0,05 µm/min. Na prática, a rede seria incentivada a reproduzir bem o início das curvas e a "
        r"negligenciar a etapa lenta, justamente a que define a aproximação ao patamar final de conversão. "
        r"Para equilibrar a contribuição das duas etapas, a saída foi transformada por:"
    )
    w.equation(r"y=\ln(1+\nu)", "4.X.10")
    w.paragraph(
        r"Transformações logarítmicas são usadas com frequência para reduzir a assimetria e a amplitude de "
        r"variáveis positivas que se estendem por várias ordens de grandeza (Box; Cox, 1964). A forma "
        r"$\ln(1+\nu)$ foi preferida ao logaritmo simples porque é definida para $\nu=0$, valor presente em "
        r"126 registros de treino. Além disso, ela se comporta de maneira distinta nas duas extremidades da "
        r"faixa: para taxas pequenas, $\ln(1+\nu)\approx\nu$, e os erros são tratados praticamente na escala "
        r"original; para taxas elevadas, uma diferença em $y$ corresponde aproximadamente a uma diferença "
        r"relativa em $\nu$, de modo que, na etapa rápida, a função de perda passa a ponderar erros "
        r"relativos. Com isso, a faixa da saída foi comprimida de 0 a 94 µm/min para 0 a 4,55 (Figura "
        r"4.X.10b). Nota-se que a transformação não elimina a concentração de registros próximos de zero, que "
        r"é uma característica física do processo, mas reduz o peso desproporcional dos valores elevados."
    )
    w.paragraph(
        r"A rede é treinada para prever $y$, e a taxa de retração é recuperada pela operação inversa, "
        r"$\nu=e^{y}-1$, aplicada na própria camada de saída da rede, conforme descrito na seção seguinte."
    )
    w.figure(FIG_DIR / "fig_hs_09_distribuicao_alvo.png", 15.0, "Figura 4.X.10",
             "Distribuição da taxa de retração nos registros de treino: (a) na escala original; (b) após "
             "a transformação logarítmica")

    # ---------------------------------------------------------------- arquitetura da rede
    w.subheading("Arquitetura da rede neural")
    w.paragraph(
        r"A relação entre as condições do ensaio e a taxa de retração, $\nu=f(C_{A0},\eta,t)$, foi "
        r"aproximada por uma rede neural do tipo perceptron multicamadas (*multilayer perceptron*, MLP). "
        r"Nesse tipo de rede, a informação percorre uma sequência de camadas, e cada camada aplica aos "
        r"valores recebidos uma transformação linear seguida de uma função não linear, de modo que a "
        r"composição de várias camadas é capaz de representar relações complexas entre as variáveis "
        r"(Goodfellow; Bengio; Courville, 2016; Bishop, 2006). No modelo híbrido, a rede tem uma tarefa "
        r"restrita: ela não prevê a conversão, mas apenas a taxa de retração em cada instante, que é "
        r"depois integrada e convertida em $X_{Zn}$ pelo modelo fenomenológico. A Figura 4.X.11 apresenta "
        r"a arquitetura adotada, cujos elementos são descritos a seguir, na ordem em que a informação os "
        r"percorre."
    )
    w.figure(FIG_DIR / "fig_hs_11_arquitetura_mlp.png", 16.0, "Figura 4.X.11",
             "Arquitetura da rede neural que prevê a taxa de retração: entrada temporal em ln t, três "
             "blocos residuais e camada de saída não negativa, com o detalhe de um bloco residual")
    w.paragraph(
        r"A rede recebe as três entradas padronizadas pela Equação 4.X.9, $\tilde{C}_{A0}$, $\tilde{\eta}$ "
        r"e $\tilde{t}$. Antes da primeira camada, porém, o tempo passa por uma transformação adicional: "
        r"o valor padronizado é convertido de volta em minutos, $t=\mu_t+\sigma_t\,\tilde{t}$, e "
        r"substituído pelo seu logaritmo, novamente padronizado:"
    )
    w.equation(r"\tilde{\tau}=\frac{\ln t-m_{\tau}}{s_{\tau}}", "4.X.11")
    w.paragraph(
        r"Em que $m_{\tau}=1,758$ e $s_{\tau}=0,893$ são a média e o desvio-padrão de $\ln t$ nos 60 nós "
        r"da malha temporal de 0,25 a 15 min (Figura 4.X.7). Assim, a entrada efetiva da primeira camada "
        r"passa a ser o vetor $\mathbf{h}_0=[\tilde{C}_{A0},\ \tilde{\eta},\ \tilde{\tau}]$."
    )
    w.paragraph(
        r"A justificativa dessa transformação está na forma das curvas de $\nu(t)$. Como discutido na "
        r"seção anterior, a taxa de retração cai várias ordens de grandeza nos primeiros minutos de cada "
        r"ensaio e permanece próxima de zero no restante da batelada. Na escala linear, o intervalo de 0,25 "
        r"a 2 min, no qual a maior parte da conversão acontece, ocupa apenas 12% da faixa da variável "
        r"tempo; na escala logarítmica, o mesmo intervalo passa a ocupar cerca de 51% dessa faixa. Com isso, "
        r"a rede dispõe de mais resolução justamente nos instantes em que $\nu$ é elevada e define o avanço "
        r"de $\delta$, e de menos resolução no trecho final, em que a taxa varia pouco. A operação é feita "
        r"dentro da própria rede e é diferenciável, de modo que a interface com o restante do modelo "
        r"híbrido não se altera: as entradas continuam sendo as variáveis padronizadas da Tabela 4.X.6. O "
        r"uso de $t$ ou de $\ln t$ foi tratado como uma das opções da busca de hiperparâmetros (Seção 4.X), "
        r"e a entrada em $\ln t$ foi a adotada na configuração final."
    )
    w.paragraph(
        r"As camadas ocultas foram organizadas em três blocos residuais, com 90, 45 e 22 neurônios, "
        r"respectivamente. A largura decrescente, em que cada bloco tem aproximadamente a metade dos "
        r"neurônios do anterior, faz com que a rede extraia inicialmente um grande número de combinações "
        r"das entradas e, em seguida, as condense progressivamente até a única variável de saída. Cada "
        r"bloco $l$ recebe o vetor $\mathbf{h}_{l-1}$, produzido pelo bloco anterior, e calcula:"
    )
    w.equation(r"\mathbf{h}_{l}=\mathbf{P}_{l}\,\mathbf{h}_{l-1}+\alpha_{l}\,\mathbf{F}_{l}(\mathbf{h}_{l-1})",
               "4.X.12")
    w.equation(r"\mathbf{F}_{l}(\mathbf{h}_{l-1})=\mathbf{W}_{l,2}\,\mathrm{D}\!\left[\phi\left(\mathbf{W}_{l,1}"
               r"\,\mathbf{h}_{l-1}+\mathbf{b}_{l,1}\right)\right]+\mathbf{b}_{l,2}", "4.X.13")
    w.paragraph(
        r"Em que $\mathbf{W}_{l,1}$, $\mathbf{W}_{l,2}$, $\mathbf{b}_{l,1}$ e $\mathbf{b}_{l,2}$ são as "
        r"matrizes de pesos e os vetores de viés das duas camadas lineares do bloco, $\phi$ é a função de "
        r"ativação, $\mathrm{D}$ representa a operação de *dropout*, descrita adiante, $\mathbf{P}_l$ é uma "
        r"matriz de projeção e $\alpha_l$ é um escalar que pondera a contribuição do ramo não linear. Os "
        r"três conjuntos de parâmetros são ajustados durante o treinamento, e $\alpha_l$ é iniciado em "
        r"0,25."
    )
    w.paragraph(
        r"O vetor de saída de cada bloco é, portanto, a soma de dois caminhos, ilustrados na parte "
        r"inferior da Figura 4.X.11. O primeiro, chamado de atalho ou conexão residual, leva a informação "
        r"de entrada diretamente à saída do bloco por meio de uma transformação apenas linear; como os "
        r"blocos mudam a dimensão do vetor (de 3 para 90, de 90 para 45 e de 45 para 22), essa "
        r"transformação é feita por uma projeção $\mathbf{P}_l$ sem viés. O segundo caminho, o ramo não "
        r"linear $\mathbf{F}_l$, calcula uma correção sobre essa projeção. Conexões desse tipo foram "
        r"propostas para facilitar o treinamento de redes com várias camadas, pois o atalho oferece ao "
        r"gradiente um caminho direto até as primeiras camadas e permite que cada bloco aprenda apenas o "
        r"que falta à transformação linear, em vez de reconstruí-la por completo (He et al., 2016). O valor "
        r"inicial reduzido de $\alpha_l$ faz com que, no início do treinamento, a rede se comporte de forma "
        r"próxima a uma sequência de projeções lineares, e a parcela não linear cresça à medida que se "
        r"mostra necessária. A presença ou não das conexões residuais também foi uma das opções avaliadas "
        r"na busca de hiperparâmetros (Seção 4.X)."
    )
    w.paragraph(
        r"Como função de ativação $\phi$, adotou-se a GELU (*Gaussian Error Linear Unit*), definida por "
        r"(Hendrycks; Gimpel, 2016):"
    )
    w.equation(r"\phi(z)=z\,\Phi(z)", "4.X.14")
    w.paragraph(
        r"Em que $\Phi(z)$ é a função de distribuição acumulada da distribuição normal padrão. A Figura "
        r"4.X.12(a) compara a GELU com a ReLU (*Rectified Linear Unit*), $\max(0,z)$, uma das ativações "
        r"mais empregadas em redes neurais. As duas têm comportamento semelhante para valores de $z$ "
        r"afastados de zero, mas a GELU é suave em toda a sua extensão, enquanto a ReLU apresenta uma "
        r"quina em $z=0$, onde sua derivada muda bruscamente de 0 para 1. A escolha de uma ativação suave "
        r"é coerente com a natureza do problema: a rede deve representar uma taxa que varia de forma "
        r"contínua com o tempo e com as condições do ensaio e que, depois, é integrada pelo modelo "
        r"fenomenológico. Com uma ativação suave, a função representada pela rede e todas as suas "
        r"derivadas em relação às entradas também são contínuas, o que evita trechos com variações "
        r"abruptas de $\nu$ e mantém aberta a possibilidade de impor, no futuro, restrições sobre essas "
        r"derivadas, como a de que $\nu$ não aumente ao longo do tempo."
    )
    w.paragraph(
        r"Durante o treinamento, aplicou-se ainda o *dropout* no ramo não linear de cada bloco, logo após a "
        r"ativação. Nessa técnica, a cada passo do treinamento, cada neurônio tem sua saída anulada com "
        r"probabilidade $p$, e as saídas restantes são multiplicadas por $1/(1-p)$ para manter a mesma "
        r"escala média. Como os neurônios desligados mudam a cada passo, a rede é impedida de depender de "
        r"combinações muito específicas entre eles, o que funciona como uma forma de regularização e reduz "
        r"o risco de sobreajuste (Srivastava et al., 2014). Na previsão, todos os neurônios permanecem "
        r"ativos. Adotou-se $p=0,125$, valor definido pela busca de hiperparâmetros. Essa regularização é "
        r"particularmente relevante neste trabalho, em que o treino reúne apenas 13 ensaios."
    )
    w.paragraph(
        r"Por fim, a camada de saída combina linearmente os 22 valores do último bloco em um único número, "
        r"$z=\mathbf{w}_{o}^{\top}\mathbf{h}_{3}+b_{o}$, que é transformado pela função *softplus*:"
    )
    w.equation(r"\hat{y}=\ln\left(1+e^{z}\right)", "4.X.15")
    w.paragraph(
        r"Em que $\hat{y}$ é a previsão da rede para a variável transformada $y=\ln(1+\nu)$ da Equação "
        r"4.X.10. A taxa de retração é então recuperada pela operação inversa:"
    )
    w.equation(r"\hat{\nu}=e^{\hat{y}}-1", "4.X.16")
    w.paragraph(
        r"Essa combinação foi escolhida para garantir, por construção, que a taxa prevista nunca seja "
        r"negativa. Fisicamente, a taxa de retração não pode ser negativa, pois isso corresponderia ao "
        r"crescimento das partículas e a uma diminuição da conversão ao longo do tempo. Como a função "
        r"*softplus* só assume valores positivos, tem-se $\hat{y}>0$ e, consequentemente, $\hat{\nu}>0$ "
        r"para qualquer combinação de entradas, inclusive em condições fora das ensaiadas. Substituindo a "
        r"Equação 4.X.15 na Equação 4.X.16, verifica-se que o conjunto equivale a $\hat{\nu}=e^{z}$, ou "
        r"seja, a saída linear da rede passa a representar o logaritmo da taxa. A Figura 4.X.12(b) ilustra "
        r"esse comportamento: para valores negativos de $z$, a taxa se aproxima de zero sem nunca se "
        r"anular, o que permite representar a etapa final dos ensaios, em que $\nu$ é muito pequena, e, "
        r"para valores positivos, a taxa cresce rapidamente, cobrindo a etapa inicial, em que $\nu$ chega "
        r"a cerca de 90 µm/min. A rede é treinada na escala de $\hat{y}$, que é a mesma da variável de "
        r"saída transformada, e a conversão para $\hat{\nu}$ ocorre apenas quando a taxa é enviada ao "
        r"modelo fenomenológico."
    )
    w.figure(FIG_DIR / "fig_hs_12_funcoes_rede.png", 16.0, "Figura 4.X.12",
             "Funções empregadas na rede: (a) ativação GELU das camadas ocultas, comparada à ReLU; (b) "
             "função softplus da camada de saída e taxa de retração resultante")
    w.paragraph(
        r"A Tabela 4.X.7 resume a arquitetura e o número de parâmetros ajustáveis de cada parte da rede, "
        r"que somam 21.569. Esse número é superior ao de registros de treino (780), situação comum em redes "
        r"neurais, mas que exige cuidado com o sobreajuste. Por esse motivo, além do *dropout*, foram "
        r"empregadas a penalização dos pesos durante a otimização, descrita na próxima seção, e a média de "
        r"várias redes treinadas de forma independente (Seção 4.X), e a capacidade de generalização foi "
        r"sempre avaliada em ensaios não utilizados no ajuste (Seção 4.X). A rede foi implementada com a "
        r"biblioteca PyTorch (Paszke et al., 2019)."
    )
    w.table(
        "Tabela 4.X.7", "Arquitetura da rede neural e número de parâmetros ajustáveis",
        ["Parte da rede", "Elementos", "Dimensão", "Parâmetros"],
        [
            ["Transformação temporal", r"$t\rightarrow\tilde{\tau}$ (Eq. 4.X.11)", "3 → 3", "0"],
            ["Bloco residual 1", r"$\mathbf{W}_{1,1}$, $\mathbf{W}_{1,2}$, $\mathbf{P}_{1}$, $\alpha_{1}$", "3 → 90", "8.821"],
            ["Bloco residual 2", r"$\mathbf{W}_{2,1}$, $\mathbf{W}_{2,2}$, $\mathbf{P}_{2}$, $\alpha_{2}$", "90 → 45", "10.216"],
            ["Bloco residual 3", r"$\mathbf{W}_{3,1}$, $\mathbf{W}_{3,2}$, $\mathbf{P}_{3}$, $\alpha_{3}$", "45 → 22", "2.509"],
            ["Camada de saída", r"$\mathbf{w}_{o}$, $b_{o}$ e softplus", "22 → 1", "23"],
            ["Total", "", "", "21.569"],
        ],
        [4.0, 6.0, 2.8, 2.8],
    )

    # ---------------------------------------------------------------- perda e treinamento
    w.subheading("Função de perda e algoritmo de treinamento")
    w.paragraph(
        r"O treinamento consiste em ajustar o conjunto $\boldsymbol{\theta}$ de todos os parâmetros da "
        r"rede (pesos, vieses, matrizes de projeção e coeficientes $\alpha_l$) de modo que as previsões "
        r"$\hat{y}$ se aproximem dos valores-alvo $y=\ln(1+\nu)$ obtidos no problema inverso. Como medida "
        r"da discrepância, adotou-se o erro quadrático médio na escala transformada:"
    )
    w.equation(r"\mathcal{L}(\boldsymbol{\theta})=\frac{1}{B}\sum_{i=1}^{B}{\left[\hat{y}_{i}(\boldsymbol{\theta})"
               r"-y_{i}\right]^{2}}", "4.X.17")
    w.paragraph(
        r"Em que $B$ é o número de registros considerados no cálculo e $\hat{y}_i$ e $y_i$ são, "
        r"respectivamente, a previsão da rede e o valor-alvo do registro $i$. Por ser calculado sobre "
        r"$y=\ln(1+\nu)$, e não sobre $\nu$, esse erro tem as propriedades discutidas na construção da base "
        r"de dados: na etapa rápida dos ensaios, ele pondera diferenças relativas da taxa, e, na etapa "
        r"lenta, diferenças praticamente absolutas, evitando que os poucos registros com taxa elevada "
        r"dominem o ajuste. Todos os registros receberam o mesmo peso."
    )
    w.paragraph(
        r"A minimização foi feita por descida de gradiente em mini-lotes (*mini-batches*). Em vez de "
        r"calcular a perda com todos os registros de treino a cada passo, os registros são embaralhados no "
        r"início de cada época, isto é, de cada passagem completa pelo conjunto de treino, e divididos em "
        r"lotes de $B=16$ registros. Para cada lote, calcula-se a perda da Equação 4.X.17, obtêm-se as "
        r"derivadas da perda em relação a todos os parâmetros por retropropagação (*backpropagation*) e "
        r"atualizam-se os parâmetros. Com os 780 registros de treino, cada época compreende 49 lotes e, "
        r"portanto, 49 atualizações. O uso de lotes pequenos aumenta o número de atualizações por época, "
        r"e a variação aleatória do gradiente entre os lotes tende a favorecer soluções que generalizam "
        r"melhor (Goodfellow; Bengio; Courville, 2016). O ciclo completo está representado na Figura "
        r"4.X.13(a)."
    )
    w.figure(FIG_DIR / "fig_hs_13_treinamento_mlp.png", 16.0, "Figura 4.X.13",
             "Treinamento da rede: (a) ciclo de treinamento por mini-lotes; (b) redução da taxa de "
             "aprendizado ao longo das épocas")
    w.paragraph(
        r"A atualização dos parâmetros seguiu o algoritmo AdamW (Loshchilov; Hutter, 2019), uma variação "
        r"do algoritmo Adam (Kingma; Ba, 2017). No Adam, o passo dado em cada parâmetro é ajustado de "
        r"acordo com o histórico dos gradientes: em cada atualização $k$, são calculadas médias móveis do "
        r"gradiente, $\mathbf{g}_k=\partial\mathcal{L}/\partial\boldsymbol{\theta}$, e do seu quadrado:"
    )
    w.equation(r"\mathbf{m}_{k}=\beta_{1}\,\mathbf{m}_{k-1}+(1-\beta_{1})\,\mathbf{g}_{k}", "4.X.18")
    w.equation(r"\mathbf{v}_{k}=\beta_{2}\,\mathbf{v}_{k-1}+(1-\beta_{2})\,\mathbf{g}_{k}^{2}", "4.X.19")
    w.paragraph(
        r"Em que $\beta_1=0,9$ e $\beta_2=0,999$ controlam a memória das médias. Após a correção do viés "
        r"inicial dessas médias, $\hat{\mathbf{m}}_k=\mathbf{m}_k/(1-\beta_1^{k})$ e "
        r"$\hat{\mathbf{v}}_k=\mathbf{v}_k/(1-\beta_2^{k})$, os parâmetros são atualizados por:"
    )
    w.equation(r"\boldsymbol{\theta}_{k}=\boldsymbol{\theta}_{k-1}-\gamma_{e}\left(\frac{\hat{\mathbf{m}}_{k}}"
               r"{\sqrt{\hat{\mathbf{v}}_{k}}+\epsilon}+\lambda_{w}\,\boldsymbol{\theta}_{k-1}\right)", "4.X.20")
    w.paragraph(
        r"Em que $\gamma_e$ é a taxa de aprendizado na época $e$, $\epsilon=10^{-8}$ evita divisões por "
        r"zero e $\lambda_w$ é o coeficiente de penalização dos pesos (*weight decay*). A divisão por "
        r"$\sqrt{\hat{\mathbf{v}}_k}$ faz com que parâmetros com gradientes grandes e instáveis recebam "
        r"passos menores e parâmetros com gradientes pequenos recebam passos relativamente maiores, o que "
        r"torna o método pouco sensível às diferenças de escala entre os parâmetros. O último termo da "
        r"Equação 4.X.20 reduz, a cada passo, uma pequena fração de todos os parâmetros, puxando-os em "
        r"direção a zero; com isso, a rede é desestimulada a usar pesos muito grandes, que costumam estar "
        r"associados a funções com oscilações e a sobreajuste. A diferença do AdamW em relação ao Adam "
        r"original está justamente nesse termo: no Adam, a penalização é somada ao gradiente e, portanto, "
        r"também dividida por $\sqrt{\hat{\mathbf{v}}_k}$, o que enfraquece seu efeito justamente nos "
        r"parâmetros com gradientes maiores; no AdamW, ela é aplicada diretamente aos parâmetros, de forma "
        r"desacoplada do gradiente, o que preserva o seu papel de regularização (Loshchilov; Hutter, 2019). "
        r"Adotou-se $\lambda_w=1,02\times10^{-3}$."
    )
    w.paragraph(
        r"A taxa de aprendizado não foi mantida constante. Ela foi reduzida ao longo das épocas segundo uma "
        r"curva cossenoidal (Loshchilov; Hutter, 2017):"
    )
    w.equation(r"\gamma_{e}=\gamma_{min}+\frac{1}{2}\left(\gamma_{0}-\gamma_{min}\right)"
               r"\left[1+\cos\left(\frac{\pi\,e}{E}\right)\right]", "4.X.21")
    w.paragraph(
        r"Em que $\gamma_0=4,08\times10^{-3}$ é a taxa inicial, $\gamma_{min}=10^{-5}$ é a taxa final e "
        r"$E$ é o número total de épocas. Como mostra a Figura 4.X.13(b), a taxa permanece elevada nas "
        r"primeiras épocas, quando os parâmetros ainda estão distantes de uma boa solução e passos grandes "
        r"aceleram o ajuste, e diminui gradualmente até um valor muito pequeno nas últimas épocas, quando "
        r"passos pequenos permitem refinar a solução e reduzem a oscilação da perda causada pela "
        r"variação entre os mini-lotes."
    )
    w.paragraph(
        r"Restava definir por quantas épocas treinar. Treinar por poucas épocas deixa a rede incapaz de "
        r"reproduzir os dados, enquanto treinar por épocas demais pode levá-la a memorizar particularidades "
        r"dos ensaios de treino, prejudicando a previsão em condições novas. Foram consideradas duas "
        r"estratégias para essa decisão. Na primeira, a parada antecipada (*early stopping*), dois ensaios "
        r"do próprio conjunto de ajuste são separados para acompanhamento, e o treinamento é interrompido "
        r"quando o erro nesses ensaios deixa de diminuir por um número predefinido de épocas, recuperando-se "
        r"os parâmetros da melhor época (Goodfellow; Bengio; Courville, 2016). Para não forçar a rede a "
        r"extrapolar, os quatro vértices do planejamento (Ensaios 1, 2, 5 e 16) nunca foram usados como "
        r"ensaios de acompanhamento. Na segunda estratégia, todos os ensaios disponíveis são usados no "
        r"ajuste, e o número de épocas $E$ é fixado de antemão, sendo tratado como mais um hiperparâmetro, "
        r"escolhido pela validação cruzada como os demais (Seção 4.X). A primeira estratégia tem a vantagem "
        r"de adaptar a duração do treinamento a cada caso, mas, com apenas 13 ensaios, reservar dois deles "
        r"significa retirar do ajuste cerca de 15% das condições experimentais; a segunda aproveita todos os "
        r"ensaios, mas depende de uma boa escolha de $E$. A escolha entre as duas estratégias fez parte da "
        r"busca de hiperparâmetros, e a configuração final adotou a segunda, com $E=928$ épocas, o que "
        r"corresponde a 45.472 atualizações dos parâmetros."
    )
    w.paragraph(
        r"Por fim, o resultado do treinamento depende de elementos aleatórios: os valores iniciais dos "
        r"parâmetros, sorteados pela inicialização padrão da biblioteca, a ordem dos registros em cada "
        r"época e os neurônios desligados pelo *dropout*. Para que os resultados fossem reprodutíveis, "
        r"esses sorteios foram controlados por uma semente numérica fixa. Redes treinadas com sementes "
        r"diferentes, contudo, chegam a soluções ligeiramente distintas, e essa variabilidade foi levada em "
        r"conta tanto na escolha da configuração, que utilizou várias sementes, quanto no modelo final, "
        r"formado pela média de dez redes (Seção 4.X). Com a configuração adotada, o treinamento de cada "
        r"rede levou cerca de 75 s em um processador comum. A Tabela 4.X.8 reúne os valores utilizados no "
        r"treinamento."
    )
    w.table(
        "Tabela 4.X.8", "Parâmetros do treinamento da rede neural na configuração final",
        ["Elemento", "Valor adotado"],
        [
            ["Função de perda", r"erro quadrático médio em $y=\ln(1+\nu)$ (Eq. 4.X.17)"],
            ["Registros de treino", "780 (13 ensaios, malha de 0,25 min)"],
            ["Tamanho do lote, $B$", "16 registros (49 lotes por época)"],
            ["Otimizador", r"AdamW, com $\beta_1=0,9$, $\beta_2=0,999$ e $\epsilon=10^{-8}$"],
            [r"Taxa de aprendizado inicial, $\gamma_0$", r"$4,08\times10^{-3}$"],
            [r"Taxa de aprendizado final, $\gamma_{min}$", r"$10^{-5}$ (redução cossenoidal, Eq. 4.X.21)"],
            [r"Penalização dos pesos, $\lambda_w$", r"$1,02\times10^{-3}$"],
            [r"Probabilidade de *dropout*, $p$", "0,125"],
            [r"Número de épocas, $E$", "928 (fixo, sem parada antecipada)"],
            ["Sementes", "42 a 51 (uma por rede do modelo final)"],
        ],
        [6.5, 9.1],
    )

    # ---------------------------------------------------------------- critério de avaliação
    w.subheading("Critério de avaliação das configurações da rede")
    w.paragraph(
        r"Os valores apresentados nas Tabelas 4.X.7 e 4.X.8 não são ajustados durante o treinamento, como os "
        r"pesos da rede, mas definidos antes dele. São os chamados hiperparâmetros: o número de camadas e de "
        r"neurônios, a função de ativação, o uso de conexões residuais, a probabilidade de *dropout*, a taxa "
        r"de aprendizado, a penalização dos pesos, o tamanho do lote e o número de épocas, entre outros. "
        r"Cada combinação desses valores constitui uma configuração da rede, e configurações diferentes "
        r"levam a modelos com capacidades de generalização diferentes. Para escolher entre elas, foi "
        r"necessário definir um critério de avaliação, calculado apenas com os 13 ensaios de treino, por "
        r"meio da validação cruzada por ensaio apresentada na Tabela 4.X.5. O conjunto de teste cego não foi "
        r"utilizado em nenhum momento dessa escolha."
    )
    w.paragraph(
        r"A primeira decisão foi a grandeza a ser avaliada. Como a rede é treinada para prever a taxa de "
        r"retração, uma opção imediata seria medir a qualidade da previsão de $\nu$ nos ensaios de "
        r"validação, por exemplo pelo coeficiente de determinação. Essa medida, contudo, não reflete "
        r"diretamente o desempenho do modelo híbrido, cuja variável de interesse é a conversão. Como a "
        r"retração acumulada é a integral da taxa (Equação 4.X.1), um erro em $\nu$ nos primeiros instantes "
        r"se acumula em $\delta$ e permanece na conversão até o fim do ensaio, enquanto um erro da mesma "
        r"ordem na etapa final, quando a conversão já se aproxima do patamar, tem efeito pequeno. Além disso, "
        r"o coeficiente de determinação de $\nu$ é dominado pelos poucos registros com taxa elevada. Assim, "
        r"uma configuração pode apresentar boa previsão de $\nu$ e, ainda assim, gerar curvas de conversão "
        r"insatisfatórias, e o contrário também pode ocorrer."
    )
    w.paragraph(
        r"Por esse motivo, adotou-se como critério o erro na própria conversão de zinco. Para cada "
        r"configuração candidata e cada dobra $k$, a rede é treinada com os ensaios de ajuste da dobra, a "
        r"taxa prevista para os ensaios de validação é acoplada ao modelo fenomenológico, exatamente como no "
        r"uso final do modelo (Seção 4.X), e a conversão resultante é comparada com a conversão medida nos "
        r"sete instantes experimentais de cada ensaio. Ao final das quatro dobras, cada um dos 13 ensaios de "
        r"treino terá sido previsto exatamente uma vez por uma rede que não o utilizou no ajuste, o que "
        r"resulta em $13\times7=91$ previsões fora da dobra. O erro de uma rodada completa da validação "
        r"cruzada, com a semente $s$, é então:"
    )
    w.equation(
        r"\mathrm{RMSE}_{VC}^{(s)}=\sqrt{\frac{1}{91}\sum_{k=1}^{4}{\sum_{(j,i)\in V_{k}}{\left[X_{Zn,j}^{exp}"
        r"(t_{i})-\hat{X}_{Zn,j}^{(-k,s)}(t_{i})\right]^{2}}}}", "4.X.22")
    w.paragraph(
        r"Em que $V_k$ reúne os pares formados pelos ensaios $j$ de validação da dobra $k$ e pelos instantes "
        r"experimentais $t_i>0$, $X_{Zn,j}^{exp}$ é a conversão medida e $\hat{X}_{Zn,j}^{(-k,s)}$ é a "
        r"conversão prevista pelo modelo híbrido com a rede treinada sem a dobra $k$. Ressalta-se que a "
        r"comparação é feita com a conversão medida, e não com a conversão reconstruída no problema "
        r"inverso, de modo que o critério permanece ancorado nos dados experimentais."
    )
    w.paragraph(
        r"Um cuidado adicional foi necessário nas configurações com parada antecipada. Nesse caso, os dois "
        r"ensaios de acompanhamento foram retirados dos próprios ensaios de ajuste da dobra, por sorteio "
        r"fixo para cada dobra e semente, e nunca dos ensaios de validação. Se os ensaios de validação "
        r"fossem usados para decidir quando interromper o treinamento e, também, para calcular o erro da "
        r"configuração, esse erro seria otimista, pois a própria nota teria influenciado o modelo avaliado "
        r"(Cawley; Talbot, 2010). Com a separação adotada, os ensaios de validação de cada dobra servem "
        r"apenas para atribuir a nota."
    )
    w.paragraph(
        r"Por fim, como o resultado do treinamento varia com a semente (Seção 4.X), uma única rodada da "
        r"validação cruzada poderia favorecer ou prejudicar uma configuração por acaso. Por isso, cada "
        r"configuração foi avaliada com $S$ sementes, e a nota atribuída a ela foi a média:"
    )
    w.equation(r"J=\frac{1}{S}\sum_{s=1}^{S}{\mathrm{RMSE}_{VC}^{(s)}}", "4.X.23")
    w.paragraph(
        r"Adotaram-se $S=3$ sementes (42, 43 e 44) durante a busca, em que centenas de configurações foram "
        r"avaliadas, e $S=10$ sementes (42 a 51) na avaliação final das configurações mais promissoras, "
        r"descrita na próxima seção. O procedimento completo está esquematizado na Figura 4.X.14. Como "
        r"referência, o mesmo procedimento foi aplicado à configuração utilizada no início do "
        r"desenvolvimento, aqui denominada configuração de referência: uma rede com duas camadas de 64 e 32 "
        r"neurônios, ativação GELU e normalização de camada (*layer normalization*), treinada com taxa de "
        r"aprendizado de $3\times10^{-3}$, penalização de $10^{-4}$, lotes de 32 registros e parada "
        r"antecipada com paciência de 60 épocas, em até 350 épocas. Essa configuração havia sido escolhida "
        r"manualmente, pelo coeficiente de determinação de $\nu$ na validação, e sua avaliação pelo novo "
        r"critério permite verificar o efeito do procedimento de seleção sobre o modelo final."
    )
    w.figure(FIG_DIR / "fig_hs_14_avaliacao_configuracao.png", 15.5, "Figura 4.X.14",
             "Procedimento de avaliação de uma configuração da rede pelo erro na conversão de zinco fora da "
             "dobra")

    # ---------------------------------------------------------------- busca de hiperparâmetros
    w.subheading("Busca de hiperparâmetros")
    w.paragraph(
        r"Com o critério definido, restava explorar o conjunto de configurações possíveis. Como os "
        r"hiperparâmetros são numerosos e interagem entre si, testar todas as combinações em uma grade "
        r"regular seria inviável, e a escolha manual de poucas configurações dificilmente encontraria uma "
        r"boa combinação. Uma alternativa é a busca aleatória, que sorteia configurações dentro de faixas "
        r"predefinidas; outra, mais eficiente, é a busca guiada por modelo, que utiliza os resultados das "
        r"configurações já avaliadas para decidir qual avaliar em seguida (Goodfellow; Bengio; Courville, "
        r"2016; Bergstra et al., 2011). Adotou-se esta segunda estratégia, com o algoritmo TPE (*Tree-structured "
        r"Parzen Estimator*), implementado na biblioteca Optuna (Akiba et al., 2019)."
    )
    w.paragraph(
        r"O funcionamento do TPE está ilustrado na Figura 4.X.15(a). Nas primeiras tentativas, as "
        r"configurações são sorteadas ao acaso, para cobrir o espaço de busca. A partir daí, o histórico é "
        r"dividido em dois grupos: as tentativas com as melhores notas e as demais. Para cada grupo, estima-se "
        r"a densidade de probabilidade dos hiperparâmetros, $\ell(\mathbf{x})$ para o grupo das melhores e "
        r"$g(\mathbf{x})$ para o das demais, e a próxima configuração é escolhida, entre vários candidatos "
        r"sorteados de $\ell(\mathbf{x})$, como aquela que maximiza a razão (Bergstra et al., 2011):"
    )
    w.equation(r"\mathbf{x}^{*}=\arg\max_{\mathbf{x}}{\frac{\ell(\mathbf{x})}{g(\mathbf{x})}}", "4.X.24")
    w.paragraph(
        r"Em que $\mathbf{x}$ representa uma configuração. Em termos práticos, o algoritmo privilegia "
        r"regiões do espaço que aparecem com frequência entre as boas configurações e raramente entre as "
        r"ruins, mas, como os candidatos são sorteados, continua explorando outras regiões. Utilizou-se a "
        r"versão multivariada do método, que considera a dependência entre os hiperparâmetros, como a "
        r"relação entre a taxa de aprendizado e o número de épocas. Para economizar tempo de cálculo, "
        r"aplicou-se ainda uma regra de poda: depois da segunda dobra, se a nota parcial de uma tentativa "
        r"fosse pior que a mediana das tentativas anteriores no mesmo ponto, a tentativa era interrompida. "
        r"As avaliações foram executadas em 24 processos paralelos."
    )
    w.paragraph(
        r"A busca foi realizada em dois estágios, cujos espaços estão apresentados na Tabela 4.X.9. No "
        r"primeiro, foram consideradas redes de uma a quatro camadas ocultas, com largura constante ou "
        r"decrescente, três funções de ativação suaves, a presença ou não da normalização de camada e as "
        r"duas estratégias de parada descritas anteriormente. A configuração de referência foi incluída como "
        r"uma das primeiras tentativas. O segundo estágio foi definido a partir do que o primeiro mostrou "
        r"(Seção 5.X): como as melhores configurações se concentraram no limite superior de profundidade e "
        r"utilizaram número fixo de épocas, o espaço foi ampliado para até oito camadas e até 4.000 épocas, "
        r"a parada antecipada foi retirada e foram incluídas três opções novas: as conexões residuais, a "
        r"entrada temporal em $\ln t$ e a inicialização de Glorot e Bengio (2010), alternativa à "
        r"inicialização padrão da biblioteca. A configuração escolhida no primeiro estágio e a finalista "
        r"empatada com ela foram incluídas como pontos de partida do segundo. Foram realizadas 423 tentativas no primeiro estágio "
        r"e 523 no segundo."
    )
    w.table(
        "Tabela 4.X.9", "Espaços de busca dos hiperparâmetros nos dois estágios",
        ["Hiperparâmetro", "Estágio 1", "Estágio 2"],
        [
            ["Camadas ocultas", "1 a 4", "2 a 8"],
            ["Neurônios na 1ª camada", "8 a 256 (escala log)", "8 a 96 (escala log)"],
            ["Forma das camadas", "constante ou decrescente", "constante ou decrescente"],
            ["Função de ativação", "GELU, SiLU ou tanh", "GELU, SiLU ou tanh"],
            ["Normalização de camada", "com ou sem", "com ou sem"],
            ["Conexões residuais", "não", "com ou sem"],
            ["Entrada temporal", r"$t$", r"$t$ ou $\ln t$"],
            ["Inicialização dos pesos", "padrão", "padrão ou Glorot"],
            [r"Probabilidade de *dropout*", "0 a 0,2", "0 a 0,3"],
            ["Taxa de aprendizado inicial", r"$10^{-4}$ a $10^{-2}$ (log)", r"$10^{-4}$ a $10^{-2}$ (log)"],
            ["Penalização dos pesos", r"$10^{-6}$ a $10^{-1}$ (log)", r"$10^{-6}$ a $10^{-1}$ (log)"],
            ["Tamanho do lote", "16, 32, 64, 128 ou 256", "16, 32, 64, 128 ou 256"],
            ["Estratégia de parada", "antecipada ou épocas fixas", "épocas fixas"],
            ["Número de épocas", "50 a 2.000 (fixas); até 300 a 2.000 (antecipada)", "200 a 4.000 (log)"],
            ["Paciência (parada antecipada)", "20 a 200 épocas", "–"],
            ["Tentativas realizadas", "423", "523"],
        ],
        [4.6, 5.6, 5.4],
    )
    w.paragraph(
        r"Encerrada cada busca, as cinco configurações com as melhores notas foram reavaliadas com dez "
        r"sementes. Essa etapa é necessária porque, quando centenas de configurações são comparadas com "
        r"apenas três sementes, a melhor delas tende a ter sido favorecida também pelo acaso, e sua nota "
        r"tende a ser otimista (Cawley; Talbot, 2010). Com dez sementes, a nota de cada finalista passa a "
        r"ser estimada com menor incerteza, expressa pelo erro-padrão $EP=\sigma_J/\sqrt{10}$, em que "
        r"$\sigma_J$ é o desvio-padrão dos dez valores de $\mathrm{RMSE}_{VC}^{(s)}$. A configuração de "
        r"referência e a escolhida no primeiro estágio foram reavaliadas da mesma forma, para comparação."
    )
    w.paragraph(
        r"A escolha final seguiu a regra de um erro-padrão (Hastie; Tibshirani; Friedman, 2009): entre as "
        r"finalistas cuja nota média não supera a da melhor em mais de um erro-padrão desta, escolhe-se a "
        r"mais simples, isto é, a de menor número de parâmetros:"
    )
    w.equation(r"\bar{J}\leq\bar{J}_{melhor}+EP_{melhor}", "4.X.25")
    w.paragraph(
        r"A ideia da regra é que diferenças menores que a incerteza da própria estimativa não justificam a "
        r"escolha de um modelo mais complexo. Além disso, como todas as finalistas foram avaliadas com as "
        r"mesmas dez sementes, as diferenças entre duas configurações puderam ser analisadas semente a "
        r"semente, por meio do teste $t$ pareado e do teste de postos sinalizados de Wilcoxon (Wilcoxon, "
        r"1945), que verificam se a diferença média entre elas é compatível com zero. A sequência completa "
        r"de seleção está resumida na Figura 4.X.15(b), e a configuração escolhida é a descrita nas Tabelas "
        r"4.X.7 e 4.X.8."
    )
    w.figure(FIG_DIR / "fig_hs_15_busca_hiperparametros.png", 16.0, "Figura 4.X.15",
             "Busca de hiperparâmetros: (a) ciclo de uma busca com o algoritmo TPE e poda pela mediana; "
             "(b) sequência de seleção até o modelo final")

    # ---------------------------------------------------------------- comitê final
    w.subheading("Modelo final: comitê de redes")
    w.paragraph(
        r"Definida a configuração, o modelo final foi treinado com todos os 780 registros dos 13 ensaios "
        r"de treino. Como a configuração escolhida utiliza número fixo de épocas, nenhum ensaio precisou "
        r"ser reservado. Em vez de uma única rede, porém, foram treinadas dez redes com a mesma "
        r"configuração e com as sementes 42 a 51, formando um comitê (*ensemble*). Redes treinadas com "
        r"sementes diferentes partem de pesos iniciais diferentes e percorrem os dados em ordens diferentes, "
        r"chegando a soluções que concordam nas regiões bem representadas pelos dados e divergem nas demais. "
        r"A média das previsões reduz a parcela do erro associada a essa variabilidade, e a dispersão entre "
        r"os membros fornece uma indicação da incerteza do modelo (Goodfellow; Bengio; Courville, 2016; "
        r"Lakshminarayanan; Pritzel; Blundell, 2017)."
    )
    w.paragraph(
        r"A combinação foi feita na taxa de retração, antes do acoplamento:"
    )
    w.equation(r"\bar{\nu}(t)=\frac{1}{M}\sum_{m=1}^{M}{\hat{\nu}_{m}(t)}", "4.X.26")
    w.paragraph(
        r"Em que $M=10$ e $\hat{\nu}_m$ é a taxa prevista pela rede $m$. A média é calculada na escala "
        r"física de $\nu$, e não na escala transformada $y$, para que a taxa média corresponda à média das "
        r"velocidades de retração; como cada $\hat{\nu}_m$ é positiva, $\bar{\nu}$ também é. A taxa média é "
        r"então acoplada ao modelo fenomenológico, fornecendo a previsão do modelo híbrido. Para representar "
        r"a incerteza, cada rede também foi acoplada separadamente, e a faixa entre a menor e a maior "
        r"conversão prevista pelos membros foi registrada em cada instante:"
    )
    w.equation(r"\hat{X}_{Zn}^{min}(t)=\min_{m}{\hat{X}_{Zn,m}(t)},\qquad\hat{X}_{Zn}^{max}(t)=\max_{m}"
               r"{\hat{X}_{Zn,m}(t)}", "4.X.27")
    w.paragraph(
        r"Essa faixa expressa apenas a variabilidade associada ao treinamento das redes. Ela não inclui o "
        r"erro experimental das medições nem as simplificações do modelo fenomenológico e, portanto, não "
        r"deve ser interpretada como um intervalo de confiança da conversão. A Figura 4.X.16 esquematiza o "
        r"modelo final."
    )
    w.figure(FIG_DIR / "fig_hs_16_comite_redes.png", 16.0, "Figura 4.X.16",
             "Modelo final: comitê de dez redes, média das taxas previstas e faixa de incerteza obtida pelo "
             "acoplamento de cada rede")
    w.paragraph(
        r"Somente depois de treinado e salvo o comitê, os três ensaios de teste cego foram simulados, uma "
        r"única vez. Nenhuma decisão de modelagem foi tomada a partir desse resultado, e o procedimento de "
        r"treinamento foi programado para não sobrescrever um comitê já salvo, de modo que o teste "
        r"permanecesse independente do modelo avaliado (Kapoor; Narayanan, 2023)."
    )

    # ---------------------------------------------------------------- acoplamento e simulação
    w.subheading("Acoplamento da rede ao modelo fenomenológico e simulação")
    w.paragraph(
        r"O acoplamento descrito nesta seção é o mesmo em todas as etapas em que a rede é convertida em "
        r"previsões de conversão: na avaliação das configurações durante a busca, na simulação do comitê "
        r"final e na geração das curvas apresentadas nos resultados. Dadas as condições de um ensaio, "
        r"$C_{A0}$ e $\eta$, e os instantes em que se deseja a previsão, o algoritmo segue as sete etapas da "
        r"Figura 4.X.17."
    )
    w.figure(FIG_DIR / "fig_hs_17_algoritmo_simulacao.png", 15.0, "Figura 4.X.17",
             "Algoritmo de simulação do modelo híbrido serial para uma condição operacional")
    w.paragraph(
        r"Inicialmente, define-se a malha canônica de cálculo, com passo de 0,25 min, a mesma utilizada no "
        r"problema inverso e na construção da base de dados (Figura 4.X.7). A rede é avaliada em cada nó "
        r"dessa malha, fornecendo $\hat{\nu}(t_k)$, e a retração acumulada é obtida pela Equação 4.X.6, com "
        r"o primeiro intervalo integrado com taxa constante. Como discutido anteriormente, a rede só é "
        r"avaliada a partir de $t=0,25$ min, que é o domínio coberto pelos dados de treino. Em seguida, a "
        r"conversão em cada nó é lida da curva $X_{Zn}(\delta)$ pré-calculada (Figura 4.X.4). Como a "
        r"integração e a leitura da conversão são idênticas às do problema inverso, a taxa prevista pela rede "
        r"e a taxa estimada a partir dos dados são convertidas em conversão exatamente da mesma forma."
    )
    w.paragraph(
        r"Antes do cálculo da concentração de ácido, a conversão é submetida a duas restrições físicas:"
    )
    w.equation(r"\tilde{X}_{Zn,k}=\min\left[\max_{j\leq k}{X_{Zn}(\delta_{j})},\ \min(1,\eta)\right]", "4.X.28")
    w.paragraph(
        r"A primeira operação garante que a conversão não diminua ao longo do tempo. Como $\hat{\nu}$ é "
        r"sempre positiva e a curva $X_{Zn}(\delta)$ é crescente, essa condição já é satisfeita pela "
        r"construção do modelo, e a operação funciona apenas como uma salvaguarda numérica. A segunda "
        r"operação é a mais relevante: a relação $X_{Zn}(\delta)$ decorre apenas da granulometria e não "
        r"leva em conta a quantidade de ácido disponível, de modo que, nos ensaios com deficiência de ácido, "
        r"uma taxa prevista um pouco acima da real poderia levar a conversões superiores a $\eta$, o que "
        r"violaria o balanço estequiométrico. A limitação em $\min(1,\eta)$ impede essa situação. Além disso, "
        r"quando $\eta<1$ e a conversão atinge o limite, o ácido está esgotado e a dissolução cessa; a partir "
        r"desse instante, a retração acumulada é mantida constante e a taxa é considerada nula, ainda que a "
        r"rede preveja um valor residual. A concentração de ácido livre é então calculada pela Equação "
        r"4.X.4."
    )
    w.paragraph(
        r"Por fim, a condição inicial $X_{Zn}(0)=0$, $\delta(0)=0$ e $C_A(0)=C_{A0}$ é imposta diretamente, "
        r"e os valores nos instantes solicitados são obtidos por interpolação linear entre os nós da malha. "
        r"Como os sete instantes experimentais coincidem com nós da malha canônica, as previsões nesses "
        r"instantes não dependem da interpolação. Todo o procedimento foi implementado em uma classe Python "
        r"que recebe a rede, ou o comitê, como argumento, o que permitiu aplicá-lo sem alterações a todas as "
        r"configurações avaliadas."
    )

    # ---------------------------------------------------------------- avaliação
    w.subheading("Avaliação do modelo híbrido")
    w.paragraph(
        r"O desempenho do modelo híbrido foi quantificado pelo coeficiente de determinação ($R^2$), pela "
        r"raiz do erro quadrático médio (RMSE) e pelo erro absoluto médio (MAE), calculados conforme as "
        r"Equações 3.25 a 3.27 da revisão bibliográfica (Chicco; Warrens; Jurman, 2021). As métricas foram "
        r"calculadas sobre a conversão de zinco, comparando a previsão do modelo com a conversão medida, "
        r"apenas nos instantes com $t>0$, pelo motivo já discutido na Seção 4.X. Consideraram-se três "
        r"conjuntos de pontos: os 91 pontos dos 13 ensaios de treino, os 21 pontos dos três ensaios de "
        r"teste cego e o conjunto global, com os 112 pontos."
    )
    w.paragraph(
        r"Esses conjuntos têm significados diferentes. Nos ensaios de treino, as taxas obtidas no problema "
        r"inverso foram utilizadas no ajuste da rede, de modo que as métricas desse conjunto indicam a "
        r"capacidade do modelo de reproduzir as curvas utilizadas na sua construção, e não a sua capacidade "
        r"de previsão em condições novas. Essa capacidade é estimada de duas formas complementares: pelo "
        r"erro fora da dobra da validação cruzada (Equação 4.X.22), que cobre os 13 ensaios de treino, cada "
        r"um previsto por redes que não o utilizaram, e pelo teste cego, que avalia o modelo final em três "
        r"condições que não participaram de nenhuma etapa do desenvolvimento. Como o teste cego reúne apenas "
        r"três ensaios, diferenças pequenas entre modelos nesse conjunto devem ser interpretadas com cautela. "
        r"De forma complementar, a qualidade da taxa prevista para os ensaios de teste foi verificada em "
        r"relação às taxas estimadas no problema inverso, na malha de 0,25 min, pelo coeficiente de "
        r"determinação calculado nas escalas de $\nu$ e de $\ln(1+\nu)$."
    )
    w.paragraph(
        r"Para situar o desempenho do modelo híbrido, foram utilizadas três referências. A primeira é o "
        r"modelo fenomenológico puro (Seção 4.X), que utiliza o mesmo balanço populacional, mas com a taxa "
        r"de retração dada pela lei cinética de reação interfacial, sem o fator empírico $\alpha$; a "
        r"comparação com ele mostra o efeito de substituir a lei cinética pela rede. A segunda é a "
        r"configuração de referência da rede, acoplada da mesma forma, que mostra o efeito do procedimento "
        r"de seleção descrito nas seções anteriores. A terceira é o modelo puramente orientado por dados "
        r"(Seção 4.X), no qual a rede neural prevê diretamente a conversão de zinco. As principais diferenças "
        r"entre os dois modelos baseados em redes neurais estão resumidas na Tabela 4.X.10. A mais importante "
        r"é a grandeza aprendida: no modelo puramente orientado por dados, a rede é o próprio modelo do "
        r"processo, enquanto, no modelo híbrido, ela fornece apenas a taxa de retração, e a conversão "
        r"continua sendo calculada pelos balanços populacional e de ácido. Para que a comparação seja feita "
        r"nas mesmas condições, as métricas dos dois modelos devem ser calculadas sobre os mesmos 21 pontos "
        r"do teste cego com $t>0$."
    )
    w.table(
        "Tabela 4.X.10", "Comparação entre o modelo puramente orientado por dados e o modelo híbrido serial",
        ["Característica", "Modelo puramente orientado por dados", "Modelo híbrido serial"],
        [
            ["Grandeza prevista pela rede", r"conversão $X_{Zn}(t)$", r"taxa de retração $\nu(t)$"],
            ["Cálculo de $X_{Zn}$", "saída direta da rede", "balanço populacional (Eqs. 4.X.1 a 4.X.3)"],
            ["Dados de treino", "104 pontos experimentais (com $t=0$)",
             "780 registros de $\\nu$ do problema inverso"],
            ["Escalonamento das entradas", "Min-Max, de −1 a 1", "escore Z, com $t$ em $\\ln t$"],
            ["Restrição física na saída", r"sigmoide: $0<X_{Zn}<1$",
             r"$\nu>0$; $X_{Zn}\leq\min(1,\eta)$; ácido pelo balanço"],
            ["Arquitetura", "4 camadas de 64 neurônios, tanh", "3 blocos residuais (90, 45, 22), GELU"],
            ["Seleção da configuração", "topologia fixa, comum à PINN", "busca por validação cruzada"],
            ["Ensaios de teste cego", "7, 8 e 14", "7, 8 e 14"],
        ],
        [4.4, 5.6, 5.6],
    )

def remover_secao_existente(doc, i_titulo: int, anchor) -> int:
    """Remove os elementos entre o título da seção e a âncora (inclusive o título)."""
    start = doc.paragraphs[i_titulo]._p
    body = start.getparent()
    removed = 0
    el = start
    while el is not None and el is not anchor:
        nxt = el.getnext()
        body.remove(el)
        removed += 1
        el = nxt
    return removed


def main() -> None:
    substituir = "--substituir" in sys.argv
    lock = DOC_PATH.parent / ("~$" + DOC_PATH.name[2:])
    if lock.exists():
        sys.exit("O relatório parece estar aberto no Word. Feche-o e rode novamente.")

    doc = docx.Document(str(DOC_PATH))
    ps = doc.paragraphs
    i_res = find_paragraph(doc, "RESULTADOS E DISCUSSÃO", style_prefix="Heading 2")
    # âncora: primeiro parágrafo vazio de título logo antes de RESULTADOS (ou o próprio título)
    anchor = ps[i_res]._p
    prev = anchor.getprevious()
    if prev is not None and prev.tag == qn("w:p") and not "".join(prev.itertext()).strip():
        anchor = prev

    existentes = [i for i, p in enumerate(ps) if p.text.strip() == TITULO_SECAO]
    if existentes and not substituir:
        sys.exit("A seção já existe no relatório. Use --substituir para reescrevê-la.")

    copia = backup(DOC_PATH)
    print(f"Backup salvo em: {copia}")
    if existentes:
        print(f"Removidos {remover_secao_existente(doc, existentes[0], anchor)} elementos da versão anterior.")

    i_pinn = find_paragraph(doc, "Modelagem Híbrida: Redes Neurais Informadas pela Física (PINN)")
    refs = {
        "heading": ps[i_pinn]._p,
        "subheading": ps[i_pinn + 1]._p,
        "body": ps[i_pinn + 2]._p,
    }
    i_cap = next(i for i, p in enumerate(ps) if p.text.startswith("Figura 4.X"))
    refs.update({"figure": ps[i_cap - 1]._p, "caption": ps[i_cap]._p, "source": ps[i_cap + 1]._p})

    writer = SectionWriter(doc, refs, anchor)
    conteudo(writer)
    novas = add_references(doc, REFERENCIAS_NOVAS)
    doc.save(str(DOC_PATH))
    print(f"Seção escrita: {len(writer.inserted)} elementos inseridos.")
    print(f"Referências adicionadas: {len(novas)}")


if __name__ == "__main__":
    main()
