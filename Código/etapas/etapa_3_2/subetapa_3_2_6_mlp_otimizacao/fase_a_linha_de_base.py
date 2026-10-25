"""Fase A (Subetapa 3.2.6): linha de base honesta da MLP-B v1 no protocolo comum.

Compara a mesma arquitetura e os mesmos hiperparâmetros da v1 ([64, 32], GELU, LayerNorm,
AdamW 3e-3 / 1e-4, batch 32) em dois protocolos de validação cruzada:

- Protocolo antigo (Subetapa 3.2.1): a dobra de validação decide a parada antecipada e também
  dá a nota; uma semente; nota em ν.
- Protocolo novo (protocolo_cv.py): parada antecipada em 2 ensaios internos do treino, nota em
  X_Zn nos ensaios de validação (passando pelo PBM), 3 sementes.

Referências de comparação: o teto (X_Zn reconstruído com os próprios alvos ν do problema
inverso) e o modelo final v1 avaliado no próprio treino.

Saídas em outputs/etapa_3_2/subetapa_3_2_6_mlp_otimizacao/fase_a/.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from protocolo_cv import (
    CONFIG_V1, ENSAIOS_TESTE, OUTPUTS_DIR, SEMENTES_PADRAO, MLPTrainer, SerialHybridModel,
    X_dos_alvos, carregar_dados, metricas, metricas_nu, rodar_cv, simular_X,
)

OUT = OUTPUTS_DIR / "fase_a"
NAVY, BLUE, TEAL, ORANGE, GRAY = "#1F3A5F", "#2E6DA4", "#2A9D8F", "#D9822B", "#8C8C8C"
T_CURVA = np.arange(0.0, 15.0 + 1e-9, 0.25)


def estilo() -> None:
    plt.rcParams.update({
        "font.family": "Arial", "font.size": 10, "axes.labelsize": 11, "axes.titlesize": 12,
        "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 9,
        "savefig.dpi": 300, "savefig.bbox": "tight",
    })


def salvar(fig: plt.Figure, nome: str) -> None:
    fig.savefig(OUT / f"{nome}.png", dpi=300)
    fig.savefig(OUT / f"{nome}.pdf", dpi=300)
    plt.close(fig)


def protocolo_antigo(dados) -> tuple:
    """Reproduz a validação cruzada da Subetapa 3.2.1 e mede também X_Zn nas dobras."""
    linhas, oof, modelos = [], [], {}
    trainer = MLPTrainer(
        hidden_dims=CONFIG_V1["hidden_dims"], input_dim=3, dropout_rate=0.0, use_layer_norm=True,
        activation="GELU", use_residual=False, lr=CONFIG_V1["lr"],
        weight_decay=CONFIG_V1["weight_decay"], batch_size=32, patience=60, seed=42,
    )
    for fold in dados.folds:
        val = list(fold["val_ensaios"])
        m_va = dados.mascara(val)
        model, hist = trainer.fit_with_early_stopping(
            dados.X_train_s[~m_va], dados.y_train[~m_va], dados.X_train_s[m_va], dados.y_train[m_va],
            max_epochs=350, seed_offset=fold["fold"] * 7,
        )
        px = simular_X(model, dados, val)
        px["fold"] = fold["fold"]
        oof.append(px)
        modelos[fold["fold"]] = model
        linhas.append({
            "fold": fold["fold"], "val_ensaios": str(val), "melhor_epoca": hist["best_epoch"][0],
            "epocas_rodadas": len(hist["train_loss"]),
            **{f"{c}_X": v for c, v in metricas(px["XZn_exp"].values, px["XZn_pred"].values).items()},
            **metricas_nu(model, dados.X_train_s[m_va], dados.y_train[m_va]),
        })
    return pd.DataFrame(linhas), pd.concat(oof, ignore_index=True), modelos


def curva_teto(dados, e: int) -> np.ndarray:
    """X_Zn(t) contínuo reconstruído com os alvos ν do problema inverso."""
    sub = dados.train_df[dados.train_df["ensaio"] == e].sort_values("t_min")
    eta = float(sub["razao_molar_eta"].iloc[0])
    res = dados.solver.simulate_with_v_profile(sub["t_min"].values, -sub["abs_v_alvo_um_min"].values)
    t_int = np.concatenate([[0.0], sub["t_min"].values])
    x_int = np.clip(np.maximum.accumulate(np.concatenate([[0.0], res["XZn"]])), 0.0, min(1.0, eta))
    return np.interp(T_CURVA, t_int, x_int)


def fig_protocolos(antigo: pd.DataFrame, novo, ref: Dict[str, float]) -> None:
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 4.8))
    folds = antigo["fold"].values
    nd = novo.por_dobra.groupby("fold")
    x = np.arange(len(folds))
    a1.bar(x - 0.2, antigo["R2_nu"], 0.38, color=GRAY, edgecolor="black", label="Protocolo antigo (1 semente)")
    a1.bar(x + 0.2, nd["R2_nu"].mean().values, 0.38, yerr=nd["R2_nu"].std().values, capsize=4,
           color=BLUE, edgecolor="black", label="Protocolo novo (média ± dp, 3 sementes)")
    a1.set_xticks(x, [f"Dobra {f}\n{v}" for f, v in zip(folds, antigo["val_ensaios"])])
    a1.set_ylabel(r"$R^2$ da taxa $\nu$ na validação (–)")
    a1.set_title("(a) Nota em $\\nu$ por dobra")
    a1.axhline(0, color="black", lw=0.8)
    a1.grid(axis="y", ls="--", alpha=0.5)
    a1.legend(loc="lower left")

    nomes = ["Teto\n(alvos $\\nu$)", "v1 final\n(no próprio treino)", "v1 – VC\nprotocolo antigo", "v1 – VC\nprotocolo novo"]
    vals = [ref["teto"], ref["v1_treino"], ref["antigo"], novo.objetivo]
    erros = [0, 0, 0, novo.objetivo_std]
    cores = [TEAL, NAVY, GRAY, BLUE]
    b = a2.bar(nomes, vals, yerr=erros, capsize=5, color=cores, edgecolor="black", width=0.6)
    for r, v in zip(b, vals):
        a2.text(r.get_x() + r.get_width() / 2, v + 0.0012, f"{v:.4f}", ha="center", va="bottom", fontsize=9.5)
    a2.set_ylabel(r"RMSE de $X_{Zn}$ nos 91 pontos de treino (–)")
    a2.set_title("(b) Erro em $X_{Zn}$ (13 ensaios, $t$ > 0)")
    a2.set_ylim(0, max(v + e for v, e in zip(vals, erros)) * 1.12)
    a2.grid(axis="y", ls="--", alpha=0.5)
    fig.tight_layout()
    salvar(fig, "fig_fa_01_protocolo_antigo_vs_novo")


def fig_curvas(dados, novo, antigo_modelos) -> None:
    fig, axes = plt.subplots(4, 4, figsize=(15, 12), sharex=True, sharey=True)
    fold_de = {e: f["fold"] for f in dados.folds for e in f["val_ensaios"]}
    for e, ax in zip(range(1, 17), axes.ravel()):
        m = dados.meta[dados.meta["ensaio"] == e].iloc[0]
        titulo = f"Ensaio {e:02d} – $C_{{A0}}$={m['CA0_mol_L']:.1f} M, $\\eta$={m['razao_molar_eta']:.1f}"
        if e in ENSAIOS_TESTE:
            ax.text(0.5, 0.5, "Teste cego\n(fora desta fase)", ha="center", va="center",
                    transform=ax.transAxes, color=GRAY, fontsize=11)
            ax.set_title(titulo, fontsize=9.5, color=GRAY)
            continue
        f = fold_de[e]
        curvas = np.array([
            simular_X(novo.modelos[(s, f)], dados, [e], t_eval=T_CURVA)["XZn_pred"].values for s in SEMENTES_PADRAO
        ])
        x_ant = simular_X(antigo_modelos[f], dados, [e], t_eval=T_CURVA)["XZn_pred"].values
        exp = dados.exp_df[dados.exp_df["ensaio"] == e]
        ax.plot(T_CURVA, curva_teto(dados, e), color=TEAL, lw=1.6, ls=":", label="Teto (alvos $\\nu$)")
        ax.plot(T_CURVA, x_ant, color=GRAY, lw=1.4, ls="--", label="VC protocolo antigo")
        ax.fill_between(T_CURVA, curvas.min(0), curvas.max(0), color=BLUE, alpha=0.22, label="VC protocolo novo (faixa das sementes)")
        ax.plot(T_CURVA, curvas.mean(0), color=BLUE, lw=1.8, label="VC protocolo novo (média)")
        ax.plot(np.r_[0.0, exp["t_min"]], np.r_[0.0, exp["XZn"]], "o", color="black", ms=4.5, label="Experimental")
        ax.set_title(titulo, fontsize=9.5)
        ax.grid(ls="--", alpha=0.45)
    for ax in axes[-1]:
        ax.set_xlabel("$t$ (min)")
    for ax in axes[:, 0]:
        ax.set_ylabel("$X_{Zn}$ (–)")
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    salvar(fig, "fig_fa_02_XZn_fora_da_dobra_13_ensaios")


def fig_por_ensaio(oof_antigo: pd.DataFrame, novo, teto: pd.DataFrame) -> pd.DataFrame:
    def rmse_por_ensaio(df: pd.DataFrame) -> pd.Series:
        return df.groupby("ensaio").apply(lambda g: np.sqrt(np.mean((g["XZn_exp"] - g["XZn_pred"]) ** 2)))

    r_novo = novo.oof.groupby(["semente", "ensaio"]).apply(
        lambda g: np.sqrt(np.mean((g["XZn_exp"] - g["XZn_pred"]) ** 2))).unstack(0)
    tab = pd.DataFrame({
        "RMSE_X_teto": rmse_por_ensaio(teto),
        "RMSE_X_antigo": rmse_por_ensaio(oof_antigo),
        "RMSE_X_novo_media": r_novo.mean(1),
        "RMSE_X_novo_dp": r_novo.std(1, ddof=1),
    })
    fig, ax = plt.subplots(figsize=(12.5, 4.6))
    x = np.arange(len(tab))
    ax.bar(x - 0.27, tab["RMSE_X_teto"], 0.26, color=TEAL, edgecolor="black", label="Teto (alvos $\\nu$)")
    ax.bar(x, tab["RMSE_X_antigo"], 0.26, color=GRAY, edgecolor="black", label="VC protocolo antigo")
    ax.bar(x + 0.27, tab["RMSE_X_novo_media"], 0.26, yerr=tab["RMSE_X_novo_dp"], capsize=3,
           color=BLUE, edgecolor="black", label="VC protocolo novo (média ± dp)")
    ax.set_xticks(x, [f"{e:02d}" for e in tab.index])
    ax.set_xlabel("Ensaio de treino (avaliado quando está na dobra de validação)")
    ax.set_ylabel("RMSE de $X_{Zn}$ (–)")
    ax.grid(axis="y", ls="--", alpha=0.5)
    ax.legend(loc="upper right")
    fig.tight_layout()
    salvar(fig, "fig_fa_03_rmse_XZn_por_ensaio")
    return tab


def relatorio(antigo, novo, ref, tab_ens, tempo) -> None:
    nd = novo.por_dobra
    txt = f"""# Fase A — Linha de base honesta da MLP-B v1 (Subetapa 3.2.6)

## Objetivo
Medir o desempenho da configuração v1 ([64, 32], GELU, LayerNorm, AdamW 3e-3 / 1e-4, batch 32,
paciência 60, até 350 épocas) num protocolo de validação sem viés de seleção e com nota em X_Zn,
que é a variável efetivamente reportada pelo híbrido serial.

## Como foi feito
- **Protocolo antigo** (Subetapa 3.2.1): a dobra de validação decide a parada antecipada e dá a nota;
  semente 42; nota na taxa ν.
- **Protocolo novo** (`protocolo_cv.py`): em cada dobra, 2 ensaios do treino (sorteio fixo, sem os
  vértices 1, 2, 5 e 16) servem só para a parada antecipada; os ensaios de validação da dobra passam
  pelo PBM e dão a nota em X_Zn (7 pontos t > 0 por ensaio, 91 no total); sementes 42, 43 e 44.
- O teste cego (ensaios 7, 8 e 14) não foi usado.
- Tempo total: {tempo:.0f} s.

## Resultados
| Referência / protocolo | RMSE X_Zn (91 pts) | R² X_Zn | R² médio de ν nas dobras |
| :--- | :---: | :---: | :---: |
| Teto: X_Zn dos próprios alvos ν | {ref['teto']:.4f} | {ref['teto_r2']:.4f} | – |
| v1 final, no próprio treino (não é validação) | {ref['v1_treino']:.4f} | {ref['v1_treino_r2']:.4f} | – |
| v1, VC protocolo antigo | {ref['antigo']:.4f} | {ref['antigo_r2']:.4f} | {antigo['R2_nu'].mean():.4f} |
| v1, VC protocolo novo (média ± dp, 3 sementes) | {novo.objetivo:.4f} ± {novo.objetivo_std:.4f} | {novo.por_semente['R2_X'].mean():.4f} | {nd['R2_nu'].mean():.4f} |

Verificação de coerência: o R² médio de ν no protocolo antigo deve reproduzir o valor da Subetapa 3.2.1
(0,8210). Obtido: {antigo['R2_nu'].mean():.4f}.

### Por dobra (protocolo novo, média das 3 sementes)
| Dobra | Validação | Parada interna (semente 42) | RMSE X_Zn | R² ν | R²_log ν | Melhor época |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: |
"""
    for f, g in nd.groupby("fold"):
        txt += (f"| {f} | {g['val_ensaios'].iloc[0]} | {g['parada_ensaios'].iloc[0]} | {g['RMSE_X'].mean():.4f} | "
                f"{g['R2_nu'].mean():.4f} | {g['R2_log_nu'].mean():.4f} | {g['melhor_epoca'].mean():.0f} |\n")
    txt += """
### Por ensaio (RMSE de X_Zn quando o ensaio está na validação)
| Ensaio | Teto | Protocolo antigo | Protocolo novo (média ± dp) |
| :---: | :---: | :---: | :---: |
"""
    for e, r in tab_ens.iterrows():
        txt += f"| {e:02d} | {r['RMSE_X_teto']:.4f} | {r['RMSE_X_antigo']:.4f} | {r['RMSE_X_novo_media']:.4f} ± {r['RMSE_X_novo_dp']:.4f} |\n"
    txt += """
## Figuras
- `fig_fa_01_protocolo_antigo_vs_novo`: (a) R² de ν por dobra nos dois protocolos; (b) RMSE de X_Zn das referências e dos dois protocolos.
- `fig_fa_02_XZn_fora_da_dobra_13_ensaios`: X_Zn(t) de cada ensaio previsto pelo modelo da dobra em que ele ficou de fora.
- `fig_fa_03_rmse_XZn_por_ensaio`: RMSE de X_Zn por ensaio.

## Base bibliográfica
- Validação cruzada por grupos (ensaios): Roberts et al. (2017); Hastie, Tibshirani e Friedman (2009).
- Viés de selecionar e avaliar no mesmo conjunto: Cawley e Talbot (2010) [referência nova]; vazamento: Kapoor e Narayanan (2023).
- Parada antecipada como regularização: Goodfellow, Bengio e Courville (2016, seção 7.8).
"""
    (OUT / "relatorio_fase_a.md").write_text(txt, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    estilo()
    t0 = time.time()
    dados = carregar_dados()
    ensaios_treino = sorted(dados.train_df["ensaio"].unique())

    teto = X_dos_alvos(dados, ensaios_treino)
    v1 = SerialHybridModel(model_type="mlp")
    px_v1 = simular_X(v1.model, dados, ensaios_treino)

    print("Protocolo antigo...")
    antigo, oof_antigo, modelos_antigos = protocolo_antigo(dados)
    print(antigo[["fold", "R2_nu", "RMSE_X"]])

    print("Protocolo novo...")
    novo = rodar_cv(CONFIG_V1, dados)
    print(novo.por_semente)

    m_teto = metricas(teto["XZn_exp"], teto["XZn_pred"])
    m_v1 = metricas(px_v1["XZn_exp"], px_v1["XZn_pred"])
    m_ant = metricas(oof_antigo["XZn_exp"], oof_antigo["XZn_pred"])
    ref = {
        "teto": m_teto["RMSE"], "teto_r2": m_teto["R2"], "v1_treino": m_v1["RMSE"], "v1_treino_r2": m_v1["R2"],
        "antigo": m_ant["RMSE"], "antigo_r2": m_ant["R2"],
    }

    antigo.to_csv(OUT / "tabela_fase_a_protocolo_antigo_por_dobra.csv", index=False)
    novo.por_dobra.to_csv(OUT / "tabela_fase_a_protocolo_novo_por_dobra.csv", index=False)
    novo.por_semente.to_csv(OUT / "tabela_fase_a_protocolo_novo_por_semente.csv", index=False)
    novo.oof.to_csv(OUT / "predicoes_fora_da_dobra_protocolo_novo.csv", index=False)
    oof_antigo.to_csv(OUT / "predicoes_fora_da_dobra_protocolo_antigo.csv", index=False)
    pd.DataFrame([{"referencia": k, "valor": v} for k, v in ref.items()] +
                 [{"referencia": "novo_RMSE_X_media", "valor": novo.objetivo},
                  {"referencia": "novo_RMSE_X_dp", "valor": novo.objetivo_std}]
                 ).to_csv(OUT / "tabela_fase_a_resumo.csv", index=False)

    fig_protocolos(antigo, novo, ref)
    fig_curvas(dados, novo, modelos_antigos)
    tab_ens = fig_por_ensaio(oof_antigo, novo, teto)
    tab_ens.to_csv(OUT / "tabela_fase_a_rmse_por_ensaio.csv")
    relatorio(antigo, novo, ref, tab_ens, time.time() - t0)
    print(f"Fase A concluída em {time.time() - t0:.0f} s. Saídas em {OUT}")


if __name__ == "__main__":
    main()
