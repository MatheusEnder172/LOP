"""Figuras, tabelas e relatório da Fase B (Subetapa 3.2.6).

Lê o estudo Optuna (journal) e as reavaliações dos finalistas gravadas por fase_b_optuna_hpo.py
e gera as figuras fig_fb_01 a fig_fb_07 (300 DPI, PNG + PDF) e o relatorio_fase_b.md.
"""

from __future__ import annotations

import json
from typing import Dict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from fase_b_optuna_hpo import OUT, T_CURVA, carregar_estudo, exportar_tentativas
from protocolo_cv import ENSAIOS_TESTE, X_dos_alvos, carregar_dados

NAVY, BLUE, TEAL, ORANGE, GRAY, RED = "#1F3A5F", "#2E6DA4", "#2A9D8F", "#D9822B", "#8C8C8C", "#B23A48"
COR_MODO = {"interna": ORANGE, "epocas_fixas": BLUE}
ROTULO_MODO = {"interna": "Parada interna (2 ensaios reservados)", "epocas_fixas": "Épocas fixas (todos os ensaios da dobra)"}
ROTULOS = {
    "n_camadas": "Nº de camadas ocultas", "largura": "Largura da 1ª camada", "forma": "Forma (constante/afunilada)",
    "activation": "Função de ativação", "use_layer_norm": "LayerNorm", "dropout_rate": "Dropout",
    "lr": "Taxa de aprendizado", "weight_decay": "Weight decay", "batch_size": "Tamanho do lote",
    "modo_parada": "Modo de parada", "patience": "Paciência", "max_epochs_interna": "Épocas máx. (parada interna)",
    "max_epochs_fixas": "Épocas (fixas)",
}
TETO_RMSE = 0.0142  # X_Zn dos próprios alvos ν, 13 ensaios de treino (Fase A)


def estilo() -> None:
    plt.rcParams.update({
        "font.family": "Arial", "font.size": 10, "axes.labelsize": 11, "axes.titlesize": 12,
        "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 9,
        "savefig.dpi": 300, "savefig.bbox": "tight",
    })


def salvar(fig, nome: str) -> None:
    fig.savefig(OUT / f"{nome}.png", dpi=300)
    fig.savefig(OUT / f"{nome}.pdf", dpi=300)
    plt.close(fig)


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["epocas"] = df["params_max_epochs_interna"].fillna(df["params_max_epochs_fixas"])
    return df


def fig_historico(df: pd.DataFrame, v1: float) -> None:
    comp = df[df["state"] == "COMPLETE"].sort_values("number")
    pod = df[df["state"] == "PRUNED"]
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.scatter(comp["number"], comp["value"], s=18, color=BLUE, alpha=0.75, label="Tentativa completa")
    if len(pod):
        ult = [max(v.values()) if isinstance(v, dict) and v else np.nan for v in pod["iv"]]
        ax.scatter(pod["number"], ult, s=16, marker="x", color=GRAY, alpha=0.7, label="Tentativa podada (último valor parcial)")
    melhor = comp["value"].cummin()
    ax.step(comp["number"], melhor, where="post", color=NAVY, lw=2, label="Melhor até o momento")
    ax.axhline(v1, color=ORANGE, ls="--", lw=1.4, label=f"v1 no protocolo novo ({v1:.3f})")
    ax.axhline(TETO_RMSE, color=TEAL, ls=":", lw=1.6, label=f"Teto: alvos $\\nu$ ({TETO_RMSE:.4f})")
    ax.set_yscale("log")
    ax.set_xlabel("Número da tentativa")
    ax.set_ylabel("RMSE de $X_{Zn}$ fora da dobra (–)")
    ax.grid(ls="--", alpha=0.5, which="both")
    ax.legend(loc="upper right", ncol=2)
    fig.tight_layout()
    salvar(fig, "fig_fb_01_historico_busca")


def fig_importancia(imp: Dict[str, float]) -> None:
    itens = sorted(imp.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.barh([ROTULOS.get(k, k) for k, _ in itens], [v for _, v in itens], color=BLUE, edgecolor="black")
    for i, (_, v) in enumerate(itens):
        ax.text(v + 0.005, i, f"{v:.2f}", va="center", fontsize=9)
    ax.set_xlabel("Importância relativa (fANOVA, soma = 1)")
    ax.grid(axis="x", ls="--", alpha=0.5)
    fig.tight_layout()
    salvar(fig, "fig_fb_02_importancia_hiperparametros")


def fig_fatias(df: pd.DataFrame) -> None:
    comp = df[df["state"] == "COMPLETE"]
    paineis = [("params_lr", "Taxa de aprendizado", True), ("params_weight_decay", "Weight decay", True),
               ("params_largura", "Largura da 1ª camada", True), ("epocas", "Épocas (máximas ou fixas)", True),
               ("params_batch_size", "Tamanho do lote", True), ("params_dropout_rate", "Dropout", False)]
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), sharey=True)
    for ax, (col, rot, logx) in zip(axes.ravel(), paineis):
        for modo, g in comp.groupby("params_modo_parada"):
            ax.scatter(g[col], g["value"], s=16, alpha=0.7, color=COR_MODO[modo], label=ROTULO_MODO[modo])
        if logx:
            ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel(rot)
        ax.grid(ls="--", alpha=0.45, which="both")
    for ax in axes[:, 0]:
        ax.set_ylabel("RMSE de $X_{Zn}$ fora da dobra (–)")
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    salvar(fig, "fig_fb_03_fatias_hiperparametros")


def fig_categoricos(df: pd.DataFrame) -> None:
    comp = df[df["state"] == "COMPLETE"]
    paineis = [("params_modo_parada", "Modo de parada", lambda v: ROTULO_MODO[v].split(" (")[0]),
               ("params_activation", "Função de ativação", str),
               ("params_use_layer_norm", "LayerNorm", lambda v: "com" if v else "sem"),
               ("params_n_camadas", "Nº de camadas ocultas", lambda v: str(int(v)))]
    fig, axes = plt.subplots(1, 4, figsize=(15, 4.6), sharey=True)
    for ax, (col, rot, fmt) in zip(axes, paineis):
        cats = sorted(comp[col].dropna().unique(), key=str)
        dados = [comp.loc[comp[col] == c, "value"].values for c in cats]
        bp = ax.boxplot(dados, patch_artist=True, widths=0.55, showfliers=False, medianprops={"color": NAVY, "lw": 1.6})
        for patch in bp["boxes"]:
            patch.set(facecolor=BLUE, alpha=0.35)
        for i, d in enumerate(dados, start=1):
            ax.scatter(np.random.default_rng(i).normal(i, 0.06, len(d)), d, s=9, color=NAVY, alpha=0.5)
        ax.set_xticks(range(1, len(cats) + 1), [f"{fmt(c)}\n(n={len(d)})" for c, d in zip(cats, dados)])
        ax.set_title(rot)
        ax.set_yscale("log")
        ax.grid(axis="y", ls="--", alpha=0.5, which="both")
    axes[0].set_ylabel("RMSE de $X_{Zn}$ fora da dobra (–)")
    fig.tight_layout()
    salvar(fig, "fig_fb_04_hiperparametros_categoricos")


def rotulo_config(nome: str, cfg: dict) -> str:
    if nome.startswith("v1"):
        return "v1\n[64, 32] GELU\nparada interna"
    modo = "épocas fixas" if cfg["modo_parada"] == "epocas_fixas" else "parada interna"
    return f"{nome.replace('Tentativa', 'Tent.')}\n{cfg['hidden_dims']} {cfg['activation']}\n{modo}, {cfg['max_epochs']} ép."


def fig_finalistas(ps: pd.DataFrame, resumo: pd.DataFrame) -> None:
    ordem = resumo["config"].tolist()
    cfgs = {r["config"]: json.loads(r["config_json"]) for _, r in resumo.iterrows()}
    fig, ax = plt.subplots(figsize=(13, 5.2))
    dados = [ps.loc[ps["config"] == c, "RMSE_X"].values for c in ordem]
    bp = ax.boxplot(dados, patch_artist=True, widths=0.55, showfliers=False, medianprops={"color": NAVY, "lw": 1.6})
    for patch, c in zip(bp["boxes"], ordem):
        esc = bool(resumo.loc[resumo["config"] == c, "escolhida"].iloc[0])
        patch.set(facecolor=ORANGE if c.startswith("v1") else (TEAL if esc else BLUE), alpha=0.55)
    for i, d in enumerate(dados, start=1):
        ax.scatter(np.random.default_rng(i).normal(i, 0.05, len(d)), d, s=14, color=NAVY, alpha=0.7, zorder=3)
        ax.text(i, np.max(d) * 1.04, f"{np.mean(d):.4f}", ha="center", fontsize=9)
    ax.axhline(TETO_RMSE, color=TEAL, ls=":", lw=1.6, label=f"Teto: alvos $\\nu$ ({TETO_RMSE:.4f})")
    ax.set_xticks(range(1, len(ordem) + 1), [rotulo_config(c, cfgs[c]) for c in ordem], fontsize=8.5)
    ax.set_ylabel("RMSE de $X_{Zn}$ fora da dobra (–)\n10 sementes por configuração")
    ax.set_ylim(0, max(np.max(d) for d in dados) * 1.15)
    ax.grid(axis="y", ls="--", alpha=0.5)
    ax.legend(loc="upper left")
    fig.tight_layout()
    salvar(fig, "fig_fb_05_finalistas_10_sementes")


def fig_curvas(curvas: pd.DataFrame, dados, escolhida: str) -> None:
    fig, axes = plt.subplots(4, 4, figsize=(15, 12), sharex=True, sharey=True)
    for e, ax in zip(range(1, 17), axes.ravel()):
        m = dados.meta[dados.meta["ensaio"] == e].iloc[0]
        titulo = f"Ensaio {e:02d} – $C_{{A0}}$={m['CA0_mol_L']:.1f} M, $\\eta$={m['razao_molar_eta']:.1f}"
        if e in ENSAIOS_TESTE:
            ax.text(0.5, 0.5, "Teste cego\n(fora desta fase)", ha="center", va="center", transform=ax.transAxes,
                    color=GRAY, fontsize=11)
            ax.set_title(titulo, fontsize=9.5, color=GRAY)
            continue
        for nome, cor, rot in (("v1 (MLP-B, parada interna)", ORANGE, "v1"), (escolhida, BLUE, "Fase B")):
            c = curvas[(curvas["config"] == nome) & (curvas["ensaio"] == e)]
            mat = c.pivot_table(index="t_min", columns="semente", values="XZn_pred").reindex(T_CURVA)
            ax.fill_between(T_CURVA, mat.quantile(0.1, axis=1), mat.quantile(0.9, axis=1), color=cor, alpha=0.2)
            ax.plot(T_CURVA, mat.mean(axis=1), color=cor, lw=1.8, label=f"{rot} (média; faixa 10–90 % das sementes)")
        exp = dados.exp_df[dados.exp_df["ensaio"] == e]
        ax.plot(np.r_[0.0, exp["t_min"]], np.r_[0.0, exp["XZn"]], "o", color="black", ms=4.5, label="Experimental")
        ax.set_title(titulo, fontsize=9.5)
        ax.grid(ls="--", alpha=0.45)
    for ax in axes[-1]:
        ax.set_xlabel("$t$ (min)")
    for ax in axes[:, 0]:
        ax.set_ylabel("$X_{Zn}$ (–)")
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    salvar(fig, "fig_fb_06_XZn_fora_da_dobra_v1_vs_fase_b")


def fig_por_ensaio(oof: pd.DataFrame, teto: pd.DataFrame, escolhida: str) -> pd.DataFrame:
    def rmse(g):
        return np.sqrt(np.mean((g["XZn_exp"] - g["XZn_pred"]) ** 2))

    r = oof.groupby(["config", "semente", "ensaio"]).apply(rmse).rename("rmse").reset_index()
    tab = pd.DataFrame({"RMSE_X_teto": teto.groupby("ensaio").apply(rmse)})
    for nome, rot in (("v1 (MLP-B, parada interna)", "v1"), (escolhida, "fase_b")):
        g = r[r["config"] == nome].groupby("ensaio")["rmse"]
        tab[f"RMSE_X_{rot}_media"], tab[f"RMSE_X_{rot}_dp"] = g.mean(), g.std()
    fig, ax = plt.subplots(figsize=(12.5, 4.6))
    x = np.arange(len(tab))
    ax.bar(x - 0.27, tab["RMSE_X_teto"], 0.26, color=TEAL, edgecolor="black", label="Teto (alvos $\\nu$)")
    ax.bar(x, tab["RMSE_X_v1_media"], 0.26, yerr=tab["RMSE_X_v1_dp"], capsize=3, color=ORANGE, edgecolor="black",
           label="v1 (média ± dp, 10 sementes)")
    ax.bar(x + 0.27, tab["RMSE_X_fase_b_media"], 0.26, yerr=tab["RMSE_X_fase_b_dp"], capsize=3, color=BLUE,
           edgecolor="black", label="Fase B (média ± dp, 10 sementes)")
    ax.set_xticks(x, [f"{e:02d}" for e in tab.index])
    ax.set_xlabel("Ensaio de treino (avaliado quando está na dobra de validação)")
    ax.set_ylabel("RMSE de $X_{Zn}$ (–)")
    ax.grid(axis="y", ls="--", alpha=0.5)
    ax.legend(loc="upper right")
    fig.tight_layout()
    salvar(fig, "fig_fb_07_rmse_XZn_por_ensaio")
    return tab


def relatorio(df, imp, resumo, tab_ens, melhor) -> None:
    comp = df[df["state"] == "COMPLETE"].sort_values("value")
    n_pod = int((df["state"] == "PRUNED").sum())
    v1 = float(df.loc[df["number"] == 0, "value"].iloc[0])
    v1_fix = float(df.loc[df["number"] == 1, "value"].iloc[0])
    dur = pd.to_timedelta(df["duration"]).dt.total_seconds()
    txt = f"""# Fase B — Busca de hiperparâmetros com Optuna (Subetapa 3.2.6)

## Objetivo
Escolher os hiperparâmetros da MLP pelo erro que o híbrido realmente comete, o RMSE de X_Zn fora da
dobra (91 pontos experimentais t > 0 dos 13 ensaios de treino), em vez da nota em ν usada na v1.

## Como foi feito
- Amostrador TPE multivariado (Bergstra et al., 2011) do Optuna (Akiba et al., 2019), com 30 tentativas
  iniciais aleatórias, e poda pela mediana a partir da 2ª dobra (tentativas claramente piores que a
  mediana das anteriores são interrompidas).
- Cada tentativa: protocolo comum (4 dobras por ensaio × 3 sementes); teste cego intocado.
- As duas primeiras tentativas foram enfileiradas com a configuração v1: com parada interna (tentativa 0,
  RMSE {v1:.4f}, igual à Fase A) e com 350 épocas fixas usando todos os ensaios da dobra (tentativa 1,
  RMSE {v1_fix:.4f}).
- Espaço de busca: 1–4 camadas ocultas; largura da 1ª camada 8–256 (escala log), constante ou afunilada
  (metade a cada camada); ativação GELU, SiLU ou Tanh; LayerNorm com ou sem; dropout 0–0,2; taxa de
  aprendizado 1e-4 a 1e-2 (log); weight decay 1e-6 a 1e-1 (log); lote 16–256; modo de parada: parada
  interna (paciência 20–200, até 300–2000 épocas) ou número fixo de épocas (50–2000) com todos os
  ensaios da dobra no treino.
- Tentativas: {len(df)} no total ({len(comp)} completas, {n_pod} podadas); tempo de CPU somado
  {dur.sum() / 3600:.1f} h.
- Finalistas: as 5 melhores tentativas e a v1 foram reavaliadas com 10 sementes (42–51); a escolha segue
  a regra de um erro-padrão (Hastie; Tibshirani; Friedman, 2009): entre as configurações cuja média
  fica a menos de 1 erro-padrão da melhor, fica a de menos parâmetros.

## Melhores tentativas (3 sementes)
| Tentativa | RMSE X_Zn | Camadas | Ativação | LayerNorm | lr | weight decay | Lote | Modo | Épocas |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
"""
    for _, r in comp.head(10).iterrows():
        txt += (f"| {r['number']} | {r['value']:.4f} | {r['user_attrs_hidden_dims']} | {r['params_activation']} | "
                f"{r['params_use_layer_norm']} | {r['params_lr']:.2e} | {r['params_weight_decay']:.2e} | "
                f"{int(r['params_batch_size'])} | {r['params_modo_parada']} | {int(r['epocas'])} |\n")
    txt += "\n## Importância dos hiperparâmetros (fANOVA)\n| Hiperparâmetro | Importância |\n| :--- | :---: |\n"
    for k, v in sorted(imp.items(), key=lambda kv: -kv[1]):
        txt += f"| {ROTULOS.get(k, k)} | {v:.3f} |\n"
    if resumo is not None:
        txt += "\n## Finalistas (10 sementes)\n| Configuração | RMSE X_Zn (média ± dp) | R² X_Zn | Parâmetros | Dentro de 1 EP | Escolhida |\n| :--- | :---: | :---: | :---: | :---: | :---: |\n"
        for _, r in resumo.iterrows():
            txt += (f"| {r['config']} | {r['RMSE_X_media']:.4f} ± {r['RMSE_X_dp']:.4f} | {r['R2_X_media']:.4f} | "
                    f"{r['n_parametros']} | {'sim' if r['dentro_de_1_EP'] else 'não'} | {'**sim**' if r['escolhida'] else ''} |\n")
        txt += f"\nConfiguração escolhida ({melhor['origem']}):\n\n```json\n{json.dumps(melhor['config'], indent=2, ensure_ascii=False)}\n```\n"
        txt += "\n## RMSE de X_Zn por ensaio (10 sementes)\n| Ensaio | Teto | v1 | Fase B |\n| :---: | :---: | :---: | :---: |\n"
        for e, r in tab_ens.iterrows():
            txt += (f"| {e:02d} | {r['RMSE_X_teto']:.4f} | {r['RMSE_X_v1_media']:.4f} ± {r['RMSE_X_v1_dp']:.4f} | "
                    f"{r['RMSE_X_fase_b_media']:.4f} ± {r['RMSE_X_fase_b_dp']:.4f} |\n")
    med = lambda col: comp.groupby(col)["value"].median()  # noqa: E731
    mm, ma, mc = med("params_modo_parada"), med("params_activation"), med("params_n_camadas")
    txt += f"""
## Leitura dos resultados
- **Modo de parada.** A mediana do RMSE foi {mm.get('epocas_fixas', np.nan):.3f} com épocas fixas contra
  {mm.get('interna', np.nan):.3f} com parada interna. Com só 13 ensaios, reservar 2 deles para parar o treino
  custa mais do que o risco de sobreajuste que a parada evita; o número de épocas passa a ser escolhido pela
  validação cruzada.
- **Ativação e profundidade.** Medianas por ativação: GELU {ma.get('GELU', np.nan):.3f}, SiLU {ma.get('SiLU', np.nan):.3f},
  Tanh {ma.get('Tanh', np.nan):.3f}. Por número de camadas: 1 → {mc.get(1, np.nan):.3f}, 2 → {mc.get(2, np.nan):.3f},
  3 → {mc.get(3, np.nan):.3f}, 4 → {mc.get(4, np.nan):.3f}. Redes estreitas e mais profundas com Tanh foram as melhores,
  sem LayerNorm.
- **Importância (fANOVA) × diferenças categóricas.** O fANOVA mede a variação do erro dentro da região que o
  TPE efetivamente explorou. Como o amostrador abandonou cedo a parada interna, GELU/SiLU e LayerNorm
  (poucas tentativas nessas categorias), esses hiperparâmetros aparecem com importância baixa, embora as
  diferenças entre categorias sejam grandes (fig_fb_04). Dentro da região boa, o que mais mexe no erro é a
  largura, o dropout, a taxa de aprendizado, o weight decay e o número de épocas.
- **Efeito do vencedor.** A melhor tentativa teve RMSE {comp['value'].min():.4f} com 3 sementes; com 10 sementes,
  os finalistas ficaram entre {resumo['RMSE_X_media'].min() if resumo is not None else float('nan'):.4f} e
  {resumo[~resumo['config'].str.startswith('v1')]['RMSE_X_media'].max() if resumo is not None else float('nan'):.4f}.
  A diferença é esperada, porque a melhor de 400 tentativas tende a ter tido sementes favoráveis; por isso a
  escolha foi feita com 10 sementes e pela regra de um erro-padrão.
- **Limites do espaço de busca.** Quase todas as boas tentativas usam 4 camadas, o limite superior do espaço;
  o número de épocas ficou abaixo do limite de 2000.

## Figuras
- `fig_fb_01_historico_busca`: valor de cada tentativa e melhor valor acumulado.
- `fig_fb_02_importancia_hiperparametros`: importância relativa (fANOVA).
- `fig_fb_03_fatias_hiperparametros`: RMSE de X_Zn contra os hiperparâmetros contínuos, por modo de parada.
- `fig_fb_04_hiperparametros_categoricos`: distribuição do RMSE por modo de parada, ativação, LayerNorm e profundidade.
- `fig_fb_05_finalistas_10_sementes`: reavaliação dos finalistas e da v1 com 10 sementes.
- `fig_fb_06_XZn_fora_da_dobra_v1_vs_fase_b`: X_Zn(t) fora da dobra, v1 contra a configuração escolhida.
- `fig_fb_07_rmse_XZn_por_ensaio`: RMSE de X_Zn por ensaio.

## Base bibliográfica
- Busca de hiperparâmetros (aleatória e guiada por modelo): Goodfellow, Bengio e Courville (2016, seção 11.4).
- TPE: Bergstra et al. (2011) [nova]; Optuna: Akiba et al. (2019) [nova].
- Seleção por validação cruzada e regra de um erro-padrão: Hastie, Tibshirani e Friedman (2009).
- Parada antecipada e número de épocas como hiperparâmetro: Goodfellow, Bengio e Courville (2016, seção 7.8).
"""
    (OUT / "relatorio_fase_b.md").write_text(txt, encoding="utf-8")


def gerar_tudo() -> None:
    import optuna

    estilo()
    df = preparar(exportar_tentativas())
    study = carregar_estudo()
    df["iv"] = [t.intermediate_values for t in study.trials]
    imp = optuna.importance.get_param_importances(study)
    v1 = float(df.loc[df["number"] == 0, "value"].iloc[0])

    fig_historico(df, v1)
    fig_importancia(imp)
    fig_fatias(df)
    fig_categoricos(df)
    pd.DataFrame(list(imp.items()), columns=["hiperparametro", "importancia"]).to_csv(
        OUT / "tabela_fase_b_importancia.csv", index=False)

    resumo = tab_ens = melhor = None
    if (OUT / "tabela_fase_b_finalistas.csv").exists():
        dados = carregar_dados()
        resumo = pd.read_csv(OUT / "tabela_fase_b_finalistas.csv")
        ps = pd.read_csv(OUT / "finalistas_por_semente.csv")
        oof = pd.read_csv(OUT / "finalistas_oof.csv")
        curvas = pd.read_csv(OUT / "finalistas_curvas.csv")
        melhor = json.loads((OUT / "melhor_config_fase_b.json").read_text(encoding="utf-8"))
        escolhida = melhor["origem"]
        fig_finalistas(ps, resumo)
        fig_curvas(curvas, dados, escolhida)
        teto = X_dos_alvos(dados, sorted(dados.train_df["ensaio"].unique()))
        tab_ens = fig_por_ensaio(oof, teto, escolhida)
        tab_ens.to_csv(OUT / "tabela_fase_b_rmse_por_ensaio.csv")
    relatorio(df, imp, resumo, tab_ens, melhor)
    print(f"Figuras e relatório da Fase B gravados em {OUT}")
