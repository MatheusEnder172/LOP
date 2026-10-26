"""Figuras, tabelas e relatório da Fase E mínima (ensemble final e teste cego) da Subetapa 3.2.6."""

from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from fase_e_ensemble_final import MODELOS_DIR, OUT, OUTPUTS_DIR
from figuras_fase_b import BLUE, GRAY, NAVY, ORANGE, TEAL, TETO_RMSE, estilo
from protocolo_cv import ENSAIOS_TESTE, TARGET, carregar_dados

RED = "#B23A48"
V2, V1, FPM = "MLP v2 (ensemble)", "MLP v1", "Fenomenológico puro"
COR = {V2: BLUE, V1: ORANGE, FPM: GRAY}


def salvar(fig, nome: str) -> None:
    fig.savefig(OUT / f"{nome}.png", dpi=300)
    fig.savefig(OUT / f"{nome}.pdf", dpi=300)
    plt.close(fig)


def _titulo(meta: pd.DataFrame, e: int) -> str:
    m = meta[meta["ensaio"] == e].iloc[0]
    return f"Ensaio {e}: $C_{{A0}}$ = {m['CA0_mol_L']:.1f} mol/L, $\\eta$ = {m['razao_molar_eta']:.1f}"


def fig_XZn_teste(curvas: pd.DataFrame, pts: pd.DataFrame, meta: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), sharey=True)
    for ax, e in zip(axes, ENSAIOS_TESTE):
        c = curvas[curvas["ensaio"] == e]
        memb = c[c["modelo"].str.startswith("membro")].pivot(index="t_min", columns="modelo", values="XZn_pred")
        ax.fill_between(memb.index, memb.min(axis=1), memb.max(axis=1), color=BLUE, alpha=0.18,
                        label="Faixa dos 10 membros (mín.–máx.)")
        v2 = c[c["modelo"] == "v2_ensemble"]
        v1 = c[c["modelo"] == "v1"]
        ax.plot(v2["t_min"], v2["XZn_pred"], color=BLUE, lw=2.2, label=V2)
        ax.plot(v1["t_min"], v1["XZn_pred"], color=ORANGE, lw=1.8, ls="--", label=V1)
        p = pts[pts["ensaio"] == e]
        ax.scatter(p["t_min"], p["XZn_FPM"], marker="x", s=40, color=GRAY, zorder=4, label=FPM)
        ax.scatter(p["t_min"], p["XZn_exp"], s=42, color=NAVY, edgecolor="white", zorder=5, label="Experimental")
        ax.set_title(_titulo(meta, e), fontsize=10.5)
        ax.set_xlabel("Tempo (min)")
        ax.grid(ls="--", alpha=0.5)
        ax.set_xlim(0, 15.3)
    axes[0].set_ylabel("Conversão de zinco, $X_{Zn}$ (–)")
    axes[0].legend(loc="lower right", fontsize=8.5)
    fig.tight_layout()
    salvar(fig, "fig_fe_01_XZn_teste_cego")


def fig_nu_teste(curvas: pd.DataFrame, dados, meta: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), sharey=True)
    piso = 1e-3
    for ax, e in zip(axes, ENSAIOS_TESTE):
        c = curvas[(curvas["ensaio"] == e) & (curvas["t_min"] > 0)]
        memb = c[c["modelo"].str.startswith("membro")].pivot(index="t_min", columns="modelo", values="abs_v_pred")
        ax.fill_between(memb.index, np.maximum(memb.min(axis=1), piso), np.maximum(memb.max(axis=1), piso),
                        color=BLUE, alpha=0.18, label="Faixa dos 10 membros")
        v2 = c[c["modelo"] == "v2_ensemble"]
        v1 = c[c["modelo"] == "v1"]
        ax.plot(v2["t_min"], np.maximum(v2["abs_v_pred"], piso), color=BLUE, lw=2.2, label=V2)
        ax.plot(v1["t_min"], np.maximum(v1["abs_v_pred"], piso), color=ORANGE, lw=1.8, ls="--", label=V1)
        alvo = dados.test_df[dados.test_df["ensaio"] == e].sort_values("t_min")
        ax.scatter(alvo["t_min"], np.maximum(alvo[TARGET], piso), s=14, color=NAVY, zorder=5,
                   label="Alvo $\\nu$ (problema inverso)")
        ax.set_yscale("log")
        ax.set_ylim(piso * 0.8, 200)
        ax.set_title(_titulo(meta, e), fontsize=10.5)
        ax.set_xlabel("Tempo (min)")
        ax.grid(ls="--", alpha=0.5, which="both")
    axes[0].set_ylabel("Taxa de retração, $\\nu$ (µm/min)")
    axes[0].legend(loc="upper right", fontsize=8.5)
    fig.tight_layout()
    salvar(fig, "fig_fe_02_nu_teste_cego")


def fig_paridade(pts: pd.DataFrame, tab: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2), sharey=True)
    for ax, (col, nome) in zip(axes, [("XZn_v1", V1), ("XZn_v2_ensemble", V2)]):
        for part, mk, cor in [("Treino", "o", COR[nome]), ("Teste cego", "D", RED)]:
            p = pts[pts["particao"] == part]
            ax.scatter(p["XZn_exp"], p[col], marker=mk, s=30 if part == "Treino" else 46, color=cor,
                       alpha=0.65 if part == "Treino" else 0.95, edgecolor="white", lw=0.5,
                       label=f"{part} ({len(p)} pontos)")
        ax.plot([0, 1.02], [0, 1.02], color="black", lw=1)
        for d in (0.05, -0.05):
            ax.plot([0, 1.02], [d, 1.02 + d], color="black", lw=0.8, ls=":")
        t = tab[(tab["Modelo"] == nome)].set_index("Particao")
        ax.text(0.03, 0.97, f"Treino: RMSE = {t.loc['Treino', 'RMSE']:.4f}\n"
                            f"Teste cego: RMSE = {t.loc['Teste cego', 'RMSE']:.4f}",
                transform=ax.transAxes, va="top", fontsize=9.5,
                bbox={"boxstyle": "round", "fc": "white", "ec": GRAY})
        ax.set_title(nome)
        ax.set_xlabel("$X_{Zn}$ experimental (–)")
        ax.set_xlim(0, 1.02)
        ax.set_ylim(0, 1.02)
        ax.set_aspect("equal")
        ax.grid(ls="--", alpha=0.5)
        ax.legend(loc="lower right")
    axes[0].set_ylabel("$X_{Zn}$ previsto (–)")
    fig.tight_layout()
    salvar(fig, "fig_fe_03_paridade_XZn")


def fig_rmse_teste(por_ensaio: pd.DataFrame, tab: pd.DataFrame, memb: pd.DataFrame) -> None:
    grupos = [f"Ensaio {e}" for e in ENSAIOS_TESTE] + ["Teste cego\n(21 pontos)"]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    largura = 0.26
    x = np.arange(len(grupos))
    hi_membros = memb["RMSE_teste_cego"].max()
    for i, nome in enumerate([FPM, V1, V2]):
        vals = [por_ensaio[(por_ensaio["ensaio"] == e) & (por_ensaio["Modelo"] == nome)]["RMSE"].iloc[0]
                for e in ENSAIOS_TESTE]
        vals.append(tab[(tab["Modelo"] == nome) & (tab["Particao"] == "Teste cego")]["RMSE"].iloc[0])
        b = ax.bar(x + (i - 1) * largura, vals, largura, color=COR[nome], edgecolor="black", label=nome)
        for j, (r, v) in enumerate(zip(b, vals)):
            topo = max(v, hi_membros) if (nome == V2 and j == len(vals) - 1) else v
            ax.text(r.get_x() + r.get_width() / 2, topo + 0.002, f"{v:.3f}", ha="center", fontsize=8)
    # Dispersão de um único membro (RMSE de cada membro isolado, mín.–máx.)
    lo, hi = memb["RMSE_teste_cego"].min(), memb["RMSE_teste_cego"].max()
    v2_glob = tab[(tab["Modelo"] == V2) & (tab["Particao"] == "Teste cego")]["RMSE"].iloc[0]
    ax.errorbar(x[-1] + largura, v2_glob, yerr=[[max(v2_glob - lo, 0)], [max(hi - v2_glob, 0)]], fmt="none",
                ecolor=NAVY, capsize=5, lw=1.4, label="Membros isolados (mín.–máx.)")
    ax.set_xticks(x, grupos)
    ax.set_ylabel("RMSE de $X_{Zn}$ (–)")
    ax.grid(axis="y", ls="--", alpha=0.5)
    ax.legend(loc="upper left")
    fig.tight_layout()
    salvar(fig, "fig_fe_04_rmse_teste_cego")


def fig_evolucao(tab: pd.DataFrame) -> None:
    fin = pd.read_csv(OUTPUTS_DIR / "fase_b2" / "tabela_fase_b2_finalistas.csv").set_index("config")
    etapas = [("v1\n(Fase A)", "v1 (MLP-B, parada interna)", ORANGE), ("Fase B\n(4×21, Tanh)", "Fase B (Tentativa 211)", TEAL),
              ("Fase B2\n([90,45,22], ln t)", "B2 – tentativa 511", BLUE)]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw={"width_ratios": [1.3, 1]})
    ax = axes[0]
    for i, (rot, chave, cor) in enumerate(etapas):
        m, d = fin.loc[chave, "RMSE_X_media"], fin.loc[chave, "RMSE_X_dp"]
        ax.bar(i, m, 0.6, yerr=d, capsize=5, color=cor, edgecolor="black")
        ax.text(i, m + d + 0.004, f"{m:.4f}\n± {d:.4f}", ha="center", fontsize=9)
    ax.axhline(TETO_RMSE, color=NAVY, ls=":", lw=1.6, label=f"Teto: alvos $\\nu$ ({TETO_RMSE:.4f})")
    ax.set_xticks(range(len(etapas)), [e[0] for e in etapas])
    ax.set_ylabel("RMSE de $X_{Zn}$ fora da dobra (–)")
    ax.set_title("(a) Validação cruzada por ensaio, 10 sementes (91 pontos)", fontsize=10.5)
    ax.set_ylim(0, 0.25)
    ax.grid(axis="y", ls="--", alpha=0.5)
    ax.legend(loc="upper right")

    ax = axes[1]
    nomes = [FPM, V1, V2]
    for i, nome in enumerate(nomes):
        t = tab[(tab["Modelo"] == nome)].set_index("Particao")
        ax.bar(i - 0.18, t.loc["Treino", "RMSE"], 0.36, color=COR[nome], alpha=0.45, edgecolor="black",
               hatch="//", label="Treino (91 pontos)" if i == 0 else None)
        ax.bar(i + 0.18, t.loc["Teste cego", "RMSE"], 0.36, color=COR[nome], edgecolor="black",
               label="Teste cego (21 pontos)" if i == 0 else None)
        for dx, v in ((-0.18, t.loc["Treino", "RMSE"]), (0.18, t.loc["Teste cego", "RMSE"])):
            ax.text(i + dx, v + 0.0015, f"{v:.3f}", ha="center", fontsize=8.5)
    ax.set_xticks(range(len(nomes)), ["Fenomenológico\npuro", "MLP v1", "MLP v2\n(ensemble)"])
    ax.set_ylabel("RMSE de $X_{Zn}$ (–)")
    ax.set_title("(b) Modelos finais: treino e teste cego", fontsize=10.5)
    ax.grid(axis="y", ls="--", alpha=0.5)
    ax.legend(loc="upper right")
    fig.tight_layout()
    salvar(fig, "fig_fe_05_evolucao_e_teste")


def _md_tabela(df: pd.DataFrame) -> str:
    cab = "| " + " | ".join(df.columns) + " |\n| " + " | ".join([":---"] + [":---:"] * (len(df.columns) - 1)) + " |\n"
    return cab + "".join("| " + " | ".join(str(v) for v in r) + " |\n" for r in df.values)


def relatorio(tab, por_ensaio, nu, memb, treino_m, resumo, info) -> None:
    cfg = info["config"]
    t = tab.copy()
    for c in ("R2", "RMSE", "MAE", "MaxErro"):
        t[c] = t[c].map(lambda v: f"{v:.4f}")
    pe = por_ensaio[por_ensaio["particao"] == "Teste cego"].pivot(index="ensaio", columns="Modelo", values="RMSE")
    pe = pe[[FPM, V1, V2]].map(lambda v: f"{v:.4f}").reset_index()
    nu_t = nu.copy()
    for c in nu_t.columns[1:]:
        nu_t[c] = nu_t[c].map(lambda v: f"{v:.4f}")
    v2t = tab[(tab["Modelo"] == V2) & (tab["Particao"] == "Teste cego")].iloc[0]
    v1t = tab[(tab["Modelo"] == V1) & (tab["Particao"] == "Teste cego")].iloc[0]
    texto = f"""# Fase E mínima — Ensemble final da MLP v2 e teste cego (Subetapa 3.2.6)

## Objetivo
Treinar o modelo final da MLP v2 com a configuração escolhida na Fase B2 e avaliá-lo uma única vez no
teste cego (ensaios 7, 8 e 14), para que a metodologia descreva o pipeline completo. As Fases C e D
continuam pausadas; esta é a versão mínima da Fase E.

## Como foi feito
- Configuração: {info['origem_config']} — camadas {cfg['hidden_dims']} com conexões residuais,
  {cfg['activation']}, sem LayerNorm, entrada em ln t, dropout {cfg['dropout_rate']:.3f}, AdamW com lr
  {cfg['lr']:.2e} e weight decay {cfg['weight_decay']:.2e}, lote {cfg['batch_size']},
  {cfg['max_epochs']} épocas fixas com taxa de aprendizado em cosseno.
- Ensemble de {len(info['sementes'])} membros (sementes {info['sementes'][0]} a {info['sementes'][-1]}), cada um
  treinado nos {len(info['ensaios_treino'])} ensaios de treino ({info['n_registros_treino']} registros), sem reserva
  de ensaios. A predição é a média de ν entre os membros, passada pelo PBM (`SerialHybridModel`);
  a faixa de incerteza vem de integrar cada membro separadamente (Lakshminarayanan et al., 2017).
- Tempo de treino: {treino_m['segundos'].mean() / 60:.1f} min por membro (média), em paralelo.
- O teste cego foi avaliado uma única vez, com o modelo já congelado (Kapoor; Narayanan, 2023).
  O script recusa retreinar se já houver membros salvos.
- Referências na mesma avaliação: MLP v1 (`mlp_kinetics_v1.pt`, pipeline oficial) e modelo
  fenomenológico puro (predições da Etapa 4.2).
- Modelos salvos em `Código/outputs/models_saved/mlp_v2/` (membros `.pt` e `mlp_v2_config.json`);
  `mlp_kinetics_v1.pt` não foi alterado.

## Resultados — X_Zn nos pontos experimentais (t > 0)
{_md_tabela(t)}
Conferência: as linhas da v1 e do modelo fenomenológico devem reproduzir a Etapa 4.2
(v1: RMSE de treino 0,0229 e de teste cego 0,0353; fenomenológico: 0,0682 e 0,0780).

### RMSE de X_Zn por ensaio do teste cego
{_md_tabela(pe)}
### Membros isolados no teste cego
RMSE de um único membro: {resumo['RMSE_teste_cego_membros_media']:.4f} ± {resumo['RMSE_teste_cego_membros_dp']:.4f}
(mín. {resumo['RMSE_teste_cego_membros_min']:.4f}, máx. {resumo['RMSE_teste_cego_membros_max']:.4f}), contra
{v2t['RMSE']:.4f} do ensemble.

### Taxa ν no teste cego (malha densa, alvos do problema inverso)
{_md_tabela(nu_t)}
## Leitura dos resultados
- Teste cego: RMSE de X_Zn de {v2t['RMSE']:.4f} (R² {v2t['R2']:.3f}) para a v2, contra {v1t['RMSE']:.4f}
  (R² {v1t['R2']:.3f}) para a v1.
- Validação cruzada da configuração (B2, 10 sementes, 91 pontos fora da dobra): 0,0326 ± 0,0050.
  O teste cego (0,020) ficou abaixo desse valor, o que é coerente com o que a Seção de partição já
  previa: a 1ª dobra reúne vértices do planejamento, enquanto o teste avalia só condições internas.
- O ensemble ({v2t['RMSE']:.4f}) ficou ligeiramente melhor que a média de um membro isolado
  ({resumo['RMSE_teste_cego_membros_media']:.4f}); a faixa entre membros é estreita em X_Zn e mais larga em ν
  no fim da batelada, onde ν é pequena e quase não altera X_Zn.
- Em ν, a v2 não superou a v1 no teste (R²_log 0,904 contra 0,945), embora seja melhor em X_Zn. A maior
  parte da diferença está depois de cerca de 4 min nos ensaios 8 e 14, onde os alvos do problema inverso
  ficam parados em 0,03 µm/min, o limite superior do parâmetro c; ali ν é pequena e pesa pouco em X_Zn.
  É o mesmo desalinhamento entre a perda em ν e o erro em X_Zn que motivou a nota em X_Zn (e as Fases C e D).
- No ensaio 7 (η = 3,1, maior excesso de ácido) a v2 ficou um pouco pior que a v1 (0,022 contra 0,016);
  nos ensaios 8 e 14 ficou melhor (0,025 contra 0,056; 0,011 contra 0,018).
- Ressalva sobre a comparação: o teste cego da v1 já tinha sido calculado na Etapa 4.2 e usado na MCDA,
  então ele não é mais "cego" para a v1. Para a v2, é a primeira e única avaliação.
- Com só 3 ensaios e 21 pontos, diferenças pequenas de RMSE no teste não são conclusivas; a validação
  cruzada (13 ensaios) é a evidência principal para a escolha da configuração.

## Figuras
- `fig_fe_01_XZn_teste_cego`: X_Zn(t) dos 3 ensaios de teste (experimental, v2 com faixa dos membros, v1 e fenomenológico).
- `fig_fe_02_nu_teste_cego`: ν(t) dos 3 ensaios de teste contra os alvos do problema inverso.
- `fig_fe_03_paridade_XZn`: paridade de X_Zn, v1 e v2, treino e teste cego.
- `fig_fe_04_rmse_teste_cego`: RMSE por ensaio de teste e global.
- `fig_fe_05_evolucao_e_teste`: (a) RMSE fora da dobra de A a B2; (b) treino e teste dos modelos finais.

## Base bibliográfica
- Ensemble de redes com sementes diferentes: Lakshminarayanan et al. (2017) [nova]; Goodfellow, Bengio e Courville (2016, seção 7.11).
- Teste usado uma única vez, fora da seleção: Kapoor e Narayanan (2023); Hastie, Tibshirani e Friedman (2009).
"""
    (OUT / "relatorio_fase_e.md").write_text(texto, encoding="utf-8")


def gerar_tudo() -> None:
    estilo()
    dados = carregar_dados()
    tab = pd.read_csv(OUT / "tabela_fase_e_metricas_XZn.csv")
    por_ensaio = pd.read_csv(OUT / "tabela_fase_e_rmse_por_ensaio.csv")
    pts = pd.read_csv(OUT / "predicoes_fase_e_pontos_experimentais.csv")
    curvas = pd.read_csv(OUT / "curvas_fase_e_teste_cego.csv")
    memb = pd.read_csv(OUT / "tabela_fase_e_membros_teste_cego.csv")
    nu = pd.read_csv(OUT / "tabela_fase_e_metricas_nu_teste_cego.csv")
    treino_m = pd.read_csv(OUT / "tabela_fase_e_treino_membros.csv")
    resumo = json.loads((OUT / "resumo_fase_e.json").read_text(encoding="utf-8"))
    info = json.loads((MODELOS_DIR / "mlp_v2_config.json").read_text(encoding="utf-8"))
    fig_XZn_teste(curvas, pts, dados.meta)
    fig_nu_teste(curvas, dados, dados.meta)
    fig_paridade(pts, tab)
    fig_rmse_teste(por_ensaio, tab, memb)
    fig_evolucao(tab)
    relatorio(tab, por_ensaio, nu, memb, treino_m, resumo, info)
    print("Figuras e relatório da Fase E gerados em", OUT)


if __name__ == "__main__":
    gerar_tudo()
