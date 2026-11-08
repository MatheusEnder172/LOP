# Fase E mínima — Ensemble final da MLP v2 e teste cego (Subetapa 3.2.6)

## Objetivo
Treinar o modelo final da MLP v2 com a configuração escolhida na Fase B2 e avaliá-lo uma única vez no
teste cego (ensaios 7, 8 e 14), para que a metodologia descreva o pipeline completo. As Fases C e D
continuam pausadas; esta é a versão mínima da Fase E.

## Como foi feito
- Configuração: Fase B2 – B2 – tentativa 511 — camadas [90, 45, 22] com conexões residuais,
  GELU, sem LayerNorm, entrada em ln t, dropout 0.125, AdamW com lr
  4.08e-03 e weight decay 1.02e-03, lote 16,
  928 épocas fixas com taxa de aprendizado em cosseno.
- Ensemble de 10 membros (sementes 42 a 51), cada um
  treinado nos 13 ensaios de treino (780 registros), sem reserva
  de ensaios. A predição é a média de ν entre os membros, passada pelo PBM (`SerialHybridModel`);
  a faixa de incerteza vem de integrar cada membro separadamente (Lakshminarayanan et al., 2017).
- Tempo de treino: 1.3 min por membro (média), em paralelo.
- O teste cego foi avaliado uma única vez, com o modelo já congelado (Kapoor; Narayanan, 2023).
  O script recusa retreinar se já houver membros salvos.
- Referências na mesma avaliação: MLP v1 (`mlp_kinetics_v1.pt`, pipeline oficial) e modelo
  fenomenológico puro (predições da Etapa 4.2).
- Modelos salvos em `Código/outputs/models_saved/mlp_v2/` (membros `.pt` e `mlp_v2_config.json`);
  `mlp_kinetics_v1.pt` não foi alterado.

## Resultados — X_Zn nos pontos experimentais (t > 0)
| Particao | Modelo | n_pontos | R2 | RMSE | MAE | MaxErro |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Treino | MLP v2 (ensemble) | 91 | 0.9950 | 0.0145 | 0.0106 | 0.0371 |
| Teste cego | MLP v2 (ensemble) | 21 | 0.8881 | 0.0202 | 0.0165 | 0.0403 |
| Global | MLP v2 (ensemble) | 112 | 0.9935 | 0.0157 | 0.0117 | 0.0403 |
| Treino | MLP v1 | 91 | 0.9876 | 0.0229 | 0.0169 | 0.0636 |
| Teste cego | MLP v1 | 21 | 0.6570 | 0.0353 | 0.0269 | 0.0822 |
| Global | MLP v1 | 112 | 0.9827 | 0.0257 | 0.0188 | 0.0822 |
| Treino | Fenomenológico puro | 91 | 0.8900 | 0.0682 | 0.0488 | 0.1634 |
| Teste cego | Fenomenológico puro | 21 | -0.6747 | 0.0780 | 0.0637 | 0.1255 |
| Global | Fenomenológico puro | 112 | 0.8709 | 0.0702 | 0.0516 | 0.1634 |

Conferência: as linhas da v1 e do modelo fenomenológico devem reproduzir a Etapa 4.2
(v1: RMSE de treino 0,0229 e de teste cego 0,0353; fenomenológico: 0,0682 e 0,0780).

### RMSE de X_Zn por ensaio do teste cego
| ensaio | Fenomenológico puro | MLP v1 | MLP v2 (ensemble) |
| :--- | :---: | :---: | :---: |
| 7 | 0.0521 | 0.0156 | 0.0217 |
| 8 | 0.1149 | 0.0564 | 0.0249 |
| 14 | 0.0484 | 0.0176 | 0.0113 |

### Membros isolados no teste cego
RMSE de um único membro: 0.0203 ± 0.0015
(mín. 0.0183, máx. 0.0229), contra
0.0202 do ensemble.

### Taxa ν no teste cego (malha densa, alvos do problema inverso)
| Modelo | R2_nu | R2_log_nu | RMSE_nu | MAE_nu |
| :--- | :---: | :---: | :---: | :---: |
| MLP v2 (ensemble) | 0.9213 | 0.9043 | 2.3925 | 1.1062 |
| MLP v1 | 0.9231 | 0.9453 | 2.3659 | 0.8875 |

## Leitura dos resultados
- Teste cego: RMSE de X_Zn de 0.0202 (R² 0.888) para a v2, contra 0.0353
  (R² 0.657) para a v1.
- Validação cruzada da configuração (B2, 10 sementes, 91 pontos fora da dobra): 0,0326 ± 0,0050.
  O teste cego (0,020) ficou abaixo desse valor, o que é coerente com o que a Seção de partição já
  previa: a 1ª dobra reúne vértices do planejamento, enquanto o teste avalia só condições internas.
- O ensemble (0.0202) ficou ligeiramente melhor que a média de um membro isolado
  (0.0203); a faixa entre membros é estreita em X_Zn e mais larga em ν
  no fim da batelada, onde ν é pequena e quase não altera X_Zn.
- Em ν, a v2 não superou a v1 no teste (R²_log 0,904 contra 0,945), embora seja melhor em X_Zn. A maior
  parte da diferença está depois de cerca de 4 min nos ensaios 8 e 14, onde os alvos do problema inverso
  ficam parados em 0,03 µm/min, o limite superior do parâmetro c; ali ν é pequena e pesa pouco em X_Zn.
  É o mesmo desalinhamento entre a perda em ν e o erro em X_Zn que motivou a nota em X_Zn (e as Fases C e D).
- No ensaio 7 (η = 3,1, maior excesso de ácido) a v2 ficou um pouco pior que a v1 (0,022 contra 0,016);
  nos ensaios 8 e 14 ficou melhor (0,025 contra 0,056; 0,011 contra 0,018).
- Ressalva sobre a comparação: o teste cego da v1 já tinha sido calculado na Etapa 4.2 e usado na MCDA,
  então ele não é mais "cego" para a v1. Para a v2, é a primeira e única avaliação.
- Com só 3 ensaios e 21 pontos, diferenças pequenas de RMSE no teste não são conclusivas; a validação
  cruzada (13 ensaios) é a evidência principal para a escolha da configuração.

## Figuras
- `fig_fe_01_XZn_teste_cego`: X_Zn(t) dos 3 ensaios de teste (experimental, v2 com faixa dos membros, v1 e fenomenológico).
- `fig_fe_02_nu_teste_cego`: ν(t) dos 3 ensaios de teste contra os alvos do problema inverso.
- `fig_fe_03_paridade_XZn`: paridade de X_Zn, v1 e v2, treino e teste cego.
- `fig_fe_04_rmse_teste_cego`: RMSE por ensaio de teste e global.
- `fig_fe_05_evolucao_e_teste`: (a) RMSE fora da dobra de A a B2; (b) treino e teste dos modelos finais.

## Base bibliográfica
- Ensemble de redes com sementes diferentes: Lakshminarayanan et al. (2017) [nova]; Goodfellow, Bengio e Courville (2016, seção 7.11).
- Teste usado uma única vez, fora da seleção: Kapoor e Narayanan (2023); Hastie, Tibshirani e Friedman (2009).
