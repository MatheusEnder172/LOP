# Subetapa 3.2.6: Otimização do treino da MLP do híbrido serial

Esta subetapa revisa como a MLP que prevê a taxa de retração ν(t) é treinada e escolhida, sem alterar a v1 (Subetapa 3.2.1), que continua reproduzível. O desenvolvimento é feito em fases. Cada fase tem um script, uma pasta de saídas com tabelas, figuras (300 DPI, PNG + PDF) e um relatório `.md`, e uma entrada no `DEVLOG.md`.

## Motivação

- A v1 foi escolhida entre 4 configurações manuais, e taxa de aprendizado, *weight decay* e *batch* nunca variaram.
- Na v1, a mesma dobra decide a parada antecipada e dá a nota, o que torna a nota otimista (Cawley; Talbot, 2010).
- A rede é treinada e avaliada em ν, mas o que o híbrido reporta é X_Zn.
- O modelo final v1 foi destilado com 260 épocas fixas, sem validação.

## Estrutura

```
subetapa_3_2_6_mlp_otimizacao/
├── README.md                  # este documento
├── protocolo_cv.py            # protocolo comum de validação (todas as fases)
├── modelo_mlp_v2.py           # MLPTrainerV2 (parada interna, pesos, monotonia) e KineticsMLPEnsemble
├── fase_a_linha_de_base.py    # Fase A: linha de base honesta da v1
├── fase_b_optuna_hpo.py       # Fase B: busca de hiperparâmetros com Optuna
├── figuras_fase_b.py          # Fase B: figuras, tabelas e relatório
├── fase_b2_busca_ampliada.py  # Fase B2: busca ampliada (até 8 camadas, ln t, residual, Glorot)
├── figuras_fase_b2.py         # Fase B2: figuras, tabelas e relatório
├── test_mlp_otimizacao.py     # testes (pytest)
└── PLANO_PENDENTE_FASES_C_D_E.md  # o que falta (Fases C, D e E), pausado em 25/10/2026
```

Saídas: `Código/outputs/etapa_3_2/subetapa_3_2_6_mlp_otimizacao/fase_<a..e>/`.

## Protocolo comum (`protocolo_cv.py`)

1. O teste cego (ensaios 7, 8 e 14) não entra em nenhuma seleção e é usado uma única vez, na Fase E (Kapoor; Narayanan, 2023).
2. Mantêm-se as 4 dobras por ensaio da Etapa 3.1 (Roberts et al., 2017; Hastie; Tibshirani; Friedman, 2009).
3. Em cada dobra, 2 ensaios do treino servem só para a parada antecipada. O sorteio é fixo por dobra e semente, e os vértices 1, 2, 5 e 16 nunca são sorteados. A nota vem dos ensaios de validação da dobra (Goodfellow; Bengio; Courville, 2016, seção 7.8; Cawley; Talbot, 2010).
4. São usadas 3 sementes (42, 43 e 44) por configuração.
5. Métrica principal: RMSE de X_Zn nos 7 pontos t > 0 de cada ensaio de validação (91 pontos nas 4 dobras), obtido passando ν pelo PBM (`SerialHybridModel`), e depois promediado entre as sementes.

## Como rodar

```bash
python fase_a_linha_de_base.py
python fase_b_optuna_hpo.py buscar --tentativas 400 --trabalhadores 24   # cerca de 42 min
python fase_b_optuna_hpo.py finalistas --trabalhadores 24                # cerca de 3 min
python fase_b_optuna_hpo.py figuras
python fase_b2_busca_ampliada.py buscar --tentativas 500 --trabalhadores 24   # cerca de 2h20
python fase_b2_busca_ampliada.py finalistas --trabalhadores 24
python fase_b2_busca_ampliada.py figuras
python -m pytest -q test_mlp_otimizacao.py
```

Na Fase B, o modo de parada também pode ser "épocas fixas": nenhum ensaio é reservado e o número de épocas vira hiperparâmetro escolhido pela validação cruzada.

## Situação das fases

| Fase | Situação | Resultado principal |
| :--- | :--- | :--- |
| A. Linha de base honesta | concluída (25/10/2026) | A v1 reproduz R² médio de ν de 0,8210 no protocolo antigo, mas tem RMSE de X_Zn fora da dobra de 0,130 (protocolo antigo) e 0,177 ± 0,046 (protocolo novo), contra 0,014 do teto e 0,023 no próprio treino |
| B. Optuna | concluída (25/10/2026) | 423 tentativas; escolhida a tentativa 211 ([21, 21, 21, 21], Tanh, sem LayerNorm, dropout 0,15, lr 5,9e-3, 1714 épocas fixas, lote 64): RMSE de X_Zn de 0,0363 ± 0,0053 em 10 sementes, contra 0,1828 ± 0,039 da v1 |
| B2. Busca ampliada | concluída (25/10/2026) | 523 tentativas; escolhida a tentativa 511 ([90, 45, 22] com conexões residuais, GELU, entrada em ln t, dropout 0,13, lr 4,1e-3, lote 16, 928 épocas): RMSE de X_Zn de 0,0326 ± 0,0050 em 10 sementes, contra 0,0363 ± 0,0053 da Fase B (melhor em 7 de 10 sementes; t pareado p = 0,028). Redes com 5 a 8 camadas não ajudaram |
| C. D1 + D2 | pausada | ver `PLANO_PENDENTE_FASES_C_D_E.md` |
| D. Ponta a ponta | pausada | ver `PLANO_PENDENTE_FASES_C_D_E.md` |
| E. Ensemble final | pausada | ver `PLANO_PENDENTE_FASES_C_D_E.md` |

## Mapa de referências

| Decisão | Referências já na revisão | Referências novas |
| :--- | :--- | :--- |
| Validação cruzada por ensaio | Roberts et al. (2017); Hastie et al. (2009) | – |
| Teste cego fora da seleção | Kapoor e Narayanan (2023) | – |
| Parada interna, sem viés de seleção | Goodfellow et al. (2016) | Cawley e Talbot (2010) |
| Busca de hiperparâmetros | Goodfellow et al. (2016, seção 11.4) | Bergstra et al. (2011); Akiba et al. (2019) |
| Otimizador | Kingma e Ba (2017) | – |
| Monotonia por autograd (D2) | Raissi et al. (2019); von Stosch et al. (2014); Schweidtmann et al. (2024) | – |
| Treino através do modelo fenomenológico (D4) | Psichogios e Ungar (1992); Thompson e Kramer (1994); Oliveira (2004); Shah et al. | – |
| Escolha pela regra de um erro-padrão | Hastie et al. (2009) | – |
| Inicialização e conexões residuais (B2) | Goodfellow et al. (2016) | Glorot e Bengio (2010); He et al. (2016) |
| *Ensemble* final | Goodfellow et al. (2016, seção 7.11) | Lakshminarayanan et al. (2017) |
