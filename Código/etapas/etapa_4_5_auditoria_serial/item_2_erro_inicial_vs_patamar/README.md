# Item 2 — Erro em 0,5 min contra o patamar

Separa o erro de cada modelo em três faixas de tempo (0,5 min; 1 a 3 min; 4 a 15 min) e verifica se, em 0,5 min, os modelos reproduzem o efeito de C_A0.

- **Depende de:** saídas dos Itens 1 e 3 (rode os dois antes).
- **Não treina nada.** Lê as previsões fora da dobra e as previsões já gravadas no teste cego; nada é escolhido com ele.
- **Conferência:** o script para se o erro de todos os pontos não reproduzir os valores globais já calculados.
- **Não altera nada fora de** `Código/outputs/etapa_4_5_auditoria_serial/item_2_erro_inicial_vs_patamar/`.

```bash
python erro_por_faixa_de_tempo.py
python -m pytest test_erro_por_faixa_de_tempo.py -q -p no:cacheprovider
```
