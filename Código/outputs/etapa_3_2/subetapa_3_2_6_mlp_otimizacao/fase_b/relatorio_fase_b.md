# Fase B — Busca de hiperparâmetros com Optuna (Subetapa 3.2.6)

## Objetivo
Escolher os hiperparâmetros da MLP pelo erro que o híbrido realmente comete, o RMSE de X_Zn fora da
dobra (91 pontos experimentais t > 0 dos 13 ensaios de treino), em vez da nota em ν usada na v1.

## Como foi feito
- Amostrador TPE multivariado (Bergstra et al., 2011) do Optuna (Akiba et al., 2019), com 30 tentativas
  iniciais aleatórias, e poda pela mediana a partir da 2ª dobra (tentativas claramente piores que a
  mediana das anteriores são interrompidas).
- Cada tentativa: protocolo comum (4 dobras por ensaio × 3 sementes); teste cego intocado.
- As duas primeiras tentativas foram enfileiradas com a configuração v1: com parada interna (tentativa 0,
  RMSE 0.1772, igual à Fase A) e com 350 épocas fixas usando todos os ensaios da dobra (tentativa 1,
  RMSE 0.1001).
- Espaço de busca: 1–4 camadas ocultas; largura da 1ª camada 8–256 (escala log), constante ou afunilada
  (metade a cada camada); ativação GELU, SiLU ou Tanh; LayerNorm com ou sem; dropout 0–0,2; taxa de
  aprendizado 1e-4 a 1e-2 (log); weight decay 1e-6 a 1e-1 (log); lote 16–256; modo de parada: parada
  interna (paciência 20–200, até 300–2000 épocas) ou número fixo de épocas (50–2000) com todos os
  ensaios da dobra no treino.
- Tentativas: 423 no total (402 completas, 21 podadas); tempo de CPU somado
  16.1 h.
- Finalistas: as 5 melhores tentativas e a v1 foram reavaliadas com 10 sementes (42–51); a escolha segue
  a regra de um erro-padrão (Hastie; Tibshirani; Friedman, 2009): entre as configurações cuja média
  fica a menos de 1 erro-padrão da melhor, fica a de menos parâmetros.

## Melhores tentativas (3 sementes)
| Tentativa | RMSE X_Zn | Camadas | Ativação | LayerNorm | lr | weight decay | Lote | Modo | Épocas |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| 392 | 0.0319 | [21, 21, 21, 21] | Tanh | False | 4.53e-03 | 1.78e-03 | 64 | epocas_fixas | 1987 |
| 180 | 0.0325 | [21, 21, 21, 21] | Tanh | False | 5.99e-03 | 1.50e-04 | 64 | epocas_fixas | 1824 |
| 354 | 0.0328 | [27, 27, 27, 27] | Tanh | False | 3.80e-03 | 2.17e-04 | 64 | epocas_fixas | 1576 |
| 264 | 0.0329 | [21, 21, 21, 21] | Tanh | False | 4.68e-03 | 3.69e-05 | 64 | epocas_fixas | 1638 |
| 211 | 0.0331 | [21, 21, 21, 21] | Tanh | False | 5.92e-03 | 1.47e-04 | 64 | epocas_fixas | 1714 |
| 315 | 0.0333 | [27, 27, 27, 27] | Tanh | False | 3.74e-03 | 3.99e-04 | 64 | epocas_fixas | 1171 |
| 182 | 0.0334 | [21, 21, 21, 21] | Tanh | False | 4.54e-03 | 8.45e-05 | 64 | epocas_fixas | 1713 |
| 306 | 0.0336 | [21, 21, 21, 21] | Tanh | False | 3.56e-03 | 1.46e-04 | 64 | epocas_fixas | 1997 |
| 402 | 0.0337 | [20, 20, 20, 20] | Tanh | False | 4.53e-03 | 3.09e-04 | 64 | epocas_fixas | 1216 |
| 343 | 0.0339 | [23, 23, 23, 23] | Tanh | False | 2.47e-03 | 2.88e-04 | 64 | epocas_fixas | 1966 |

## Importância dos hiperparâmetros (fANOVA)
| Hiperparâmetro | Importância |
| :--- | :---: |
| Largura da 1ª camada | 0.240 |
| Dropout | 0.191 |
| Taxa de aprendizado | 0.184 |
| Weight decay | 0.164 |
| Épocas (fixas) | 0.144 |
| Nº de camadas ocultas | 0.058 |
| Tamanho do lote | 0.008 |
| Forma (constante/afunilada) | 0.006 |
| Função de ativação | 0.003 |
| Modo de parada | 0.002 |
| LayerNorm | 0.000 |
| Paciência | 0.000 |
| Épocas máx. (parada interna) | 0.000 |

## Finalistas (10 sementes)
| Configuração | RMSE X_Zn (média ± dp) | R² X_Zn | Parâmetros | Dentro de 1 EP | Escolhida |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Tentativa 354 | 0.0363 ± 0.0048 | 0.9685 | 2404 | sim |  |
| Tentativa 211 | 0.0363 ± 0.0053 | 0.9682 | 1492 | sim | **sim** |
| Tentativa 392 | 0.0372 ± 0.0065 | 0.9664 | 1492 | sim |  |
| Tentativa 264 | 0.0378 ± 0.0056 | 0.9656 | 1492 | não |  |
| Tentativa 180 | 0.0416 ± 0.0090 | 0.9574 | 1492 | não |  |
| v1 (MLP-B, parada interna) | 0.1828 ± 0.0393 | 0.1781 | 2369 | não |  |

Configuração escolhida (Tentativa 211):

```json
{
  "hidden_dims": [
    21,
    21,
    21,
    21
  ],
  "activation": "Tanh",
  "use_layer_norm": false,
  "dropout_rate": 0.1456585594122226,
  "lr": 0.005919830803896044,
  "weight_decay": 0.00014662849381975973,
  "batch_size": 64,
  "modo_parada": "epocas_fixas",
  "mono_lambda": 0.0,
  "patience": 0,
  "max_epochs": 1714
}
```

## RMSE de X_Zn por ensaio (10 sementes)
| Ensaio | Teto | v1 | Fase B |
| :---: | :---: | :---: | :---: |
| 01 | 0.0095 | 0.0400 ± 0.0250 | 0.0214 ± 0.0131 |
| 02 | 0.0047 | 0.1389 ± 0.1130 | 0.0366 ± 0.0044 |
| 03 | 0.0093 | 0.1547 ± 0.1070 | 0.0163 ± 0.0053 |
| 04 | 0.0216 | 0.2431 ± 0.0938 | 0.0311 ± 0.0069 |
| 05 | 0.0122 | 0.1989 ± 0.1122 | 0.0392 ± 0.0099 |
| 06 | 0.0148 | 0.1369 ± 0.1038 | 0.0350 ± 0.0115 |
| 09 | 0.0113 | 0.1187 ± 0.0352 | 0.0447 ± 0.0104 |
| 10 | 0.0167 | 0.3261 ± 0.2023 | 0.0348 ± 0.0210 |
| 11 | 0.0256 | 0.1019 ± 0.0461 | 0.0570 ± 0.0086 |
| 12 | 0.0071 | 0.0517 ± 0.1109 | 0.0300 ± 0.0062 |
| 13 | 0.0125 | 0.0652 ± 0.0365 | 0.0320 ± 0.0155 |
| 15 | 0.0090 | 0.1626 ± 0.1523 | 0.0333 ± 0.0148 |
| 16 | 0.0153 | 0.0353 ± 0.0177 | 0.0274 ± 0.0015 |

## Leitura dos resultados
- **Modo de parada.** A mediana do RMSE foi 0.043 com épocas fixas contra
  0.258 com parada interna. Com só 13 ensaios, reservar 2 deles para parar o treino
  custa mais do que o risco de sobreajuste que a parada evita; o número de épocas passa a ser escolhido pela
  validação cruzada.
- **Ativação e profundidade.** Medianas por ativação: GELU 0.136, SiLU 0.154,
  Tanh 0.041. Por número de camadas: 1 → 0.279, 2 → 0.155,
  3 → 0.146, 4 → 0.041. Redes estreitas e mais profundas com Tanh foram as melhores,
  sem LayerNorm.
- **Importância (fANOVA) × diferenças categóricas.** O fANOVA mede a variação do erro dentro da região que o
  TPE efetivamente explorou. Como o amostrador abandonou cedo a parada interna, GELU/SiLU e LayerNorm
  (poucas tentativas nessas categorias), esses hiperparâmetros aparecem com importância baixa, embora as
  diferenças entre categorias sejam grandes (fig_fb_04). Dentro da região boa, o que mais mexe no erro é a
  largura, o dropout, a taxa de aprendizado, o weight decay e o número de épocas.
- **Efeito do vencedor.** A melhor tentativa teve RMSE 0.0319 com 3 sementes; com 10 sementes,
  os finalistas ficaram entre 0.0363 e
  0.0416.
  A diferença é esperada, porque a melhor de 400 tentativas tende a ter tido sementes favoráveis; por isso a
  escolha foi feita com 10 sementes e pela regra de um erro-padrão.
- **Limites do espaço de busca.** Quase todas as boas tentativas usam 4 camadas, o limite superior do espaço;
  o número de épocas ficou abaixo do limite de 2000.

## Figuras
- `fig_fb_01_historico_busca`: valor de cada tentativa e melhor valor acumulado.
- `fig_fb_02_importancia_hiperparametros`: importância relativa (fANOVA).
- `fig_fb_03_fatias_hiperparametros`: RMSE de X_Zn contra os hiperparâmetros contínuos, por modo de parada.
- `fig_fb_04_hiperparametros_categoricos`: distribuição do RMSE por modo de parada, ativação, LayerNorm e profundidade.
- `fig_fb_05_finalistas_10_sementes`: reavaliação dos finalistas e da v1 com 10 sementes.
- `fig_fb_06_XZn_fora_da_dobra_v1_vs_fase_b`: X_Zn(t) fora da dobra, v1 contra a configuração escolhida.
- `fig_fb_07_rmse_XZn_por_ensaio`: RMSE de X_Zn por ensaio.

## Base bibliográfica
- Busca de hiperparâmetros (aleatória e guiada por modelo): Goodfellow, Bengio e Courville (2016, seção 11.4).
- TPE: Bergstra et al. (2011) [nova]; Optuna: Akiba et al. (2019) [nova].
- Seleção por validação cruzada e regra de um erro-padrão: Hastie, Tibshirani e Friedman (2009).
- Parada antecipada e número de épocas como hiperparâmetro: Goodfellow, Bengio e Courville (2016, seção 7.8).
