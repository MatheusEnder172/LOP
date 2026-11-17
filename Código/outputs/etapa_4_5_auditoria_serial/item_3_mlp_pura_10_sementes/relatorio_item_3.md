# Item 3 — MLP pura com 10 sementes

Gerado por `mlp_pura_10_sementes.py`. Sem nova busca e sem uso do teste cego.

## Reprodução do valor antigo

- Sementes 42 a 44, RMSE médio: 0,042141 (gravado: 0,042141).
- Maior diferença ponto a ponto contra as previsões gravadas: 2,2 × 10^-16.

## Comparação pareada (RMSE de X_Zn fora da dobra, 91 pontos)

Diferença negativa significa v2 melhor.

| Sementes | v2 (média ± dp) | MLP pura (média ± dp) | Diferença | Sementes em que a v2 ganha | p (t pareado) | p (Wilcoxon) | IC 95% reamostrando ensaios |
| :-- | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 42 a 51 (todas) | 0,0326 ± 0,0050 | 0,0437 ± 0,0041 | -0,0110 | 10 de 10 | < 0,0001 | 0,0020 | -0,0209 a -0,0017 |
| 42 a 44 (usadas na escolha) | 0,0308 ± 0,0057 | 0,0421 ± 0,0035 | -0,0114 | 3 de 3 | — | — | -0,0178 a -0,0042 |
| 45 a 51 (não vistas) | 0,0334 ± 0,0049 | 0,0443 ± 0,0045 | -0,0109 | 7 de 7 | 0,0012 | 0,0156 | -0,0221 a -0,0004 |

## Leitura

- Com as 10 sementes, o intervalo por ensaios não contém zero: a v2 é melhor que a MLP pura também quando se considera a variação entre ensaios.
- Os testes pareados por semente mantêm os 13 ensaios fixos. Eles medem se a diferença supera a variação de treinamento, não se ela se repetiria com outros ensaios.
- O pareamento é só pelo número da semente: as duas redes não compartilham inicialização.
- As sementes 42 a 44 foram usadas para escolher a configuração da MLP pura; as sementes 45 a 51 não foram vistas nessa escolha.
- A assimetria de busca permanece: cerca de 950 tentativas para a v2 e 32 configurações para a MLP pura.

## Contexto: referências sem modelo (Item 1)

Média por η: 0,0343. Interpolação em C_A0: 0,0323.

## RMSE por ensaio (média das 10 sementes)

| Ensaio | η | C_A0 (mol/L) | v2 | MLP pura | Diferença |
| :-: | :-: | :-: | :-: | :-: | :-: |
| 1 | 0,5 | 0,1 | 0,0268 | 0,0416 | -0,0148 |
| 2 | 3,1 | 0,1 | 0,0228 | 0,0598 | -0,0370 |
| 3 | 0,5 | 0,5 | 0,0193 | 0,0204 | -0,0012 |
| 4 | 0,5 | 1,0 | 0,0215 | 0,0251 | -0,0036 |
| 5 | 0,5 | 1,5 | 0,0213 | 0,0660 | -0,0446 |
| 6 | 1,0 | 0,1 | 0,0437 | 0,0582 | -0,0145 |
| 9 | 1,0 | 1,0 | 0,0162 | 0,0250 | -0,0089 |
| 10 | 1,0 | 1,5 | 0,0542 | 0,0395 | 0,0147 |
| 11 | 1,5 | 0,1 | 0,0344 | 0,0235 | 0,0109 |
| 12 | 3,1 | 1,0 | 0,0131 | 0,0222 | -0,0091 |
| 13 | 1,5 | 0,5 | 0,0222 | 0,0383 | -0,0162 |
| 15 | 1,5 | 1,5 | 0,0580 | 0,0576 | 0,0004 |
| 16 | 3,1 | 1,5 | 0,0174 | 0,0261 | -0,0087 |
