"""Escreve no relatório a seção de Resultados do modelo híbrido serial, toda em vermelho.

A seção é inserida ao final de RESULTADOS E DISCUSSÃO (antes de CONCLUSÕES), depois dos
marcadores já deixados pelo grupo. Por estar fora de Materiais e Métodos, todo o texto,
as tabelas e as equações são pintados de vermelho (COR_FORA_METODOS), para revisão.
Antes de qualquer alteração, uma cópia do relatório é salva em Documento/old/.

Uso:
    python escrever_resultados_hibrido.py               # insere a seção (falha se já existir)
    python escrever_resultados_hibrido.py --substituir  # reescreve a seção já inserida
"""

from __future__ import annotations

import sys
from pathlib import Path

import docx
from docx.oxml.ns import qn

from docx_utils import SectionWriter, add_references, backup, find_paragraph, pintar

DOC_DIR = Path(__file__).resolve().parents[1]
DOC_PATH = DOC_DIR / "RELATÓRIO FINAL LOP.docx"
FIG_RES = DOC_DIR / "figuras_resultados"
SAIDAS = DOC_DIR.parent / "Código" / "outputs" / "etapa_3_2" / "subetapa_3_2_6_mlp_otimizacao"

TITULO_SECAO = "Modelo Híbrido Serial"
REFERENCIAS_NOVAS: list = []


def conteudo(w: SectionWriter) -> None:
    """Texto da seção, na ordem em que aparece no relatório."""
    w.heading(TITULO_SECAO)
    w.paragraph(
        r"Esta seção apresenta os resultados obtidos com o modelo híbrido serial descrito na Seção 4.X, na "
        r"mesma ordem em que as etapas foram executadas: a estimativa das taxas de retração pelo problema "
        r"inverso, a avaliação da configuração de referência da rede, a busca de hiperparâmetros e, por fim, "
        r"o desempenho do modelo final nos ensaios de treino e de teste cego."
    )

    # ------------------------------------------------------------ problema inverso
    w.subheading("Estimativa da taxa de retração pelo problema inverso")
    w.paragraph(
        r"A Figura 5.X.1 compara a conversão reconstruída a partir das taxas estimadas no problema inverso "
        r"com a conversão medida nos 16 ensaios. Considerando os 112 pontos experimentais com $t>0$, a "
        r"reconstrução apresentou $R^2=0,995$, RMSE de 0,0137 e MAE de 0,0102. Por ensaio, o RMSE variou "
        r"entre 0,0047 (Ensaio 2) e 0,0256 (Ensaio 11), valores da mesma ordem da dispersão observada entre "
        r"medições consecutivas no patamar final das curvas, como no Ensaio 11, em que a conversão medida "
        r"passa de 0,97 em 3 min para 0,94 em 4 min. Assim, a parametrização da Equação 4.X.5, com os termos "
        r"de regularização, foi capaz de reproduzir as curvas dentro da incerteza aparente dos dados."
    )
    w.figure(FIG_RES / "fig_res_01_reconstrucao_problema_inverso.png", 16.0, "Figura 5.X.1",
             "Conversão de zinco reconstruída pelo problema inverso (linhas) e medida (símbolos) nos 16 "
             "ensaios, agrupados pela razão molar; linhas tracejadas indicam os ensaios de teste cego")
    w.paragraph(
        r"A Tabela 5.X.1 apresenta as métricas por ensaio. Em alguns ensaios, sobretudo naqueles com "
        r"$\eta=0,5$, o coeficiente de determinação calculado por ensaio é baixo ou até negativo, apesar de o "
        r"RMSE ser pequeno. Isso ocorre porque, nesses ensaios, a conversão atinge o patamar de 0,5 já na "
        r"primeira medição e varia muito pouco depois disso, de modo que a variância dos dados dentro do "
        r"ensaio é da mesma ordem do erro experimental. Nessas condições, o $R^2$ por ensaio deixa de ser um "
        r"bom indicador, e o RMSE é a medida mais adequada da qualidade da reconstrução."
    )
    w.table(
        "Tabela 5.X.1", "Qualidade da reconstrução e características das taxas estimadas em cada ensaio",
        ["Ensaio", r"$C_{A0}$ (mol/L)", r"$\eta$", "RMSE", "MAE", r"$\nu(0,25)$ (µm/min)", r"$\delta(15)$ (µm)"],
        [
            ["1", "0,10", "0,5", "0,0095", "0,0074", "8,3", "4,9"],
            ["2", "0,10", "3,1", "0,0047", "0,0032", "38,6", "81,9"],
            ["3", "0,50", "0,5", "0,0094", "0,0069", "9,3", "4,8"],
            ["4", "1,00", "0,5", "0,0215", "0,0188", "11,2", "4,9"],
            ["5", "1,50", "0,5", "0,0122", "0,0098", "10,7", "4,6"],
            ["6", "0,10", "1,0", "0,0148", "0,0134", "28,4", "23,0"],
            ["7*", "0,50", "3,1", "0,0073", "0,0066", "51,3", "110,5"],
            ["8*", "0,50", "1,0", "0,0150", "0,0115", "40,5", "21,4"],
            ["9", "1,00", "1,0", "0,0113", "0,0083", "39,6", "20,0"],
            ["10", "1,50", "1,0", "0,0167", "0,0131", "38,8", "19,5"],
            ["11", "0,10", "1,5", "0,0256", "0,0208", "42,0", "57,4"],
            ["12", "1,00", "3,1", "0,0071", "0,0059", "88,8", "140,0"],
            ["13", "0,50", "1,5", "0,0125", "0,0094", "62,4", "40,4"],
            ["14*", "1,00", "1,5", "0,0104", "0,0088", "62,6", "46,8"],
            ["15", "1,50", "1,5", "0,0090", "0,0077", "61,2", "42,0"],
            ["16", "1,50", "3,1", "0,0153", "0,0113", "93,9", "83,2"],
        ],
        [1.6, 2.4, 1.4, 2.0, 2.0, 3.2, 2.6],
        source="Fonte: Elaborado pelos autores (2026). *Ensaios de teste cego.",
    )
    w.paragraph(
        r"As taxas estimadas estão apresentadas na Figura 5.X.2. Em todos os ensaios, a taxa é máxima no "
        r"início e decresce várias ordens de grandeza ao longo do ensaio. A taxa inicial cresce com a "
        r"disponibilidade de ácido: no primeiro nó da malha, ela fica entre 8 e 11 µm/min nos ensaios com "
        r"$\eta=0,5$, entre 28 e 41 µm/min com $\eta=1,0$, entre 42 e 63 µm/min com $\eta=1,5$ e chega a "
        r"94 µm/min no Ensaio 16 ($C_{A0}=1,5$ mol/L e $\eta=3,1$). Nos ensaios com deficiência de ácido, a "
        r"taxa cai para valores próximos de zero em cerca de 1 a 2 min, o que corresponde ao esgotamento do "
        r"ácido, e a retração acumulada ao final fica abaixo de 5 µm. No outro extremo, nos ensaios com "
        r"$\eta=3,1$, a retração acumulada ao final varia de 82 a 140 µm."
    )
    w.figure(FIG_RES / "fig_res_02_taxas_alvo.png", 16.0, "Figura 5.X.2",
             "Taxas de retração estimadas pelo problema inverso, em escala logarítmica, agrupadas pela razão "
             "molar; a linha pontilhada indica o limite superior da taxa residual c, e valores nulos estão "
             "representados em 10⁻³ µm/min")
    w.paragraph(
        r"Um aspecto a ser destacado é que, em 12 dos 16 ensaios, ao menos um parâmetro da Equação 4.X.5 "
        r"terminou em um dos limites da Tabela 4.X.1: a amplitude $a_2$ no limite superior de 80 µm/min em "
        r"sete ensaios, a constante $b_2$ no limite de 4 min⁻¹ em outros sete e a taxa residual $c$ no "
        r"limite de 0,03 µm/min em cinco. A consequência mais visível aparece na Figura 5.X.2: nos ensaios "
        r"8, 13, 14, 15 e 16, a taxa permanece constante em 0,03 µm/min na etapa final, valor imposto pelo "
        r"limite, e não pelos dados. Como essa etapa corresponde ao patamar da conversão, o efeito sobre "
        r"$X_{Zn}$ é pequeno, mas ele deve ser considerado na interpretação dos valores de $\nu$ nesse "
        r"trecho, inclusive na avaliação da rede (Seção 5.X)."
    )
    w.paragraph(
        r"Por fim, a reconstrução define um limite inferior para o erro do modelo híbrido. Se a rede "
        r"reproduzisse exatamente as taxas estimadas, o modelo híbrido apresentaria, nos 91 pontos dos 13 "
        r"ensaios de treino, o mesmo erro da reconstrução, isto é, RMSE de 0,0142. Esse valor é utilizado "
        r"como referência nas seções seguintes."
    )

    # ------------------------------------------------------------ configuração de referência
    w.subheading("Avaliação da configuração de referência")
    w.paragraph(
        r"A Tabela 5.X.2 resume a avaliação da configuração de referência da rede. Quando ajustada a todos "
        r"os ensaios de treino e avaliada nesses mesmos ensaios, ela apresentou RMSE de 0,0229 na conversão, "
        r"próximo do limite inferior de 0,0142. A avaliação fora da dobra, contudo, mostrou um quadro "
        r"diferente. No procedimento utilizado no início do desenvolvimento, em que a mesma dobra decidia a "
        r"parada antecipada e fornecia a nota, a rede obteve coeficiente de determinação médio de 0,821 para a "
        r"taxa $\nu$, valor que havia motivado a escolha dessa configuração; a conversão correspondente, "
        r"porém, teve RMSE de 0,130. No procedimento adotado neste trabalho (Seção 4.X), em que a parada "
        r"antecipada utiliza ensaios separados, o RMSE da conversão aumentou para 0,177 ± 0,046, com três "
        r"sementes, e para 0,183 ± 0,039, com dez."
    )
    w.table(
        "Tabela 5.X.2", "Desempenho da configuração de referência da rede em diferentes formas de avaliação",
        ["Avaliação", r"RMSE de $X_{Zn}$", r"$R^2$ de $X_{Zn}$", r"$R^2$ médio de $\nu$"],
        [
            ["Limite inferior (taxas do problema inverso)", "0,0142", "0,995", "–"],
            ["Configuração de referência, no próprio treino", "0,0229", "0,988", "–"],
            ["Fora da dobra, procedimento inicial (1 semente)", "0,130", "0,600", "0,821"],
            ["Fora da dobra, procedimento adotado (3 sementes)", "0,177 ± 0,046", "0,224", "0,370"],
            ["Fora da dobra, procedimento adotado (10 sementes)", "0,183 ± 0,039", "0,178", "–"],
        ],
        [7.0, 3.2, 2.8, 2.8],
    )
    w.paragraph(
        r"Dois resultados se destacam. O primeiro é que um coeficiente de determinação elevado para $\nu$ "
        r"coexistiu com um erro elevado na conversão, o que confirma, com os dados deste trabalho, o "
        r"argumento apresentado na Seção 4.X para avaliar as configurações diretamente em $X_{Zn}$. O segundo "
        r"é a grande diferença entre o erro no próprio treino (0,023) e o erro fora da dobra (0,18), que "
        r"indica que a configuração de referência reproduzia bem os ensaios utilizados no ajuste, mas "
        r"generalizava mal para condições não vistas. A Figura 5.X.3 mostra ainda que o resultado por dobra "
        r"variou bastante entre as sementes, sobretudo na terceira dobra, o que reforça a necessidade de "
        r"avaliar cada configuração com mais de uma semente. Os ensaios com maior erro fora da dobra foram o "
        r"10 (0,41), o 4 (0,24) e o 3 (0,21), todos nas extremidades de $C_{A0}$ ou com deficiência de ácido."
    )
    w.figure(SAIDAS / "fase_a" / "fig_fa_01_protocolo_antigo_vs_novo.png", 16.0, "Figura 5.X.3",
             "Avaliação da configuração de referência: (a) coeficiente de determinação da taxa por dobra, "
             "nos procedimentos inicial e adotado; (b) RMSE da conversão no limite inferior, no próprio "
             "treino e fora da dobra; na legenda, v1 designa a configuração de referência")

    # ------------------------------------------------------------ busca
    w.subheading("Busca de hiperparâmetros")
    w.paragraph(
        r"O primeiro estágio da busca reuniu 423 tentativas, das quais 402 foram concluídas e 21 foram "
        r"interrompidas pela regra de poda, com cerca de 16 horas de processamento somadas entre os "
        r"processos paralelos. A Figura 5.X.4 mostra a distribuição da nota das tentativas concluídas "
        r"segundo os principais hiperparâmetros categóricos. A diferença mais marcante foi entre as "
        r"estratégias de parada: a mediana do RMSE fora da dobra foi de 0,043 com número fixo de épocas e de "
        r"0,258 com parada antecipada, cerca de seis vezes maior. Com apenas 9 ou 10 ensaios de ajuste em "
        r"cada dobra, reservar dois deles para acompanhamento retira da rede uma parcela importante das "
        r"condições experimentais, e essa perda superou o benefício da interrupção do treinamento. Por esse "
        r"motivo, o algoritmo de busca abandonou cedo a parada antecipada, que reuniu apenas 22 tentativas."
    )
    w.figure(SAIDAS / "fase_b" / "fig_fb_04_hiperparametros_categoricos.png", 16.0, "Figura 5.X.4",
             "Primeiro estágio da busca: nota das tentativas concluídas segundo a estratégia de parada, a "
             "função de ativação, a normalização de camada e o número de camadas ocultas")
    w.paragraph(
        r"Entre as funções de ativação, a tangente hiperbólica apresentou a menor mediana (0,041), contra "
        r"0,136 da GELU e 0,154 da SiLU, e as redes sem normalização de camada tiveram desempenho melhor que "
        r"as redes com essa normalização. Essas comparações devem ser lidas com cautela, pois o algoritmo "
        r"concentra as tentativas nas regiões promissoras: a tangente hiperbólica reuniu 341 das 402 "
        r"tentativas, e as demais ativações foram testadas principalmente nas fases iniciais, com outros "
        r"hiperparâmetros ainda pouco ajustados. Quanto à profundidade, a mediana caiu de 0,279 com uma "
        r"camada para 0,041 com quatro, e as melhores configurações se concentraram no limite superior do "
        r"espaço de busca. Esse resultado, junto com a superioridade do número fixo de épocas, motivou a "
        r"definição do segundo estágio (Tabela 4.X.9)."
    )
    w.paragraph(
        r"O segundo estágio reuniu 523 tentativas, sendo 479 concluídas e 44 podadas, com cerca de 52 horas "
        r"de processamento somadas. A Figura 5.X.5 mostra que o aumento da profundidade não trouxe ganho: "
        r"as medianas foram de 0,037 com três camadas e 0,039 com quatro, contra 0,052 a 0,076 com cinco a "
        r"oito camadas. Com apenas 13 ensaios de treino, redes mais profundas não encontraram informação "
        r"adicional a ser explorada. A opção nova com maior efeito foi a entrada temporal em $\ln t$, com "
        r"mediana de 0,037 contra 0,047 com a entrada em $t$, o que confirma a vantagem de dar mais "
        r"resolução aos primeiros minutos do ensaio. A inicialização de Glorot, ao contrário, piorou o "
        r"resultado (mediana de 0,078, contra 0,037 com a inicialização padrão), e as conexões residuais "
        r"tiveram efeito pequeno na mediana (0,0368 com e 0,0377 sem), embora tenham estado presentes em "
        r"todas as melhores tentativas. As melhores configurações convergiram para uma mesma região: três "
        r"camadas decrescentes, com cerca de 90, 45 e 22 neurônios, ativação GELU, conexões residuais, "
        r"entrada em $\ln t$, lotes de 16 registros e entre 700 e 1.000 épocas."
    )
    w.figure(SAIDAS / "fase_b2" / "fig_fb2_03_hiperparametros_categoricos.png", 16.0, "Figura 5.X.5",
             "Segundo estágio da busca: nota das tentativas concluídas segundo o número de camadas, a "
             "função de ativação, a entrada temporal, a inicialização, as conexões residuais e a "
             "normalização de camada")
    w.paragraph(
        r"As finalistas dos dois estágios, reavaliadas com dez sementes, estão na Tabela 5.X.3 e na Figura "
        r"5.X.6. Como esperado, as notas com dez sementes foram um pouco piores que as obtidas com três "
        r"durante a busca: a melhor tentativa do primeiro estágio, por exemplo, passou de 0,0319 para "
        r"0,0372. No primeiro estágio, duas configurações ficaram empatadas dentro de um erro-padrão "
        r"(0,0363), e a regra da Equação 4.X.25 selecionou a de menor número de parâmetros, com quatro "
        r"camadas de 21 neurônios e tangente hiperbólica. No segundo, as duas melhores finalistas também "
        r"empataram (0,0326), com estruturas praticamente iguais, e foi escolhida a de menor largura, com "
        r"camadas de 90, 45 e 22 neurônios, descrita nas Tabelas 4.X.7 e 4.X.8. Uma das finalistas do "
        r"segundo estágio teve uma semente cujo treinamento divergiu (RMSE de 0,444), o que elevou sua média "
        r"para 0,074 e ilustra o risco de basear a escolha em uma única rede."
    )
    w.table(
        "Tabela 5.X.3", "Configurações finalistas reavaliadas com dez sementes",
        ["Configuração", "Camadas ocultas", "Ativação", "Épocas", r"RMSE de $X_{Zn}$ (média ± dp)", r"$R^2$"],
        [
            ["Referência", "64, 32", "GELU", "parada antecipada", "0,1828 ± 0,0393", "0,178"],
            ["Estágio 1, escolhida", "21, 21, 21, 21", "tanh", "1.714", "0,0363 ± 0,0053", "0,968"],
            ["Estágio 1, empatada", "27, 27, 27, 27", "tanh", "1.576", "0,0363 ± 0,0048", "0,969"],
            ["Estágio 2, escolhida", "90, 45, 22 (residual, ln t)", "GELU", "928", "0,0326 ± 0,0050", "0,974"],
            ["Estágio 2, empatada", "91, 45, 22 (residual, ln t)", "GELU", "703", "0,0326 ± 0,0027", "0,975"],
            ["Estágio 2, 3ª finalista", "88, 44, 22 (residual, ln t)", "GELU", "670", "0,0354 ± 0,0065", "0,970"],
            ["Estágio 2, 4ª finalista", "87, 43, 21 (residual, ln t)", "GELU", "941", "0,0359 ± 0,0059", "0,969"],
        ],
        [3.6, 4.2, 1.6, 2.4, 3.6, 1.4],
    )
    w.figure(SAIDAS / "fase_b2" / "fig_fb2_05_finalistas_10_sementes.png", 16.0, "Figura 5.X.6",
             "RMSE da conversão fora da dobra das finalistas, com dez sementes (B: primeiro estágio; B2: "
             "segundo estágio); a linha pontilhada indica o limite inferior dado pelas taxas do problema "
             "inverso")
    w.paragraph(
        r"Como as duas configurações escolhidas foram avaliadas com as mesmas dez sementes, foi possível "
        r"compará-las semente a semente. A configuração do segundo estágio foi melhor em sete das dez "
        r"sementes, com diferença média de −0,0037 no RMSE, e a diferença foi estatisticamente "
        r"significativa ao nível de 5% pelos testes $t$ pareado ($p=0,028$) e de Wilcoxon ($p=0,049$). "
        r"Ressalta-se que as sementes 42 a 44 foram utilizadas na busca dos dois estágios, o que favorece "
        r"igualmente as duas configurações. O ganho, de cerca de 10%, não foi uniforme entre os ensaios: o "
        r"erro fora da dobra diminuiu na maioria deles, como nos Ensaios 9 (de 0,045 para 0,016) e 11 (de "
        r"0,057 para 0,034), mas aumentou nos Ensaios 6, 10 e 15, que permaneceram como os mais difíceis de "
        r"prever, com RMSE entre 0,044 e 0,058."
    )
    w.paragraph(
        r"A Figura 5.X.7(a) resume a evolução do erro fora da dobra ao longo do procedimento de seleção. Em "
        r"relação à configuração de referência, a configuração final reduziu o RMSE da conversão de 0,183 "
        r"para 0,033, uma redução de 82%, e ficou a cerca de 2,3 vezes do limite inferior de 0,014. A maior "
        r"parte do ganho veio do primeiro estágio, principalmente da adoção do número fixo de épocas; o "
        r"segundo estágio acrescentou um ganho menor, associado à entrada em $\ln t$ e às conexões "
        r"residuais. A parte (b) da figura antecipa o desempenho dos modelos finais, discutido a seguir."
    )
    w.figure(SAIDAS / "fase_e" / "fig_fe_05_evolucao_e_teste.png", 16.0, "Figura 5.X.7",
             "Síntese da seleção da rede: (a) RMSE da conversão fora da dobra da configuração de referência "
             "e das escolhidas nos dois estágios (Fases B e B2); (b) RMSE no treino e no teste cego dos modelos finais"
             " (nas legendas, “v1” designa a configuração de referência e “v2”, o modelo final)")

    # ------------------------------------------------------------ modelo final
    w.subheading("Desempenho do modelo final")
    w.paragraph(
        r"A Tabela 5.X.4 apresenta as métricas do modelo híbrido final, formado pelo comitê de dez redes, "
        r"ao lado das duas referências avaliadas nos mesmos pontos. Nos ensaios de treino, o modelo final "
        r"obteve RMSE de 0,0145, praticamente igual ao limite inferior de 0,0142, ou seja, o comitê "
        r"reproduz as taxas estimadas no problema inverso com fidelidade suficiente para que quase todo o "
        r"erro restante venha da própria reconstrução. No teste cego, avaliado uma única vez, o RMSE foi de "
        r"0,0202, com $R^2=0,888$ e erro máximo de 0,040."
    )
    w.table(
        "Tabela 5.X.4", "Métricas da conversão de zinco para o modelo híbrido final e as referências",
        ["Modelo", "Conjunto", r"$R^2$", "RMSE", "MAE", "Erro máximo"],
        [
            ["Fenomenológico puro", "Treino (91)", "0,890", "0,0682", "0,0488", "0,163"],
            ["", "Teste cego (21)", "−0,675", "0,0780", "0,0637", "0,126"],
            ["", "Global (112)", "0,871", "0,0702", "0,0516", "0,163"],
            ["Híbrido, configuração de referência", "Treino (91)", "0,988", "0,0229", "0,0169", "0,064"],
            ["", "Teste cego (21)", "0,657", "0,0353", "0,0269", "0,082"],
            ["", "Global (112)", "0,983", "0,0257", "0,0188", "0,082"],
            ["Híbrido final (comitê)", "Treino (91)", "0,995", "0,0145", "0,0106", "0,037"],
            ["", "Teste cego (21)", "0,888", "0,0202", "0,0165", "0,040"],
            ["", "Global (112)", "0,994", "0,0157", "0,0117", "0,040"],
        ],
        [4.6, 3.0, 1.8, 1.9, 1.9, 2.2],
    )
    w.paragraph(
        r"Em relação ao modelo fenomenológico puro, o modelo híbrido final reduziu o RMSE do teste cego de "
        r"0,078 para 0,020 (redução de 74%) e, em relação à configuração de referência, de 0,035 para 0,020 "
        r"(redução de 43%). O $R^2$ negativo do modelo fenomenológico no teste não indica um erro absoluto "
        r"muito maior que o dos treinos, mas reflete a pequena variância das conversões medidas nesses "
        r"três ensaios, que se concentram entre 0,82 e 1,0. Observa-se, ainda, que o erro do modelo final "
        r"no teste cego (0,020) ficou abaixo do erro fora da dobra estimado na seleção (0,033). Essa "
        r"diferença é coerente com a escolha dos ensaios de teste, todos no interior do planejamento, "
        r"enquanto a validação cruzada inclui ensaios nos vértices, que exigem extrapolação (Seção 4.X)."
    )
    w.figure(SAIDAS / "fase_e" / "fig_fe_01_XZn_teste_cego.png", 16.0, "Figura 5.X.8",
             "Conversão de zinco nos ensaios de teste cego: valores medidos, previsão do modelo híbrido "
             "final com a faixa dos dez membros, configuração de referência e modelo fenomenológico puro"
             " (nas legendas, “v1” designa a configuração de referência e “v2”, o modelo final)")
    w.paragraph(
        r"As curvas dos três ensaios de teste estão na Figura 5.X.8, e o erro de cada um, na Figura 5.X.9. "
        r"O maior ganho ocorreu no Ensaio 8 ($C_{A0}=0,5$ mol/L e $\eta=1,0$), cuja conversão se estabiliza "
        r"em cerca de 0,86. O modelo fenomenológico puro prevê a dissolução praticamente completa (0,995 aos "
        r"15 min), a configuração de referência subestima o patamar (0,81) e o modelo final o aproxima melhor "
        r"(0,84), com RMSE de 0,025, contra 0,115 e 0,056, respectivamente. No Ensaio 14 ($C_{A0}=1,0$ "
        r"mol/L e $\eta=1,5$), o modelo final também foi o mais preciso, com RMSE de 0,011. No Ensaio 7 "
        r"($\eta=3,1$), por outro lado, o modelo final foi ligeiramente pior que a configuração de "
        r"referência (0,022 contra 0,016), pois superestima a conversão nos primeiros instantes: 0,92 e 0,97 "
        r"em 0,5 e 1 min, contra 0,88 e 0,93 medidos."
    )
    w.figure(SAIDAS / "fase_e" / "fig_fe_04_rmse_teste_cego.png", 15.0, "Figura 5.X.9",
             "RMSE da conversão em cada ensaio de teste cego e no conjunto de teste, com a variação entre os "
             "membros do comitê"
             " (nas legendas, “v1” designa a configuração de referência e “v2”, o modelo final)")
    w.paragraph(
        r"A faixa entre os membros do comitê, visível na Figura 5.X.8, é estreita: o desvio-padrão das "
        r"conversões previstas pelos dez membros foi, em média, de 0,003 nos pontos de teste. O RMSE de um "
        r"membro isolado no teste variou entre 0,018 e 0,023, com média de 0,0203, praticamente igual ao do "
        r"comitê (0,0202). Assim, com a configuração escolhida, o treinamento é estável entre sementes, e o "
        r"principal benefício do comitê é eliminar a dependência do resultado em relação a uma semente "
        r"específica, além de fornecer a faixa de incerteza."
    )
    w.figure(SAIDAS / "fase_e" / "fig_fe_02_nu_teste_cego.png", 16.0, "Figura 5.X.10",
             "Taxa de retração nos ensaios de teste cego: taxas estimadas pelo problema inverso e previsões "
             "do modelo final, com a faixa dos membros, e da configuração de referência"
             " (nas legendas, “v1” designa a configuração de referência e “v2”, o modelo final)")
    w.paragraph(
        r"A Figura 5.X.10 compara as taxas previstas para os ensaios de teste com as estimadas pelo "
        r"problema inverso. Na escala de $\nu$, o coeficiente de determinação do modelo final foi de 0,921, "
        r"semelhante ao da configuração de referência (0,923); na escala de $\ln(1+\nu)$, foi de 0,904, "
        r"contra 0,945. A diferença entre os dois modelos está concentrada no trecho final dos Ensaios 8 e "
        r"14, a partir de cerca de 4 min, onde as taxas estimadas permanecem em 0,03 µm/min por efeito do "
        r"limite do parâmetro $c$ (Seção 5.X), enquanto o modelo final prevê taxas entre 0,002 e 0,01 "
        r"µm/min. Nesse trecho, a conversão já se encontra no patamar, e a diferença praticamente não altera "
        r"$X_{Zn}$. Esse resultado ilustra, mais uma vez, que a qualidade da previsão de $\nu$ e a da "
        r"conversão não são equivalentes, e que o modelo final foi escolhido pela segunda."
    )
    w.figure(SAIDAS / "fase_e" / "fig_fe_03_paridade_XZn.png", 15.0, "Figura 5.X.11",
             "Conversão prevista contra a medida nos ensaios de treino e de teste cego: (a) configuração de "
             "referência; (b) modelo híbrido final"
             " (nas legendas, “v1” designa a configuração de referência e “v2”, o modelo final)")
    w.paragraph(
        r"Os gráficos de paridade da Figura 5.X.11 resumem esses resultados. Para o modelo final, todos os "
        r"pontos, de treino e de teste, ficam dentro da faixa de ±0,05 em torno da diagonal, inclusive nos "
        r"ensaios com deficiência de ácido, em que a conversão se estabiliza em 0,5 por efeito da "
        r"restrição estequiométrica. Na configuração de referência, os desvios são maiores, sobretudo no "
        r"patamar dos ensaios com $\eta=1,0$ e nos primeiros instantes dos ensaios com $\eta=0,5$."
    )
    w.paragraph(
        r"Duas ressalvas devem acompanhar esses resultados. A primeira é que o teste cego reúne apenas três "
        r"ensaios e 21 pontos, de modo que diferenças pequenas entre modelos nesse conjunto não são "
        r"conclusivas; a evidência principal para a escolha da configuração é a validação cruzada, que "
        r"cobre os 13 ensaios de treino. A segunda é que o resultado da configuração de referência no teste "
        r"já havia sido calculado em uma etapa anterior do desenvolvimento, quando essa configuração ainda "
        r"era a do modelo; para o modelo final, ao contrário, a avaliação descrita nesta seção foi a primeira "
        r"e única. A comparação com o modelo puramente orientado por dados será incluída quando as métricas "
        r"daquele modelo estiverem calculadas sobre os mesmos 21 pontos com $t>0$."
    )


def remover_secao_existente(doc, i_titulo: int, anchor) -> int:
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
    i_conc = find_paragraph(doc, "CONCLUSÕES", style_prefix="Heading 2")
    anchor = ps[i_conc]._p
    prev = anchor.getprevious()
    if prev is not None and prev.tag == qn("w:p") and not "".join(prev.itertext()).strip():
        anchor = prev

    i_res = find_paragraph(doc, "RESULTADOS E DISCUSSÃO", style_prefix="Heading 2")
    existentes = [i for i, p in enumerate(ps) if p.text.strip() == TITULO_SECAO and i > i_res]
    if existentes and not substituir:
        sys.exit("A seção já existe no relatório. Use --substituir para reescrevê-la.")

    copia = backup(DOC_PATH)
    print(f"Backup salvo em: {copia}")
    if existentes:
        print(f"Removidos {remover_secao_existente(doc, existentes[0], anchor)} elementos da versão anterior.")

    i_pinn = find_paragraph(doc, "Modelagem Híbrida: Redes Neurais Informadas pela Física (PINN)")
    refs = {"heading": ps[i_pinn]._p, "subheading": ps[i_pinn + 1]._p, "body": ps[i_pinn + 2]._p}
    i_cap = next(i for i, p in enumerate(ps) if p.text.startswith("Figura 4.X"))
    refs.update({"figure": ps[i_cap - 1]._p, "caption": ps[i_cap]._p, "source": ps[i_cap + 1]._p})

    writer = SectionWriter(doc, refs, anchor)
    conteudo(writer)
    pintar(writer.inserted)
    novas = add_references(doc, REFERENCIAS_NOVAS)
    doc.save(str(DOC_PATH))
    print(f"Seção escrita: {len(writer.inserted)} elementos inseridos (em vermelho).")
    print(f"Referências adicionadas: {len(novas)}")


if __name__ == "__main__":
    main()
