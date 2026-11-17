# Item 1 — Referências sem modelo

Compara a v2 com a previsão mais simples possível: a média das curvas medidas com a mesma razão molar (η) e uma interpolação linear em C_A0 entre ensaios de mesma η.

- **Validação cruzada:** mesmas 4 dobras da v2. Cada ensaio de validação usa só os ensaios de treino da sua dobra.
- **Teste cego (7, 8, 14):** usa os 13 ensaios de treino. Nada é escolhido com ele.
- **Conferência:** o script para se o RMSE da v2 não reproduzir os valores gravados nas Fases B2 e E.
- **Não altera nada fora de** `Código/outputs/etapa_4_5_auditoria_serial/item_1_referencia_media_eta/`.

```bash
python referencia_media_eta.py
python -m pytest test_referencia_media_eta.py -q
```
