# Fase C (Subetapa 3.2.6): perdas com informação física (D1 e D2) — resultados de 07/11/2026

Rede fixa da B2 (tentativa 511); só a perda muda. Protocolo comum: 4 dobras por ensaio, nota em X_Zn fora da dobra (91 pontos). Teste cego **não usado** nesta fase.

## O que foi feito
- **Busca (Optuna, 3 sementes):** 101 tentativas (91 concluídas, 10 podadas), 99 min, 28 processos. Variáveis: γ ∈ [0, 2] (expoente do peso D1), λ da monotonia D2 (0 ou 1e-4 a 10, escala log), taxa de aprendizado (0,4× a 2,5× a da B2) e épocas (500 a 1500). Referências na fila: B2, só D1, só D2 e D1 + D2.
- **Ablação (10 sementes, 4 dobras):** B2 original; B2 com a taxa de aprendizado e as épocas da melhor tentativa (lr = 0,00438; 1.101 épocas); + D1 (γ = 1,844); + D2 (λ = 0,1); + D1 + D2.
- **Regra de ganho claro:** diferença média pareada por semente (B2 − variante) maior que 1 erro-padrão da própria diferença.

## Resultados (RMSE de X_Zn fora da dobra, 10 sementes; `tabela_fase_c_ablacao.csv`)
| Variante | RMSE médio | Desvio | Ganho vs. B2 | EP do ganho | Ganho claro | Sementes melhores que a B2 |
| :-- | :-: | :-: | :-: | :-: | :-: | :-: |
| B2 (referência) | 0,0326 | 0,0050 | – | – | – | – |
| B2 reajustada (lr, épocas) | 0,0340 | 0,0026 | −0,0014 | 0,0016 | não | 3 |
| + D1 (γ = 1,84) | 0,0639 | 0,1103 | −0,0312 | 0,0350 | não | 5 |
| + D2 (λ = 0,1) | 0,0336 | 0,0043 | −0,0009 | 0,0026 | não | 4 |
| + D1 + D2 | 0,0998 | 0,1464 | −0,0671 | 0,0467 | não | 5 |

- A B2 reproduz 0,0326 (±0,0050), como na Fase B2.
- **Nenhuma variante tem ganho claro.** Com 10 sementes, a v2 (B2) continua sendo o melhor ponto de partida.
- **D1 funciona na maioria das sementes e falha em algumas.** Nas 9 sementes que não falharam, o RMSE médio é 0,0290 (ganho de 0,0037 sobre a B2, EP 0,0021, t pareado p = 0,12; não passa de 1 EP com segurança). Em 1 semente (51, dobra 2, validação nos ensaios 4, 10 e 15) a rede **colapsou para ν ≈ 0** (X_Zn previsto ≈ 1e-7; RMSE 0,784), o que arrasta a média. D1 + D2 colapsou em 2 casos (semente 49, dobra 2; semente 45, dobra 3).
- O resultado favorável da busca com 3 sementes (0,0269 contra 0,0308 da B2) vinha das sementes 42 a 44, que não falharam: a seleção em 3 sementes superestimou o ganho e não via a instabilidade.
- **D2 (monotonia):** neutra (0,0336 contra 0,0326). A fração do domínio com ∂ν/∂t > 0 fica em cerca de 11% com ou sem D2 (`ablacao_mono.csv`); D2 com λ = 0,1 quase não muda a forma da curva. Com D1 sem D2 sobe para 35% (média; desvio 26%); com D1 + D2, 1,5%.
- Causa provável do colapso (hipótese, não testada): com γ = 1,84, o peso D1 varia de cerca de 1e-7 a 200 entre instantes, e a taxa de aprendizado maior, reajustada na busca, leva a rede a uma região em que a saída zera.

## Atenção
- `melhor_config_fase_c.json` registra `variante_menor_RMSE = "+ D2"`, porque o script escolhe a de menor média entre as variantes diferentes da B2 (0,0336 contra 0,0340 da B2 reajustada). **Isso não é uma escolha da Fase C**: a diferença é ruído. Antes de rodar a Fase D é preciso decidir de qual rede partir (B2 original, ou D1 com salvaguardas).
- O eixo da Figura 2 é dominado pelas sementes que colapsaram; os pontos pretos mostram cada semente.

## Arquivos
`tabela_fase_c_tentativas.csv`, `tabela_fase_c_ablacao.csv`, `ablacao_por_semente.csv`, `ablacao_por_dobra.csv`, `ablacao_oof.csv`, `ablacao_mono.csv`, `ablacao_curvas.csv`, `melhor_config_fase_c.json`, `estudo_optuna_fase_c.log` (journal do Optuna), `log_busca.txt`, `log_ablacao.txt`, `fig_fc_01` a `fig_fc_06` (PNG e PDF, 300 DPI).

## Adendo de 08/11/2026: D1 com γ menor e decisão sobre D2
- **D1 seguro** (taxa de aprendizado e épocas originais da B2, sem D2, 10 sementes, 120 treinos; `tabela_fase_c_d1_segura.csv`): γ = 0,5 → RMSE 0,0375 (pior que a B2, p = 0,055); γ = 1,0 → 0,0391 (pior, p = 0,014); γ = 1,5 → 0,0302 (ganho de 0,0025, EP 0,0021, p = 0,27, 5 de 10 sementes melhores). Nenhum colapso. O resultado não é monotônico em γ, o que indica ruído; **D1 não dá ganho confiável**.
- **D2 descartada.** A lei física exige ν ≥ 0 (irreversibilidade da dissolução: o sólido só encolhe, então δ e X não diminuem). Isso já é imposto por construção (saída softplus em ν = expm1(softplus), cujo menor valor em 20.000 pontos do domínio foi 3,4e-5, e X acumulado e limitado). D2 exigia algo diferente, ∂ν/∂t ≤ 0 (taxa nunca cresce com o tempo), que é uma expectativa e não uma lei; os dados e os alvos do problema inverso têm erro experimental. Com λ = 0,1 a penalidade foi neutra no RMSE (0,0336 contra 0,0326) e não mudou a fração do domínio com ∂ν/∂t > 0.
- A Fase D parte da B2 original (`../fase_d/base_fase_d.json`), não do `melhor_config_fase_c.json`.
