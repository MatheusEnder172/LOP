"""Subetapa 4.3 — Medições dos 4 ensaios novos: conversão de Zn em X_Zn e comparação com a previsão a priori.

Lê `Base de dados/Experimentos novos/Resultados.xlsx` (não alterado), converte a concentração de Zn em conversão
com o mesmo critério dos 16 ensaios originais e compara com a previsão gravada em 08/11/2026 (arquivos conferidos por
hash; a previsão não é refeita).

Conversão: X_Zn = C_Zn · V / (m · w), em que C_Zn é a concentração de Zn no licor (g/L), V = 0,200 L, m é a massa de
sólido e w = 0,611 g Zn/g de sólido, calibrado nos 16 ensaios originais (ver `calibrar_teor_zn`). A coluna "Zn (mg/L)"
da planilha (leitura × fator de diluição M2/M1) é multiplicada por `FATOR_DILUICAO_ANTERIOR` (1000, hipótese: há
uma diluição anterior não registrada; com ela, as concentrações ficam entre 16 e 35 g/L, a ordem de grandeza esperada).

Saídas em `Código/outputs/etapa_4_3_previsao_novos_ensaios/medicoes/` e a tabela de entrada do comparador em
`Base de dados/Experimentos novos/medicoes_XZn_ensaios_novos.csv`.

Uso: python analisar_medicoes_novos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import openpyxl
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prever_novos_ensaios as pn  # noqa: E402

BASE = pn.BASE_DIR / "Base de dados"
XLSX = BASE / "Experimentos novos" / "Resultados.xlsx"
SAIDA_CSV = BASE / "Experimentos novos" / "medicoes_XZn_ensaios_novos.csv"
OUT = pn.OUT / "medicoes"
FATOR_DILUICAO_ANTERIOR = 1000.0  # hipótese; ver docstring
V_L = 0.200


def calibrar_teor_zn() -> tuple[float, float]:
    """Teor de Zn do sólido (g/g) que reproduz a conversão final dos 16 ensaios originais (V = 400 mL)."""
    m = pd.read_csv(BASE / "raw" / "bancada_batelada_A1_1.csv")
    s = pd.read_csv(BASE / "raw" / "cinetica_batelada_A1_4.csv")
    x15 = s[s["t_min"] == 15.0].set_index("ensaio")["XZn"]
    w = m.set_index("ensaio").apply(lambda r: r["Zn_licor_g_L"] * 0.4 / (r["mB0_g"] * x15.loc[r.name]), axis=1)
    return float(w.mean()), float(w.std(ddof=1))


def ler_planilha() -> pd.DataFrame:
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    linhas, atual = [], None
    for row in wb.active.iter_rows(values_only=True):
        if row[0] == "Tempo":
            atual = row[1]
        elif isinstance(row[0], (int, float)) and atual:
            linhas.append({"ensaio": atual, "t_min": float(row[0]), "M1_g": row[1], "M2_g": row[2], "FD": row[3],
                           "leitura_mg_L": row[4], "Zn_planilha_mg_L": row[5]})
    return pd.DataFrame(linhas)


def converter(df: pd.DataFrame, w: float, fator: float = FATOR_DILUICAO_ANTERIOR, troca: bool = False) -> pd.DataFrame:
    out = df.copy()
    if troca:  # sensibilidade: rótulos E2 e E3 trocados entre si
        out["ensaio"] = out["ensaio"].map({"E2": "E3", "E3": "E2"}).fillna(out["ensaio"])
    out["Zn_licor_g_L"] = out["Zn_planilha_mg_L"] * fator / 1000.0
    out["m_g"] = out["ensaio"].map({k: v["m_g"] for k, v in pn.ENSAIOS_NOVOS.items()})
    out["XZn_medido"] = out["Zn_licor_g_L"] * V_L / (out["m_g"] * w)
    return out


def rmse(a, b) -> float:
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def comparar_variante(conv: pd.DataFrame, tab: pd.DataFrame, nome: str) -> pd.DataFrame:
    m = conv[conv["t_min"] > 0].merge(tab, on=["ensaio", "t_min"], how="inner")
    linhas = []
    for e, g in list(m.groupby("ensaio")) + [("Todos", m)]:
        linhas.append({
            "variante": nome, "ensaio": e, "n_pontos": len(g),
            "RMSE_v2": rmse(g["XZn_medido"], g["XZn_v2_comite"]), "RMSE_fenomenologico": rmse(g["XZn_medido"], g["XZn_fenomenologico"]),
            "RMSE_v1": rmse(g["XZn_medido"], g["XZn_v1"]), "RMSE_interp_empirica": rmse(g["XZn_medido"], g["XZn_interp_empirica_16_ensaios"]),
            "vies_medido_menos_v2": float(np.mean(g["XZn_medido"] - g["XZn_v2_comite"])),
            "X_medido_15min": float(g[g["t_min"] == 15.0]["XZn_medido"].iloc[0]) if (g["t_min"] == 15.0).any() and e != "Todos" else np.nan,
            "X_prev_15min": float(g[g["t_min"] == 15.0]["XZn_v2_comite"].iloc[0]) if (g["t_min"] == 15.0).any() and e != "Todos" else np.nan,
            "limite_min_1_eta": float(g["limite_min_1_eta"].iloc[0]) if e != "Todos" else np.nan,
            "frac_pontos_acima_do_limite": float((g["XZn_medido"] > g["limite_min_1_eta"] + 1e-9).mean()),
        })
    return pd.DataFrame(linhas)


def escrever_relatorio(r: pd.DataFrame, ct: pd.DataFrame, tab: pd.DataFrame, w: float, w_dp: float) -> None:
    f = lambda x, n=3: f"{x:.{n}f}".replace(".", ",")
    rot = r[r["variante"].str.startswith("como rotulado")].set_index("ensaio")
    tro = r[r["variante"].str.startswith("rótulos")].set_index("ensaio")
    m = ct[ct["t_min"] > 0].merge(tab, on=["ensaio", "t_min"])
    m["erro"] = m["XZn_medido"] - m["XZn_v2_comite"]
    sem_e1 = m[m["ensaio"] != "E1"]
    dentro = float((m["erro"].abs() <= 0.05).mean())
    pontos = m.pivot(index="t_min", columns="ensaio", values="XZn_medido")
    prev = m.pivot(index="t_min", columns="ensaio", values="XZn_v2_comite")

    def linhas(piv):
        return "\n".join("| " + f(t, 1) + " | " + " | ".join(f(piv.loc[t, e]) for e in piv.columns) + " |" for t in piv.index)

    tab_rot = "\n".join(
        f"| {e} | {f(rot.loc[e, 'RMSE_v2'])} | {f(rot.loc[e, 'X_medido_15min'], 2)} | {f(rot.loc[e, 'X_prev_15min'], 2)} | "
        f"{f(rot.loc[e, 'limite_min_1_eta'], 2)} |" for e in pn.ENSAIOS_NOVOS)
    tab_tro = "\n".join(
        f"| {e} | {f(tro.loc[e, 'RMSE_v2'])} | {f(tro.loc[e, 'RMSE_fenomenologico'])} | {f(tro.loc[e, 'RMSE_v1'])} | "
        f"{f(tro.loc[e, 'RMSE_interp_empirica'])} | {f(tro.loc[e, 'vies_medido_menos_v2'])} | {f(tro.loc[e, 'X_medido_15min'], 2)} | "
        f"{f(tro.loc[e, 'X_prev_15min'], 2)} |" for e in pn.ENSAIOS_NOVOS)
    cab = " | ".join(pontos.columns)
    sep = " | ".join([":-:"] * len(pontos.columns))
    md = f"""# Comparação das medições dos 4 ensaios novos com a previsão a priori (09/11/2026)

A previsão (MLP v2, gerada em 08/11/2026 às 13h14, antes das medições) não foi alterada; seus arquivos foram conferidos por hash. As medições vêm de `Base de dados/Experimentos novos/Resultados.xlsx` (não alterado), com 6 instantes por ensaio (0,5; 1; 2; 3; 5 e 15 min; **não há medição em 4 min**).

## 1. Conversão das medições em X_Zn (hipóteses a confirmar)
A planilha dá a concentração de Zn (mg/L) = leitura × FD (FD = M2/M1), sem a conversão em X_Zn. Foi usada a mesma conta dos 16 ensaios originais: X_Zn = C_Zn · V / (m · w), com V = 0,200 L, m = 6,7; 12,1; 6,7 e 12,6 g (E1 a E4) e w = {f(w, 3)} ± {f(w_dp, 3)} g de Zn por g de sólido (calibrado nos 16 ensaios originais). **Hipótese 1:** a planilha não registra uma diluição anterior; as concentrações só têm a ordem de grandeza esperada (16 a 35 g/L, contra 2 a 90 g/L nos originais) se o valor da coluna "Zn (mg/L)" for lido como g/L (isto é, com uma diluição anterior de 1000 vezes). Se o fator real for outro, todos os X_Zn mudam na mesma proporção.

## 2. Resultado como rotulado na planilha
| Ensaio | RMSE (v2) | X medido em 15 min | X previsto em 15 min | Limite min(1, η) |
| :-: | :-: | :-: | :-: | :-: |
{tab_rot}

Como rotulado, **E3 dá X_Zn = {f(rot.loc['E3', 'X_medido_15min'], 2)} (acima de 1, impossível)** e E2 dá {f(rot.loc['E2', 'X_medido_15min'], 2)}, muito abaixo do previsto. As concentrações de Zn da planilha sugerem que **os rótulos E2 e E3 estão trocados** (ou as massas): o Zn do "E3" (34,6 g/L) só é possível com a massa de 12,1 g (E2), e o do "E2" (19,9 g/L), com 6,7 g (E3).

## 3. Resultado com E2 e E3 trocados (mais plausível; a confirmar com o laboratório)
| Ensaio | RMSE v2 | RMSE fenomenológico | RMSE v1 | RMSE interpolação | Viés (medido − v2) | X medido 15 min | X previsto 15 min |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
{tab_tro}

RMSE global da v2: {f(tro.loc['Todos', 'RMSE_v2'])} nos 24 pontos; **{f(float((sem_e1['erro'] ** 2).mean() ** 0.5))} sem o E1**; {f(100 * dentro, 0)}% dos pontos a menos de 0,05 da previsão. As referências de erro do modelo eram 0,033 (validação cruzada) e 0,020 (teste cego).

X_Zn medido:

| t (min) | {cab} |
| :-: | {sep} |
{linhas(pontos)}

X_Zn previsto (v2):

| t (min) | {cab} |
| :-: | {sep} |
{linhas(prev)}

## 4. Leitura
- **E2 e E3 (η = 1,25 e 2,25):** o patamar é bem previsto (diferença de {f(tro.loc['E2', 'X_medido_15min'] - tro.loc['E2', 'X_prev_15min'], 3)} e {f(tro.loc['E3', 'X_medido_15min'] - tro.loc['E3', 'X_prev_15min'], 3)} em 15 min), e o erro vem sobretudo dos instantes iniciais (em 0,5 e 1 min, a previsão fica 0,04 a 0,07 acima do medido). O modelo híbrido foi melhor que o fenomenológico nesses dois, mas a **interpolação simples dos 16 ensaios medidos foi ainda um pouco melhor** (RMSE {f(tro.loc['E2', 'RMSE_interp_empirica'])} e {f(tro.loc['E3', 'RMSE_interp_empirica'])}), o que limita o que se pode afirmar sobre o ganho do modelo dentro do domínio.
- **E1 e E4 (C_A0 = 0,25 mol/L; η = 0,75 e 0,40):** em **todos** os instantes, o X_Zn medido fica **acima do limite estequiométrico** (E1: 0,77 a 0,87 contra 0,75; E4: 0,42 a 0,45 contra 0,40). Com as condições nominais isso é impossível, então o desvio (E1: RMSE {f(tro.loc['E1', 'RMSE_v2'])}) não pode ser atribuído ao modelo antes de se esclarecer o dado. Em E1 o X medido ainda cai de 0,87 (1 min) para 0,81 (15 min), o que não é esperado para uma conversão.
- Hipóteses, **não testadas**, para o excesso nos dois ensaios de menor C_A0: concentração real do ácido maior que 0,25 mol/L, massa ou volume diferentes dos nominais, teor de Zn do sólido diferente (w), ou viés analítico ou de diluição. Um ajuste exploratório do fator de escala em C_A0 e η dá s = 1,11 para E4 (RMSE 0,009) mas s > 1,3 para E1, ou seja, uma única correção de ácido não explicaria os dois.
- Efeito do volume (200 contra 400 mL): não é possível separá-lo dos problemas acima.

## 5. Arquivos
`Base de dados/Experimentos novos/medicoes_XZn_ensaios_novos.csv`; em `Código/outputs/etapa_4_3_previsao_novos_ensaios/` as tabelas `tabela_comparacao_medicoes*.csv` e as figuras `*_com_medicoes` (como rotulado); em `medicoes/`: `medicoes_convertidas_todas.csv`, `tabela_sensibilidade_comparacao.csv` (rótulos e w ± 0,02), `fig_ne_07_rotulagem_E2_E3` e `fig_ne_08_painel_medicoes_E2_E3_trocados`.
"""
    (OUT / "relatorio_comparacao_medicoes.md").write_text(md, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    integ_ok = pn.sha256(pn.OUT / "previsao_a_priori_instantes_amostrados.csv")
    esperado = __import__("json").loads((pn.OUT / "INTEGRIDADE_previsao_a_priori.json").read_text(encoding="utf-8"))
    assert integ_ok == esperado["sha256_previsoes"]["previsao_a_priori_instantes_amostrados.csv"], "previsão alterada"
    tab = pd.read_csv(pn.OUT / "previsao_a_priori_instantes_amostrados.csv")
    w, w_dp = calibrar_teor_zn()
    bruto = ler_planilha()
    bruto["checagem_FD_x_leitura"] = bruto["FD"] * bruto["leitura_mg_L"] - bruto["Zn_planilha_mg_L"]
    assert bruto["checagem_FD_x_leitura"].abs().max() < 1e-6, "Zn da planilha != FD × leitura"
    conv = converter(bruto, w)
    conv.to_csv(OUT / "medicoes_convertidas_todas.csv", index=False)
    conv[conv["t_min"] > 0][["ensaio", "t_min", "XZn_medido"]].to_csv(SAIDA_CSV, index=False)

    # comparação oficial (script da previsão a priori; só os arquivos gravados)
    pn.comparar(SAIDA_CSV)

    # sensibilidades
    res = [comparar_variante(conv, tab, "como rotulado (w = %.3f; fator 1000)" % w),
           comparar_variante(converter(bruto, w, troca=True), tab, "rótulos E2 e E3 trocados")]
    for dw in (-0.02, 0.02):
        res.append(comparar_variante(converter(bruto, w + dw), tab, f"w = {w + dw:.3f}"))
    r = pd.concat(res, ignore_index=True)
    r.to_csv(OUT / "tabela_sensibilidade_comparacao.csv", index=False)

    # figura: X medido (15 min e média dos instantes) × previsto, nas duas rotulagens
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    for ax, (tit, troca) in zip(axes, (("Como rotulado na planilha", False), ("Rótulos E2 e E3 trocados", True))):
        c = converter(bruto, w, troca=troca)
        for e, p in pn.ENSAIOS_NOVOS.items():
            g = c[(c["ensaio"] == e) & (c["t_min"] > 0)]
            pv = tab[tab["ensaio"] == e]
            ax.plot(pv["t_min"], pv["XZn_v2_comite"], "-", color=pn.COR["v2"], alpha=0.5, lw=1.2)
            ax.scatter(g["t_min"], g["XZn_medido"], s=36, label=f"{e} medido")
            ax.axhline(min(1.0, p["eta"]), ls=":", lw=0.8, color="k")
        ax.set_title(tit)
        ax.set_xlabel("Tempo (min)")
        ax.grid(ls="--", alpha=0.4)
    axes[0].set_ylabel("Conversão de zinco, $X_{Zn}$ (–); linhas: previsão a priori (v2)")
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig_ne_07_rotulagem_E2_E3.png", dpi=300)
    fig.savefig(OUT / "fig_ne_07_rotulagem_E2_E3.pdf", dpi=300)
    plt.close(fig)
    # painel principal: rótulos E2 e E3 trocados, com as medições sobrepostas à previsão a priori
    cur = pd.read_csv(pn.OUT / "previsao_a_priori_curvas.csv")
    ct = converter(bruto, w, troca=True)
    med = ct[ct["t_min"] > 0][["ensaio", "t_min", "XZn_medido"]]
    pn.estilo()
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), sharex=True, sharey=True)
    for ax, nome in zip(axes.ravel(), pn.ENSAIOS_NOVOS):
        pn._painel(ax, nome, tab, cur, med)
    axes[0, 0].legend(loc="lower right", fontsize=7.5)
    fig.suptitle("Previsão a priori e medições dos 4 ensaios novos (rótulos E2 e E3 trocados em relação à planilha)", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT / "fig_ne_08_painel_medicoes_E2_E3_trocados.png", dpi=300)
    fig.savefig(OUT / "fig_ne_08_painel_medicoes_E2_E3_trocados.pdf", dpi=300)
    plt.close(fig)
    escrever_relatorio(r, ct, tab, w, w_dp)
    print(f"w = {w:.4f} ± {w_dp:.4f}")
    pd.set_option("display.width", 220)
    print(r.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
