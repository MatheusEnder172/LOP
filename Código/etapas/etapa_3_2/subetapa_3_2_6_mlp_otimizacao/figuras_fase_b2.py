"""Figuras, tabelas e relatório da Fase B2 (busca ampliada) da Subetapa 3.2.6."""

from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from fase_b2_busca_ampliada import OUT, carregar_estudo, exportar_tentativas
from fase_b_optuna_hpo import T_CURVA
from figuras_fase_b import BLUE, GRAY, NAVY, ORANGE, TEAL, TETO_RMSE, estilo
from protocolo_cv import ENSAIOS_TESTE, X_dos_alvos, carregar_dados

PURPLE = "#6A4C93"
ROTULOS = {
    "n_camadas": "Nº de camadas ocultas", "largura": "Largura da 1ª camada", "forma": "Forma (constante/afunilada)",
    "activation": "Função de ativação", "use_layer_norm": "LayerNorm", "use_residual": "Conexões residuais",
    "inicializacao": "Inicialização", "entrada_log_t": "Entrada temporal (t ou ln t)", "dropout_rate": "Dropout",
    "lr": "Taxa de aprendizado", "weight_decay": "Weight decay", "batch_size": "Tamanho do lote",
    "max_epochs": "Épocas (fixas)",
}
NOME_V1 = "v1 (MLP-B, parada interna)"


def salvar(fig, nome: str) -> None:
    fig.savefig(OUT / f"{nome}.png", dpi=300)
    fig.savefig(OUT / f"{nome}.pdf", dpi=300)
    plt.close(fig)


def fig_historico(df: pd.DataFrame, ref_b: float) -> None:
    comp = df[df["state"] == "COMPLETE"].sort_values("number")
    pod = df[df["state"] == "PRUNED"]
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.scatter(comp["number"], comp["value"], s=18, color=BLUE, alpha=0.75, label="Tentativa completa")
    ax.step(comp["number"], comp["value"].cummin(), where="post", color=NAVY, lw=2, label="Melhor até o momento")
    ax.axhline(ref_b, color=PURPLE, ls="--", lw=1.4, label=f"Escolhida na Fase B, mesma avaliação ({ref_b:.4f})")
    ax.axhline(TETO_RMSE, color=TEAL, ls=":", lw=1.6, label=f"Teto: alvos $\\nu$ ({TETO_RMSE:.4f})")
    ax.set_yscale("log")
    ax.set_xlabel("Número da tentativa")
    ax.set_ylabel("RMSE de $X_{Zn}$ fora da dobra (–)")
    ax.grid(ls="--", alpha=0.5, which="both")
    ax.legend(loc="upper right")
    ax.set_title(f"{len(comp)} tentativas completas, {len(pod)} podadas", fontsize=10)
    fig.tight_layout()
    salvar(fig, "fig_fb2_01_historico_busca")


def fig_importancia(imp: dict) -> None:
    itens = sorted(imp.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(8, 5.2))
    ax.barh([ROTULOS.get(k, k) for k, _ in itens], [v for _, v in itens], color=BLUE, edgecolor="black")
    for i, (_, v) in enumerate(itens):
        ax.text(v + 0.005, i, f"{v:.2f}", va="center", fontsize=9)
    ax.set_xlabel("Importância relativa (fANOVA, soma = 1)")
    ax.grid(axis="x", ls="--", alpha=0.5)
    fig.tight_layout()
    salvar(fig, "fig_fb2_02_importancia_hiperparametros")


def fig_categoricos(df: pd.DataFrame) -> None:
    comp = df[df["state"] == "COMPLETE"]
    paineis = [("params_n_camadas", "Nº de camadas ocultas", lambda v: str(int(v))),
               ("params_activation", "Função de ativação", str),
               ("params_entrada_log_t", "Entrada temporal", lambda v: "ln t" if v else "t"),
               ("params_inicializacao", "Inicialização", lambda v: "Glorot" if v == "xavier" else "padrão"),
               ("params_use_residual", "Conexões residuais", lambda v: "com" if v else "sem"),
               ("params_use_layer_norm", "LayerNorm", lambda v: "com" if v else "sem")]
    fig, axes = plt.subplots(2, 3, figsize=(15, 8.5), sharey=True)
    for ax, (col, rot, fmt) in zip(axes.ravel(), paineis):
        cats = sorted(comp[col].dropna().unique(), key=lambda v: (str(type(v)), v))
        dados = [comp.loc[comp[col] == c, "value"].values for c in cats]
        bp = ax.boxplot(dados, patch_artist=True, widths=0.55, showfliers=False,
                        medianprops={"color": NAVY, "lw": 1.6})
        for patch in bp["boxes"]:
            patch.set(facecolor=BLUE, alpha=0.35)
        for i, d in enumerate(dados, start=1):
            ax.scatter(np.random.default_rng(i).normal(i, 0.06, len(d)), d, s=8, color=NAVY, alpha=0.45)
        ax.set_xticks(range(1, len(cats) + 1), [f"{fmt(c)}\n(n={len(d)})" for c, d in zip(cats, dados)])
        ax.set_title(rot)
        ax.set_yscale("log")
        ax.grid(axis="y", ls="--", alpha=0.5, which="both")
    for ax in axes[:, 0]:
        ax.set_ylabel("RMSE de $X_{Zn}$ fora da dobra (–)")
    fig.tight_layout()
    salvar(fig, "fig_fb2_03_hiperparametros_categoricos")


def fig_fatias(df: pd.DataFrame) -> None:
    comp = df[df["state"] == "COMPLETE"]
    paineis = [("params_lr", "Taxa de aprendizado", True), ("params_weight_decay", "Weight decay", True),
               ("params_largura", "Largura da 1ª camada", True), ("params_max_epochs", "Épocas (fixas)", True),
               ("params_batch_size", "Tamanho do lote", True), ("params_dropout_rate", "Dropout", False)]
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), sharey=True)
    for ax, (col, rot, logx) in zip(axes.ravel(), paineis):
        for flag, cor, lab in ((False, ORANGE, "Entrada t"), (True, BLUE, "Entrada ln t")):
            g = comp[comp["params_entrada_log_t"] == flag]
            ax.scatter(g[col], g["value"], s=15, alpha=0.65, color=cor, label=lab)
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
    salvar(fig, "fig_fb2_04_fatias_hiperparametros")


def rotulo(nome: str, cfg: dict) -> str:
    if nome == NOME_V1:
        return "v1\n[64, 32] GELU\nparada interna"
    extra = []
    if cfg.get("entrada_log_t"):
        extra.append("ln t")
    if cfg.get("use_residual"):
        extra.append("residual")
    if cfg.get("inicializacao") == "xavier":
        extra.append("Glorot")
    h = cfg["hidden_dims"]
    camadas = f"{len(h)}×{h[0]}" if len(set(h)) == 1 else str(h)
    return (f"{nome.replace('B2 – tentativa', 'B2 – tent.')}\n{camadas} {cfg['activation']}\n"
            f"{cfg['max_epochs']} ép.{(', ' + ', '.join(extra)) if extra else ''}")


def fig_finalistas(ps: pd.DataFrame, resumo: pd.DataFrame) -> None:
    resumo = resumo[resumo["config"] != NOME_V1]
    ordem = resumo["config"].tolist()
    cfgs = {r["config"]: json.loads(r["config_json"]) for _, r in resumo.iterrows()}
    fig, ax = plt.subplots(figsize=(13.5, 5.4))
    dados = [ps.loc[ps["config"] == c, "RMSE_X"].values for c in ordem]
    bp = ax.boxplot(dados, patch_artist=True, widths=0.55, showfliers=False, medianprops={"color": NAVY, "lw": 1.6})
    for patch, c in zip(bp["boxes"], ordem):
        esc = bool(resumo.loc[resumo["config"] == c, "escolhida"].iloc[0])
        patch.set(facecolor=PURPLE if c.startswith("Fase B") else (TEAL if esc else BLUE), alpha=0.55)
    # Eixo limitado pela faixa típica; sementes que divergiram são marcadas no topo com o valor
    lim = 1.35 * max(np.percentile(d, 90) for d in dados)
    for i, d in enumerate(dados, start=1):
        dentro, fora = d[d <= lim], d[d > lim]
        ax.scatter(np.random.default_rng(i).normal(i, 0.05, len(dentro)), dentro, s=14, color=NAVY, alpha=0.7, zorder=3)
        for v in fora:
            ax.annotate(f"1 semente divergiu\n({v:.3f})", xy=(i, lim * 0.985), xytext=(i, lim * 0.86), ha="center",
                        fontsize=8, color=ORANGE, arrowprops={"arrowstyle": "->", "color": ORANGE})
        ax.text(i + 0.3, np.median(d), f"média\n{np.mean(d):.4f}", ha="left", va="center", fontsize=8.5)
    ax.axhline(TETO_RMSE, color=TEAL, ls=":", lw=1.6, label=f"Teto: alvos $\\nu$ ({TETO_RMSE:.4f})")
    ax.set_xticks(range(1, len(ordem) + 1), [rotulo(c, cfgs[c]) for c in ordem], fontsize=8.3)
    ax.set_ylabel("RMSE de $X_{Zn}$ fora da dobra (–)\n10 sementes por configuração")
    ax.set_ylim(0, lim)
    ax.grid(axis="y", ls="--", alpha=0.5)
    ax.legend(loc="lower right")
    fig.tight_layout()
    salvar(fig, "fig_fb2_05_finalistas_10_sementes")


def fig_curvas(curvas: pd.DataFrame, dados, nome_b: str, escolhida: str) -> None:
    fig, axes = plt.subplots(4, 4, figsize=(15, 12), sharex=True, sharey=True)
    for e, ax in zip(range(1, 17), axes.ravel()):
        m = dados.meta[dados.meta["ensaio"] == e].iloc[0]
        titulo = f"Ensaio {e:02d} – $C_{{A0}}$={m['CA0_mol_L']:.1f} M, $\\eta$={m['razao_molar_eta']:.1f}"
        if e in ENSAIOS_TESTE:
            ax.text(0.5, 0.5, "Teste cego\n(fora desta fase)", ha="center", va="center", transform=ax.transAxes,
                    color=GRAY, fontsize=11)
            ax.set_title(titulo, fontsize=9.5, color=GRAY)
            continue
        for nome, cor, rot in ((nome_b, PURPLE, "Fase B"), (escolhida, BLUE, "Fase B2")):
            c = curvas[(curvas["config"] == nome) & (curvas["ensaio"] == e)]
            mat = c.pivot_table(index="t_min", columns="semente", values="XZn_pred").reindex(T_CURVA)
            ax.fill_between(T_CURVA, mat.quantile(0.1, axis=1), mat.quantile(0.9, axis=1), color=cor, alpha=0.2)
            ax.plot(T_CURVA, mat.mean(axis=1), color=cor, lw=1.6, label=f"{rot} (média; faixa 10–90 % das sementes)")
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
    salvar(fig, "fig_fb2_06_XZn_fora_da_dobra_fase_b_vs_b2")


def fig_por_ensaio(oof: pd.DataFrame, teto: pd.DataFrame, nome_b: str, escolhida: str) -> pd.DataFrame:
    def rmse(g):
        return np.sqrt(np.mean((g["XZn_exp"] - g["XZn_pred"]) ** 2))

    r = oof.groupby(["config", "semente", "ensaio"]).apply(rmse).rename("rmse").reset_index()
    tab = pd.DataFrame({"RMSE_X_teto": teto.groupby("ensaio").apply(rmse)})
    for nome, rot in ((nome_b, "fase_b"), (escolhida, "fase_b2")):
        g = r[r["config"] == nome].groupby("ensaio")["rmse"]
        tab[f"RMSE_X_{rot}_media"], tab[f"RMSE_X_{rot}_dp"] = g.mean(), g.std()
    fig, ax = plt.subplots(figsize=(12.5, 4.6))
    x = np.arange(len(tab))
    ax.bar(x - 0.27, tab["RMSE_X_teto"], 0.26, color=TEAL, edgecolor="black", label="Teto (alvos $\\nu$)")
    ax.bar(x, tab["RMSE_X_fase_b_media"], 0.26, yerr=tab["RMSE_X_fase_b_dp"], capsize=3, color=PURPLE,
           edgecolor="black", label="Fase B (média ± dp, 10 sementes)")
    ax.bar(x + 0.27, tab["RMSE_X_fase_b2_media"], 0.26, yerr=tab["RMSE_X_fase_b2_dp"], capsize=3, color=BLUE,
           edgecolor="black", label="Fase B2 (média ± dp, 10 sementes)")
    ax.set_xticks(x, [f"{e:02d}" for e in tab.index])
    ax.set_xlabel("Ensaio de treino (avaliado quando está na dobra de validação)")
    ax.set_ylabel("RMSE de $X_{Zn}$ (–)")
    ax.grid(axis="y", ls="--", alpha=0.5)
    ax.legend(loc="upper left")
    fig.tight_layout()
    salvar(fig, "fig_fb2_07_rmse_XZn_por_ensaio")
    return tab


def comparacao_pareada(escolhida: str) -> str:
    """Compara a escolhida com a configuração da Fase B semente a semente (mesmas 10 sementes)."""
    from scipy import stats

    p = pd.read_csv(OUT / "finalistas_por_semente.csv").pivot(index="semente", columns="config", values="RMSE_X")
    nome_b = next(c for c in p.columns if c.startswith("Fase B"))
    if escolhida == nome_b:
        return ""
    d = p[escolhida] - p[nome_b]
    return (f"\n### Comparação pareada com a Fase B (mesmas 10 sementes)\n"
            f"- Diferença média de RMSE (B2 − B): {d.mean():.4f}; a B2 foi melhor em {(d < 0).sum()} de {len(d)} sementes.\n"
            f"- Teste t pareado: p = {stats.ttest_rel(p[escolhida], p[nome_b]).pvalue:.3f}; "
            f"Wilcoxon pareado: p = {stats.wilcoxon(p[escolhida], p[nome_b]).pvalue:.3f}.\n"
            f"- Ressalva: as sementes 42–44 também foram usadas na busca das duas fases, o que favorece igualmente B e B2.\n")


def relatorio(df, imp, resumo, tab_ens, melhor, ref_b) -> None:
    comp = df[df["state"] == "COMPLETE"].sort_values("value")
    n_pod = int((df["state"] == "PRUNED").sum())
    dur = pd.to_timedelta(df["duration"]).dt.total_seconds()
    med = lambda col: comp.groupby(col)["value"].median()  # noqa: E731
    txt = f"""# Fase B2 — Busca ampliada de hiperparâmetros (Subetapa 3.2.6)

## Objetivo
A Fase B terminou com as melhores redes no limite do espaço de busca (4 camadas). A B2 verifica se redes
mais profundas e outras escolhas de projeto reduzem ainda mais o erro de X_Zn fora da dobra.

## O que mudou em relação à Fase B
- Profundidade de 2 a 8 camadas ocultas e largura de 8 a 96 (constante ou afunilada).
- Somente épocas fixas, de 200 a 4000 (a parada interna teve mediana 6 vezes pior na Fase B).
- Novas opções: conexões residuais; inicialização de Glorot (Glorot; Bengio, 2010) com o ganho de Tanh;
  entrada temporal em ln t (`KineticsMLPLogT`), que espalha melhor os primeiros minutos, onde ν é grande.
- Dropout de 0 a 0,3; o restante como na Fase B.
- As tentativas 211 (escolhida) e 354 da Fase B foram enfileiradas como tentativas 0 e 1 da B2; a
  tentativa 0 deu {ref_b:.4f}, reproduzindo o valor da Fase B no mesmo protocolo.
- Tentativas: {len(df)} ({len(comp)} completas, {n_pod} podadas); CPU somada {dur.sum() / 3600:.1f} h.

## Melhores tentativas (3 sementes)
| Tentativa | RMSE X_Zn | Camadas | Ativação | ln t | Residual | Inicialização | LayerNorm | Dropout | lr | Lote | Épocas |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for _, r in comp.head(10).iterrows():
        txt += (f"| {r['number']} | {r['value']:.4f} | {r['user_attrs_hidden_dims']} | {r['params_activation']} | "
                f"{'sim' if r['params_entrada_log_t'] else 'não'} | {'sim' if r['params_use_residual'] else 'não'} | "
                f"{r['params_inicializacao']} | {'sim' if r['params_use_layer_norm'] else 'não'} | "
                f"{r['params_dropout_rate']:.2f} | {r['params_lr']:.2e} | {int(r['params_batch_size'])} | "
                f"{int(r['params_max_epochs'])} |\n")
    txt += "\n## Medianas por categoria (tentativas completas)\n"
    for col, rot in (("params_n_camadas", "Camadas"), ("params_activation", "Ativação"),
                     ("params_entrada_log_t", "Entrada ln t"), ("params_inicializacao", "Inicialização"),
                     ("params_use_residual", "Residual"), ("params_use_layer_norm", "LayerNorm")):
        m = med(col)
        n = comp.groupby(col).size()
        txt += f"- {rot}: " + "; ".join(f"{k} → {v:.4f} (n={n[k]})" for k, v in m.items()) + "\n"
    txt += "\n## Importância dos hiperparâmetros (fANOVA)\n| Hiperparâmetro | Importância |\n| :--- | :---: |\n"
    for k, v in sorted(imp.items(), key=lambda kv: -kv[1]):
        txt += f"| {ROTULOS.get(k, k)} | {v:.3f} |\n"
    txt += ("\nObservação: o fANOVA mede a variação do erro dentro da região explorada pelo TPE; categorias pouco "
            "amostradas tendem a aparecer com importância baixa mesmo quando a diferença entre elas é grande.\n")
    if resumo is not None:
        txt += ("\n## Finalistas (10 sementes)\n| Configuração | RMSE X_Zn (média ± dp) | R² X_Zn | Parâmetros | "
                "Dentro de 1 EP | Escolhida |\n| :--- | :---: | :---: | :---: | :---: | :---: |\n")
        for _, r in resumo.iterrows():
            txt += (f"| {r['config']} | {r['RMSE_X_media']:.4f} ± {r['RMSE_X_dp']:.4f} | {r['R2_X_media']:.4f} | "
                    f"{r['n_parametros']} | {'sim' if r['dentro_de_1_EP'] else 'não'} | "
                    f"{'**sim**' if r['escolhida'] else ''} |\n")
        txt += f"\nConfiguração escolhida ({melhor['origem']}):\n\n```json\n{json.dumps(melhor['config'], indent=2, ensure_ascii=False)}\n```\n"
        txt += comparacao_pareada(melhor["origem"])
        txt += "\n## RMSE de X_Zn por ensaio (10 sementes)\n| Ensaio | Teto | Fase B | Fase B2 |\n| :---: | :---: | :---: | :---: |\n"
        for e, r in tab_ens.iterrows():
            txt += (f"| {e:02d} | {r['RMSE_X_teto']:.4f} | {r['RMSE_X_fase_b_media']:.4f} ± {r['RMSE_X_fase_b_dp']:.4f} | "
                    f"{r['RMSE_X_fase_b2_media']:.4f} ± {r['RMSE_X_fase_b2_dp']:.4f} |\n")
    txt += """
## Figuras
- `fig_fb2_01_historico_busca`: valor de cada tentativa e melhor valor acumulado.
- `fig_fb2_02_importancia_hiperparametros`: importância relativa (fANOVA).
- `fig_fb2_03_hiperparametros_categoricos`: RMSE por profundidade, ativação, entrada temporal, inicialização, residual e LayerNorm.
- `fig_fb2_04_fatias_hiperparametros`: RMSE contra os hiperparâmetros contínuos, por entrada temporal.
- `fig_fb2_05_finalistas_10_sementes`: Fase B e finalistas da B2 com 10 sementes.
- `fig_fb2_06_XZn_fora_da_dobra_fase_b_vs_b2`: X_Zn(t) fora da dobra.
- `fig_fb2_07_rmse_XZn_por_ensaio`: RMSE de X_Zn por ensaio.

## Base bibliográfica
- Busca de hiperparâmetros: Goodfellow, Bengio e Courville (2016, seção 11.4); Bergstra et al. (2011) [nova]; Akiba et al. (2019) [nova].
- Inicialização de Glorot: Glorot e Bengio (2010) [nova]. Conexões residuais: He et al. (2016) [nova].
- Seleção por validação cruzada e regra de um erro-padrão: Hastie, Tibshirani e Friedman (2009).
"""
    (OUT / "relatorio_fase_b2.md").write_text(txt, encoding="utf-8")


def gerar_tudo() -> None:
    import optuna

    estilo()
    df = exportar_tentativas()
    study = carregar_estudo()
    imp = optuna.importance.get_param_importances(study)
    ref_b = float(df.loc[df["number"] == 0, "value"].iloc[0])
    fig_historico(df, ref_b)
    fig_importancia(imp)
    fig_categoricos(df)
    fig_fatias(df)
    pd.DataFrame(list(imp.items()), columns=["hiperparametro", "importancia"]).to_csv(
        OUT / "tabela_fase_b2_importancia.csv", index=False)

    resumo = tab_ens = melhor = None
    if (OUT / "tabela_fase_b2_finalistas.csv").exists():
        dados = carregar_dados()
        resumo = pd.read_csv(OUT / "tabela_fase_b2_finalistas.csv")
        ps = pd.read_csv(OUT / "finalistas_por_semente.csv")
        oof = pd.read_csv(OUT / "finalistas_oof.csv")
        curvas = pd.read_csv(OUT / "finalistas_curvas.csv")
        melhor = json.loads((OUT / "melhor_config_fase_b2.json").read_text(encoding="utf-8"))
        nome_b = next(c for c in resumo["config"] if c.startswith("Fase B"))
        escolhida = melhor["origem"]
        if escolhida == nome_b:  # se a Fase B continuar escolhida, compara com a melhor da B2
            escolhida = next(c for c in resumo["config"] if c.startswith("B2"))
        fig_finalistas(ps, resumo)
        fig_curvas(curvas, dados, nome_b, escolhida)
        teto = X_dos_alvos(dados, sorted(dados.train_df["ensaio"].unique()))
        tab_ens = fig_por_ensaio(oof, teto, nome_b, escolhida)
        tab_ens.to_csv(OUT / "tabela_fase_b2_rmse_por_ensaio.csv")
    relatorio(df, imp, resumo, tab_ens, melhor, ref_b)
    print(f"Figuras e relatório da Fase B2 gravados em {OUT}")
