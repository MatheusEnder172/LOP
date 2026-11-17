# Item 4 — δ e taxas médias por intervalo

Calcula as grandezas que os dados identificam: o encolhimento acumulado δ(t), por inversão de X = g(δ), e a taxa média ν̄ = Δδ/Δt em cada intervalo entre amostras. Compara a medição com a v2 (comitê e fora da dobra) e com o fenomenológico.

- **Pontos com X ≥ 0,99** ficam marcados e fora das métricas, porque g é plana ali ou X ≥ 1 não tem inversa.
- **Treino não é previsão:** nos 13 ensaios de treino o comitê mostra ajuste. A previsão está na coluna fora da dobra e no teste cego.
- **Conferência:** o script para se os hashes do comitê mudarem ou se X_Zn não reproduzir as previsões da Etapa 4.2.
- **Não altera nada fora de** `Código/outputs/etapa_4_5_auditoria_serial/item_4_taxa_efetiva/`.

```bash
python delta_e_taxas_medias.py
python -m pytest test_delta_e_taxas_medias.py -q -p no:cacheprovider
```
