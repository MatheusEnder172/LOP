# Relatório de Validação da Etapa 2.1 — Otimização Inversa em t > 0 (RRB ÷ D³ e t = 0 Hardcoded)

**Status de Homologação**: Aprovado (R² Global em t > 0 = 0.99508, RMSE = 1.37%, MAE = 1.02%)

## 1. Sumário Executivo
1. **Hardcode de `t = 0` (`X_Zn(0) = 0, δ(0) = 0`)**: A origem física em `t = 0` é cravada diretamente no solver e excluída dos datasets de treino/validação/teste e do cálculo das métricas.
2. **Integração Consistente em `t > 0`**: Os parâmetros bi-exponenciais foram otimizados sobre os **112 pontos experimentais ativos (`t > 0`)** integrando `δ(t)` na malha `t_dense = [0,25; 0,50; ...; 15,00] min` (60 pontos por ensaio, 960 registros totais) com `BatchPBMSolver.simulate_with_v_profile`.
3. **Eliminação do Salto Impulsivo**: A velocidade inicial máxima cai de `> 600 µm/min` para **`72,1 µm/min`**, tornando o campo `|v(C_A0, η, t)|` suave e ideal para o aprendizado do MLP na Fase 3.
