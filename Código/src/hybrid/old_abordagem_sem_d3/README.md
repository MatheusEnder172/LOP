# Arquivo Histórico: Abordagem Antiga (Sem Ponderação D³ explícita / Com t=0 nos datasets / 4 entradas com Temperatura)

Esta pasta preserva integralmente os scripts, tabelas, figuras e relatórios da abordagem anterior à refatoração física completa:
- Na abordagem antiga, o ponto trivial t = 0 (X_Zn = 0) era incluído nos conjuntos de treino, validação, teste e métricas R²/RMSE, e os modelos Black-Box recebiam 4 entradas (incluindo temperatura_C invariante).
- Na nova abordagem (diretório pai), a condição inicial em t = 0 (X_Zn(0) = 0, δ(0) = 0, C_Af(0) = C_A0) é hardcodada fisicamente no orquestrador híbrido, os modelos Black-Box operam estritamente sobre t > 0 com 3 entradas cinéticas ativas [C_A0, η, t] acoplados ao solver PBM com distribuição RRB ÷ D³ (sem α empírico), e o MLP (Opção 1 + Autograd + Opção 5 MCDA) atua como modelo campeão.
