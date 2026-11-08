"""Figuras da Fase D (ajuste fino ponta a ponta) da Subetapa 3.2.6 (300 DPI, PNG + PDF)."""

from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import fase_d_ponta_a_ponta as fd
from figuras_fase_b import BLUE, GRAY, NAVY, ORANGE, RED, TETO_RMSE, estilo
from protocolo_cv import TARGET, carregar_dados

OUT = fd.OUT


def salvar(fig, nome: str) -> None:
    fig.savefig(OUT / f"{nome}.png", dpi=300)
    fig.savefig(OUT / f"{nome}.pdf", dpi=300)
    plt.close(fig)


def _rmse_ens(o: pd.DataFrame) -> pd.Series:
    return o.groupby("ensaio").apply(lambda g: np.sqrt(((g["XZn_exp"] - g["XZn_pred"]) ** 2).mean()), include_groups=False)


def fig_XZn(dados, c_oof: pd.DataFrame, d_oof: pd.DataFrame, rotulo_c: str) -> None:
    fig, axes = plt.subplots(4, 4, figsize=(15, 11), sharex=True, sharey=True)
    for ax, e in zip(axes.ravel(), range(1, 17)):
        m = dados.meta[dados.meta["ensaio"] == e].iloc[0]
        for o, cor, rot in ((c_oof, ORANGE, rotulo_c), (d_oof, BLUE, "Fase D")):
            g = o[o["ensaio"] == e].groupby("t_min")["XZn_pred"].agg(["mean", "min", "max"])
            ax.plot(g.index, g["mean"], "-o", ms=3, color=cor, lw=1.4, label=rot)
            ax.fill_between(g.index, g["min"], g["max"], color=cor, alpha=0.12)
        x = d_oof[d_oof["ensaio"] == e].groupby("t_min")["XZn_exp"].first()
        ax.scatter(x.index, x.values, s=22, color=NAVY, zorder=5, label="Experimental")
        ax.set_title(f"Ensaio {e}: $C_{{A0}}$={m['CA0_mol_L']:.1f}, η={m['razao_molar_eta']:.1f}", fontsize=9)
        ax.grid(ls="--", alpha=0.5)
    axes[0, 0].legend(fontsize=7.5, loc="lower right")
    for ax in axes[-1]:
        ax.set_xlabel("Tempo (min)")
    for ax in axes[:, 0]:
        ax.set_ylabel("$X_{Zn}$ (–)")
    fig.suptitle("Predição fora da dobra: média e faixa de 10 sementes (Fase C × Fase D)", fontsize=12)
    fig.tight_layout()
    salvar(fig, "fig_fd_01_XZn_por_ensaio")


def fig_nu(dados, nu: pd.DataFrame, ensaios=(3, 6, 12, 15)) -> None:
    alvo = pd.concat([dados.train_df, dados.test_df])
    fig, axes = plt.subplots(1, len(ensaios), figsize=(15, 4.2), sharey=True)
    for ax, e in zip(axes, ensaios):
        fold = next(f["fold"] for f in dados.folds if e in f["val_ensaios"])
        sub = nu[(nu["ensaio"] == e) & (nu["fold"] == fold)]
        for q, cor, rot in (("antes", ORANGE, "Antes (Fase C)"), ("depois", BLUE, "Depois (Fase D)")):
            g = sub[sub["quando"] == q].groupby("t_min")["nu"].quantile([0.1, 0.5, 0.9]).unstack()
            ax.plot(g.index, np.maximum(g[0.5], 1e-3), color=cor, lw=1.8, label=rot)
            ax.fill_between(g.index, np.maximum(g[0.1], 1e-3), np.maximum(g[0.9], 1e-3), color=cor, alpha=0.15)
        a = alvo[alvo["ensaio"] == e].sort_values("t_min")
        ax.scatter(a["t_min"], np.maximum(a[TARGET], 1e-3), s=10, color=NAVY, zorder=5, label="Alvo ν (problema inverso)")
        ax.set_yscale("log")
        ax.set_title(f"Ensaio {e} (fora da dobra {fold})", fontsize=10)
        ax.set_xlabel("Tempo (min)")
        ax.grid(ls="--", alpha=0.5)
    axes[0].set_ylabel("Taxa ν (µm/min)")
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    salvar(fig, "fig_fd_02_nu_antes_depois")


def fig_barras(abl: pd.DataFrame, d_ps: pd.DataFrame, rotulo_c: str, nome_c: str) -> None:
    series = [("B2", abl[abl["config"] == "B2 (referência)"], GRAY), (rotulo_c, abl[abl["config"] == nome_c], ORANGE),
              ("Fase D", d_ps, BLUE)]
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    for i, (nome, df, cor) in enumerate(series):
        v = df.sort_values("semente")["RMSE_X"].values
        ax.bar(i, v.mean(), yerr=v.std(ddof=1), color=cor, alpha=0.85, capsize=4)
        ax.scatter(np.full(len(v), i) + np.linspace(-0.18, 0.18, len(v)), v, s=14, color="k", zorder=5)
        ax.text(i, v.mean() + v.std(ddof=1) + 0.002, f"{v.mean():.4f}", ha="center", fontsize=9)
    ax.axhline(TETO_RMSE, color=RED, ls=":", lw=1.2, label="Teto")
    ax.set_xticks(range(3))
    ax.set_xticklabels([s[0] for s in series], fontsize=9)
    ax.set_ylabel("RMSE de $X_{Zn}$ fora da dobra (–)")
    ax.set_ylim(0, 0.06)
    ax.grid(axis="y", ls="--", alpha=0.5)
    ax.legend(fontsize=8.5)
    fig.tight_layout()
    salvar(fig, "fig_fd_03_rmse_barras")


def fig_por_ensaio(abl: pd.DataFrame, c_oof: pd.DataFrame, d_oof: pd.DataFrame, rotulo_c: str) -> None:
    b2 = _rmse_ens(abl[abl["config"] == "B2 (referência)"])
    c = _rmse_ens(c_oof)
    d = _rmse_ens(d_oof)
    ens = list(d.index)
    fig, ax = plt.subplots(figsize=(12, 4.2))
    for j, (s, cor, rot) in enumerate(((b2, GRAY, "B2"), (c, ORANGE, rotulo_c), (d, BLUE, "Fase D"))):
        ax.bar(np.arange(len(ens)) + (j - 1) * 0.27, s.reindex(ens).values, 0.27, color=cor, label=rot)
    ax.set_xticks(range(len(ens)))
    ax.set_xticklabels(ens)
    ax.set_xlabel("Ensaio (fora da dobra; 10 sementes juntas)")
    ax.set_ylabel("RMSE de $X_{Zn}$ (–)")
    ax.grid(axis="y", ls="--", alpha=0.5)
    ax.legend(fontsize=8.5)
    fig.tight_layout()
    salvar(fig, "fig_fd_04_rmse_por_ensaio")


def fig_busca(tent: pd.DataFrame) -> None:
    comp = tent[tent["state"] == "COMPLETE"]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, col, rot in zip(axes, ("params_lr_ft", "params_epocas_ft", "params_lambda_nu"),
                            ("Taxa de aprendizado do ajuste fino", "Épocas do ajuste fino", "λ_ν (âncora em ν)")):
        ax.scatter(comp[col], comp["value"], s=22, color=BLUE, alpha=0.8)
        ax.set_xscale("log")
        ax.set_xlabel(rot)
        ax.grid(ls="--", alpha=0.5)
    axes[0].set_ylabel("RMSE de $X_{Zn}$, 3 sementes (–)")
    fig.tight_layout()
    salvar(fig, "fig_fd_05_busca")


def gerar_tudo() -> None:
    estilo()
    dados = carregar_dados()
    base = fd.base_da_fase_c()
    rotulo_c = f"Fase C ({base['variante']})"
    abl = pd.read_csv(fd.FASE_C / "ablacao_por_semente.csv")
    abl_oof = pd.read_csv(fd.FASE_C / "ablacao_oof.csv")
    c_oof = abl_oof[abl_oof["config"] == base["variante"]]
    d_oof = pd.read_csv(OUT / "finais_oof.csv")
    d_ps = pd.read_csv(OUT / "finais_por_semente.csv")
    fig_XZn(dados, c_oof, d_oof, rotulo_c)
    fig_nu(dados, pd.read_csv(OUT / "finais_nu.csv"))
    fig_barras(abl, d_ps, rotulo_c, base["variante"])
    fig_por_ensaio(abl_oof, c_oof, d_oof, rotulo_c)
    tent = pd.read_csv(OUT / "tabela_fase_d_tentativas.csv")
    fig_busca(tent)
    print("Figuras da Fase D salvas em", OUT)
