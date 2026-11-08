"""Figuras da Fase C (perdas físicas D1 e D2) da Subetapa 3.2.6 (300 DPI, PNG + PDF)."""

from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import fase_c_perdas_fisicas as fc
from figuras_fase_b import BLUE, GRAY, NAVY, ORANGE, RED, TEAL, TETO_RMSE, estilo
from protocolo_cv import carregar_dados

OUT = fc.OUT
COR = {"B2 (referência)": GRAY, "B2 reajustada (lr, épocas)": NAVY, "+ D1": BLUE, "+ D2": TEAL, "+ D1 + D2": ORANGE}


def salvar(fig, nome: str) -> None:
    fig.savefig(OUT / f"{nome}.png", dpi=300)
    fig.savefig(OUT / f"{nome}.pdf", dpi=300)
    plt.close(fig)


def fig_pesos(dados, gamma: float) -> None:
    bruto = fc.pesos_brutos(dados)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    df = dados.train_df.assign(bruto=bruto)
    for ax, g, tit in ((axes[0], 1.0, "γ = 1"), (axes[1], gamma, f"γ = {gamma:.2f} (escolhido)")):
        w = fc.pesos_sensibilidade(dados, g, bruto)
        d = df.assign(w=w)
        for e, sub in d.groupby("ensaio"):
            ax.plot(sub["t_min"], sub["w"], lw=1.1, alpha=0.8, label=f"Ensaio {e}")
        ax.set_yscale("log")
        ax.set_xscale("log")
        ax.set_xlabel("Tempo (min)")
        ax.set_title(f"Peso D1 por instante, {tit}")
        ax.grid(ls="--", alpha=0.5)
    axes[0].set_ylabel("Peso da perda em ν (média 1)")
    axes[1].legend(fontsize=7, ncol=2, loc="lower left")
    fig.tight_layout()
    salvar(fig, "fig_fc_01_pesos_d1")


def fig_ablacao(tab: pd.DataFrame, ps: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    for i, (_, r) in enumerate(tab.iterrows()):
        v = ps[ps["config"] == r["variante"]].sort_values("semente")["RMSE_X"].values
        ax.bar(i, r["RMSE_X_media"], yerr=r["RMSE_X_dp"], color=COR[r["variante"]], alpha=0.85, capsize=4)
        ax.scatter(np.full(len(v), i) + np.linspace(-0.18, 0.18, len(v)), v, s=14, color="k", zorder=5)
        if i > 0:
            ax.text(i, r["RMSE_X_media"] + r["RMSE_X_dp"] + 0.002, f"Δ = {r['ganho_medio_vs_B2']:+.4f}\n(EP {r['ep_ganho_pareado']:.4f})",
                    ha="center", fontsize=8)
    ax.axhline(TETO_RMSE, color=RED, ls=":", lw=1.2, label="Teto (X_Zn dos próprios alvos ν)")
    ax.set_xticks(range(len(tab)))
    ax.set_xticklabels([v.replace(" (", "\n(") for v in tab["variante"]], fontsize=8.5)
    ax.set_ylabel("RMSE de $X_{Zn}$ fora da dobra (–)")
    ax.set_ylim(0, max(0.05, (tab["RMSE_X_media"] + tab["RMSE_X_dp"]).max() * 1.35))
    ax.grid(axis="y", ls="--", alpha=0.5)
    ax.legend(loc="upper right", fontsize=8.5)
    ax.set_title("Ablação da Fase C (10 sementes; pontos = sementes)")
    fig.tight_layout()
    salvar(fig, "fig_fc_02_ablacao_rmse")


def fig_monotonia(mono: pd.DataFrame, ordem) -> None:
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    for i, nome in enumerate(ordem):
        v = mono[mono["config"] == nome]["frac_dnu_dt_positivo"].values * 100
        ax.bar(i, v.mean(), yerr=v.std(ddof=1), color=COR[nome], alpha=0.85, capsize=4)
    ax.set_xticks(range(len(ordem)))
    ax.set_xticklabels([v.replace(" (", "\n(") for v in ordem], fontsize=8.5)
    ax.set_ylabel("Pontos do domínio com ∂ν/∂t > 0 (%)")
    ax.grid(axis="y", ls="--", alpha=0.5)
    ax.set_title("Monotonia temporal da taxa (4.000 pontos sorteados; 40 redes por variante)")
    fig.tight_layout()
    salvar(fig, "fig_fc_03_monotonia")


def fig_curvas(curvas: pd.DataFrame, ordem) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    for nome in ordem:
        c = curvas[curvas["config"] == nome]
        for ax, col in zip(axes, ("nu", "XZn")):
            q = c.groupby("t_min")[col].quantile([0.1, 0.5, 0.9]).unstack()
            ax.plot(q.index, q[0.5], color=COR[nome], lw=1.8, label=nome)
            ax.fill_between(q.index, q[0.1], q[0.9], color=COR[nome], alpha=0.12)
    axes[0].set_yscale("log")
    axes[0].set_ylabel("Taxa ν (µm/min)")
    axes[1].set_ylabel("Conversão de zinco, $X_{Zn}$ (–)")
    for ax in axes:
        ax.set_xlabel("Tempo (min)")
        ax.grid(ls="--", alpha=0.5)
    axes[0].legend(fontsize=8)
    fig.suptitle("Condição sem ensaio: $C_{A0}$ = 0,75 mol/L, η = 2 (mediana e faixa de 10–90% de 40 redes)", fontsize=11)
    fig.tight_layout()
    salvar(fig, "fig_fc_04_curvas_sem_ensaio")


def fig_por_ensaio(oof: pd.DataFrame, ordem) -> None:
    ens = sorted(oof["ensaio"].unique())
    fig, ax = plt.subplots(figsize=(12, 4.2))
    larg = 0.8 / len(ordem)
    for j, nome in enumerate(ordem):
        o = oof[oof["config"] == nome]
        r = [np.sqrt(((g["XZn_exp"] - g["XZn_pred"]) ** 2).mean()) for _, g in o.groupby("ensaio")]
        ax.bar(np.arange(len(ens)) + j * larg - 0.4 + larg / 2, r, larg, color=COR[nome], label=nome)
    ax.set_xticks(range(len(ens)))
    ax.set_xticklabels(ens)
    ax.set_xlabel("Ensaio (fora da dobra; erro de todas as sementes juntas)")
    ax.set_ylabel("RMSE de $X_{Zn}$ (–)")
    ax.grid(axis="y", ls="--", alpha=0.5)
    ax.legend(fontsize=8, ncol=3)
    fig.tight_layout()
    salvar(fig, "fig_fc_05_rmse_por_ensaio")


def fig_busca(tent: pd.DataFrame) -> None:
    comp = tent[tent["state"] == "COMPLETE"]
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for usa, cor, rot in ((False, BLUE, "Sem D2"), (True, ORANGE, "Com D2")):
        d = comp[comp["params_usar_mono"] == usa]
        ax.scatter(d["params_gamma"], d["value"], s=24, color=cor, alpha=0.8, label=rot)
    ax.set_xlabel("γ (expoente do peso D1)")
    ax.set_ylabel("RMSE de $X_{Zn}$ fora da dobra, 3 sementes (–)")
    ax.grid(ls="--", alpha=0.5)
    ax.legend()
    ax.set_title("Busca da Fase C (tentativas concluídas)")
    fig.tight_layout()
    salvar(fig, "fig_fc_06_busca")


def gerar_tudo() -> None:
    estilo()
    dados = carregar_dados()
    resumo = json.loads((OUT / "melhor_config_fase_c.json").read_text(encoding="utf-8"))
    tab = pd.read_csv(OUT / "tabela_fase_c_ablacao.csv")
    ps = pd.read_csv(OUT / "ablacao_por_semente.csv")
    ordem = list(tab["variante"])
    fig_pesos(dados, float(resumo["params"]["gamma"]))
    fig_ablacao(tab, ps)
    fig_monotonia(pd.read_csv(OUT / "ablacao_mono.csv"), ordem)
    fig_curvas(pd.read_csv(OUT / "ablacao_curvas.csv"), [ordem[0], ordem[-1]])
    fig_por_ensaio(pd.read_csv(OUT / "ablacao_oof.csv"), ordem)
    fig_busca(fc.exportar_tentativas())
    print("Figuras da Fase C salvas em", OUT)
