# Item 4 — O que a rede prevê: δ e taxas médias por intervalo

Gerado por `delta_e_taxas_medias.py`. Nenhum modelo foi treinado.

## O que é físico e o que não é

- δ(t) é identificado pelas medições: X = g(δ) é crescente e fixada pela granulometria.
- ν̄ = Δδ/Δt entre amostras também é física e, em princípio, não depende da malha (o Item 5 testa isso).
- O valor de ν em um nó não é identificado: cada medição fixa só uma combinação dos ν nodais (tabela de pesos abaixo).

## Medições usadas

- Pontos bem determinados: 96 de 112. Foram excluídos 16 pontos com X ≥ 0,99, em que g fica plana ou X ≥ 1 não tem inversa.
- Intervalos bem determinados: 96 de 112.
- 21 das 96 taxas medidas são negativas, o que é fisicamente impossível, porque δ não diminui. Elas vêm de flutuações de X entre amostras, e por isso o RMSE de ν̄ inclui o ruído da medição, principalmente nos intervalos finais.
- Como X foi medido com duas casas decimais, a largura mediana da faixa de δ correspondente a ± 0,005 em X é 1,02 µm (máxima: 10,62 µm).
- δ previsto foi limitado a g⁻¹(0,99) = 71,9 µm em todos os modelos, porque acima disso X não determina δ. Sem o limite, o fenomenológico continua acumulando δ depois de X chegar a 1: em 31 dos 112 pontos ele passa do diâmetro máximo da distribuição (297 µm), valor sem significado físico.

## RMSE de δ e de ν̄ (pontos bem determinados)

Entre parênteses, o erro médio com sinal (previsto − medido). No treino, o comitê mostra ajuste; a coluna fora da dobra e o teste cego mostram previsão.

| Grandeza | Conjunto | n | v2 (comitê) | v2 (fora da dobra) | Fenomenológico |
| :-- | :-- | :-: | :-: | :-: | :-: |
| δ (µm) | Treino (ajuste) | 79 | 4,614 (0,268) | — | 25,871 (18,327) |
| δ (µm) | Validação cruzada | 79 | — | 7,723 (-1,666) | 25,871 (18,327) |
| δ (µm) | Teste cego | 17 | 6,551 (0,984) | — | 32,716 (30,552) |
| ν̄ (µm/min) | Treino (ajuste) | 79 | 7,816 (0,723) | — | 17,229 (6,339) |
| ν̄ (µm/min) | Validação cruzada | 79 | — | 9,113 (0,035) | 17,229 (6,339) |
| ν̄ (µm/min) | Teste cego | 17 | 8,551 (0,867) | — | 34,353 (9,457) |

## RMSE de ν̄ por intervalo

Em µm/min. Validação cruzada (fora da dobra) e teste cego.

| Intervalo (min) | n (CV) | v2 fora da dobra | Fenomenológico (CV) | n (teste) | v2 comitê (teste) | Fenomenológico (teste) |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 0 a 0,5 | 13 | 13,360 | 37,180 | 3 | 9,048 | 75,632 |
| 0,5 a 1 | 12 | 14,789 | 16,652 | 3 | 11,712 | 23,291 |
| 1 a 2 | 12 | 6,461 | 10,329 | 3 | 4,618 | 14,965 |
| 2 a 3 | 11 | 7,418 | 4,658 | 2 | 6,808 | 8,122 |
| 3 a 4 | 11 | 5,730 | 6,997 | 2 | 7,055 | 7,532 |
| 4 a 5 | 10 | 2,340 | 2,989 | 2 | 12,824 | 13,345 |
| 5 a 15 | 10 | 0,375 | 0,752 | 2 | 0,591 | 0,757 |

## Pesos de ν nodal em cada δ medido

Extraídos do solver por perfis unitários. A soma dos pesos de cada linha é o próprio tempo (min). Sete medições fixam sete combinações dos 60 valores nodais.

| t (min) | Nós envolvidos | Peso de ν(0,25) | Peso de cada nó intermediário | Peso do último nó | Soma |
| :-: | :-: | :-: | :-: | :-: | :-: |
| 0,5 | 2 | 0,375 | — | 0,125 | 0,500 |
| 1,0 | 4 | 0,375 | 0,250 | 0,125 | 1,000 |
| 2,0 | 8 | 0,375 | 0,250 | 0,125 | 2,000 |
| 3,0 | 12 | 0,375 | 0,250 | 0,125 | 3,000 |
| 4,0 | 16 | 0,375 | 0,250 | 0,125 | 4,000 |
| 5,0 | 20 | 0,375 | 0,250 | 0,125 | 5,000 |
| 15,0 | 60 | 0,375 | 0,250 | 0,125 | 15,000 |

## Pontos mal determinados

| Ensaio | t (min) | X_Zn medido |
| :-: | :-: | :-: |
| 2 | 5 | 0,99 |
| 2 | 15 | 1,00 |
| 7 | 3 | 0,99 |
| 7 | 4 | 1,00 |
| 7 | 5 | 0,99 |
| 7 | 15 | 1,01 |
| 12 | 1 | 1,00 |
| 12 | 2 | 1,00 |
| 12 | 3 | 0,99 |
| 12 | 4 | 0,99 |
| 12 | 5 | 0,99 |
| 12 | 15 | 1,00 |
| 16 | 3 | 0,99 |
| 16 | 4 | 0,99 |
| 16 | 5 | 1,00 |
| 16 | 15 | 1,00 |
