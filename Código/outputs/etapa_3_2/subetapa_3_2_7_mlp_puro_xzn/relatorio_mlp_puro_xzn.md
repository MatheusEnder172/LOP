# Subetapa 3.2.7 — MLP pura (caixa-preta direta): (C_A0, η, t) → X_Zn

Data: 08/11/2026. Script: `Código/etapas/etapa_3_2/subetapa_3_2_7_mlp_puro_xzn/mlp_puro_xzn.py`.
Comitê: `Código/outputs/models_saved/mlp_puro_xzn/` (10 membros, `SHA256SUMS.txt`).

## 1. O que é e para que serve
Referência puramente orientada a dados, para comparar depois com o white-box e com o híbrido serial.
Diferente das MLPs das Subetapas 3.2.1 e 3.2.6 (que aprendem a taxa |ν|, alvo vindo do problema inverso
e depois passam pelo PBM), esta rede aprende **X_Zn direto dos pares experimentais**, sem PBM, sem
sigmoide, sem teto min(1, η) e sem monotonia.

## 2. Protocolo (o mesmo da 3.2.6)
- Treino: 13 ensaios, 91 pontos t > 0. Teste cego: ensaios 7, 8 e 14 (21 pontos), usado uma vez, depois de congelar o comitê.
- Entradas: C_A0, η e ln t, padronizadas. Os pontos t = 0 não entram no treino.
- Seleção por validação cruzada com as 4 dobras por ensaio da Etapa 3.1, 3 sementes, nota = RMSE de X_Zn fora da dobra (91 pontos).
- Rodada 1 (8 configurações, parada antecipada em 2 ensaios internos): RMSE da CV de 0,108 a 0,156, com desvio alto entre sementes. A parada antecipada parava em cerca de 30 épocas (subtreino). Resultados em `busca_cv_configuracoes_rodada1.csv`.
- Rodada 2 (24 configurações novas: 4 arquiteturas × 2 taxas de aprendizado × 150, 400 e 900 épocas fixas): o melhor RMSE da CV caiu para 0,042. As 15 melhores ficam entre 0,042 e 0,055, dentro do ruído entre sementes, então a busca parou ali. Só a CV foi consultada; o teste cego estava intacto. Resultados em `busca_cv_configuracoes.csv`.
- Escolhida: rede [90, 45, 22], GELU, lr 0,01, AdamW (wd 1e-4), lote 16, 900 épocas; CV = 0,0421 ± 0,0035 (3 sementes).
- Modelo final: comitê de 10 redes (sementes 42 a 51), cada uma nos 13 ensaios; previsão = média; a faixa mín–máx é variação entre membros, não intervalo de confiança.

## 3. Resultados (RMSE de X_Zn, t > 0)

| Modelo | CV (fora da dobra, 91 pts) | Treino (91) | Teste cego (21) | Global (112) |
| :--- | :---: | :---: | :---: | :---: |
| White-box novo (RRB ÷ D³, sem α) | — | 0,0682 | 0,0780 | 0,0702 |
| Híbrido v1 (MLP em ν → PBM) | — | 0,0229 | 0,0353 | 0,0257 |
| Híbrido v2 (comitê em ν → PBM) | 0,0326 ± 0,0050 (10 sem.) | 0,0145 | 0,0202 | 0,0157 |
| **MLP pura (comitê em X_Zn)** | **0,0421 ± 0,0035 (3 sem.)** | **0,0055** | **0,0184** | **0,0094** |

R² da MLP pura: treino 0,9993; teste cego 0,9067; global 0,9977. Por ensaio: `metricas_por_ensaio_vs_referencias.csv`.

## 4. Leitura honesta
- No teste cego e no global a MLP pura erra pouco, no nível do híbrido v2 (0,0184 contra 0,0202). Com só 3 ensaios e 21 pontos, essa diferença **não é conclusiva**. Os três ensaios cegos ficam dentro do planejamento, entre vizinhos de treino.
- Na validação cruzada (fora da dobra, mesmas dobras) o híbrido v2 ainda leva vantagem (0,0326 contra 0,0421). Os números de CV têm quantidades de sementes diferentes (10 e 3).
- Treino 0,0055 contra teste cego 0,0184: a rede acompanha o ruído experimental. As curvas ondulam para passar pelos pontos (visível nos ensaios 1, 4 e 11).
- Sem física, a rede viola limites: no ensaio 3 e no ensaio 4 a média do comitê passa de 0,5 em até 1,2 ponto percentual (teto de η = 0,5), e há quedas de X_Zn(t) de até 0,22 p.p. (`violacoes_fisicas_curvas.csv`). Nos pontos experimentais, 3 de 112 ficam acima do teto.
- Abaixo de 0,5 min (primeira amostra) a rede extrapola; no gráfico esse trecho está pontilhado.
- O que este teste **não** mede: extrapolação. Todos os ensaios, inclusive os cegos, estão no interior do planejamento. A comparação que mais separa os modelos é fora do domínio (por exemplo o ensaio novo com η = 0,40, abaixo do mínimo de 0,5 do treino), onde o híbrido tem a física e a MLP pura não.

## 5. Arquivos
- `fig_mlp_puro_xzn_4x4.png/.pdf` — um quadro por ensaio (300 DPI).
- `metricas_mlp_puro.csv`, `metricas_por_ensaio_vs_referencias.csv` (inclui white-box, híbrido v1 e v2), `predicoes_pontos_experimentais.csv`, `curvas_densas_mlp_puro.csv`, `violacoes_fisicas_curvas.csv`.
- `busca_cv_configuracoes_rodada1.csv`, `busca_cv_configuracoes.csv`, `busca_cv_predicoes_fora_da_dobra.csv`, `config_escolhida.json` (e a da rodada 1).
