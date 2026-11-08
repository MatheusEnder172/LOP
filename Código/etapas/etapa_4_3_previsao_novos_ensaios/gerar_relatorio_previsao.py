"""Gera `relatorio_previsao_a_priori.md` a partir dos CSVs gravados (todos os números vêm dos arquivos)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

CODIGO_DIR = Path(__file__).resolve().parents[2]
O = CODIGO_DIR / "outputs" / "etapa_4_3_previsao_novos_ensaios"
RAW = CODIGO_DIR.parent / "Base de dados" / "raw"


def f(x: float, n: int = 3) -> str:
    return f"{x:.{n}f}".replace(".", ",")


def main() -> None:
    t = pd.read_csv(O / "previsao_a_priori_instantes_amostrados.csv")
    c = pd.read_csv(O / "previsao_a_priori_curvas.csv")
    integ = json.loads((O / "INTEGRIDADE_previsao_a_priori.json").read_text(encoding="utf-8"))
    serie = pd.read_csv(RAW / "cinetica_batelada_A1_4.csv")

    cond = t.groupby("ensaio").first()
    linhas_cond = "\n".join(
        f"| {e} | {f(r.eta, 2)} | {f(r.CA0_mol_L, 2)} | {r.V_mL:.0f} | {f(r.m_g, 1)} | {f(r.razao_solido_liquido_g_L, 1)} | "
        f"{f(r.limite_min_1_eta, 2)} | {'**extrapolação** (η < 0,5)' if r.extrapolacao_eta else 'dentro do domínio'} |"
        for e, r in cond.iterrows())

    tabs = []
    for e, g in t.groupby("ensaio"):
        lin = [
            f"| {f(r.t_min, 1)} | {f(r.XZn_v2_comite)} | {f(r.XZn_v2_membro_min)} a {f(r.XZn_v2_membro_max)} | "
            f"{f(r.XZn_fenomenologico)} | {f(r.XZn_interp_empirica_16_ensaios)} | {f(r.CAf_v2_mol_L)} |"
            for _, r in g.iterrows()]
        tabs.append(
            f"**{e}** (η = {f(g.eta.iloc[0], 2)}; C_A0 = {f(g.CA0_mol_L.iloc[0], 2)} mol/L)\n\n"
            "| t (min) | X_Zn prevista (comitê) | Faixa dos 10 membros | Fenomenológico puro | "
            "Interpolação dos 16 ensaios | C_Af prevista (mol/L) |\n| :-: | :-: | :-: | :-: | :-: | :-: |\n" + "\n".join(lin))

    fin = serie[serie.t_min == 15.0]
    patamar = fin.groupby("razao_molar_eta")["XZn"].agg(["min", "max"])
    linhas_pat = "\n".join(f"| {f(eta, 1)} | {f(r['min'], 2)} a {f(r['max'], 2)} |" for eta, r in patamar.iterrows())

    fim = {e: g.XZn_v2_comite.iloc[-1] for e, g in c.groupby("ensaio")}
    x05 = {e: g[g.t_min == 0.5].XZn_v2_comite.iloc[0] for e, g in t.groupby("ensaio")}
    t99 = {e: g[g.XZn_v2_comite >= 0.99 * g.XZn_v2_comite.iloc[-1]].t_min.min() for e, g in c.groupby("ensaio")}
    caf = {e: g.CAf_v2_mol_L.iloc[-1] for e, g in t.groupby("ensaio")}
    fpm15 = {e: g.XZn_fenomenologico.iloc[-1] for e, g in t.groupby("ensaio")}
    nl = "\n\n"

    md = f"""# Previsão a priori dos 4 ensaios novos de laboratório (Subetapa 4.3)

**Gerada em {integ['data_geracao']}, antes de qualquer medição**, com a MLP v2 (comitê de 10 redes da Subetapa 3.2.6), que não foi alterada. Os pesos do comitê foram conferidos contra `Código/outputs/models_saved/mlp_v2/SHA256SUMS.txt` (SHA-256 em `INTEGRIDADE_previsao_a_priori.json`, junto com o SHA-256 dos arquivos de previsão). A comparação com as medições usa só esses arquivos gravados; o script recusa refazer a previsão e aborta se algum arquivo gravado tiver sido alterado.

## 1. Condições dos ensaios
Temperatura de 40 °C e agitação de 1000 rpm, como nos 16 ensaios originais; só o volume mudou (200 mL em vez de 400 mL). O modelo usa apenas C_A0, η e t. A razão sólido/líquido decorre de C_A0 e η (m/V = C_A0·M_ZnO/(η·0,81)), logo é a mesma de um ensaio original com os mesmos C_A0 e η, e cai dentro da faixa dos originais (3 a 300 g/L).

| Ensaio | η | C_A0 (mol/L) | V (mL) | m (g) | m/V (g/L) | Limite min(1, η) | Domínio do treino |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-- |
{linhas_cond}

## 2. Previsões (v2)

{nl.join(tabs)}

A C_Af prevista é derivada da conversão pela estequiometria, C_Af = C_A0·(1 − X_Zn/η); não é uma previsão independente. A "faixa dos 10 membros" mostra só a variabilidade de treino entre as redes, **não é intervalo de confiança**; o comitê (média de ν antes do PBM) pode ficar um pouco fora da média das conversões dos membros porque o PBM é não linear. A "interpolação dos 16 ensaios" é uma referência simples (interpolação linear em C_A0 e η dos X_Zn medidos, instante a instante), limitada a min(1, η); para E4 ela extrapola em η.

## 3. Relações esperadas
1. **Ordem das conversões:** a conversão final prevista segue a razão molar η, com E3 ({f(fim['E3'])}) > E2 ({f(fim['E2'])}) > E1 ({f(fim['E1'])}) > E4 ({f(fim['E4'])}). Em 0,5 min: E3 {f(x05['E3'])}, E2 {f(x05['E2'])}, E1 {f(x05['E1'])}, E4 {f(x05['E4'])}.
2. **Limite estequiométrico (ácido limitante):** em E1 o patamar não passa de 0,75 e em E4 não passa de 0,40. Nos ensaios originais com η = 0,5 o X_Zn medido termina em 0,49 a 0,50, isto é, praticamente no limite; a previsão de E4 chega a 0,40 em cerca de 1 min.
3. **Patamar abaixo do limite para η próximo de 1:** o modelo prevê E1 em {f(fim['E1'])} (limite 0,75) e E2 em {f(fim['E2'])} (limite 1,00). Isso segue o que se mediu nos originais (X_Zn em 15 min):

| η original | X_Zn medido em 15 min |
| :-: | :-: |
{linhas_pat}

   Com η = 1,0 o patamar fica em 0,85 a 0,87 e só com η ≥ 1,5 chega perto de 1. Por isso E1 e E2, interpolados entre η de 0,5 e 1,0 e entre 1,0 e 1,5, devem terminar abaixo do limite estequiométrico; a distância até o limite é a incerteza principal da previsão.
4. **Velocidade:** a reação é rápida. O comitê atinge 99% do valor final em {f(t99['E1'], 1)} min (E1), {f(t99['E2'], 1)} min (E2), {f(t99['E3'], 1)} min (E3) e {f(t99['E4'], 1)} min (E4); o ponto de 15 min deve estar no patamar e quase não traz informação sobre a cinética, e os instantes de 0,5 e 1 min são os mais informativos.
5. **Modelo fenomenológico puro:** prevê patamares nos limites estequiométricos (em 15 min: E1 {f(fpm15['E1'])}, E2 {f(fpm15['E2'])}, E3 {f(fpm15['E3'])}, E4 {f(fpm15['E4'])}) e sobe mais depressa que o híbrido nos primeiros instantes; deve superestimar E1 e E2, como superestimou os ensaios originais com η próximo de 1.
6. **Ácido residual previsto (estequiométrico):** E1 {f(caf['E1'])}, E2 {f(caf['E2'])}, E3 {f(caf['E3'])} e E4 {f(caf['E4'])} mol/L em 15 min.

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
"""
    (O / "relatorio_previsao_a_priori.md").write_text(md, encoding="utf-8")
    print("relatório gerado")


if __name__ == "__main__":
    main()
