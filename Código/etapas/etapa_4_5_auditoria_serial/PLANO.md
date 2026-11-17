# Etapa 4.5 — Auditoria do híbrido serial (plano)

Escrito em 09/11/2026. Entrega do relatório: 13/11/2026.

## Regras desta etapa

- **Nada do que existe é alterado.** O modelo v2 (`outputs/models_saved/mlp_v2/`), o `SerialHybridModel`, o problema inverso da Etapa 2.1 e os scripts das Etapas 3 e 4 ficam como estão. Os scripts novos só importam funções deles.
- **O teste cego não é usado para escolher nada.** Aqui ele só é lido para calcular referências que não têm ajuste (item 1) ou para decompor previsões já congeladas (itens 2 e 4).
- **Cada item tem a sua pasta**, com o script e um `README.md` curto, e a sua pasta de saída.

```
Código/etapas/etapa_4_5_auditoria_serial/
├── PLANO.md
├── comum.py                              (leitura de dados e métricas, usada pelos 5 itens)
├── item_1_referencia_media_eta/
├── item_2_erro_inicial_vs_patamar/
├── item_3_mlp_pura_10_sementes/
├── item_4_taxa_efetiva/
└── item_5_malha_fina_problema_inverso/

Código/outputs/etapa_4_5_auditoria_serial/
├── item_1_referencia_media_eta/
├── ... (uma pasta por item, com CSVs, figuras e um relatorio_item_N.md)
```

## Ordem de execução

| Ordem | Item | Tempo estimado | Depende de |
| :-: | :-- | :-: | :-- |
| 1 | Item 1 — referência "média por η" | 30 min | — |
| 2 | Item 2 — erro em 0,5 min e no patamar | 1 h | Item 1 |
| 3 | Item 3 — MLP pura com 10 sementes | 1 h (maior parte é máquina) | — |
| 4 | Item 4 — δ e taxas médias por intervalo | 1 h 30 | — |
| 5 | Item 5 — problema inverso em malha fina | 2 a 3 h | Item 4 |

Os itens 1 a 3 medem o que o modelo entrega. Os itens 4 e 5 definem o que a taxa ν significa.

---

## Item 1 — Referência sem modelo: média por η

**Por quê.** A v2 só é comparada com o fenomenológico, que erra o patamar. Falta a referência mais simples possível: prever a curva de um ensaio pela média das curvas medidas com a mesma razão molar. Uma conta preliminar deu 0,0343 na validação cruzada (v2: 0,0326 ± 0,0050) e 0,0222 no teste cego (v2: 0,0202). Sem essa linha na tabela, o ganho da v2 parece maior do que os dados sustentam.

**Como.**
1. Para cada ensaio de validação de uma dobra, usar só os ensaios de treino fora da dobra com a mesma η e tirar a média de X_Zn em cada instante (mesmas 4 dobras de `cv_folds_info.json`).
2. Para o teste cego (7, 8, 14), usar os 13 ensaios de treino.
3. Segunda referência, um pouco mais esperta: interpolação linear em C_A0 entre os vizinhos da mesma η (quando só há vizinho de um lado, usa-se o mais próximo).
4. Comparação com a v2 semente a semente, com as previsões fora da dobra de `fase_b2/finalistas_oof.csv` (10 sementes), e intervalo por reamostragem dos 13 ensaios (bootstrap por ensaio, 10.000 réplicas) para a diferença de RMSE.

**Saídas.** `tabela_referencias.csv` (CV, teste cego, por ensaio), `tabela_diferenca_v2_vs_referencia.csv` (diferença, intervalo, número de sementes em que a v2 ganha), `fig_i1_rmse_por_ensaio`.

**Pronto quando.** Os números da v2 lidos do CSV batem com 0,0326 e 0,0202, e a tabela diz, com intervalo, se a v2 é ou não distinguível da média por η.

---

## Item 2 — Onde está o erro: 0,5 min contra o patamar

**Por quê.** Em 0,5 min a conversão já é, em média, 93% da final. Seis das sete medições de cada ensaio estão no patamar, então o RMSE global mede quase só o patamar. O ponto de 0,5 min é o único com informação de cinética e do efeito de C_A0. É ali que o híbrido pode mostrar que aprende algo além de η.

**Como.**
1. Separar os pontos em três grupos: t = 0,5 min (16 pontos), 1 a 3 min (48), 4 a 15 min (48).
2. Calcular o RMSE e o erro médio com sinal em cada grupo para: v2 fora da dobra (10 sementes), v2 no teste cego, média por η (item 1), MLP pura (fora da dobra) e fenomenológico.
3. No grupo de 0,5 min, olhar o efeito de C_A0 dentro de cada η: a medição sobe de C_A0 = 0,1 para 0,5 a 1,0 mol/L; verificar se a v2 reproduz essa tendência (a média por η, por definição, não reproduz).

**Saídas.** `tabela_erro_por_faixa_de_tempo.csv`, `tabela_tendencia_CA0_em_0_5min.csv`, `fig_i2_erro_por_faixa`, `fig_i2_X_0_5min_vs_CA0`.

**Pronto quando.** Há uma resposta numérica para "a v2 ganha da média por η em 0,5 min?". Qualquer que seja a resposta, ela entra no relatório do item.

---

## Item 3 — MLP pura com 10 sementes

**Por quê.** A única comparação em que o híbrido vence a MLP pura é a validação cruzada (0,0326 contra 0,0421), mas com 10 sementes de um lado e 3 do outro.

**Como.**
1. Script novo que importa `treinar_rede`, `padronizador`, `aplicar` e `prever` de `subetapa_3_2_7_mlp_puro_xzn/mlp_puro_xzn.py` e roda a configuração já escolhida (`config_escolhida.json`, sem nova busca) nas mesmas 4 dobras, com as sementes 42 a 51.
2. Conferir antes que as sementes 42 a 44 reproduzem 0,0421.
3. Comparar com a v2 com as mesmas 10 sementes: média, desvio, erro-padrão, teste t pareado e Wilcoxon (mesmos testes do Apêndice E).

**Ressalva que fica registrada.** A assimetria de busca continua (cerca de 950 tentativas para a v2, 32 configurações para a MLP pura). Igualar isso exigiria uma busca nova, que não cabe no prazo.

**Saídas.** `cv_mlp_pura_10_sementes.csv`, `oof_mlp_pura_10_sementes.csv` (usado pelo item 2), `tabela_v2_vs_mlp_pura.csv`.

**Pronto quando.** As 3 primeiras sementes reproduzem o valor antigo e a tabela pareada está fechada.

---

## Item 4 — O que a rede prevê: δ e taxas médias por intervalo

**Por quê.** O solver integra a taxa com passo de 0,25 min: retângulo no primeiro passo (δ₁ = ν₁ · 0,25) e trapézios depois. Com decaimentos de até 7 min⁻¹, essa regra não converge: integrando a mesma bi-exponencial de forma exata, o RMSE do Ensaio 5 vai de 0,012 para 0,172. Logo, o valor de ν em cada nó não é a velocidade instantânea de retração. Ele só tem sentido junto com a regra de integração.

**O que é físico e o que não é.**
- X = g(δ) é uma função crescente fixada pela granulometria. Cada medição de X determina um δ. O **encolhimento acumulado δ(t)** é a grandeza física que os dados identificam e é o que entra no balanço populacional.
- A **taxa média em cada intervalo entre amostras**, ν̄ = Δδ/Δt, também é física (µm/min) e não depende da malha.
- O **valor de ν em um nó** não é identificado pelos dados. Exemplo: δ(0,5) = 0,375 ν₁ + 0,125 ν₂. A primeira medição fixa essa soma; a divisão entre ν₁ e ν₂ vem da forma bi-exponencial e das penalizações.
- Sete medições por ensaio fixam sete combinações dos 60 valores nodais.

**Como.**
1. Inverter g para os 112 pontos medidos: δ_exp = g⁻¹(X_exp). Marcar os pontos com X ≥ 0,99, em que δ é mal determinado (g fica plana) ou não existe (X = 1,01 no Ensaio 7).
2. Tirar da v2 (e de cada membro do comitê) δ(t) nos instantes experimentais e as taxas médias por intervalo.
3. Fazer o mesmo para o fenomenológico (integração de `solve_ivp`, que é convergida).
4. Comparar δ e ν̄ previstos com os obtidos das medições: RMSE de δ (µm) e de ν̄ (µm/min) nos pontos bem determinados.
5. Tabela de pesos: quais combinações dos ν nodais cada medição fixa.

**Saídas.** `tabela_delta_exp_vs_previsto.csv`, `tabela_taxa_media_por_intervalo.csv`, `tabela_pesos_quadratura.csv`, `fig_i4_delta_16_ensaios`, `fig_i4_taxa_media_por_intervalo`.

**Pronto quando.** Existe uma tabela de δ(t) e de ν̄ por intervalo, com faixa do comitê, que pode ser apresentada como "o parâmetro físico que a caixa-preta entrega".

---

## Item 5 — Diagnóstico: problema inverso em malha fina

**Por quê.** Serve de prova para o item 4. Se, ao refazer o problema inverso com integração exata, δ(t) e as taxas médias quase não mudarem e só os valores pontuais de ν mudarem, fica demonstrado que δ e ν̄ são as grandezas identificáveis e que a malha de 0,25 min afeta só a representação. Se mudarem, o item 4 precisa dizer isso.

**Como.**
1. Cópia de `optimize_single_experiment` (Etapa 2.1) em que δ(t) é a integral analítica da bi-exponencial: δ(t) = (a₁/b₁)(1 − e^(−b₁t)) + (a₂/b₂)(1 − e^(−b₂t)) + c·t. Mesmos limites, mesmas penalizações, mesmos pontos de partida.
2. Rodar nos 16 ensaios. **Os alvos novos não são salvos em `Base de dados/processed/` nem usados em treino.**
3. Comparar malha de 0,25 min contra integração exata: RMSE da reconstrução, δ nos instantes experimentais, ν̄ por intervalo, ν pontual em 0,25 e 0,5 min, parâmetros no limite da faixa.

**Saídas.** `parametros_inverso_malha_fina.csv`, `tabela_malha_025_vs_exata.csv`, `fig_i5_nu_pontual_vs_taxa_media`.

**Pronto quando.** A tabela mostra, por ensaio, a diferença em δ, em ν̄ e em ν pontual entre as duas integrações.

**Fora do escopo.** Retreinar a rede com os alvos novos. Exigiria refazer a busca e o comitê e consultar o teste cego de novo.

---

## Fecho

- `relatorio_etapa_4_5.md` na pasta de saída, com uma tabela-resumo dos cinco itens e o que cada um muda no que o relatório pode afirmar.
- Entrada no `DEVLOG.md`.
- Commit só depois de autorização.
