"""Exemplos de formatação para o padrão de gráficos da seção de Resultados.

Os quatro estilos (A, B, C, D) desenham exatamente a mesma figura, com os dados reais do projeto
(ensaio 9 e os 112 pontos dos 16 ensaios, quatro modelos), para que a comparação seja só de formatação.
Tamanho: largura de coluna A4 (16 cm), 300 DPI.

Saídas em `exemplos/`: estilo_A.png, estilo_B.png, estilo_C.png, estilo_D.png e comparativo_estilos.png.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

CODIGO = Path(__file__).resolve().parents[2] / "Código"
sys.path.insert(0, str(CODIGO))
from src.hybrid.serial_hybrid import SerialHybridModel  # noqa: E402
from src.physics.granulometry import RosinRammlerBennet, RosinRammlerMassaAntiga  # noqa: E402
from src.physics.kinetics import LeachingKinetics  # noqa: E402
from src.physics.pbm_batch import BatchPBMSolver  # noqa: E402

AQUI = Path(__file__).resolve().parent
SAIDA = AQUI / "exemplos"
RAW = CODIGO.parent / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv"
PURO = CODIGO / "outputs" / "etapa_3_2" / "subetapa_3_2_7_mlp_puro_xzn"
ENSAIOS_TESTE = [7, 8, 14]
ENSAIO_EXEMPLO = 9
LARGURA_IN = 16 / 2.54  # 16 cm

NOMES = {"fab": "White-box (Fabrício)", "novo": "White-box (novo)", "puro": "MLP pura", "hib": "Híbrido serial"}
ORDEM = ["fab", "novo", "puro", "hib"]


# ----------------------------------------------------------------------------------------------
# Dados reais (modelos já congelados)
# ----------------------------------------------------------------------------------------------
def dados() -> dict:
    exp = pd.read_csv(RAW)
    pos = exp[exp["t_min"] > 0].sort_values(["ensaio", "t_min"])
    puro_pts = pd.read_csv(PURO / "predicoes_pontos_experimentais.csv")
    puro_dense = pd.read_csv(PURO / "curvas_densas_mlp_puro.csv")
    sol_novo = BatchPBMSolver(granulometry=RosinRammlerBennet(use_number_density_d3=True),
                              kinetics=LeachingKinetics(alpha_nominal=0.0), n_mesh_points=5000)
    sol_fab = BatchPBMSolver(granulometry=RosinRammlerMassaAntiga(),
                             kinetics=LeachingKinetics(alpha_nominal=5500.0), n_mesh_points=5000)
    hib = SerialHybridModel(model_type="mlp_v2")

    linhas = []
    for e in sorted(pos["ensaio"].unique()):
        d = pos[pos["ensaio"] == e]
        ca0, eta, t, x = float(d["CA0_mol_L"].iloc[0]), float(d["razao_molar_eta"].iloc[0]), d["t_min"].values, d["XZn"].values
        preds = {
            "fab": np.asarray(sol_fab.simulate(ca0=ca0, eta=eta, t_eval=t)["XZn"]),
            "novo": np.asarray(sol_novo.simulate(ca0=ca0, eta=eta, t_eval=t)["XZn"]),
            "puro": puro_pts[puro_pts["ensaio"] == e].sort_values("t_min")["XZn_pred"].values,
            "hib": np.asarray(hib.simulate(T=40.0, ca0=ca0, eta=eta, t_eval=t)["XZn"]),
        }
        for k, p in preds.items():
            for ti, xi, pi in zip(t, x, p):
                linhas.append({"ensaio": e, "modelo": k, "t": ti, "x": xi, "p": pi,
                               "particao": "Teste cego" if e in ENSAIOS_TESTE else "Treino"})
    pts = pd.DataFrame(linhas)

    d9 = pos[pos["ensaio"] == ENSAIO_EXEMPLO]
    ca0, eta = float(d9["CA0_mol_L"].iloc[0]), float(d9["razao_molar_eta"].iloc[0])
    tf = np.linspace(0.0, 15.0, 301)
    curvas = {
        "fab": np.asarray(sol_fab.simulate(ca0=ca0, eta=eta, t_eval=tf)["XZn"]),
        "novo": np.asarray(sol_novo.simulate(ca0=ca0, eta=eta, t_eval=tf)["XZn"]),
        "hib": np.asarray(hib.simulate(T=40.0, ca0=ca0, eta=eta, t_eval=tf)["XZn"]),
    }
    pd9 = puro_dense[puro_dense["ensaio"] == ENSAIO_EXEMPLO]
    puro_curva = (pd9["t_min"].values, pd9["XZn_pred"].values)

    rmse = {}
    for nome, filtro in (("Treino", pts["particao"] == "Treino"), ("Teste cego", pts["particao"] == "Teste cego"),
                         ("Global", pts["particao"].notna())):
        rmse[nome] = {k: float(np.sqrt(np.mean((pts[filtro & (pts["modelo"] == k)]["x"] - pts[filtro & (pts["modelo"] == k)]["p"]) ** 2)))
                      for k in ORDEM}
    return {"pts": pts, "tf": tf, "curvas": curvas, "puro": puro_curva, "t9": d9["t_min"].values, "x9": d9["XZn"].values,
            "ca0": ca0, "eta": eta, "rmse": rmse}


# ----------------------------------------------------------------------------------------------
# Definição dos estilos
# ----------------------------------------------------------------------------------------------
OKABE = {"fab": "#E69F00", "novo": "#0072B2", "puro": "#009E73", "hib": "#CC79A7"}

ESTILOS = {
    "A": {
        "titulo": "A — Clássico, preto e branco (impressão)",
        "rc": {"font.family": "Times New Roman", "font.size": 10, "axes.grid": False, "axes.spines.top": True,
               "axes.spines.right": True, "axes.linewidth": 0.8},
        "modelos": {  # cor, linestyle, marcador, hachura, espessura
            "fab": ("#7F7F7F", "--", "s", "///", 1.4), "novo": ("#4D4D4D", ":", "^", "...", 1.6),
            "puro": ("#A6A6A6", "-.", "D", "xxx", 1.4), "hib": ("#000000", "-", "o", "", 2.0)},
        "exp": ("#000000", "o", "white"), "legenda": "dentro", "rotulo_painel": "(a)", "grade": False,
        "ref": "#000000",
    },
    "B": {
        "titulo": "B — Moderno colorido (como os gráficos que fizemos)",
        "rc": {"font.family": "Arial", "font.size": 9, "axes.grid": True, "grid.alpha": 0.35, "grid.linestyle": "--",
               "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.8},
        "modelos": {"fab": (OKABE["fab"], "--", "s", "", 1.7), "novo": (OKABE["novo"], "-", "^", "", 1.7),
                    "puro": (OKABE["puro"], "-.", "D", "", 1.7), "hib": (OKABE["hib"], "-", "o", "", 2.4)},
        "exp": ("#222222", "o", "white"), "legenda": "topo", "rotulo_painel": "(a)", "grade": True, "ref": "gray",
    },
    "C": {
        "titulo": "C — Serifado, colorido com redundância (sobrevive ao P&B)",
        "rc": {"font.family": "Times New Roman", "font.size": 10, "axes.grid": True, "grid.alpha": 0.25, "grid.linestyle": ":",
               "axes.spines.top": True, "axes.spines.right": True, "axes.linewidth": 0.8},
        "modelos": {"fab": (OKABE["fab"], "--", "s", "///", 1.6), "novo": (OKABE["novo"], ":", "^", "...", 1.9),
                    "puro": (OKABE["puro"], "-.", "D", "xxx", 1.6), "hib": (OKABE["hib"], "-", "o", "", 2.2)},
        "exp": ("#000000", "o", "white"), "legenda": "topo", "rotulo_painel": "(a)", "grade": True, "ref": "#555555",
    },
    "D": {
        "titulo": "D — Minimalista, rótulos diretos nas curvas",
        "rc": {"font.family": "Arial", "font.size": 9.5, "axes.grid": False, "axes.spines.top": False,
               "axes.spines.right": False, "axes.linewidth": 1.0},
        "modelos": {"fab": (OKABE["fab"], "-", "s", "", 2.2), "novo": (OKABE["novo"], "-", "^", "", 2.2),
                    "puro": (OKABE["puro"], "-", "D", "", 2.2), "hib": (OKABE["hib"], "-", "o", "", 3.0)},
        "exp": ("#222222", "o", "white"), "legenda": "direta", "rotulo_painel": "a", "grade": False, "ref": "#999999",
    },
}


def desenhar(chave: str, D: dict, caminho: Path) -> None:
    est = ESTILOS[chave]
    with plt.rc_context(est["rc"] | {"savefig.dpi": 300, "savefig.bbox": "tight", "mathtext.fontset": "stix"}):
        fig = plt.figure(figsize=(LARGURA_IN, 5.9))
        gs = GridSpec(2, 2, figure=fig, height_ratios=[1.15, 1], hspace=0.48, wspace=0.32,
                      left=0.10, right=0.98, top=0.90 if est["legenda"] == "topo" else 0.96, bottom=0.09)
        a, b, c = fig.add_subplot(gs[0, :]), fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])
        M = est["modelos"]
        cor_e, mk_e, mec_e = est["exp"]
        lab = (lambda s: f"({s})") if est["rotulo_painel"].startswith("(") else (lambda s: s)

        # (a) cinética
        a.axhline(min(1.0, D["eta"]), color=est["ref"], lw=0.8, ls=":", zorder=1)
        for k in ("fab", "novo", "hib"):
            cor, ls, mk, hat, lw = M[k]
            a.plot(D["tf"], D["curvas"][k], color=cor, ls=ls, lw=lw, zorder=3)
        cor, ls, mk, hat, lw = M["puro"]
        a.plot(*D["puro"], color=cor, ls=ls, lw=lw, zorder=3)
        a.plot(D["t9"], D["x9"], mk_e, color=cor_e, ms=5.5, mec=mec_e, mew=0.6, zorder=6)
        a.set_xlim(-0.3, 15.5); a.set_ylim(-0.02, 1.12)
        a.set_xlabel("Tempo de reação, t (min)"); a.set_ylabel("Conversão de zinco, $X_{Zn}$ (–)")
        a.text(0.012, 0.95, lab("a"), transform=a.transAxes, fontweight="bold", va="top")
        a.text(0.985, 0.06, f"Ensaio {ENSAIO_EXEMPLO}: $C_{{A0}}$ = {D['ca0']:.2f} mol/L, η = {D['eta']:g}", transform=a.transAxes,
               ha="right", va="bottom", fontsize=est["rc"]["font.size"] - 0.5)
        if est["legenda"] == "direta":
            pos_rot = {"novo": (5.0, 1.045), "hib": (9.5, 0.915), "puro": (9.5, 0.795), "fab": (9.5, 0.705)}
            for k, (tx, ty) in pos_rot.items():
                a.text(tx, ty, NOMES[k], color=M[k][0], fontsize=8.8, fontweight="bold", va="center")
            a.text(1.4, 0.60, "● Experimental", color=cor_e, fontsize=8.8, va="center")

        # (b) paridade
        b.plot([0.3, 1.05], [0.3, 1.05], color=est["ref"], lw=0.8, ls=":", zorder=1)
        for k in ORDEM:
            s = D["pts"][D["pts"]["modelo"] == k]
            cor, ls, mk, hat, lw = M[k]
            fill = "none" if chave in ("A",) and k in ("fab", "puro") else cor
            b.scatter(s["x"], s["p"], s=11 if k != "hib" else 14, marker=mk, facecolors=fill, edgecolors=cor, linewidths=0.6,
                      alpha=0.85, zorder=3 if k != "hib" else 4)
        b.set_xlim(0.3, 1.05); b.set_ylim(0.3, 1.05); b.set_aspect("equal")
        b.set_xlabel("$X_{Zn}$ experimental (–)"); b.set_ylabel("$X_{Zn}$ do modelo (–)")
        b.text(0.04, 0.95, lab("b"), transform=b.transAxes, fontweight="bold", va="top")

        # (c) barras de RMSE
        grupos = ["Treino", "Teste cego", "Global"]
        w = 0.2; xs = np.arange(3)
        for i, k in enumerate(ORDEM):
            cor, ls, mk, hat, lw = M[k]
            vals = [D["rmse"][g][k] * 100 for g in grupos]
            if chave == "A":
                c.bar(xs + (i - 1.5) * w, vals, w, facecolor="white" if k in ("fab", "puro") else cor, edgecolor="black",
                      hatch=hat, linewidth=0.6)
            elif chave == "C":
                c.bar(xs + (i - 1.5) * w, vals, w, facecolor=cor, edgecolor="black", hatch=hat, linewidth=0.5, alpha=0.9)
            else:
                c.bar(xs + (i - 1.5) * w, vals, w, facecolor=cor, linewidth=0)
        c.set_xticks(xs); c.set_xticklabels(grupos)
        c.set_ylabel("RMSE de $X_{Zn}$ (p.p.)")
        c.text(0.04, 0.95, lab("c"), transform=c.transAxes, fontweight="bold", va="top")
        c.set_ylim(0, 17 if est["legenda"] == "direta" else 14)
        if est["grade"]:
            c.grid(axis="x", visible=False)

        # legenda
        proxies = []
        for k in ORDEM:
            cor, ls, mk, hat, lw = M[k]
            proxies.append(Line2D([], [], color=cor, ls=ls, lw=lw, marker=mk, ms=4.5, markevery=1, label=NOMES[k]))
        proxies.append(Line2D([], [], color=cor_e, ls="none", marker=mk_e, ms=5, mec=mec_e, label="Experimental"))
        if est["legenda"] == "topo":
            fig.legend(handles=proxies, loc="upper center", ncol=5, frameon=False, fontsize=8.2, bbox_to_anchor=(0.54, 0.995),
                       handlelength=2.2, columnspacing=1.0)
        elif est["legenda"] == "dentro":
            a.legend(handles=proxies, loc="center right", frameon=True, edgecolor="black", fancybox=False, fontsize=8.5,
                     bbox_to_anchor=(0.99, 0.40))
        else:  # direta: legenda mínima só nas barras
            c.legend(handles=[Patch(facecolor=M[k][0], label=NOMES[k]) for k in ORDEM], frameon=False, fontsize=7.0,
                     loc="upper center", ncol=2, bbox_to_anchor=(0.55, 1.0), columnspacing=1.0, handlelength=1.2)
        fig.savefig(caminho, dpi=300)
        plt.close(fig)


def montagem(caminhos: dict) -> None:
    from PIL import Image
    imgs = {k: Image.open(p) for k, p in caminhos.items()}
    fig, axs = plt.subplots(2, 2, figsize=(14, 12.2))
    for ax, k in zip(axs.flatten(), imgs):
        ax.imshow(imgs[k]); ax.axis("off")
        ax.set_title(ESTILOS[k]["titulo"], fontsize=12, fontweight="bold", loc="left")
    fig.tight_layout()
    fig.savefig(SAIDA / "comparativo_estilos.png", dpi=150)
    plt.close(fig)


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    D = dados()
    caminhos = {}
    for k in ESTILOS:
        caminhos[k] = SAIDA / f"estilo_{k}.png"
        desenhar(k, D, caminhos[k])
        print("ok", k)
    montagem(caminhos)


if __name__ == "__main__":
    main()
