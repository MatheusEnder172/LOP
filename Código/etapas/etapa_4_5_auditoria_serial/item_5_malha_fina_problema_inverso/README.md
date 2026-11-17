# Item 5 — Problema inverso com integração exata

Refaz o problema inverso da Etapa 2.1 em duas versões, a original (malha de 0,25 min) e uma com δ(t) dado pela integral analítica da bi-exponencial, e compara δ, ν̄ e ν pontual.

- **Mesmos limites, penalizações e pontos de partida da Etapa 2.1** (um teste compara com o código-fonte original).
- **Conferência:** o script para se a malha de 0,25 min não reproduzir o RMSE gravado na Etapa 2.1.
- **Os alvos novos não são salvos em** `Base de dados/processed/` **nem usados em treino.**
- **Não altera nada fora de** `Código/outputs/etapa_4_5_auditoria_serial/item_5_malha_fina_problema_inverso/`.

```bash
python problema_inverso_malha_fina.py --trabalhadores 8
python -m pytest test_problema_inverso_malha_fina.py -q -p no:cacheprovider
```
