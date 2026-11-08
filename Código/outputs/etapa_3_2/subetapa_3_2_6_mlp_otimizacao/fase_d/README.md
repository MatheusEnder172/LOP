# Fase D (Subetapa 3.2.6): ajuste fino ponta a ponta através do PBM — resultados de 08/11/2026

## Método
- Partida: a rede **B2 original** (tentativa 511), treinada em cada (semente, dobra) como na Fase B2 (`pretreino/`; reproduz a ablação da Fase C com diferença 0,0 em X_Zn). Sem D1 e sem D2 (ver `../fase_c/README.md`).
- Ajuste fino, em lote completo e com a rede em modo de avaliação (sem dropout): perda = MSE(X_Zn experimental) + λ_ν · MSE_log(ν, ν_alvo). O PBM em PyTorch (`src/hybrid/pbm_torch.py`) reproduz o `SerialHybridModel` com diferença menor que 1e-6, então o gradiente de X_Zn chega à rede passando por ν → δ → X.
- Busca (Optuna, 3 sementes: 42 a 44): 87 tentativas (71 concluídas, 16 podadas), 1 min. Espaço: taxa de aprendizado de 1e-5 a 3e-3, 10 a 600 épocas, λ_ν de 1e-3 a 100 (escala log). Referências na fila: ajuste praticamente nulo (RMSE 0,0310 em 3 sementes) e ajuste moderado (0,0319).
- Escolhida (tentativa 82): taxa de aprendizado 0,00187; **17 épocas**; λ_ν = 0,0115. Ajuste fino curto e com âncora fraca.
- Comparação final: 10 sementes (42 a 51), mesmas redes de partida da B2, protocolo comum (4 dobras, 91 pontos), teste cego **não usado**.

## Resultados (RMSE de X_Zn fora da dobra; `tabela_fase_d_comparacao.csv`)
| Escopo | B2 | Fase D | Ganho médio | EP do ganho | Passa 1 EP? | p (t pareado) | p (Wilcoxon) | Sementes melhores |
| :-- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 10 sementes | 0,0326 | 0,0310 ± 0,0057 | 0,0016 | 0,0006 | sim | 0,020 | 0,037 | 8 de 10 |
| 7 sementes não vistas na busca (45 a 51) | 0,0334 | 0,0322 ± 0,0056 | 0,0013 | 0,0007 | sim | 0,135 | 0,156 | 5 de 7 |

- Ganho de cerca de 5% no RMSE (0,0326 → 0,0310), pequeno diante do desvio entre sementes (0,0057). Melhora em 11 dos 13 ensaios (fora da dobra); piora nos ensaios 5 e 9 (−0,0019 e −0,0059).
- As sementes 42 a 44 participaram da escolha dos parâmetros, então o ganho nelas é otimista; nas 7 sementes não vistas ele cai para 0,0013, ainda acima de 1 EP, mas com p = 0,14.
- Pelo critério fixado (ganho médio pareado > 1 erro-padrão), o ganho é "claro" por pouco; pelos testes de significância, é fraco. Não há colapso de rede: maior RMSE por dobra é 0,078 (B2: 0,072).
- ν continua positivo por construção (saída softplus). Os perfis de ν mudam pouco com o ajuste fino (`fig_fd_02`): as redes continuam seguindo o alvo no início e divergindo do alvo onde o próprio alvo do problema inverso é a parte incerta (ensaios 12 e 15).

## Arquivos
`base_fase_d.json`, `pretreino/` (redes de partida, 40 `.pt`), `tabela_fase_d_tentativas.csv`, `tabela_fase_d_comparacao.csv`, `melhor_config_fase_d.json`, `finais_*.csv`, `estudo_optuna_fase_d.log`, `fig_fd_01` a `fig_fd_05` (PNG e PDF, 300 DPI).
