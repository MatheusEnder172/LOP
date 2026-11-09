# Os 4 ensaios novos: o que fica para depois (extra nos Resultados)

Decisão de 09/11: por enquanto os Resultados são escritos **só com 13 ensaios de treino/validação cruzada e 3 de teste cego**. Os 4 ensaios novos entram **depois**, como um extra, se e quando os dados forem esclarecidos. O modelo v2 continua congelado.

## Estado

- Previsão a priori da v2 gravada em **08/11/2026, 13h14**, antes das medições (hash conferido; `Código/outputs/etapa_4_3_previsao_novos_ensaios/INTEGRIDADE_previsao_a_priori.json`). O script `prever_novos_ensaios.py` recusa refazer a previsão.
- Condições: E1 (η 0,75; C_A0 0,25 mol/L; 200 mL; 6,7 g), E2 (1,25; 0,75; 200 mL; 12,1 g), E3 (2,25; 0,75; 200 mL; 6,7 g), E4 (0,40; 0,25; 200 mL; 12,6 g). Instantes previstos: 0,5; 1; 2; 3; 4; 5; 15 min.
- Medições: `Base de dados/Experimentos novos/Resultados.xlsx` (não alterar). Só Zn em mg/L (leitura × FD), em 0,5; 1; 2; 3; 5; 15 min (**sem 4 min**). Conversão: X = C_Zn·V/(m·w), w = 0,611 ± 0,004 (calibrado nos 16 originais), com a hipótese (a confirmar) de uma diluição anterior de 1000×.
- Comparação: `Código/outputs/etapa_4_3_previsao_novos_ensaios/medicoes/relatorio_comparacao_medicoes.md`; reexecutar com `python Código/etapas/etapa_4_3_previsao_novos_ensaios/analisar_medicoes_novos.py` (um comando) quando houver dados corrigidos.

## Resultado da primeira comparação (provisório, não é para o relatório ainda)

- **Como rotulado** na planilha: impossível (E3 dá X > 1; E2 dá 0,54). Os valores de Zn sugerem **E2 e E3 trocados** (ou as massas).
- **Com E2 e E3 trocados:** RMSE da v2 = E1 0,144; E2 0,049; E3 0,042; E4 0,041; global 0,081; **0,044 sem o E1**. Referências do modelo: 0,033 (validação cruzada) e 0,020 (teste cego).
- **E1 e E4 (C_A0 = 0,25):** X medido acima do limite estequiométrico em todos os instantes. Impossível com as condições nominais. O desvio de E1 não pode ser atribuído ao modelo antes de esclarecer o dado.
- A interpolação simples dos 16 ensaios foi um pouco melhor que a v2 em E2 e E3. O efeito do volume (200 × 400 mL) não se separa dos problemas de dado.

## O que o laboratório precisa confirmar

Rótulos de E2 e E3; diluição anterior à coluna FD; massa pesada e volume reais; concentração real do ácido (titulação); teor de Zn do lote de calcina; o ponto de 4 min; volume retirado por amostra; réplicas analíticas.

## Como entra no relatório quando chegar a hora

- Nova subseção em Resultados (final de MODELAGEM HÍBRIDA SERIAL): **"Validação externa com ensaios novos"**, em vermelho, curta, com as ressalvas acima. Reescrever o Apêndice E.11 de "Previsão a priori" para "Previsão a priori e validação com ensaios novos" (a previsão já é o texto atual).
- Atualizar "Discussão e limitações" (a v10 diz que não há ensaios novos).
- **Não** retreinar com os 4 ensaios sem o usuário decidir (opções discutidas: manter a v2 e validar com os 4; retreinar com 16 ensaios incluindo os 3 do teste cego; incluir os 4 no treino, o que exige problema inverso para eles e o modelo não conhece o volume). Retreinar muda todos os números dos Resultados e dos Apêndices.
- Se os dados forem esclarecidos até 12/11, dá tempo de incluir; senão, o relatório entrega sem a validação externa e o extra vira "trabalho futuro" em uma frase.
