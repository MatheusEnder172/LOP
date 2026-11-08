"""Subetapa 4.3 — Previsão a priori dos 4 ensaios novos de laboratório com a MLP v2 (comitê de 10 redes).

Ensaios (T = 40 °C e 1000 rpm, como os 16 originais; só o volume mudou, de 400 para 200 mL):

    E1: η = 0,75; C_A0 = 0,25 mol/L; V = 200 mL; m = 6,7 g
    E2: η = 1,25; C_A0 = 0,75 mol/L; V = 200 mL; m = 12,1 g
    E3: η = 2,25; C_A0 = 0,75 mol/L; V = 200 mL; m = 6,7 g
    E4: η = 0,40; C_A0 = 0,25 mol/L; V = 200 mL; m = 12,6 g   (η abaixo do mínimo do treino, 0,5)

O modelo só usa C_A0, η e t. As previsões são gravadas ANTES de qualquer medição, com a data, o
SHA-256 dos arquivos do comitê (conferido contra `models_saved/mlp_v2/SHA256SUMS.txt`) e o SHA-256 dos
arquivos de previsão (`INTEGRIDADE_previsao_a_priori.json`). A comparação com medições usa só esses
arquivos gravados, nunca refaz a previsão.

Uso:
    python prever_novos_ensaios.py prever                      # gera as previsões a priori (uma vez)
    python prever_novos_ensaios.py comparar --medicoes medicoes.csv   # sobrepõe medições e calcula o RMSE
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator

CODIGO_DIR = Path(__file__).resolve().parents[2]
BASE_DIR = CODIGO_DIR.parent
SUBETAPA_3_2_6 = CODIGO_DIR / "etapas" / "etapa_3_2" / "subetapa_3_2_6_mlp_otimizacao"
for p in (CODIGO_DIR, SUBETAPA_3_2_6):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.hybrid.serial_hybrid import SerialHybridModel  # noqa: E402
from src.physics.pbm_batch import BatchPBMSolver  # noqa: E402

OUT = Path(os.environ.get("NOVOS_ENSAIOS_OUT", CODIGO_DIR / "outputs" / "etapa_4_3_previsao_novos_ensaios"))
MODELOS_V2 = CODIGO_DIR / "outputs" / "models_saved" / "mlp_v2"
T_AMOSTRAS = np.array([0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 15.0])
T_DENSO = np.round(np.arange(0.0, 15.0 + 1e-9, 0.1), 6)
ETA_MIN_TREINO = 0.5
ENSAIOS_NOVOS: Dict[str, Dict[str, float]] = {
    "E1": {"eta": 0.75, "CA0": 0.25, "V_mL": 200.0, "m_g": 6.7},
    "E2": {"eta": 1.25, "CA0": 0.75, "V_mL": 200.0, "m_g": 12.1},
    "E3": {"eta": 2.25, "CA0": 0.75, "V_mL": 200.0, "m_g": 6.7},
    "E4": {"eta": 0.40, "CA0": 0.25, "V_mL": 200.0, "m_g": 12.6},
}
COR = {"v2": "#2E6DA4", "fpm": "#8C8C8C", "emp": "#2A9D8F", "med": "#B23A48", "v1": "#D9822B", "navy": "#1F3A5F"}


def estilo() -> None:
    plt.rcParams.update({
        "font.family": "Arial", "font.size": 10, "axes.labelsize": 11, "axes.titlesize": 12,
        "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 9, "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })


def sha256(arq: Path) -> str:
    h = hashlib.sha256()
    h.update(arq.read_bytes())
    return h.hexdigest()


def conferir_modelo() -> Dict[str, str]:
    """Confere os hashes dos arquivos do comitê contra SHA256SUMS.txt; aborta se algum mudou."""
    esperado = {}
    for linha in (MODELOS_V2 / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if linha.strip():
            h, nome = linha.split(None, 1)
            esperado[nome.strip().lstrip("*")] = h
    atual = {}
    for nome, h in esperado.items():
        atual[nome] = sha256(MODELOS_V2 / nome)
        if atual[nome] != h:
            raise SystemExit(f"Hash diferente para {nome}: o comitê v2 foi alterado. Previsão abortada.")
    return atual


def referencia_empirica() -> RegularGridInterpolator:
    """X_Zn medido nos 16 ensaios originais, interpolado linearmente em (C_A0, η) para cada instante amostrado."""
    meta = pd.read_csv(BASE_DIR / "Base de dados" / "raw" / "bancada_batelada_A1_1.csv")
    serie = pd.read_csv(BASE_DIR / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv")
    ca0s = sorted(meta["CA0_mol_L"].unique())
    etas = sorted(meta["razao_molar_eta"].unique())
    tt = [0.0] + list(T_AMOSTRAS)
    grade = np.zeros((len(ca0s), len(etas), len(tt)))
    for i, c in enumerate(ca0s):
        for j, e in enumerate(etas):
            ens = meta[(meta["CA0_mol_L"] == c) & (meta["razao_molar_eta"] == e)]["ensaio"].iloc[0]
            s = serie[serie["ensaio"] == ens].set_index("t_min")["XZn"]
            grade[i, j, :] = [s.loc[t] for t in tt]
    return RegularGridInterpolator((ca0s, etas, tt), grade, method="linear", bounds_error=False, fill_value=None)


def prever() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "INTEGRIDADE_previsao_a_priori.json").exists():
        raise SystemExit("A previsão a priori já foi gerada e gravada; não é refeita (mova a pasta para old/ com README).")
    hashes = conferir_modelo()
    v2 = SerialHybridModel(model_type="mlp_v2")
    v1 = SerialHybridModel(model_type="mlp")
    solver = BatchPBMSolver()
    emp = referencia_empirica()

    linhas, curvas = [], []
    for nome, p in ENSAIOS_NOVOS.items():
        eta, ca0 = p["eta"], p["CA0"]
        cap = min(1.0, eta)
        extrap = eta < ETA_MIN_TREINO
        carga = p["m_g"] / (p["V_mL"] / 1000.0)
        for rotulo, t in (("amostra", T_AMOSTRAS), ("denso", T_DENSO)):
            c = v2.simulate(ca0=ca0, eta=eta, t_eval=t)
            m = v2.simulate_members(ca0=ca0, eta=eta, t_eval=t)
            fpm = solver.simulate(ca0=ca0, eta=eta, t_eval=t, alpha=0.0)["XZn"]
            x1 = v1.simulate(ca0=ca0, eta=eta, t_eval=t)["XZn"]
            e = emp(np.column_stack([np.full(len(t), ca0), np.full(len(t), eta), t])) if rotulo == "amostra" else np.full(len(t), np.nan)
            df = pd.DataFrame({
                "ensaio": nome, "eta": eta, "CA0_mol_L": ca0, "V_mL": p["V_mL"], "m_g": p["m_g"],
                "razao_solido_liquido_g_L": carga, "extrapolacao_eta": extrap, "t_min": t,
                "XZn_v2_comite": c["XZn"], "XZn_v2_membro_min": m["XZn_min"], "XZn_v2_membro_max": m["XZn_max"],
                "XZn_v2_membro_dp": m["XZn_dp"], "XZn_fenomenologico": fpm, "XZn_v1": x1,
                "XZn_interp_empirica_16_ensaios": np.minimum(e, cap), "limite_min_1_eta": cap,
                "CAf_v2_mol_L": c["CAf"], "CAf_v2_membro_min": m["CAf_membros"].min(axis=0),
                "CAf_v2_membro_max": m["CAf_membros"].max(axis=0), "nu_v2_um_min": c["abs_v"],
            })
            (linhas if rotulo == "amostra" else curvas).append(df)
    tab = pd.concat(linhas, ignore_index=True)
    cur = pd.concat(curvas, ignore_index=True)
    tab.to_csv(OUT / "previsao_a_priori_instantes_amostrados.csv", index=False)
    cur.to_csv(OUT / "previsao_a_priori_curvas.csv", index=False)

    modelo = pd.DataFrame({"ensaio": list(ENSAIOS_NOVOS), **{k: [v[k] for v in ENSAIOS_NOVOS.values()] for k in ("eta", "CA0", "V_mL", "m_g")}})
    modelo["razao_solido_liquido_g_L"] = modelo["m_g"] / (modelo["V_mL"] / 1000.0)
    modelo["extrapolacao_eta"] = modelo["eta"] < ETA_MIN_TREINO
    pd.DataFrame([{"ensaio": n, "t_min": t, "XZn_medido": ""} for n in ENSAIOS_NOVOS for t in T_AMOSTRAS]).to_csv(
        OUT / "medicoes_template.csv", index=False)
    with pd.ExcelWriter(OUT / "previsao_a_priori_novos_ensaios.xlsx") as xw:
        modelo.to_excel(xw, sheet_name="ensaios", index=False)
        tab.to_excel(xw, sheet_name="previsao_instantes", index=False)
        cur.to_excel(xw, sheet_name="curvas_0_15min", index=False)
        pd.read_csv(OUT / "medicoes_template.csv").to_excel(xw, sheet_name="medicoes_template", index=False)

    figuras(tab, cur)

    integ = {
        "data_geracao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "descricao": "Previsão a priori (antes de qualquer medição) dos 4 ensaios novos com a MLP v2 (comitê de 10 redes).",
        "modelo": "MLP v2 (Subetapa 3.2.6, Fase E mínima), pesos conferidos contra SHA256SUMS.txt",
        "sha256_modelo": hashes,
        "sha256_previsoes": {n: sha256(OUT / n) for n in (
            "previsao_a_priori_instantes_amostrados.csv", "previsao_a_priori_curvas.csv", "medicoes_template.csv")},
    }
    (OUT / "INTEGRIDADE_previsao_a_priori.json").write_text(json.dumps(integ, indent=2, ensure_ascii=False), encoding="utf-8")
    print(tab[["ensaio", "t_min", "XZn_v2_comite", "XZn_v2_membro_min", "XZn_v2_membro_max", "XZn_fenomenologico",
               "XZn_interp_empirica_16_ensaios", "limite_min_1_eta"]].round(3).to_string(index=False))


# ----------------------------------------------------------------------------------------------
# Figuras
# ----------------------------------------------------------------------------------------------
def salvar(fig, nome: str) -> None:
    fig.savefig(OUT / f"{nome}.png", dpi=300)
    fig.savefig(OUT / f"{nome}.pdf", dpi=300)
    plt.close(fig)


def _painel(ax, nome: str, tab: pd.DataFrame, cur: pd.DataFrame, med: pd.DataFrame | None = None) -> None:
    p = ENSAIOS_NOVOS[nome]
    c = cur[cur["ensaio"] == nome]
    a = tab[tab["ensaio"] == nome]
    ax.fill_between(c["t_min"], c["XZn_v2_membro_min"], c["XZn_v2_membro_max"], color=COR["v2"], alpha=0.2,
                    label="Faixa dos 10 membros (mín.–máx.)")
    ax.plot(c["t_min"], c["XZn_v2_comite"], color=COR["v2"], lw=2.2, label="MLP v2 (comitê)")
    ax.scatter(a["t_min"], a["XZn_v2_comite"], s=36, color=COR["v2"], edgecolor="white", zorder=5,
               label="Previsão nos instantes de amostragem")
    ax.plot(c["t_min"], c["XZn_fenomenologico"], color=COR["fpm"], lw=1.6, ls="--", label="Fenomenológico puro")
    ax.plot(a["t_min"], a["XZn_interp_empirica_16_ensaios"], color=COR["emp"], lw=1.0, ls=":", marker="D", ms=4,
            label="Interpolação dos 16 ensaios medidos")
    ax.axhline(min(1.0, p["eta"]), color="k", ls=":", lw=1.2, label="Limite estequiométrico min(1, η)")
    if med is not None and not med.empty:
        m = med[med["ensaio"] == nome]
        ax.scatter(m["t_min"], m["XZn_medido"], s=48, marker="o", color=COR["med"], edgecolor="white", zorder=6,
                   label="Medido")
    extrap = p["eta"] < ETA_MIN_TREINO
    ax.set_title(f"{nome}: η = {p['eta']:.2f}, $C_{{A0}}$ = {p['CA0']:.2f} mol/L" + ("  (extrapolação)" if extrap else ""),
                 fontsize=11, color=COR["med"] if extrap else "black")
    ax.set_xlabel("Tempo (min)")
    ax.set_ylabel("Conversão de zinco, $X_{Zn}$ (–)")
    ax.set_xlim(0, 15.3)
    ax.set_ylim(-0.02, 1.08)
    ax.grid(ls="--", alpha=0.5)
    if extrap:
        ax.text(0.97, 0.06, f"η = {p['eta']:.2f} < {ETA_MIN_TREINO} (mínimo do treino)", transform=ax.transAxes, ha="right",
                fontsize=8.5, color=COR["med"], bbox=dict(boxstyle="round", fc="white", ec=COR["med"], alpha=0.9))


def figuras(tab: pd.DataFrame, cur: pd.DataFrame, med: pd.DataFrame | None = None, sufixo: str = "") -> None:
    estilo()
    for i, nome in enumerate(ENSAIOS_NOVOS, start=1):
        fig, ax = plt.subplots(figsize=(7.2, 4.8))
        _painel(ax, nome, tab, cur, med)
        ax.legend(loc="lower right", fontsize=8)
        fig.tight_layout()
        salvar(fig, f"fig_ne_{i:02d}_{nome}{sufixo}")
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), sharex=True, sharey=True)
    for ax, nome in zip(axes.ravel(), ENSAIOS_NOVOS):
        _painel(ax, nome, tab, cur, med)
    for ax in axes[0]:
        ax.set_xlabel("")
    for ax in axes[:, 1]:
        ax.set_ylabel("")
    axes[0, 0].legend(loc="lower right", fontsize=7.5)
    fig.suptitle("Previsão a priori dos 4 ensaios novos (T = 40 °C, 1000 rpm, V = 200 mL)", fontsize=12)
    fig.tight_layout()
    salvar(fig, f"fig_ne_05_painel{sufixo}")
    figura_contexto(tab, sufixo)


def figura_contexto(tab: pd.DataFrame, sufixo: str = "") -> None:
    """Previsão de cada ensaio novo ao lado dos 2 ensaios originais mais próximos em (C_A0, η), medidos."""
    meta = pd.read_csv(BASE_DIR / "Base de dados" / "raw" / "bancada_batelada_A1_1.csv")
    serie = pd.read_csv(BASE_DIR / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv")
    fig, axes = plt.subplots(1, 4, figsize=(17, 4.4), sharey=True)
    for ax, (nome, p) in zip(axes, ENSAIOS_NOVOS.items()):
        d = np.hypot(np.log(meta["CA0_mol_L"] / p["CA0"]) / np.log(15), np.log(meta["razao_molar_eta"] / p["eta"]) / np.log(6.2))
        viz = meta.assign(d=d).sort_values("d").head(2)
        for (_, r), mk, cor in zip(viz.iterrows(), ("s", "^"), (COR["navy"], COR["v1"])):
            s = serie[serie["ensaio"] == r["ensaio"]]
            ax.plot(s["t_min"], s["XZn"], marker=mk, ms=5, lw=1.0, color=cor,
                    label=f"Ensaio {int(r['ensaio'])} (η = {r['razao_molar_eta']:.1f}; $C_{{A0}}$ = {r['CA0_mol_L']:.1f})")
        a = tab[tab["ensaio"] == nome]
        ax.plot(a["t_min"], a["XZn_v2_comite"], "-o", color=COR["v2"], lw=2.2, ms=5, label=f"{nome} previsto (v2)")
        ax.axhline(min(1.0, p["eta"]), color="k", ls=":", lw=1.1)
        ax.set_title(f"{nome}: η = {p['eta']:.2f}, $C_{{A0}}$ = {p['CA0']:.2f}", fontsize=10.5)
        ax.set_xlabel("Tempo (min)")
        ax.grid(ls="--", alpha=0.5)
        ax.legend(fontsize=7.5, loc="lower right")
    axes[0].set_ylabel("Conversão de zinco, $X_{Zn}$ (–)")
    fig.tight_layout()
    salvar(fig, f"fig_ne_06_contexto_vizinhos{sufixo}")


# ----------------------------------------------------------------------------------------------
# Comparação com medições (usa só os arquivos gravados)
# ----------------------------------------------------------------------------------------------
def comparar(arq_medicoes: Path) -> None:
    integ = json.loads((OUT / "INTEGRIDADE_previsao_a_priori.json").read_text(encoding="utf-8"))
    for nome, h in integ["sha256_previsoes"].items():
        if sha256(OUT / nome) != h:
            raise SystemExit(f"{nome} foi alterado depois da gravação (hash diferente); comparação abortada.")
    tab = pd.read_csv(OUT / "previsao_a_priori_instantes_amostrados.csv")
    cur = pd.read_csv(OUT / "previsao_a_priori_curvas.csv")
    med = pd.read_csv(arq_medicoes)
    med = med.dropna(subset=["XZn_medido"]).copy()
    med["XZn_medido"] = med["XZn_medido"].astype(float)
    m = med.merge(tab, on=["ensaio", "t_min"], how="left")
    m["erro_v2"] = m["XZn_medido"] - m["XZn_v2_comite"]
    m["dentro_da_faixa_dos_membros"] = (m["XZn_medido"] >= m["XZn_v2_membro_min"]) & (m["XZn_medido"] <= m["XZn_v2_membro_max"])
    linhas = []
    for nome, g in list(m.groupby("ensaio")) + [("Todos", m)]:
        y = g["XZn_medido"].values
        linha = {"ensaio": nome, "n_pontos": len(g)}
        for col, rot in (("XZn_v2_comite", "v2"), ("XZn_fenomenologico", "fenomenologico"), ("XZn_v1", "v1"),
                         ("XZn_interp_empirica_16_ensaios", "interp_empirica")):
            linha[f"RMSE_{rot}"] = float(np.sqrt(np.mean((y - g[col].values) ** 2)))
        linha["vies_v2_medido_menos_previsto"] = float(np.mean(g["erro_v2"]))
        linha["erro_max_abs_v2"] = float(np.max(np.abs(g["erro_v2"])))
        linhas.append(linha)
    res = pd.DataFrame(linhas)
    res.to_csv(OUT / "tabela_comparacao_medicoes.csv", index=False)
    m.to_csv(OUT / "tabela_comparacao_medicoes_pontos.csv", index=False)
    figuras(tab, cur, med, sufixo="_com_medicoes")
    print(res.round(4).to_string(index=False))
    print("Referências de erro típico do modelo: 0,033 (validação cruzada) e 0,020 (teste cego).")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("etapa", choices=["prever", "comparar"])
    ap.add_argument("--medicoes", type=Path)
    a = ap.parse_args()
    if a.etapa == "prever":
        prever()
    else:
        if a.medicoes is None:
            raise SystemExit("Informe --medicoes arquivo.csv (colunas: ensaio, t_min, XZn_medido).")
        comparar(a.medicoes)


if __name__ == "__main__":
    main()
