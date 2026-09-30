# Etapa 1.2: Módulo Cinético e Balanço Estequiométrico (`src/physics/kinetics.py`)

## Objetivo
Implementar o módulo permanente de primeiros princípios que governa a velocidade de retração interfacial das partículas minerais $v(D) = dD/dt$, o acoplamento estequiométrico da lixiviação de zincita ($\text{ZnO}$) e a equação de consumo de ácido de Herbst (1979).

## Estrutura da Etapa
- **Código-fonte de produção**: [`Código/src/physics/kinetics.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/src/physics/kinetics.py)
- **Script de Testes Unitários e Validação**: [`test_kinetics.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/etapas/etapa_1_2_modulo_cinetica/test_kinetics.py)

## Métodos Implementados na Classe `LeachingKinetics`
1. `calculate_eta(ca0, v_liq_l, mb0_g)`: Cálculo rigoroso da razão molar estequiométrica $\eta = n_{A0} / n_{B0}$.
2. `acid_concentration(ca0, x_zn, eta)`: Balanço analítico de consumo de ácido de Herbst (1979): $C_{Af}(t) = C_{A0}[1 - X_{\text{Zn}}(t)/\eta]$.
3. `dissolution_driving_force(ca0, caf, alpha)`: Cálculo da força motriz líquida $[k_s C_{Af} - \alpha(C_{A0} - C_{Af})]$.
4. `shrinkage_rate(ca0, caf, alpha)`: Velocidade de retração diametral $v(D) = -(2/\rho_s) \cdot F_{\text{motriz}}$, com imposição de $v(D) \le 0$.
5. `dissolution_stopping_acid(ca0, alpha)`: Acidez crítica $C_{Af}^* = C_{A0}[\alpha / (k_s + \alpha)]$ na qual a dissolução cessa ($v = 0$).
6. `theoretical_max_conversion(eta, alpha)`: Conversão assintótica teórica máxima $X_{\text{Zn}}^{\text{Max}} = \eta [1 - \alpha / (k_s + \alpha)]$.

## Entregas (Outputs)
- [`Código/outputs/etapa_1_2/relatorio_validacao_etapa_1_2.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_2/relatorio_validacao_etapa_1_2.md): Relatório com tabela de validação nos 16 ensaios experimentais e limites físicos.
- [`Código/outputs/etapa_1_2/nota_conceitual_cinetica.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_2/nota_conceitual_cinetica.md): Nota conceitual e termodinâmica sobre a cinética heterogênea e o termo de amortecimento $\alpha$.
