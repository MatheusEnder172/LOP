# Item 3 — MLP pura com 10 sementes

Roda a configuração já escolhida da MLP pura (`config_escolhida.json`, sem nova busca) nas mesmas 4 dobras e nas sementes 42 a 51, usando a função de treino da Subetapa 3.2.7.

- **Conferência:** o script treina primeiro as sementes 42 a 44 e para se elas não reproduzirem o valor gravado (0,0421).
- **Comparação com a v2:** média, desvio, erro-padrão, t pareado e Wilcoxon por semente, mais um intervalo que reamostra os 13 ensaios.
- **Teste cego:** não é usado.
- **Não altera nada fora de** `Código/outputs/etapa_4_5_auditoria_serial/item_3_mlp_pura_10_sementes/`.

```bash
python mlp_pura_10_sementes.py --trabalhadores 8
python -m pytest test_mlp_pura_10_sementes.py -q -p no:cacheprovider
```
