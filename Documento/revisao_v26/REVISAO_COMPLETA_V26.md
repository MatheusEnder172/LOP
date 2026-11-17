# Revisão completa do relatório (v26)

Feita em 15/11/2026 sobre `RELATÓRIO FINAL LOP_v26_limpo.docx` (texto inteiro, 187 comentários do Google Docs, lista de referências e Apêndices A a C). Nada foi alterado no Word.

Como as referências foram conferidas: as 92 entradas da lista foram buscadas no Crossref; as que não bateram foram buscadas na web; as quatro fontes que estão em `Artigos base/` (Bortot Coelho 2017, Balarini et al. 2025, Sansana et al. 2024, Shah et al. 2025) foram abertas e comparadas com o que o texto atribui a elas. "Não localizada" quer dizer que não achei nem no Crossref nem na busca; não é prova de que não existe, mas é o que a banca também vai encontrar.

Ordem deste arquivo: (1) o que mais vale olhar num TCC e pode estar passando; (2) inconsistências de conteúdo; (3) remissões e numeração; (4) redação; (5) revisão bibliográfica; (6) lista de referências, entrada por entrada.

---

## 1. Pontos de um TCC que podem estar sendo esquecidos

1. **Partes vazias.** Resumo, Abstract e palavras-chave estão com "Aa". Seção 5.3 (PINN) só tem título. "Comparação final" é uma imagem solta sem texto nem legenda. Conclusões vazias. Apêndice C só tem o título, e o texto da PINN manda o leitor para ele (chamando de "Apêndice F").
2. **Objetivos, resultados e conclusão amarrados.** Cada objetivo específico precisa de uma resposta explícita na conclusão. Hoje o objetivo da PINN fala em "estimando os parâmetros cinéticos durante o treinamento", o que a Seção 4.4 não faz mais (item 2.1). O último objetivo termina em ponto e vírgula.
3. **Comparação dos cinco modelos em base única.** Falta a tabela final com os mesmos 21 pontos, a mesma unidade, o mesmo η e os mesmos números do white-box. Hoje isso não fecha (itens 2.2 e 2.3).
4. **O resultado que a banca vai perguntar.** No teste cego, o black-box (RMSE 0,018) é melhor que o serial (0,020) e que o paralelo (0,027). A Seção 5.5 já trata disso com cuidado; a conclusão precisa partir daí: o ganho do híbrido não está no erro do teste cego, e sim na validação cruzada (0,033 contra 0,044), na dispersão entre redes (0,004 contra 0,039), no respeito aos balanços e no E4. Com 21 pontos, diferenças de 0,002 não permitem dizer que um modelo é melhor que outro.
5. **Lista de símbolos e siglas.** O documento tem muitos símbolos e alguns mudam de sentido (item 2.14). Uma lista no início resolve boa parte.
6. **Sumário e listas.** O sumário está desatualizado (lista "4.5.4 Linhas de Base", que não existe no corpo, e não lista a subseção da PINN na Revisão). Faltam lista de figuras e de tabelas, se o modelo da disciplina exigir.
7. **Parte experimental dos ensaios novos.** Para a banca é a única parte de laboratório feita pelo grupo. Faltam: procedência e lote do ustulado, preparo e padronização do ácido, equipamento e curva de calibração da absorção atômica, se houve réplica, e o efeito de retirar alíquotas de 200 mL. A frase "verificou-se que os valores registrados correspondem a g/L" passa a ideia de que a unidade foi deduzida depois; vale dizer de onde ela vem.
8. **Limitações e trabalhos futuros.** Itens que já aparecem espalhados e merecem um parágrafo próprio: temperatura e agitação fixas (os modelos não valem fora de 40 °C e 1000 rpm), 16 ensaios, teste cego com 3 ensaios, sem réplicas, problema inverso com parâmetros no limite em 12 de 16 ensaios, ensaios novos com E1 e E4 acima do limite.
9. **Reprodutibilidade.** Versões de Python, PyTorch, Optuna e scikit-learn, e onde está o código (repositório). Hoje só as sementes aparecem.
10. **Quem está na banca.** O "Julio" dos comentários é o autor de Balarini (2008, 2009, 2025). Tudo o que o texto atribui a esses trabalhos precisa estar exatamente como está neles (itens 2.4 e 2.5).
11. **Equilíbrio entre as partes.** O serial ocupa a Seção 4.6, quase toda a 5.5 e cerca de 40 páginas de apêndice; o paralelo tem duas páginas de método e não descreve o treino (comentário C144). A banca nota a diferença.
12. **Vocabulário interno.** Nos apêndices sobraram rótulos do desenvolvimento que o leitor não conhece: "v1", "v2", "Fase B", "Fase D", "Tentativa B2 511", "D1", "D2", "protocolo antigo/novo".
13. **ABNT.** Citações em três formatos diferentes (item 4), "Fonte" antes ou depois da figura, legenda colada na imagem, termos estrangeiros sem itálico.
14. **Uso de IA.** Vale confirmar se a disciplina pede declaração. O risco maior não é o estilo, é a lista de referências (Seção 6).

---

## 2. Inconsistências de conteúdo

### Graves

**2.1. A PINN descrita na seção comum não é a PINN da Seção 4.4.**
- Objetivo específico e Tabela 4.1.1: "ks e α estimados no treinamento". Seção 4.4: ks fixo em 1,8 × 10⁴ µm/min, nenhum parâmetro estimado. O α nunca é definido no documento (comentário C94 já pede para tirar).
- Tabela 4.1.3.1 e parágrafo anterior: as três restrições entram na PINN "de forma branda", como penalizações (L_ic, L_mono, L_acid). Seção 4.4.1: condição inicial e limite estequiométrico são impostos de forma exata pela arquitetura (δ = g·B); só a irreversibilidade é penalização. L_ic e L_acid não existem na Seção 4.4.2.
- A PINN reporta média ± desvio de cinco redes; black-box, paralelo e serial reportam a média de dez. Na tabela final isso precisa de uma linha de explicação.
- Seção 4.4.1 dá erros em "p.p." (0,06 a 0,08 p.p.); o resto de Métodos usa a escala de 0 a 1.

**2.2. Duas convenções de η no mesmo documento.**
- Seções 4.1, 5.1, 5.2 e 5.5: η nominal (zinco total, 0,65 g/g) → E1 a E4 com 0,75; 1,25; 2,25; 0,40.
- Seções 4.5 e 5.4 (paralelo): η_real → 0,799; 1,327; 2,396; 0,425. E a abertura da 5.4 diz que "o white-box emprega a razão molar nominal", o que contradiz a tabela da própria seção.
- Consequências visíveis:
  - RMSE do white-box no mesmo ensaio com três valores. E2: 0,116 (5.1), 0,117 (5.2, 5.5, B.6), 0,1186 (5.4). E4: 0,037, 0,036 e 0,0143. E1: 0,082 e 0,081. E3: 0,071, 0,072 e 0,0719.
  - 5.1 e B.6: "todas as medições" de E1 e E4 acima do limite. 5.4: "cinco das seis".
  - Limite de E4: 0,40 na Tabela 4.1.2.1 e 0,425 na tabela da 5.4.
- A frase da 4.1.3 "qualquer conversão superior a η tornaria negativa a concentração de ácido" só vale na convenção nominal. Como a conversão é referida ao ZnO (61,1 %) e o η ao zinco total (65 %), um leitor atento calcula 1,064·η. Falta uma frase dizendo por que o grupo manteve a convenção da dissertação (o patamar medido com η = 0,5 foi 0,49 a 0,50). O comentário C11 do Rodrigo é a base dessa frase.

**2.3. A Seção 4.1 promete o que o paralelo não cumpre.**
- 4.1 (abertura): todas as modelagens usam "a mesma partição" e "o mesmo protocolo de avaliação".
- 4.1.1: o paralelo usa η_real (C95 pede para tirar com urgência) e "protocolos de validação que retiram ensaios inteiros em rodízio"; a frase seguinte lista o teste 7, 8, 14 só para black-box, PINN e serial.
- 5.4: o paralelo é avaliado nos Ensaios 7, 8 e 14, com as mesmas quatro dobras e dez modelos com sementes 42 a 51.
- A Seção 4.5 não descreve nada disso: nem as dez sementes, nem as dobras, nem a equação de η_real ("Equação 4.XX"), nem a "terceira referência" citada na 4.1.4.
- Seção 5.4 inteira em p.p., com "Tabela 1", "Tabela 2", "Figura 2", "Figura XX" e "(–)" nos cabeçalhos.

**2.4. A constante ks.**
- A Seção 5.1 revela que ks foi obtido a 30 °C; a Revisão não diz isso e a Tabela 4.2.2.1 lista ks ao lado de "40 °C", como se fossem da mesma condição. A informação e o teste de sensibilidade (RMSE de 0,070 para 0,072) deveriam aparecer já em Métodos.
- A fonte muda: "ks de Balarini (2009)" na 3.1.4; "Balarini et al., 2025" na 3.1.5 e na 5.1.
- 5.1 remete à "equação de Arrhenius apresentada na Seção 3.1.5"; ela está na 3.1.4 (Eq. 3.1.4.1).

**2.5. O que o texto atribui a Balarini et al. (2025).**
- Seção 3.1.3: os dados "desviam" do modelo da conversão progressiva (Bortot Coelho, 2017; Balarini et al., 2025). O resumo do artigo diz, literalmente, que a lixiviação "follows the progressive conversion model and is controlled by the chemical reaction step". A conclusão do artigo fala em partícula que diminui, sem camada de produto, com controle químico, que é o que o relatório usa. Como o autor está na banca, é melhor escrever o que o artigo conclui (controle por reação química, partícula que encolhe sem camada de produto) e não dizer que ele descartou o modelo da conversão progressiva. Vale confirmar a redação com o orientador.
- Conferido e correto: Ea = 13,45 kJ/mol; ordem 0,7; ks = 3,00 × 10⁻² cm/s; ensaios com 6 g/L de H₂SO₄ (≈ 0,06 mol/L); 30 °C.

**2.6. Ferrita e patamar de conversão (Seção 3.1.1).**
- O texto diz que a ferrita "retém entre 10% e 15% do zinco total" e impõe "patamar de 85% a 90%", citando Bortot Coelho (2017). A dissertação diz "em torno de 10%". Pelos números do próprio relatório, o ZnO guarda 61,1/65 = 94 % do zinco.
- A frase seguinte diz que a conversão do trabalho é referida ao ZnO, de modo que esse patamar nem se aplica. O parágrafo pode perder os números.

**2.7. Granulometria.**
- Seção 3.1.5: "diâmetro médio de aproximadamente 29 µm". Na dissertação, a média da distribuição é 41,28 µm. 29 µm é a mediana do RRB com D' = 41,65 e m = 1,022.
- Mesma seção: partículas "inferiores a 2 µm até superiores a 74 µm". Seção 4.2.1: faixa de 0,1 a 297 µm. Seção 4.6.1: integração "entre 0,01 e 297 µm". São três limites inferiores diferentes; white-box e serial deveriam declarar o mesmo.

**2.8. Frase invertida na restrição (ii) da Seção 4.1.3.** "a taxa de retração é deve ser negativa, pois corresponderia ao crescimento das partículas" → a taxa **não pode** ser negativa.

**2.9. Seção 5.5, ensaios novos.** "as previsões do modelo superam o limite estequiométrico em todos os instantes e, em E1, diminuem de 0,87 em 1 min para 0,81 em 15 min" → são **as medições** (já avisado na v25, continua no texto).

### Médias

**2.10.** Seção 3.1.1: "o ácido é alimentado em quantidade inferior à estequiométrica". Vale só para η = 0,5 (4 dos 16 ensaios).

**2.11.** Introdução e objetivos dizem que os ensaios novos são "em condições intermediárias". As Seções 4.1.2 e B.4 dizem que o E4 é extrapolação.

**2.12.** Apêndice A.4: as médias e desvios da padronização foram calculados com os 13 ensaios e usados dentro das dobras. Isso contraria a regra que a Revisão (3.2) e a 4.1.1 enunciam. O texto admite; falta dizer por que não importa (são só as entradas, três valores de planejamento, sem informação da saída).

**2.13.** Seção 3.2.2 (PINN): "De maneira similar ao SVR, o parâmetro ε delimita a margem aceitável de tolerância." É sobra de uma versão antiga. O SVR não é explicado em lugar nenhum e a frase não tem relação com a figura. O SVR aparece mais duas vezes (3.2.3 e 3.3.2.2) sem ter sido apresentado.

**2.14. Símbolos com mais de um sentido.**
- ν: taxa de retração (todo o texto), parâmetro do núcleo de Matérn (4.5.3) e coeficiente estequiométrico (4.5.5), os três dentro da Seção 4.5.
- X_i e Y_i nas equações das métricas (3.2.4) são "previsto" e "medido", enquanto X é a conversão no resto do documento.
- B: tamanho do lote (4.6.5), limite superior da PINN (4.4.1) e reagente sólido (3.1.5).
- θ e Θ: parâmetros do problema inverso e pesos da rede; a Eq. 4.XX.17 usa θ para os pesos.
- Eq. 4.XX.11 usa m_τ e s_τ; o texto logo abaixo fala em μ_ln t e σ_ln t.
- X, X_Zn, conversão "de zinco", "do ZnO", "da ZnO"; v e ν (Seção 4.2.2 usa ∂v/∂D); D' e D63,2.
- "white box" (10 vezes) e "white-box" (58 vezes).

**2.15.** Apêndice A.2 chama de "teto" o erro mínimo possível (0,014). É um piso. O termo se repete em B.1, B.3 e nas figuras.

**2.16.** Apêndice A.2: "esses parâmetros [a₂, b₂, c] descrevem a etapa lenta". Nos Ensaios 6 e 7, b₁ ≈ 0,3 e b₂ = 4, isto é, os papéis estão trocados. Uma frase reconhecendo isso evita a pergunta.

**2.17.** (Retirado depois de conferir nos CSV.) Seção 5.2: "cerca de oito vezes o erro de ajuste" está certo com os valores sem arredondar (0,0437 / 0,0055 = 7,9), e "entre 0,45 e 0,51" em E4 também, pois vale para a curva inteira (0,446 a 0,508), não só para os seis instantes da Tabela B.16.

**2.18.** Seção 4.3.3 chama o teste cego de "etapa de validação" e "ensaios de validação"; no resto do texto validação é a validação cruzada.

**2.19.** Seção 3.2.2: "a ReLU [...] inviabiliza sua aplicação em PINNs". É forte demais; a própria 4.4.1 dá a justificativa correta (derivada descontínua e segunda derivada nula). Mesma seção, início da 3.2: aprendizado de máquina definido como generalizar a partir de "dados empíricos rotulados", o que exclui os outros dois paradigmas descritos logo depois.

### Conferido e sem problema

Contas e números que refiz e batem: massas da Tabela 4.1.2.1; 5.490 parâmetros do black-box; 91, 104, 112, 780 e 960 registros; N_m = 1.963 e 71 % dos pontos de colocação antes de 0,5 min; 12 % e 51 % da escala do tempo; 45.472 atualizações; estatísticas da Tabela A.9; contagem de parâmetros no limite (12 de 16; 7, 7 e 5); RMSE do white-box por razão molar (0,025; 0,123; 0,053; 0,033) e do serial (0,014 a 0,018) a partir das Tabelas B.10; reduções de 74 % e 66 %; RMSE do white-box em E1 e E4 a partir da Tabela B.12 (0,081 e 0,036, o que indica que os valores da Seção 5.1 é que diferem); faixa de 3 a 300 g/L; totais das Tabelas B.13 e B.17.

---

## 3. Remissões e numeração

São 87 marcadores provisórios ("XX", "X.X") no texto. Além deles, há remissões com número definido que apontam para o lugar errado, quase todas porque a seção comum 4.1 entrou depois e o white-box virou 4.2:

| Onde | Está | Deveria ser |
| :-- | :-- | :-- |
| 3.1.2 | Tabela 3.XX | Tabela 3.1.2.1 |
| 3.1.5 e 3.1.6 | conversão para base numérica "na Seção 4.2.1" e depois "na Seção 4.2.2" | 4.2.1 nas duas |
| 3.2.4 (fim) | Seção 3.4.1 | 3.3.1 |
| 3.3.3 | PINN (Seção 3.2.2) | conferir depois de separar a subseção da PINN |
| 4.1.1 | Figura 4.XX.9(a), que só aparece 30 páginas depois (C96) | trazer a figura ou tirar a remissão |
| 4.1.2 | duas equações com o número (4.1.2.2) | a primeira é (4.1.2.1) |
| 4.1.4 | Equações (3.2.4.XX); as equações de R², RMSE e MAE não têm número | numerar |
| 4.2.1 | Seção 3.1.4.1; Equação (4.1.1.2) | 3.1.6; (4.2.1.2) |
| 4.2.2 | Equações (4.1.2.1) a (4.1.2.7), sete ocorrências; Seção 3.1.4.1; Seção 3.1.4; Seção 4.1.3 | (4.2.2.x); 3.1.6; 3.1.5; 4.2.3 |
| 4.2.3 | Equação (4.1.2.6); "Seções 4.3 a 4.5" para os híbridos | (4.2.2.6); 4.4 a 4.6 |
| 4.3.2 e 4.3.3 | serial como "Seção 4.5"; Equações (3.24) a (3.27); (4.X.X) | 4.6; não existem com esses números |
| 4.3.3 | uma imagem solta depois da "Fonte" da Figura 4.3.1 | apagar |
| 4.4 | equações (4.3.1) a (4.3.7); "Figura 4.3.1 – Arquitetura da PINN" repete o número da figura do black-box; Seção 4.3.1; Equações (4.1.2.6) a (4.1.2.8); Seções 4.2.3 e 4.5.1; Seções 4.2.7 e 4.5.6; Apêndice F | (4.4.x); Figura 4.4.1; 4.4.1; (4.2.2.x); 4.2.3 e 4.6.1; 4.3.3 e 4.6.6; Apêndice C |
| 4.5 | seção 3.4.2; equações sem número; Equação 4.XX; figura 4.XX.3 | 3.3.2.2 |
| 4.6 | figuras e equações "4.XX.n" com numeração saltada (5, 6, 7, 8, 9, 10, 11, 15, 16, 17, 22, 28); "Figura 4.X.4"; "Equação 4.XX.4" (não existe; é a 3.1.6.5); "Apêndice B" para o problema inverso (três vezes); "Seção E.8"; "Figura B.2"; "Eq. D.8" na Tabela 4.XX.8; "Seção 5.XX" | 4.6.n em sequência; Apêndice A.1; B.3; A.2; A.3 |
| 5.1 | "Conforme discutido na Seção 4.1"; Tabela 5.X.1 e 5.X.2; Figura 5.X.X; Apêndice XX; um parágrafo solto "Ensaio" antes da tabela | 4.2; 5.1.n |
| 5.2 | Figura 5.X.1 e 5.X.2; Tabela 5.X.2 | 5.2.n |
| 5.5 | legendas "Tabela 5.4.1", "Figura 5.4.1", "Tabela 5.4.2", "Figura 5.4.2" e o texto chama de 5.5.n; "Tabela 4.1.3" e "Tabela 4.1.2"; legenda da tabela dos ensaios novos cita colunas que não existem | 5.5.n; 4.1.3.1 e 4.1.2.1 |
| Sumário | 4.5.4 Linhas de Base; falta a subseção da PINN em 3.2 | atualizar |
| 3.2.2 | o título "Algoritmos de regressão em engenharia de processos" aparece duas vezes seguidas | apagar um |

---

## 4. Redação

**Erros que mudam o sentido ou travam a leitura**
- 3.2.2: "é interessante comentar sobre as redes neurais [...], destacam-se na engenharia química" (frase sem sujeito); "extrair leis razoáveis".
- 3.2.2 (PINN): "Outra arquitetura [...] fundamental de ser citada é as Redes"; "Esta arquitetura são redes neurais"; "physical-informed" (é physics-informed); "Fonte: Adaptado de Farea; Yli-Harja; Emmert-Streib, 2024 et al (2024)".
- 4.2.2: "se deslocando de forma rígida em direção à menores de valores"; "reduzindo-a assim" (o balanço).
- 4.4.1: "até o instante t em que z é a saída linear da última camada" (duas frases fundidas).
- 4.5.5: "Devido ao fato do modelo [...] não conhecer [...], e a soma [...] pode ferir" (frase sem oração principal); "As restrições são efetivadas [...] e é conferida".
- 4.5.2: "O modelo fenomenológico utilizado é o experimental (Seção 4.2)".
- 4.6.1: "Por esse motivo, a relação X(δ) foi calculada uma única vez" (o motivo foi cortado); "No modelo fenomenológico, essa função é dada pela lei cinética" (a função é ν(t), mas o parágrafo anterior fala de X(δ)); "três elementos" seguidos de uma lista que não deixa ver quais são os três.
- 4.6.7: "mesmo que ν é sempre positiva e a curva X(δ) é crescente, essa condição já é satisfeita"; "A segunda operação reforça que relação X(δ) decorre apenas da granulometria".
- 5.2: "e os dados contêm a informação que falta [...], e a rede a reproduz"; "e o ensaio E4 expõe a limitação mais séria desta modelagem, na qual com razão molar de 0,40".

**Erros de digitação e concordância**
"Noo Ensaio 4" (5.2); "Por tanto" (5.5); "(MAE)e" (legenda 5.2.1); "epara" e "que foi usada" (4.6.2); "Apêndic A" (4.6.3); "não linear.." e "constante.." (4.6.4 e 4.6.7); "Xavier,indicada", "2009).Para", "(4.XX.6).A base"; "Zn⁺²"; "pH inferiores a 5,0;" e "RMSE de 0,070;" (ponto e vírgula no lugar da vírgula); "reduziriam-se"; "Embora [...] recorrem"; "ainda que as maiores consomem"; "determinam a arquitetura" (sujeito "a forma"); "Sansana et al. (2024) destaca"; "a parte" e "comparado à experimentos" (crase); "primeiro princípios"; "a obtenção de um mínimo local" (o texto fala em maximizar); "A descrição desse processo, apoia-se"; "Segundo Balarini, (2009)"; "Bortot Coelho (2017), propôs"; "(Balarini et al. 2025)"; legenda da Figura 3.1.3.1 termina em vírgula; "adimensional e entre 0 e 1 de conversão"; "porém, observou-se que [...], contudo, foi menor"; "é necessário estabelecer o embasamento [...] necessário".

**Formato das citações.** Há pelo menos cinco: "(Hastie et.al, 2009)" e "(Hastie; Tibshirani; Friedman, 2009)"; "(Russel et.al, 2010)" para um livro de dois autores (Russell e Norvig); "(MURPHY, 2012)" em maiúsculas; "(Chicco, D.; Warrens, M. J.; Jurman, G, 2021)" com iniciais; "(Sutton, Barto, 2018)" com vírgula; "Goodfellow et.al"; ponto final antes do parêntese da citação em vários parágrafos da 3.2. "Kingma; Ba" aparece com 2017 (três vezes) e com 2015 (duas); a lista tem 2015. "Schweidtmann et al., 2023" no texto e 2024 na lista (o correto é 2024).

**Frases de enchimento que o orientador já criticou.** "Neste sentido, com intuito de encerrar o tópico de aprendizado de máquina, é fundamental dizer que"; "É importante dizer que"; "Em primeiro lugar, é essencial dizer que"; "é interessante comentar que"; "Por fim, é interessante dizer que"; "Dessa maneira, primeiramente, é interessante comentar". Estão concentradas na 3.2 e na 4.4.

---

## 5. Revisão bibliográfica

### 5.1. O que é usado em Métodos e não tem base na Revisão

| Usado em | O quê | Situação |
| :-- | :-- | :-- |
| 4.5 | Processo Gaussiano, núcleo de Matérn, verossimilhança marginal | não aparece na Revisão; em Métodos só Rasmussen e Williams (2006). Colegas perguntaram o que é verossimilhança marginal (C150) |
| 4.5 | regressão isotônica | idem (C155); só Barlow et al. (1972) |
| 4.4 | solução tentativa com restrição exata (Lagaris, Likas e Fotiadis, 1998; Mattheakis et al., 2022; Cuomo et al., 2022) | citados em Métodos, **fora da lista de referências**, e a Revisão só descreve a PINN com penalização |
| 4.4 | balanceamento das parcelas da perda (Wang, Teng e Perdikaris, 2021); L-BFGS (Liu e Nocedal, 1989) | citados, **fora da lista** |
| 4.2 | Método das Características | nenhuma fonte na Seção 4.2.2. Sugestões: Randolph e Larson (1988), já na lista; Ramkrishna (2000); LeBlanc e Fogler (1987), já na lista |
| 3.1.5 | distribuição RRB | sem a fonte original (Rosin e Rammler, 1933) nem um livro de tratamento de minérios |
| 4.1.2 | absorção atômica | sem referência do método |
| 3.2.2 | inicialização de Xavier e de He | só pela resenha de Datta (2020). Glorot e Bengio (2010) já está na lista; falta He et al. (2015) |
| 3.2.2 | PINN | a subseção define PINN citando Farea et al. (2024) e Terven et al. (2025); Raissi et al. (2019) só aparece no último parágrafo |

### 5.2. A maior lacuna: trabalhos anteriores sobre lixiviação com aprendizado de máquina e modelos híbridos

A Introdução afirma que a aplicação de modelos híbridos à lixiviação de zinco "permanece pouco explorada, sobretudo em formulações que preservam o balanço populacional" (C2 e C3 já discutem se dá para afirmar). A Revisão não tem nenhuma subseção que sustente isso, e a Seção 3.3.3, que promete "aplicação em sistemas de lixiviação" no título, só resume as diretrizes de Sansana. As quatro referências que a Introdução usa para o estado da arte são justamente das que não existem como estão na lista (Zhang 2022, Zhou 2023, Song 2025, Nogueira 2026).

Trabalhos reais, conferidos no Crossref, que montam essa subseção:

- **Os artigos do próprio orientador**, que hoje não são citados: Coelho, Balarini, Araújo, Miranda, Peres et al. Roasted zinc concentrate leaching: population balance modeling and validation. *Hydrometallurgy*, v. 175, p. 208-217, 2018 (DOI 10.1016/j.hydromet.2017.11.013). Bortot Coelho et al. A population balance approach to predict the performance of continuous leaching reactors: model validation in a pilot plant [...]. *Hydrometallurgy*, v. 194, 105301, 2020. São a versão publicada em periódico do modelo que o trabalho inteiro usa.
- Zhou, Cheng, Huang e Yang. Hybrid model of mass-concentration conservation and neural network for zinc leaching. *JOM*, v. 75, n. 5, p. 1684-1694, 2023 (DOI 10.1007/s11837-023-05755-0). É o "único que vimos" do comentário C3 e o mais próximo do tema.
- Zhang, Mao, Jia e He. Real time optimization based on a serial hybrid model for gold cyanidation leaching process. *Minerals Engineering*, v. 70, p. 250-263, 2015. Híbrido serial em lixiviação.
- Dong, Zhang e Zhou. Intelligent hybrid modeling of complex leaching system based on LSTM neural network. *Systems*, v. 11, n. 2, 78, 2023.
- Bravo-Gutiérrez, Henríquez-Vargas, Díaz-Quezada e Estay. Towards generalized heap leaching modeling: a hybrid approach of phenomenological-principles and neural networks. *Minerals Engineering*, v. 242, 110197, 2026.
- Saldaña et al. Mineral leaching modeling through machine learning algorithms: a review. *Frontiers in Earth Science*, v. 10, 816751, 2022. McCoy e Auret. Machine learning applications in minerals processing: a review. *Minerals Engineering*, v. 132, p. 95-109, 2019.
- Crundwell. Progress in the mathematical modelling of leaching reactors. *Hydrometallurgy*, v. 39, p. 321-335, 1995 (balanço populacional em lixiviação).
- Para a arquitetura paralela com restrições físicas: Thompson e Kramer. Modeling chemical processes using prior knowledge and neural networks. *AIChE Journal*, v. 40, n. 8, p. 1328-1340, 1994. Para PINN: Karniadakis et al. Physics-informed machine learning. *Nature Reviews Physics*, v. 3, p. 422-440, 2021.

Não li o texto completo desses artigos (só títulos, resumos e metadados). Antes de citar, alguém do grupo precisa abrir cada um e confirmar o que ele sustenta.

### 5.3. O que sobra

- **Seção 3.1.2 (Sistemas de lixiviação).** Uma página e meia e uma tabela sobre lixiviação in situ, pilhas, biolixiviação, cubas, Pachuca e autoclaves, que o trabalho não usa. É onde estão dez das referências que não existem como citadas. Um parágrafo dizendo que concentrados finos são lixiviados em tanques agitados, apoiado em Habashi, Gupta e Mukherjee e Free, resolve as duas coisas de uma vez.
- **Seção 3.2.1.** Aprendizado não supervisionado e por reforço não são usados; cabe uma frase.
- **Min-max e tanh/sigmoide** são usados só pela PINN; SiLU e normalização de camada só aparecem na busca de hiperparâmetros do apêndice.

### 5.4. Qualidade das fontes

- Fontes fracas para afirmações simples, com substituto já na lista: Datta (2020, resenha no arXiv) e Sun, Liang e Cui (2021) → Goodfellow et al. (2016) e Haykin (2009); Jayalakshmi e Santhakumaran (2011) → Bishop (2006) ou LeCun et al. (1998); Guan e Burton (2022, engenharia de estruturas) para viés e variância → Hastie et al. (2009).
- Duas figuras do núcleo não reagido e da conversão progressiva são "adaptadas" de artigos sobre digestão anaeróbia (Da Rocha et al., 2013) e sobre extração de óleo de plantas (Mousa e Najem, 2024). Levenspiel (2000) é a fonte natural das duas.
- Quase todas as afirmações da Seção 3.3 vêm de um único artigo (Sansana et al., 2024; 21 citações). Conferi no PDF: as quatro arquiteturas, o nome da arquitetura aumentada por conhecimento e as diretrizes estão lá. Dois ajustes: o artigo fala em "hybrid models diamond", não "Hybrid Modeling Diamond"; e diz que **a serial e a aumentada por conhecimento** são as preferidas para extrapolação, enquanto o item da 3.3.3 atribui isso só à segunda.
- A afirmação "a PINN não corresponde a nenhum dos vértices do diamante" (3.3.3) é do grupo, não de Sansana; vale deixar isso claro na frase (C91 pergunta como a PINN vai ser descrita).

---

## 6. Lista de referências, entrada por entrada

Total: 92 entradas.

### 6.1. Não existem como estão na lista (20)

Em 14 delas existe um artigo real do mesmo primeiro autor, com outro título ou outro periódico. Em 6 não achei nada. Para várias, o comentário antigo do Google Docs no ponto da citação traz uma terceira versão, diferente da lista, o que indica que a lista foi reescrita sem conferência (o comentário C184 registra "lista atualizada" em 14/11).

| Entrada na lista | O que encontrei | Onde é citada |
| :-- | :-- | :-- |
| AIZHULOV et al., 2024. Fast surrogate models [...]. *Hydrometallurgy* 224, 106260 | Não existe. Real: Aizhulov, Tungatarova, Kurmanseiit, Shayakhmetov. Artificial neural networks for mineral production forecasting in the in situ leaching process: uranium case study. *Processes*, v. 12, n. 10, 2285, 2024. A versão do comentário C16 (*Journal of Hydrology* 630) também não existe | 3.1.2 |
| ALVÁN OLIVEIRA et al., 2023. *Minerals Engineering* 195, 108020 | Não localizada, nem esta nem a do comentário C24 | 3.1.2 |
| BRAVO-GUTIÉRREZ et al., 2026. *Minerals* 16(2), 145 | Não existe. Real: Towards generalized heap leaching modeling [...]. *Minerals Engineering* 242, 110197, 2026. É sobre pilhas, e o texto a cita para lixiviação em cubas | 3.1.2 |
| DA ROCHA, S. D. F. et al., 2013. Leaching kinetics of chalcopyrite [...]. *Hydrometallurgy* 138 | Não existe. Real (comentário C30): da Rocha, Paetzold, Kanswohl. The shrinking core model applied on anaerobic digestion. *Chemical Engineering and Processing*, v. 70, p. 294-300, 2013 | Figura 3.1.3.1 |
| DONG, Z. et al., 2023. *Hydrometallurgy* 219, 106095 | Esse número de artigo é o "Editorial Board" do volume. Real (comentário C23): Dong, S.; Zhang, Y.; Zhou, X. Intelligent hybrid modeling of complex leaching system based on LSTM neural network. *Systems*, v. 11, n. 2, 78, 2023 | 3.1.2 |
| FILIPPOU; DEMOPOULOS, 1992. Chemical reaction and mass transfer [...]. *Hydrometallurgy* 28(3) | Não existe (a do comentário C37 também não). Real: A reaction kinetic model for the leaching of industrial zinc ferrite particulates in sulphuric acid media. *Canadian Metallurgical Quarterly*, v. 31, n. 1, p. 41-54, 1992 | Fonte da Tabela 3.1.5.1 |
| KIM et al., 2026. *Journal of Hazardous Materials* 501 | Não existe. Real: Kim, Kang, Pae, Pak, Jo. Predicting copper leaching from slag: an interpretable machine learning approach under oxidative sulfuric acid conditions. *RSC Advances*, v. 16, n. 21, p. 19320-19333, 2026 | Fonte da Tabela 3.1.2.1 |
| MOUSA; NAJEM, S. A., 2024. *Chemical Engineering & Technology* 47(4) | Não existe. Real (comentário C33): Mousa Al-zobai; Najem, M. Extraction of oil from plants. *IJSRSET*, v. 11, n. 6, p. 88-97, 2024 | Figura 3.1.3.2 |
| NIE et al., 2026. *Bioresource Technology* 415 | Não existe. Real: Nie, Yang, Tian, Li, Liu. Review of numerical simulations for parameter control in heap bioleaching of copper sulfide ore. *Minerals*, v. 16, n. 6, 568, 2026 | 3.1.2 |
| NOGUEIRA et al., 2026. *Resources, Conservation and Recycling* 220 | Não existe. Real: Nogueira, Sosa, Dias, Coutinho, Schaeffer. An applied machine learning framework for waste lithium-ion battery leaching [...]. *Green Chemistry*, v. 28, n. 1, p. 277-294, 2026 | Introdução |
| OUASSEL et al., 2025. *J. Radioanalytical and Nuclear Chemistry* 334 | Não localizada, nem esta nem a do comentário C22 | 3.1.2 |
| PROSSER, 1996. The interpretation of rate data in hydrometallurgy [...]. *Hydrometallurgy* 42(2), 195-216 | Não existe. Real: Review of uncertainty in the collection and interpretation of leaching data. *Hydrometallurgy*, v. 41, n. 2-3, p. 119-153, 1996. É a base do critério de 25 kJ/mol, citada seis vezes | 3.1.4 |
| RAZZANI et al., 2026. *J. Environmental Chemical Engineering* 14(2) | Não existe. Real: Razzani, Hashemipour, Karimi. Experimental investigation of copper leaching from flash furnace dust and integrated mathematical-artificial neural network [...]. *Case Studies in Chemical and Environmental Engineering*, v. 13, 101319, 2026 | Fonte da Tabela 3.1.2.1 |
| SALDAÑA et al., 2022. Application of machine learning in hydrometallurgical processes [...]. *Minerals* 12(9) | Não existe. Real: Saldaña, Neira, Gallegos, Salinas-Rodríguez, Pérez-Rey, Toro. Mineral leaching modeling through machine learning algorithms: a review. *Frontiers in Earth Science*, v. 10, 816751, 2022 | Introdução |
| SCOTT et al., 1986. *Metallurgical Transactions B* 17(3) | Não localizada. Sustenta a estrutura de espinélio da ferrita. Alternativas reais: Elgersma et al., Acidic dissolution of zinc ferrite, *Hydrometallurgy*, v. 29, p. 173-189, 1992; Filippou e Demopoulos (1992, acima) | 3.1.5 |
| SONG et al., 2025. *Chemical Engineering Journal* 502 | Não localizada | Introdução |
| SURYA et al., 2025. *Hydrometallurgy* 231 | Não localizada, nem esta nem a do comentário C25 | 3.1.2 |
| WENG, W. et al., 2025. *Minerals Engineering* 222 | Não existe. Real: Weng, Lan, Tang, Chen, Xia. Acid leaching of copper from copper slag based on machine learning analysis. *Separation and Purification Technology*, v. 379, 135025, 2025. É lixiviação ácida de escória; o texto a cita para autoclaves de laterita niquelífera | 3.1.2 |
| ZHANG, L. et al., 2022. *Mineral Processing and Extractive Metallurgy Review* 43(5) | Não localizada | Introdução |
| ZHOU, X. et al., 2023. *Hydrometallurgy* 218, 106110 | Não existe. Real (comentário C27): Zhou, C.; Cheng; Huang; Yang, *JOM*, 2023 (item 5.2) | Introdução, 3.1.2 |

Trocar a entrada pela referência real só resolve quando o artigo real sustenta a frase em que é citado. Em vários casos não sustenta (Weng, Bravo-Gutiérrez, Kim, Razzani), e o mais simples é cortar a frase junto, o que a redução da Seção 3.1.2 já faz.

### 6.2. Citadas no texto e ausentes da lista (5)

- CUOMO, S. et al. Scientific machine learning through physics-informed neural networks: where we are and what's next. *Journal of Scientific Computing*, v. 92, n. 3, 88, 2022.
- LAGARIS, I. E.; LIKAS, A.; FOTIADIS, D. I. Artificial neural networks for solving ordinary and partial differential equations. *IEEE Transactions on Neural Networks*, v. 9, n. 5, p. 987-1000, 1998.
- LIU, D. C.; NOCEDAL, J. On the limited memory BFGS method for large scale optimization. *Mathematical Programming*, v. 45, p. 503-528, 1989.
- MATTHEAKIS, M. et al. Hamiltonian neural networks for solving equations of motion. *Physical Review E*, v. 105, 065305, 2022.
- WANG, S.; TENG, Y.; PERDIKARIS, P. Understanding and mitigating gradient flow pathologies in physics-informed neural networks. *SIAM Journal on Scientific Computing*, v. 43, n. 5, p. A3055-A3081, 2021.

As cinco existem (conferidas no Crossref). O artigo de Mattheakis precisa ser aberto para confirmar que é dele o "fator exponencial" citado na 4.4.1.

### 6.3. Na lista e não citada (1)

RATHORE et al., 2024 (existe; não aparece no texto).

### 6.4. Existem, com erro na entrada (10)

| Entrada | Correção |
| :-- | :-- |
| BALARINI et al., 2008 | v. 21, **n. 1**, p. 100-110 (a lista tem n. 2) |
| BALARINI et al., 2025 | título com "sulfuric"; DOI 10.55905/oelv23n11-188; artigo e12422 |
| VENKATASUBRAMANIAN, 2019 | v. 65, **n. 2, p. 466-478** (a lista tem n. 1, p. 466-472) |
| SCHWEIDTMANN et al., 2024 | a lista está certa; no texto está 2023. Título com "modeling" |
| KINGMA; BA, 2015 | a lista está certa; no texto aparece 2017 três vezes |
| HABASHI, 1997 | "Principles of extractive metallurgy, v. 2: Hydrometallurgy" é da Gordon and Breach, **1970**. De 1997 é o "Handbook of extractive metallurgy" (Wiley-VCH), que é o que os comentários C8 e C15 indicavam. Decidir qual foi consultado |
| HERBST, 1979; SOHN; WADSWORTH, 1979 | a edição original é New York: Plenum Press |
| JACKSON, 1986 | Chichester: Ellis Horwood (Halsted Press é a distribuidora nos EUA) |
| SUN; LIANG; CUI, 2021 | tem versão publicada: *Asian Journal of Research in Computer Science*, v. 12, n. 4, p. 177-185, 2021 |

### 6.5. Conferidas e corretas (61)

Akiba 2019; Aster 2018; Ba 2016; Balarini 2009 (tese, repositório da UFMG); Barlow 1972; Bergstra 2011; Bergstra e Bengio 2012; Bischoff 1963; Bishop 2006; Bortot Coelho 2017 (dissertação, repositório da UFMG); Brierley 2001; Byrd 1995; Cawley e Talbot 2010; Chen e Ierapetritou 2020; Chicco 2021; Crundwell e Bryson 1992; Crundwell et al. 2011; Datta 2020; Elfwing 2018; Farea 2024; Fogler 2006; Free 2013; Fritsch e Carlson 1980; Glorot e Bengio 2010; Goodfellow 2016; Guan e Burton 2022; Gupta e Mukherjee 1990; Hastie 2009; Haykin 2009; He 2016; Hendrycks e Gimpel 2016; Jayalakshmi 2011; Kapoor e Narayanan 2023; Lakshminarayanan 2017; LeBlanc e Fogler 1987; LeCun 1998; Levenspiel 2000; Loshchilov e Hutter 2017 e 2019; Mitchell 1997; Murphy 2012; Paszke 2019; Pedregosa 2011; Pourbaix 1974; Pradhan 2008; Psichogios e Ungar 1992; Raissi 2019; Randolph e Larson 1988; Rasmussen e Williams 2006; Roberts 2017; Rumelhart 1986; Russell e Norvig 2010; Sansana 2021 e 2024; Shah 2025; Srivastava 2014; Sutton e Barto 2018; Szekely 1976; Terven 2025; von Stosch 2014; Wilcoxon 1945.

Cerca de 40 dessas tiveram correspondência exata no Crossref (título, autores, periódico, volume e páginas). As demais são obras que o Crossref não indexa bem (pré-publicações no arXiv, anais do NeurIPS e do ICLR, JMLR, livros clássicos); essas eu reconheço como obras reais e conhecidas, mas não tive um registro externo para comparar campo a campo. Para os livros, não conferi número de páginas nem edição.

---

## 7. Ordem sugerida de correção

1. Lista de referências (Seção 6) junto com o corte da Seção 3.1.2. É o item de maior risco diante da banca.
2. Decisão do grupo sobre o η (2.2) e adequação do paralelo (2.3), porque disso depende a tabela de comparação final.
3. PINN na seção comum (2.1), Apêndice C e Seção 5.3.
4. Itens 2.4 a 2.9, que são trocas pontuais de frase.
5. Subseção de trabalhos anteriores (5.2) e bases que faltam (5.1).
6. Remissões e numeração (Seção 3), de uma vez só, quando a estrutura estiver fechada.
7. Redação (Seção 4), Resumo, Conclusão e lista de símbolos.
