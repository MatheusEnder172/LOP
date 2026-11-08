# Previsão a priori dos 4 ensaios novos de laboratório (Subetapa 4.3)

**Gerada em 2026-11-08 13:14:18, antes de qualquer medição**, com a MLP v2 (comitê de 10 redes da Subetapa 3.2.6), que não foi alterada. Os pesos do comitê foram conferidos contra `Código/outputs/models_saved/mlp_v2/SHA256SUMS.txt` (SHA-256 em `INTEGRIDADE_previsao_a_priori.json`, junto com o SHA-256 dos arquivos de previsão). A comparação com as medições usa só esses arquivos gravados; o script recusa refazer a previsão e aborta se algum arquivo gravado tiver sido alterado.

## 1. Condições dos ensaios
Temperatura de 40 °C e agitação de 1000 rpm, como nos 16 ensaios originais; só o volume mudou (200 mL em vez de 400 mL). O modelo usa apenas C_A0, η e t. A razão sólido/líquido decorre de C_A0 e η (m/V = C_A0·M_ZnO/(η·0,81)), logo é a mesma de um ensaio original com os mesmos C_A0 e η, e cai dentro da faixa dos originais (3 a 300 g/L).

| Ensaio | η | C_A0 (mol/L) | V (mL) | m (g) | m/V (g/L) | Limite min(1, η) | Domínio do treino |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-- |
| E1 | 0,75 | 0,25 | 200 | 6,7 | 33,5 | 0,75 | dentro do domínio |
| E2 | 1,25 | 0,75 | 200 | 12,1 | 60,5 | 1,00 | dentro do domínio |
| E3 | 2,25 | 0,75 | 200 | 6,7 | 33,5 | 1,00 | dentro do domínio |
| E4 | 0,40 | 0,25 | 200 | 12,6 | 63,0 | 0,40 | **extrapolação** (η < 0,5) |

## 2. Previsões (v2)

**E1** (η = 0,75; C_A0 = 0,25 mol/L)

| t (min) | X_Zn prevista (comitê) | Faixa dos 10 membros | Fenomenológico puro | Interpolação dos 16 ensaios | C_Af prevista (mol/L) |
| :-: | :-: | :-: | :-: | :-: | :-: |
| 0,5 | 0,616 | 0,607 a 0,620 | 0,721 | 0,606 | 0,045 |
| 1,0 | 0,667 | 0,658 a 0,671 | 0,745 | 0,631 | 0,028 |
| 2,0 | 0,688 | 0,676 a 0,696 | 0,750 | 0,645 | 0,021 |
| 3,0 | 0,698 | 0,686 a 0,707 | 0,750 | 0,677 | 0,017 |
| 4,0 | 0,703 | 0,691 a 0,713 | 0,750 | 0,688 | 0,016 |
| 5,0 | 0,707 | 0,694 a 0,717 | 0,750 | 0,672 | 0,014 |
| 15,0 | 0,713 | 0,700 a 0,724 | 0,750 | 0,685 | 0,012 |

**E2** (η = 1,25; C_A0 = 0,75 mol/L)

| t (min) | X_Zn prevista (comitê) | Faixa dos 10 membros | Fenomenológico puro | Interpolação dos 16 ensaios | C_Af prevista (mol/L) |
| :-: | :-: | :-: | :-: | :-: | :-: |
| 0,5 | 0,889 | 0,885 a 0,892 | 0,980 | 0,873 | 0,216 |
| 1,0 | 0,923 | 0,919 a 0,925 | 0,997 | 0,885 | 0,196 |
| 2,0 | 0,929 | 0,925 a 0,931 | 1,000 | 0,900 | 0,193 |
| 3,0 | 0,929 | 0,925 a 0,931 | 1,000 | 0,907 | 0,193 |
| 4,0 | 0,929 | 0,926 a 0,931 | 1,000 | 0,900 | 0,193 |
| 5,0 | 0,929 | 0,926 a 0,931 | 1,000 | 0,907 | 0,193 |
| 15,0 | 0,929 | 0,926 a 0,931 | 1,000 | 0,915 | 0,192 |

**E3** (η = 2,25; C_A0 = 0,75 mol/L)

| t (min) | X_Zn prevista (comitê) | Faixa dos 10 membros | Fenomenológico puro | Interpolação dos 16 ensaios | C_Af prevista (mol/L) |
| :-: | :-: | :-: | :-: | :-: | :-: |
| 0,5 | 0,923 | 0,918 a 0,927 | 0,998 | 0,917 | 0,442 |
| 1,0 | 0,970 | 0,969 a 0,972 | 1,000 | 0,952 | 0,427 |
| 2,0 | 0,985 | 0,984 a 0,987 | 1,000 | 0,969 | 0,422 |
| 3,0 | 0,988 | 0,986 a 0,989 | 1,000 | 0,974 | 0,421 |
| 4,0 | 0,988 | 0,987 a 0,990 | 1,000 | 0,971 | 0,421 |
| 5,0 | 0,989 | 0,987 a 0,990 | 1,000 | 0,977 | 0,420 |
| 15,0 | 0,989 | 0,987 a 0,990 | 1,000 | 0,986 | 0,420 |

**E4** (η = 0,40; C_A0 = 0,25 mol/L)

| t (min) | X_Zn prevista (comitê) | Faixa dos 10 membros | Fenomenológico puro | Interpolação dos 16 ensaios | C_Af prevista (mol/L) |
| :-: | :-: | :-: | :-: | :-: | :-: |
| 0,5 | 0,365 | 0,360 a 0,369 | 0,400 | 0,361 | 0,022 |
| 1,0 | 0,398 | 0,394 a 0,400 | 0,400 | 0,400 | 0,001 |
| 2,0 | 0,400 | 0,400 a 0,400 | 0,400 | 0,400 | 0,000 |
| 3,0 | 0,400 | 0,400 a 0,400 | 0,400 | 0,400 | 0,000 |
| 4,0 | 0,400 | 0,400 a 0,400 | 0,400 | 0,400 | 0,000 |
| 5,0 | 0,400 | 0,400 a 0,400 | 0,400 | 0,400 | 0,000 |
| 15,0 | 0,400 | 0,400 a 0,400 | 0,400 | 0,400 | 0,000 |

A C_Af prevista é derivada da conversão pela estequiometria, C_Af = C_A0·(1 − X_Zn/η); não é uma previsão independente. A "faixa dos 10 membros" mostra só a variabilidade de treino entre as redes, **não é intervalo de confiança**; o comitê (média de ν antes do PBM) pode ficar um pouco fora da média das conversões dos membros porque o PBM é não linear. A "interpolação dos 16 ensaios" é uma referência simples (interpolação linear em C_A0 e η dos X_Zn medidos, instante a instante), limitada a min(1, η); para E4 ela extrapola em η.

## 3. Relações esperadas
1. **Ordem das conversões:** a conversão final prevista segue a razão molar η, com E3 (0,989) > E2 (0,929) > E1 (0,713) > E4 (0,400). Em 0,5 min: E3 0,923, E2 0,889, E1 0,616, E4 0,365.
2. **Limite estequiométrico (ácido limitante):** em E1 o patamar não passa de 0,75 e em E4 não passa de 0,40. Nos ensaios originais com η = 0,5 o X_Zn medido termina em 0,49 a 0,50, isto é, praticamente no limite; a previsão de E4 chega a 0,40 em cerca de 1 min.
3. **Patamar abaixo do limite para η próximo de 1:** o modelo prevê E1 em 0,713 (limite 0,75) e E2 em 0,929 (limite 1,00). Isso segue o que se mediu nos originais (X_Zn em 15 min):

| η original | X_Zn medido em 15 min |
| :-: | :-: |
| 0,5 | 0,49 a 0,50 |
| 1,0 | 0,85 a 0,87 |
| 1,5 | 0,97 a 0,98 |
| 3,1 | 1,00 a 1,01 |

   Com η = 1,0 o patamar fica em 0,85 a 0,87 e só com η ≥ 1,5 chega perto de 1. Por isso E1 e E2, interpolados entre η de 0,5 e 1,0 e entre 1,0 e 1,5, devem terminar abaixo do limite estequiométrico; a distância até o limite é a incerteza principal da previsão.
4. **Velocidade:** a reação é rápida. O comitê atinge 99% do valor final em 4,7 min (E1), 1,0 min (E2), 1,4 min (E3) e 1,0 min (E4); o ponto de 15 min deve estar no patamar e quase não traz informação sobre a cinética, e os instantes de 0,5 e 1 min são os mais informativos.
5. **Modelo fenomenológico puro:** prevê patamares nos limites estequiométricos (em 15 min: E1 0,750, E2 1,000, E3 1,000, E4 0,400) e sobe mais depressa que o híbrido nos primeiros instantes; deve superestimar E1 e E2, como superestimou os ensaios originais com η próximo de 1.
6. **Ácido residual previsto (estequiométrico):** E1 0,012, E2 0,192, E3 0,420 e E4 0,000 mol/L em 15 min.

## 4. Como ler a comparação com as medições
- **Erro típico do modelo:** RMSE de X_Zn de 0,033 fora da dobra (validação cruzada, 10 sementes) e de 0,020 no teste cego (ensaios 7, 8 e 14). Diferenças da ordem desses valores são esperadas; diferenças bem maiores, ou sistemáticas (mesmo sinal em todos os instantes), indicam efeito que o modelo não vê.
- **E4 é extrapolação** (η = 0,40 < 0,5, mínimo do treino): o erro pode ser maior que o típico. Como o limite estequiométrico é imposto pelo modelo, a previsão de E4 é, na prática, "X_Zn = η a partir de cerca de 1 min"; a medição mostra se esse comportamento vale abaixo de η = 0,5.
- **Efeito do volume (hipótese, não testada):** o modelo não conhece o volume. Com os mesmos C_A0 e η a razão sólido/líquido é igual, mas a geometria do reator, a agitação a 1000 rpm em 200 mL e a fração do volume retirada em cada amostragem podem mudar a transferência de massa e as concentrações. Um desvio sistemático em todos os ensaios aponta para isso.

## 5. Quando as medições chegarem
Preencher `medicoes_template.csv` (ensaio, t_min, XZn_medido) e rodar:

```bash
python Código/etapas/etapa_4_3_previsao_novos_ensaios/prever_novos_ensaios.py comparar --medicoes caminho/medicoes.csv
```

Saem `tabela_comparacao_medicoes.csv` (RMSE por ensaio e global para v2, v1, fenomenológico e interpolação; viés e erro máximo), `tabela_comparacao_medicoes_pontos.csv` e as figuras `*_com_medicoes`. As previsões não são ajustadas aos ensaios novos; usá-los como treino ou validação adicional é decisão à parte.

## 6. Arquivos
`previsao_a_priori_instantes_amostrados.csv`, `previsao_a_priori_curvas.csv` (0 a 15 min, passo de 0,1 min), `previsao_a_priori_novos_ensaios.xlsx` (abas: ensaios, previsao_instantes, curvas_0_15min, medicoes_template), `medicoes_template.csv`, `INTEGRIDADE_previsao_a_priori.json`, `fig_ne_01_E1` a `fig_ne_04_E4`, `fig_ne_05_painel` e `fig_ne_06_contexto_vizinhos` (PNG e PDF, 300 DPI).
