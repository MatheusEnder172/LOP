"""Subetapa 4.4 — Figuras e tabelas de apoio aos Resultados do híbrido serial (MLP v2, comitê de 10 redes).

Não treina nada: usa o comitê congelado (hashes em `models_saved/mlp_v2/SHA256SUMS.txt`, conferidos
antes de calcular), as medições dos 16 ensaios e as saídas já gravadas das Etapas 4.2 e 3.2.6.

Saídas em `Código/outputs/etapa_4_4_resultados_hibrido_serial/` (300 DPI, PNG e PDF; CSVs):
    fig_rh_01_curvas_16_ensaios   conversão medida e prevista (v2 com faixa dos membros e fenomenológico) nos 16 ensaios
    fig_rh_02_paridade            conversão medida × prevista (fenomenológico, v1, v2), treino e teste cego
    fig_rh_03_erro_por_ensaio     RMSE por ensaio (fenomenológico, v1, v2) e erro fora da dobra da v2
    fig_rh_04_mapa_conversao      conversão prevista em 0,5 e 15 min no plano (C_A0, η) com os 16 ensaios
    tabela_consistencia_fisica.csv, tabela_mapa_conversao.csv, tabela_tendencias.csv

Uso: python analisar_resultados.py
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CODIGO_DIR = Path(__file__).resolve().parents[2]
BASE_DIR = CODIGO_DIR.parent
SUB326 = CODIGO_DIR / "etapas" / "etapa_3_2" / "subetapa_3_2_6_mlp_otimizacao"
for p in (CODIGO_DIR, SUB326):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.hybrid.serial_hybrid import SerialHybridModel  # noqa: E402
from src.physics.pbm_batch import BatchPBMSolver  # noqa: E402

OUT = CODIGO_DIR / "outputs" / "etapa_4_4_resultados_hibrido_serial"
MODELOS = CODIGO_DIR / "outputs" / "models_saved" / "mlp_v2"
SUB = CODIGO_DIR / "outputs" / "etapa_3_2" / "subetapa_3_2_6_mlp_otimizacao"
E42 = CODIGO_DIR / "outputs" / "etapa_4_2_avaliacao_indomain"
TESTE = [7, 8, 14]
T_CURVA = np.round(np.arange(0.0, 15.0 + 1e-9, 0.05), 6)
COR = {"v2": "#2E6DA4", "v1": "#D9822B", "fpm": "#8C8C8C", "exp": "#1F3A5F", "teste": "#B23A48", "cv": "#2A9D8F"}


def estilo() -> None:
    plt.rcParams.update({
        "font.family": "Arial", "font.size": 10, "axes.labelsize": 11, "axes.titlesize": 11,
        "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 9, "savefig.dpi": 300, "savefig.bbox": "tight",
    })


def salvar(fig, nome: str) -> None:
    fig.savefig(OUT / f"{nome}.png", dpi=300)
    fig.savefig(OUT / f"{nome}.pdf", dpi=300)
    plt.close(fig)


def conferir_modelo() -> None:
    for linha in (MODELOS / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if linha.strip():
            h, nome = linha.split(None, 1)
            nome = nome.strip().lstrip("*")
            if hashlib.sha256((MODELOS / nome).read_bytes()).hexdigest() != h:
                raise SystemExit(f"Hash diferente para {nome}: o comitê v2 foi alterado.")


def rmse(y, p) -> float:
    return float(np.sqrt(np.mean((np.asarray(y) - np.asarray(p)) ** 2)))


def r2(y, p) -> float:
    y, p = np.asarray(y), np.asarray(p)
    return float(1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2))


def carregar():
    meta = pd.read_csv(BASE_DIR / "Base de dados" / "raw" / "bancada_batelada_A1_1.csv")
    serie = pd.read_csv(BASE_DIR / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv")
    pred = pd.read_csv(E42 / "tabela_predicoes_detalhadas_16_ensaios.csv")
    oof = pd.read_csv(SUB / "fase_b2" / "finalistas_oof.csv")
    oof = oof[oof["config"] == "B2 – tentativa 511"]
    return meta, serie, pred, oof


def curvas(v2: SerialHybridModel, solver: BatchPBMSolver, meta: pd.DataFrame) -> dict:
    out = {}
    for _, m in meta.sort_values("ensaio").iterrows():
        eta, ca0 = float(m["razao_molar_eta"]), float(m["CA0_mol_L"])
        c = v2.simulate(ca0=ca0, eta=eta, t_eval=T_CURVA)
        mem = v2.simulate_members(ca0=ca0, eta=eta, t_eval=T_CURVA)
        fpm = solver.simulate(ca0=ca0, eta=eta, t_eval=T_CURVA, alpha=0.0)["XZn"]
        out[int(m["ensaio"])] = {"eta": eta, "ca0": ca0, "x": c["XZn"], "min": mem["XZn_min"], "max": mem["XZn_max"], "fpm": fpm,
                                 "nu": c["abs_v"]}
    return out


# ------------------------------------------------------------------------------------------ figuras
def fig_curvas(cur: dict, pred: pd.DataFrame) -> None:
    fig, axes = plt.subplots(4, 4, figsize=(15, 12), sharex=True, sharey=True)
    for ax, e in zip(axes.ravel(), range(1, 17)):
        c = cur[e]
        teste = e in TESTE
        t = T_CURVA[1:]
        ax.fill_between(t, c["min"][1:], c["max"][1:], color=COR["v2"], alpha=0.25, lw=0)
        ax.plot(t, c["fpm"][1:], color=COR["fpm"], ls="--", lw=1.3, label="Fenomenológico puro")
        ax.plot(t, c["x"][1:], color=COR["v2"], lw=2.0, label="Híbrido (comitê da MLP v2)")
        p = pred[pred["ensaio"] == e]
        ax.scatter(p["t_min"], p["XZn_exp"], s=26, color=COR["exp"], zorder=5, label="Medido")
        ax.axhline(min(1.0, c["eta"]), color="k", ls=":", lw=0.9)
        r = rmse(p["XZn_exp"], p["XZn_Hibrido_MLP_v2"])
        ax.set_title(f"Ensaio {e}{' (teste cego)' if teste else ''}: η = {c['eta']:.1f}; $C_{{A0}}$ = {c['ca0']:.1f}\nRMSE híbrido = {r:.3f}",
                     fontsize=9.5, color=COR["teste"] if teste else "black")
        ax.set_xscale("log")
        ax.set_xlim(0.1, 15.5)
        ax.set_ylim(-0.02, 1.08)
        ax.grid(ls="--", alpha=0.4)
    for ax in axes[-1]:
        ax.set_xlabel("Tempo (min)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Conversão de zinco, $X_{Zn}$ (–)")
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.01), frameon=False)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    salvar(fig, "fig_rh_01_curvas_16_ensaios")


def fig_paridade(pred: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.9), sharex=True, sharey=True)
    modelos = [("Fenomenológico puro", "XZn_FPM"), ("Híbrido com a MLP v1", "XZn_Hibrido_MLP"), ("Híbrido com a MLP v2 (comitê)", "XZn_Hibrido_MLP_v2")]
    tr, te = pred[~pred["ensaio"].isin(TESTE)], pred[pred["ensaio"].isin(TESTE)]
    x = np.linspace(-0.03, 1.05, 50)
    for ax, (nome, col) in zip(axes, modelos):
        ax.plot(x, x, "k-", lw=1.2)
        ax.fill_between(x, x - 0.05, x + 0.05, color="k", alpha=0.07, lw=0)
        ax.scatter(tr["XZn_exp"], tr[col], s=22, color=COR["v2"], alpha=0.8, label="Treino (91 pontos)")
        ax.scatter(te["XZn_exp"], te[col], s=34, marker="s", color=COR["teste"], edgecolor="white", label="Teste cego (21 pontos)")
        ax.set_title(nome, fontsize=11)
        ax.text(0.04, 0.92, f"RMSE treino = {rmse(tr['XZn_exp'], tr[col]):.4f}\nRMSE teste cego = {rmse(te['XZn_exp'], te[col]):.4f}",
                transform=ax.transAxes, va="top", fontsize=9, bbox=dict(boxstyle="round", fc="white", ec="0.7"))
        ax.set_xlabel("Conversão medida (–)")
        ax.grid(ls="--", alpha=0.4)
        ax.set_xlim(-0.03, 1.05)
        ax.set_ylim(-0.03, 1.05)
    axes[0].set_ylabel("Conversão prevista (–)")
    axes[0].legend(loc="lower right", fontsize=8.5)
    fig.tight_layout()
    salvar(fig, "fig_rh_02_paridade")


def tabela_erro_por_ensaio(pred: pd.DataFrame, oof: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for e, g in pred.groupby("ensaio"):
        o = oof[oof["ensaio"] == e]
        linhas.append({
            "ensaio": e, "teste_cego": e in TESTE, "eta": g["razao_molar_eta"].iloc[0], "CA0_mol_L": g["CA0_mol_L"].iloc[0],
            "RMSE_fenomenologico": rmse(g["XZn_exp"], g["XZn_FPM"]), "RMSE_v1": rmse(g["XZn_exp"], g["XZn_Hibrido_MLP"]),
            "RMSE_v2": rmse(g["XZn_exp"], g["XZn_Hibrido_MLP_v2"]),
            "RMSE_v2_fora_da_dobra": rmse(o["XZn_exp"], o["XZn_pred"]) if len(o) else np.nan,
        })
    t = pd.DataFrame(linhas)
    t.to_csv(OUT / "tabela_erro_por_ensaio.csv", index=False)
    return t


def fig_erro_ensaio(t: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(12.5, 4.6))
    n = len(t)
    larg = 0.27
    xs = np.arange(n)
    ax.bar(xs - larg, t["RMSE_fenomenologico"], larg, color=COR["fpm"], label="Fenomenológico puro")
    ax.bar(xs, t["RMSE_v1"], larg, color=COR["v1"], label="Híbrido com a MLP v1")
    ax.bar(xs + larg, t["RMSE_v2"], larg, color=COR["v2"], label="Híbrido com a MLP v2 (treino: ajuste; teste cego: previsão)")
    cv = t["RMSE_v2_fora_da_dobra"]
    ax.scatter((xs + larg)[cv.notna()], cv[cv.notna()], marker="D", s=34, color=COR["cv"], edgecolor="k", zorder=5,
               label="MLP v2 fora da dobra (validação cruzada, 10 sementes)")
    for i, r in t.iterrows():
        if r["teste_cego"]:
            ax.axvspan(i - 0.5, i + 0.5, color=COR["teste"], alpha=0.08, lw=0)
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{int(r['ensaio'])}\n({r['eta']:.1f}; {r['CA0_mol_L']:.1f})" for _, r in t.iterrows()], fontsize=8.5)
    ax.set_xlabel("Ensaio (η; $C_{A0}$ em mol/L); faixas rosadas: teste cego")
    ax.set_ylabel("RMSE de $X_{Zn}$ (–)")
    ax.set_yscale("log")
    ax.grid(axis="y", ls="--", alpha=0.4)
    ax.set_ylim(4e-3, 1.2)
    ax.legend(fontsize=8.5, ncol=2, loc="upper center", frameon=True)
    fig.tight_layout()
    salvar(fig, "fig_rh_03_erro_por_ensaio")


# ------------------------------------------------------------------------------------------ mapa e consistência
def mapa(v2: SerialHybridModel, n: int = 41) -> tuple:
    ca0s = np.linspace(0.1, 1.5, n)
    etas = np.linspace(0.5, 3.1, n)
    t = np.arange(0.0, 15.0 + 1e-9, 0.25)
    i05, i15 = int(np.argmin(np.abs(t - 0.5))), int(np.argmin(np.abs(t - 15.0)))
    x05 = np.zeros((n, n))
    x15 = np.zeros((n, n))
    viol = {"x_acima_do_limite": 0.0, "x_decrescente": 0.0, "caf_min": np.inf, "nu_min": np.inf, "nu_nao_positivo": 0, "n_condicoes": 0}
    for i, e in enumerate(etas):
        for j, c in enumerate(ca0s):
            r = v2.simulate(ca0=float(c), eta=float(e), t_eval=t)
            x05[i, j], x15[i, j] = r["XZn"][i05], r["XZn"][i15]
            viol["x_acima_do_limite"] = max(viol["x_acima_do_limite"], float(np.max(r["XZn"] - min(1.0, e))))
            viol["x_decrescente"] = max(viol["x_decrescente"], float(np.max(-np.diff(r["XZn"]))))
            viol["caf_min"] = min(viol["caf_min"], float(np.min(r["CAf"])))
            nu = v2.predict_rate(ca0=float(c), eta=float(e), t_eval=t[1:])  # taxa da rede, antes do acoplamento
            viol["nu_min"] = min(viol["nu_min"], float(nu.min()))
            viol["nu_nao_positivo"] += int((nu <= 0).sum())
            viol["n_condicoes"] += 1
    return ca0s, etas, x05, x15, viol


def fig_mapa(ca0s, etas, x05, x15, meta: pd.DataFrame, serie: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), sharey=True)
    for ax, x, tm, tit in ((axes[0], x05, 0.5, "(a) 0,5 min"), (axes[1], x15, 15.0, "(b) 15 min")):
        cs = ax.contourf(ca0s, etas, x, levels=np.linspace(0, 1, 21), cmap="viridis", vmin=0, vmax=1)
        ax.contour(ca0s, etas, x, levels=[0.5, 0.75, 0.9, 0.95], colors="white", linewidths=0.8, linestyles="--")
        med = serie[serie["t_min"] == tm]
        ax.scatter(med["CA0_mol_L"], med["razao_molar_eta"], c=med["XZn"], cmap="viridis", vmin=0, vmax=1, s=95, edgecolor="white",
                   linewidth=1.6, zorder=5)
        for _, r in med.iterrows():
            ax.annotate(f"{r['XZn']:.2f}".replace(".", ","), (r["CA0_mol_L"], r["razao_molar_eta"]), textcoords="offset points", xytext=(7, 5),
                        fontsize=7.5, color="white")
        ax.set_title(f"{tit}: previsão (fundo) e medição (círculos)")
        ax.set_xlabel("$C_{A0}$ (mol/L)")
        ax.grid(ls=":", alpha=0.3)
    axes[0].set_ylabel("Razão molar η (–)")
    fig.colorbar(cs, ax=axes, label="Conversão de zinco, $X_{Zn}$ (–)", shrink=0.9)
    salvar(fig, "fig_rh_04_mapa_conversao")


def tendencias(v2: SerialHybridModel, serie: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """Previsão do comitê e medição nos pontos do planejamento (conversão em 0,5 e 15 min)."""
    linhas = []
    for _, m in meta.sort_values(["razao_molar_eta", "CA0_mol_L"]).iterrows():
        r = v2.simulate(ca0=float(m["CA0_mol_L"]), eta=float(m["razao_molar_eta"]), t_eval=[0.5, 1.0, 15.0])
        s = serie[serie["ensaio"] == m["ensaio"]].set_index("t_min")["XZn"]
        linhas.append({"ensaio": int(m["ensaio"]), "eta": m["razao_molar_eta"], "CA0_mol_L": m["CA0_mol_L"],
                       "X_medido_0_5": s.loc[0.5], "X_prev_0_5": r["XZn"][0], "X_medido_15": s.loc[15.0], "X_prev_15": r["XZn"][2]})
    t = pd.DataFrame(linhas)
    t.to_csv(OUT / "tabela_tendencias.csv", index=False)
    return t


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    conferir_modelo()
    estilo()
    meta, serie, pred, oof = carregar()
    v2 = SerialHybridModel(model_type="mlp_v2")
    solver = BatchPBMSolver()
    cur = curvas(v2, solver, meta)
    fig_curvas(cur, pred)
    fig_paridade(pred)
    t = tabela_erro_por_ensaio(pred, oof)
    fig_erro_ensaio(t)
    ca0s, etas, x05, x15, viol = mapa(v2)
    fig_mapa(ca0s, etas, x05, x15, meta, serie)
    pd.DataFrame([viol]).to_csv(OUT / "tabela_consistencia_fisica.csv", index=False)
    rows = [{"eta": e, "CA0_mol_L": c, "X_0_5min": x05[i, j], "X_15min": x15[i, j]} for i, e in enumerate(etas) for j, c in enumerate(ca0s)]
    pd.DataFrame(rows).to_csv(OUT / "tabela_mapa_conversao.csv", index=False)
    tendencias(v2, serie, meta)
    print(pd.DataFrame([viol]).T)


if __name__ == "__main__":
    main()
