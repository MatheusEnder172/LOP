# Números do modelo v2 e de onde vêm

Todos conferidos em 09/11/2026 nos CSVs indicados (caminhos a partir de `Codigo_v4/Código/outputs/`). Ao escrever o texto, **leia os CSVs por script**; esta tabela é só um guia e um ponto de conferência. `SUB` = `etapa_3_2/subetapa_3_2_6_mlp_otimizacao`.

## 1. Modelo e protocolo

- **MLP v2:** comitê de 10 redes (sementes 42 a 51), arquitetura [90, 45, 22] residual, GELU, entrada ln t, 5.490 parâmetros, 928 épocas fixas, mini-lotes de 16, 780 registros de treino (13 ensaios × 60 nós). Saída ν = expm1(softplus(·)) > 0. Média das taxas antes do balanço populacional. Arquivos e hashes: `models_saved/mlp_v2/` e `SHA256SUMS.txt`.
- **Partição:** 13 ensaios de treino e validação cruzada; 3 de teste cego (7, 8 e 14). Validação cruzada com 4 dobras por ensaio: dobra 1 = {1, 5, 11, 16}; dobra 2 = {4, 10, 15}; dobra 3 = {3, 9, 13}; dobra 4 = {2, 6, 12}.
- **Métrica:** RMSE, R² e MAE de X_Zn nos instantes com t ≥ 0,5 min (7 por ensaio): 91 pontos no treino, 21 no teste cego, 112 no global.
- **Referências:** fenomenológico puro (mesmo balanço populacional, lei cinética de reação interfacial), v1 (configuração de referência da rede) e o "teto" = conversão calculada com as taxas do problema inverso.

## 2. Resultados principais (X_Zn)

Fonte: `SUB/fase_e/tabela_fase_e_metricas_XZn.csv`, `SUB/fase_a/tabela_fase_a_resumo.csv`, `SUB/fase_b2/tabela_fase_b2_finalistas.csv`.

| Conjunto | n | v2 RMSE | v2 R² | v1 RMSE | Fenomenológico RMSE |
| :-- | :-: | :-: | :-: | :-: | :-: |
| Treino (13 ensaios) | 91 | 0,0145 | 0,995 | 0,0229 | 0,0682 |
| Teste cego (7, 8, 14) | 21 | 0,0202 | 0,888 | 0,0353 (R² 0,657) | 0,0780 (R² −0,675) |
| Global | 112 | 0,0157 | 0,9935 | 0,0257 | 0,0702 |

- Redução do RMSE da v2 frente ao fenomenológico: **78%** no global e **74%** no teste cego.
- **Teto** (taxas do problema inverso, 13 ensaios): RMSE 0,0142 (R² 0,995). Reconstrução do problema inverso nos 112 pontos: RMSE 0,0137 (0,0047 a 0,0256 por ensaio; Seção B.5).
- **Validação cruzada, fora da dobra, 10 sementes:** v2 = **0,0326 ± 0,0050** (erro-padrão 0,0016), cerca de 2,3 vezes o teto. v1 = 0,183 ± 0,039. Protocolo antigo da v1 (parada nos próprios ensaios de validação, otimista) = 0,130. Finalistas: tentativa 478 = 0,0326 ± 0,0027; 499 = 0,0354; 461 = 0,0359; Fase B 211 = 0,0363; 449 = 0,074 (uma semente divergiu).
- **RMSE por dobra** (média das 10 sementes, calculado de `SUB/fase_b2/finalistas_por_dobra.csv`, tentativa 511): dobra 1 = 0,0262 ± 0,0026; dobra 2 = 0,0477 ± 0,0126; dobra 3 = 0,0196 ± 0,0017; dobra 4 = 0,0305 ± 0,0075. A dobra 2 reúne os Ensaios 4, 10 e 15 (bordas) e é a pior.
- **Comitê × membro único no teste cego:** membro único 0,0203 ± 0,0015 (de 0,0183 a 0,0229) contra 0,0202 do comitê. Faixa entre membros: média 0,0040 nos 112 pontos (máximo 0,017), ≈ 25% do RMSE global. Erro máximo absoluto no teste cego: 0,040.
- **Taxa ν no teste cego** (contra os alvos do problema inverso): R² 0,921 (escala de ν) e 0,904 (escala log), contra 0,923 e 0,945 da v1. O ganho da v2 está na conversão, não no R² de ν.
- **Treino do comitê** (`SUB/fase_e/tabela_fase_e_treino_membros.csv`): perda final (escala transformada) de 0,00039 a 0,00051 (média 0,00046); cerca de 75 s (≈ 1,3 min) por membro em CPU.
- **Consistência física** (`etapa_4_4_resultados_hibrido_serial/tabela_consistencia_fisica.csv`): 1.681 condições (41 × 41 em C_A0 de 0,1 a 1,5 e η de 0,5 a 3,1, t de 0 a 15 min, passo 0,25): X nunca acima de min(1, η), nunca decrescente, C_Af nunca negativa; ν da rede com mínimo de 3,3 × 10⁻⁵ µm/min, nenhum ≤ 0.

## 3. RMSE por ensaio

Fonte: `etapa_4_4_resultados_hibrido_serial/tabela_erro_por_ensaio.csv` (a coluna "fora da dobra" é a validação cruzada da v2, 10 sementes). "Teste" = teste cego.

| Ensaio | Partição | η | C_A0 (mol/L) | Fenomenológico | v1 | v2 (ajuste) | v2 fora da dobra |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 1 | treino | 0,5 | 0,1 | 0,0341 | 0,0248 | 0,0104 | 0,0272 |
| 2 | treino | 3,1 | 0,1 | 0,0318 | 0,0264 | 0,0047 | 0,0269 |
| 3 | treino | 0,5 | 0,5 | 0,0224 | 0,0264 | 0,0102 | 0,0198 |
| 4 | treino | 0,5 | 1,0 | 0,0204 | 0,0348 | 0,0213 | 0,0215 |
| 5 | treino | 0,5 | 1,5 | 0,0181 | 0,0278 | 0,0143 | 0,0232 |
| 6 | treino | 1,0 | 0,1 | 0,0740 | 0,0204 | 0,0149 | 0,0452 |
| 7 | teste | 3,1 | 0,5 | 0,0521 | 0,0156 | 0,0217 | — |
| 8 | teste | 1,0 | 0,5 | 0,1149 | 0,0564 | 0,0249 | — |
| 9 | treino | 1,0 | 1,0 | 0,1396 | 0,0126 | 0,0115 | 0,0165 |
| 10 | treino | 1,0 | 1,5 | 0,1509 | 0,0250 | 0,0170 | 0,0572 |
| 11 | treino | 1,5 | 0,1 | 0,0521 | 0,0316 | 0,0259 | 0,0344 |
| 12 | treino | 3,1 | 1,0 | 0,0164 | 0,0070 | 0,0070 | 0,0135 |
| 13 | treino | 1,5 | 0,5 | 0,0537 | 0,0132 | 0,0128 | 0,0222 |
| 14 | teste | 1,5 | 1,0 | 0,0484 | 0,0176 | 0,0113 | — |
| 15 | treino | 1,5 | 1,5 | 0,0558 | 0,0107 | 0,0090 | 0,0593 |
| 16 | treino | 3,1 | 1,5 | 0,0193 | 0,0178 | 0,0152 | 0,0175 |

- v2 melhor que o fenomenológico em 15 dos 16 ensaios (exceção: Ensaio 4, 0,0213 contra 0,0204).
- Maiores erros fora da dobra: Ensaios 15, 10 e 6 (0,059; 0,057; 0,045), todos com C_A0 de 0,1 ou 1,5 mol/L (bordas do domínio). Texto seguro: "compatível com extrapolação", sem afirmar causa.
- No teste cego, a v2 foi pior que a v1 só no Ensaio 7 (0,0217 contra 0,0156); o 7 tem o maior excesso de ácido (η = 3,1), e a conversão prevista em 0,5 min (0,92) ficou acima da medida (0,88).
- O fenomenológico erra muito nos ensaios com η = 1,0 (RMSE 0,140 e 0,151 nos Ensaios 9 e 10, contra 0,012 e 0,017 da v2).

## 4. Comportamento observado (Tabela 5.XX.2 da v10)

Fonte: `etapa_4_4_resultados_hibrido_serial/tabela_tendencias.csv`, `fig_rh_04_mapa_conversao`.

- Patamar medido em 15 min por razão molar: ≈ 0,50 com η = 0,5; 0,85 a 0,87 com η = 1,0; 0,97 a 0,98 com η = 1,5; ≈ 1,0 com η = 3,1. O modelo prevê 0,49 a 0,50 (η = 0,5) e 0,84 a 0,88 (η = 1,0). A causa do patamar de 0,85 a 0,87 com η = 1 **não é identificada**.
- Em 0,5 min a conversão cresce de C_A0 = 0,1 para 0,5 a 1,0 mol/L e depois se estabiliza. Com η = 3,1 e C_A0 ≥ 1,0 já é 0,96 a 0,98 em 0,5 min.

## 5. Ressalvas que o texto tem de carregar

- **Treino não é previsão:** as métricas de treino medem o ajuste às curvas usadas na construção do modelo.
- **Teste cego = 3 ensaios, 21 pontos, todos interiores** (C_A0 de 0,5 a 1,0): diferenças pequenas não são conclusivas; o erro do teste (0,020) ficar abaixo da validação cruzada (0,033) é coerente com a composição das dobras (a dobra 2 tem bordas). O teste cego da v1 já havia sido usado antes; para a v2 é a primeira avaliação.
- **Um único membro** praticamente iguala o comitê: o comitê informa variabilidade, não reduz o erro. A faixa entre membros **não é intervalo de confiança** (não inclui erro experimental nem simplificações do fenomenológico).
- **Não esclarecido:** se o erro fora da dobra (0,033, 2,3× o teto) vem de poucos ensaios ou da qualidade dos alvos. Em 12 de 16 ensaios algum parâmetro do problema inverso ficou no limite da faixa (Seção B.5) e os pesos das penalizações foram definidos empiricamente (Seção B.3).
- **Variantes testadas e descartadas (Apêndice E.8 a E.10):** D1 (peso pela sensibilidade) e D2 (monotonia) e ajuste fino ponta a ponta não superaram a v2 (ajuste fino: 0,0326 para 0,0310, p = 0,020 nas 10 sementes da busca; 0,0334 para 0,0322, p = 0,135 nas 7 sementes não vistas). Usuário decidiu **manter a v2**.
- Domínio: 16 ensaios, 40 °C, 1000 rpm, uma amostra de calcina, volume de 400 mL; sem T, agitação, granulometria ou volume como entrada. Fora de C_A0 de 0,1 a 1,5 mol/L e η de 0,5 a 3,1, as previsões não foram avaliadas.

## 6. Não verificado

- Renderização no Word (a conferência visual é do usuário).
- Se existe curva de perda por época salva (D.3 só tem a perda final). Verificar antes de prometer figura de curva de aprendizado.
- Texto de `E.3` a `E.7` e Tabela E.2 não foram relidos nesta passagem; conferir antes de remover repetição entre Resultados e Apêndices.
- Referências novas (Psichogios; Ungar e Thompson; Kramer 1994): dados bibliográficos a conferir pelo usuário.
