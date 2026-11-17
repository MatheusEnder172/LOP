"""Item 2 da Etapa 4.5 — onde está o erro: 0,5 min contra o patamar.

Seis das sete medições de cada ensaio estão no patamar, então o RMSE global mede quase só o
patamar. Este script separa o erro por faixa de tempo e verifica, em 0,5 min, se os modelos
reproduzem o efeito de C_A0. Não treina nada; lê as saídas dos Itens 1 e 3 e da Etapa 4.2.

Saídas em `Código/outputs/etapa_4_5_auditoria_serial/item_2_erro_inicial_vs_patamar/`:
    tabela_erro_por_faixa_de_tempo.csv        RMSE e erro com sinal por faixa, conjunto e modelo
    tabela_diferenca_v2_por_faixa.csv         v2 contra cada modelo, com intervalo por ensaio
    tabela_tendencia_CA0_em_0_5min.csv        X_Zn em 0,5 min por η e C_A0
    tabela_tendencia_CA0_resumo.csv           subida com C_A0 e erro no efeito de C_A0
    fig_i2_erro_por_faixa, fig_i2_X_0_5min_vs_CA0 (.png e .pdf)
    relatorio_item_2.md

Uso: python erro_por_faixa_de_tempo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comum  # noqa: E402

FAIXAS = ("0,5 min", "1 a 3 min", "4 a 15 min")
TODOS = "Todos"
MODELOS = ("v2", "mlp_pura", "media_eta", "interp_CA0", "fenomenologico")
ROTULO = {"v2": "v2", "mlp_pura": "MLP pura", "media_eta": "Média por η", "interp_CA0": "Interpolação em $C_{A0}$",
          "fenomenologico": "Fenomenológico"}
NOME = {**ROTULO, "interp_CA0": "Interpolação em C_A0"}
COR = {"v2": "#2E6DA4", "mlp_pura": "#E070A8", "media_eta": "#D9822B", "interp_CA0": "#2A9D8F", "fenomenologico": "#94761A"}
MARCADOR = {"v2": "o", "mlp_pura": "^", "media_eta": "s", "interp_CA0": "D", "fenomenologico": "v"}
N_REPLICAS = 10_000
SEMENTE_BOOTSTRAP = 2026
TOLERANCIA_CONFERENCIA = 1e-4
ITEM_1 = comum.SAIDA_ETAPA / "item_1_referencia_media_eta"
ITEM_3 = comum.SAIDA_ETAPA / "item_3_mlp_pura_10_sementes"
PURA_TESTE = comum.OUTPUTS / "etapa_3_2" / "subetapa_3_2_7_mlp_puro_xzn" / "predicoes_pontos_experimentais.csv"


def faixa_de_tempo(t_min: float) -> str:
    """Classifica um instante (min) em uma das três faixas de tempo."""
    if np.isclose(t_min, 0.5):
        return FAIXAS[0]
    if 1.0 <= t_min <= 3.0:
        return FAIXAS[1]
    if 4.0 <= t_min <= 15.0:
        return FAIXAS[2]
    raise ValueError(f"Instante fora das faixas: {t_min}.")


def montar_previsoes() -> pd.DataFrame:
    """Reúne, em formato longo, as previsões fora da amostra de todos os modelos.

    Returns:
        Tabela com conjunto, modelo, semente, ensaio, t_min, XZn_exp, XZn_pred e faixa.
        Modelos sem sementes (referências, fenomenológico, comitês no teste cego) têm semente 0.
    """
    for arquivo in (ITEM_1 / "previsoes_referencias.csv", ITEM_3 / "oof_mlp_pura_10_sementes.csv"):
        if not arquivo.exists():
            raise SystemExit(f"Falta a saída de um item anterior: {arquivo}.")

    referencias = pd.read_csv(ITEM_1 / "previsoes_referencias.csv").melt(
        id_vars=["conjunto", "ensaio", "t_min", "XZn_exp"], value_vars=["media_eta", "interp_CA0"],
        var_name="modelo", value_name="XZn_pred").assign(semente=0)
    fenomenologico = comum.carregar_fenomenologico().assign(modelo="fenomenologico", semente=0)
    fenomenologico["conjunto"] = np.where(fenomenologico["ensaio"].isin(comum.ENSAIOS_TESTE), "Teste cego", "CV")
    pura_teste = pd.read_csv(PURA_TESTE)
    pura_teste = pura_teste[pura_teste["ensaio"].isin(comum.ENSAIOS_TESTE)]

    partes = [
        comum.carregar_oof_v2().assign(conjunto="CV", modelo="v2"),
        pd.read_csv(ITEM_3 / "oof_mlp_pura_10_sementes.csv").assign(conjunto="CV", modelo="mlp_pura"),
        referencias, fenomenologico,
        comum.carregar_v2_teste_cego().assign(conjunto="Teste cego", modelo="v2", semente=0),
        pura_teste[["ensaio", "t_min", "XZn_exp", "XZn_pred"]].assign(conjunto="Teste cego", modelo="mlp_pura", semente=0),
    ]
    colunas = ["conjunto", "modelo", "semente", "ensaio", "t_min", "XZn_exp", "XZn_pred"]
    previsoes = pd.concat([p[colunas] for p in partes], ignore_index=True)
    previsoes["faixa"] = previsoes["t_min"].map(faixa_de_tempo)
    return previsoes


def selecionar_faixa(dados: pd.DataFrame, faixa: str) -> pd.DataFrame:
    """Devolve só as linhas da faixa pedida (ou todas, para `TODOS`)."""
    return dados if faixa == TODOS else dados[dados["faixa"] == faixa]


def erro_por_faixa(previsoes: pd.DataFrame) -> pd.DataFrame:
    """Calcula RMSE e erro médio com sinal (previsto − medido) por conjunto, faixa e modelo.

    Para modelos com sementes, os valores são a média entre as sementes.
    """
    linhas = []
    for (conjunto, modelo), dados in previsoes.groupby(["conjunto", "modelo"]):
        for faixa in (*FAIXAS, TODOS):
            parte = selecionar_faixa(dados, faixa)
            por_semente = parte.groupby("semente")
            rmse_semente = por_semente[["XZn_exp", "XZn_pred"]].apply(lambda g: comum.rmse(g["XZn_exp"], g["XZn_pred"]))
            sinal_semente = (parte["XZn_pred"] - parte["XZn_exp"]).groupby(parte["semente"]).mean()
            linhas.append({
                "conjunto": conjunto, "faixa": faixa, "modelo": modelo, "n_pontos": int(por_semente.size().iloc[0]),
                "n_sementes": len(rmse_semente), "RMSE": rmse_semente.mean(), "RMSE_dp_sementes": rmse_semente.std(ddof=1),
                "erro_medio_com_sinal": sinal_semente.mean(), "erro_medio_dp_sementes": sinal_semente.std(ddof=1),
            })
    return pd.DataFrame(linhas)


def matriz_sse(dados: pd.DataFrame, ensaios: list[int]) -> np.ndarray:
    """Soma dos erros quadráticos, com forma (n_sementes, n_ensaios)."""
    erro2 = (dados["XZn_exp"] - dados["XZn_pred"]) ** 2
    return erro2.groupby([dados["semente"], dados["ensaio"]]).sum().unstack("ensaio").reindex(columns=ensaios).to_numpy()


def bootstrap_diferenca(sse_a: np.ndarray, sse_b: np.ndarray, pontos_por_ensaio: int, rng: np.random.Generator) -> tuple[float, float]:
    """Intervalo de 95% para RMSE médio de A menos o de B, reamostrando ensaios.

    Args:
        sse_a: somas por semente e ensaio do modelo A.
        sse_b: somas por semente e ensaio do modelo B.
        pontos_por_ensaio: número de medições de cada ensaio na faixa.
        rng: gerador de números aleatórios.

    Returns:
        Limites inferior e superior do intervalo percentil.
    """
    n_ensaios = sse_a.shape[1]
    n_pontos = n_ensaios * pontos_por_ensaio
    pesos = rng.multinomial(n_ensaios, np.full(n_ensaios, 1 / n_ensaios), size=N_REPLICAS)
    rmse_a = np.sqrt(pesos @ sse_a.T / n_pontos).mean(axis=1)
    rmse_b = np.sqrt(pesos @ sse_b.T / n_pontos).mean(axis=1)
    return tuple(np.percentile(rmse_a - rmse_b, [2.5, 97.5]))


def diferencas_v2(previsoes: pd.DataFrame) -> pd.DataFrame:
    """Compara a v2 com cada modelo na validação cruzada, por faixa de tempo."""
    rng = np.random.default_rng(SEMENTE_BOOTSTRAP)
    cv = previsoes[previsoes["conjunto"] == "CV"]
    ensaios = sorted(int(e) for e in cv["ensaio"].unique())
    linhas = []
    for faixa in (*FAIXAS, TODOS):
        parte = selecionar_faixa(cv, faixa)
        pontos_por_ensaio = int(parte[parte["modelo"] == "v2"].groupby(["semente", "ensaio"]).size().iloc[0])
        n_pontos = pontos_por_ensaio * len(ensaios)
        sse_v2 = matriz_sse(parte[parte["modelo"] == "v2"], ensaios)
        rmse_v2 = np.sqrt(sse_v2.sum(axis=1) / n_pontos)
        rmse_v2_ensaio = np.sqrt(sse_v2 / pontos_por_ensaio).mean(axis=0)
        for comparador in MODELOS[1:]:
            sse_comp = matriz_sse(parte[parte["modelo"] == comparador], ensaios)
            rmse_comp = np.sqrt(sse_comp.sum(axis=1) / n_pontos)
            inferior, superior = bootstrap_diferenca(sse_v2, sse_comp, pontos_por_ensaio, rng)
            linhas.append({
                "faixa": faixa, "comparador": comparador, "n_pontos": n_pontos,
                "RMSE_v2": rmse_v2.mean(), "RMSE_comparador": rmse_comp.mean(),
                "diferenca_v2_menos_comparador": rmse_v2.mean() - rmse_comp.mean(),
                "IC95_inf": inferior, "IC95_sup": superior, "IC_exclui_zero": bool(inferior > 0 or superior < 0),
                "sementes_v2_ganha": int((rmse_v2 < rmse_comp).sum()),
                "ensaios_v2_ganha": int((rmse_v2_ensaio < np.sqrt(sse_comp / pontos_por_ensaio).mean(axis=0)).sum()),
                "n_ensaios": len(ensaios),
            })
    return pd.DataFrame(linhas)


def tabela_tendencia(previsoes: pd.DataFrame, medicoes: pd.DataFrame) -> pd.DataFrame:
    """Monta X_Zn em 0,5 min por η e C_A0: medição e previsão fora da amostra de cada modelo.

    Modelos com sementes entram pela média das previsões. As colunas `delta_*` são a diferença
    em relação ao ensaio de C_A0 = 0,1 mol/L com a mesma η.
    """
    em_05 = previsoes[np.isclose(previsoes["t_min"], 0.5)]
    medias = em_05.groupby(["ensaio", "modelo"])["XZn_pred"].mean().unstack("modelo")[list(MODELOS)]
    info = medicoes[np.isclose(medicoes["t_min"], 0.5)].set_index("ensaio")[["eta", "CA0_mol_L", "XZn_exp"]]
    tabela = info.join(medias).reset_index().sort_values(["eta", "CA0_mol_L"]).reset_index(drop=True)
    tabela["conjunto"] = np.where(tabela["ensaio"].isin(comum.ENSAIOS_TESTE), "Teste cego", "CV")
    for coluna in ("XZn_exp", *MODELOS):
        tabela[f"delta_{coluna}"] = tabela[coluna] - tabela.groupby("eta")[coluna].transform("first")
    return tabela


def resumo_tendencia(tendencia: pd.DataFrame) -> pd.DataFrame:
    """Resume, por η, a subida de X_Zn de C_A0 = 0,1 para a média de 0,5 e 1,0 mol/L.

    Inclui, para cada modelo, o erro e a correlação do desvio de X_Zn em relação à média da
    sua η (o efeito de C_A0 separado do efeito de η).
    """
    linhas = []
    fontes = ("XZn_exp", *MODELOS)
    desvios = {f: tendencia[f] - tendencia.groupby("eta")[f].transform("mean") for f in fontes}
    for fonte in fontes:
        for eta, grupo in tendencia.groupby("eta"):
            baixo = float(grupo.loc[np.isclose(grupo["CA0_mol_L"], 0.1), fonte].iloc[0])
            medio = float(grupo.loc[grupo["CA0_mol_L"].isin([0.5, 1.0]), fonte].mean())
            linhas.append({"fonte": fonte, "eta": eta, "subida": medio - baixo})
    resumo = pd.DataFrame(linhas).pivot(index="fonte", columns="eta", values="subida").loc[list(fontes)]
    resumo.columns = [f"subida_eta_{e:g}" for e in resumo.columns]
    resumo["eta_com_mesmo_sinal_da_medicao"] = [
        int((np.sign(resumo.loc[f].to_numpy()) == np.sign(resumo.loc["XZn_exp"].to_numpy())).sum()) for f in fontes
    ]
    resumo["RMSE_desvio_CA0"] = [comum.rmse(desvios["XZn_exp"], desvios[f]) for f in fontes]
    resumo["correlacao_desvio_CA0"] = [float(np.corrcoef(desvios["XZn_exp"], desvios[f])[0, 1]) for f in fontes]
    return resumo.reset_index()


def razao_inicial_final(medicoes: pd.DataFrame) -> float:
    """Média, entre os ensaios, de X_Zn(0,5 min) dividida por X_Zn(15 min)."""
    tabela = medicoes.pivot(index="ensaio", columns="t_min", values="XZn_exp")
    return float((tabela[0.5] / tabela[15.0]).mean())


def figura_erro_por_faixa(erros: pd.DataFrame, pasta: Path) -> None:
    """Desenha o RMSE por faixa de tempo em dois painéis com a mesma escala."""
    comum.estilo()
    fig, eixos = plt.subplots(1, 2, figsize=(9.6, 4.5), sharey=True)
    deslocamento = dict(zip(MODELOS, np.linspace(-0.28, 0.28, len(MODELOS))))
    for eixo, conjunto in zip(eixos, ("CV", "Teste cego")):
        dados = erros[(erros["conjunto"] == conjunto) & (erros["faixa"] != TODOS)]
        for modelo in MODELOS:
            linha = dados[dados["modelo"] == modelo].set_index("faixa").loc[list(FAIXAS)]
            x = np.arange(len(FAIXAS)) + deslocamento[modelo]
            eixo.errorbar(x, linha["RMSE"], yerr=linha["RMSE_dp_sementes"].fillna(0), fmt=MARCADOR[modelo], color=COR[modelo],
                          markersize=7.5, markeredgecolor="white", markeredgewidth=0.6, elinewidth=1.2, capsize=0,
                          label=ROTULO[modelo], zorder=3)
        eixo.set_xticks(range(len(FAIXAS)), FAIXAS)
        eixo.set_xlim(-0.55, len(FAIXAS) - 0.45)
        titulo = "Validação cruzada (13 ensaios)" if conjunto == "CV" else "Teste cego (3 ensaios)"
        eixo.set_title(titulo, loc="left", fontsize=12)
        eixo.grid(axis="y", color="#E3E3E3", linewidth=0.8)
        eixo.set_axisbelow(True)
        eixo.spines[["top", "right"]].set_visible(False)
        eixo.set_xlabel("Faixa de tempo")
        for separador in (0.5, 1.5):
            eixo.axvline(separador, color="#D0D0D0", linewidth=0.8)
    eixos[0].set_ylim(bottom=0)
    eixos[0].set_ylabel("RMSE de $X_{Zn}$ (−)")
    eixos[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.2f}".replace(".", ",")))
    identificadores, rotulos = eixos[0].get_legend_handles_labels()
    fig.legend(identificadores, rotulos, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.5, -0.07))
    comum.salvar_figura(fig, pasta, "fig_i2_erro_por_faixa")


def figura_tendencia(tendencia: pd.DataFrame, pasta: Path) -> None:
    """Desenha X_Zn em 0,5 min contra C_A0, um painel por η, com o mesmo intervalo de eixo."""
    comum.estilo()
    fig, eixos = plt.subplots(2, 2, figsize=(9.2, 6.6), sharex=True)
    colunas = ["XZn_exp", *MODELOS]
    faixa_maxima = max(g[colunas].to_numpy().max() - g[colunas].to_numpy().min() for _, g in tendencia.groupby("eta"))
    estilo_linha = {"v2": "-", "mlp_pura": "--", "media_eta": ":", "interp_CA0": "-.", "fenomenologico": (0, (5, 1.5))}
    for eixo, (eta, grupo) in zip(eixos.ravel(), tendencia.groupby("eta")):
        for modelo in MODELOS:
            eixo.plot(grupo["CA0_mol_L"], grupo[modelo], linestyle=estilo_linha[modelo], color=COR[modelo], linewidth=1.8,
                      marker=MARCADOR[modelo], markersize=5, label=ROTULO[modelo], zorder=2)
        cv, teste = grupo[grupo["conjunto"] == "CV"], grupo[grupo["conjunto"] == "Teste cego"]
        eixo.scatter(cv["CA0_mol_L"], cv["XZn_exp"], s=62, color="#1F3A5F", zorder=4, label="Medição (validação cruzada)")
        eixo.scatter(teste["CA0_mol_L"], teste["XZn_exp"], s=62, facecolor="white", edgecolor="#1F3A5F", linewidth=1.6, zorder=4,
                     label="Medição (teste cego)")
        centro = (grupo[colunas].to_numpy().max() + grupo[colunas].to_numpy().min()) / 2
        eixo.set_ylim(centro - 0.56 * faixa_maxima, centro + 0.56 * faixa_maxima)
        eixo.set_title(f"η = {eta:.1f}".replace(".", ","), loc="left", fontsize=12)
        eixo.grid(color="#E3E3E3", linewidth=0.8)
        eixo.set_axisbelow(True)
        eixo.spines[["top", "right"]].set_visible(False)
        eixo.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.2f}".replace(".", ",")))
        eixo.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ",")))
    for eixo in eixos[1]:
        eixo.set_xlabel("$C_{A0}$ (mol·L$^{-1}$)")
    for eixo in eixos[:, 0]:
        eixo.set_ylabel("$X_{Zn}$ em 0,5 min (−)")
    identificadores, rotulos = eixos[0, 0].get_legend_handles_labels()
    fig.legend(identificadores, rotulos, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.05))
    fig.tight_layout()
    comum.salvar_figura(fig, pasta, "fig_i2_X_0_5min_vs_CA0")


def conferir(erros: pd.DataFrame) -> None:
    """Interrompe se o erro de todos os pontos não reproduzir os valores já calculados."""
    def valor(conjunto: str, modelo: str) -> float:
        filtro = (erros["conjunto"] == conjunto) & (erros["faixa"] == TODOS) & (erros["modelo"] == modelo)
        return float(erros.loc[filtro, "RMSE"].iloc[0])

    fase_e = pd.read_csv(comum.SUB326 / "fase_e" / "tabela_fase_e_metricas_XZn.csv").set_index(["Particao", "Modelo"])["RMSE"]
    item_1 = pd.read_csv(ITEM_1 / "tabela_referencias.csv")
    item_1 = item_1[item_1["ensaio"] == "global"].set_index(["conjunto", "modelo"])["RMSE"]
    item_3 = pd.read_csv(ITEM_3 / "tabela_v2_vs_mlp_pura.csv").iloc[0]["RMSE_pura_media"]
    esperados = {
        ("CV", "v2"): comum.valor_oficial_cv_v2(), ("Teste cego", "v2"): comum.valor_oficial_teste_v2(),
        ("CV", "fenomenologico"): fase_e[("Treino", "Fenomenológico puro")],
        ("Teste cego", "fenomenologico"): fase_e[("Teste cego", "Fenomenológico puro")],
        ("CV", "mlp_pura"): item_3, ("CV", "media_eta"): item_1[("CV", "media_eta")],
        ("CV", "interp_CA0"): item_1[("CV", "interp_CA0")], ("Teste cego", "media_eta"): item_1[("Teste cego", "media_eta")],
        ("Teste cego", "interp_CA0"): item_1[("Teste cego", "interp_CA0")],
    }
    for (conjunto, modelo), esperado in esperados.items():
        if abs(valor(conjunto, modelo) - float(esperado)) > TOLERANCIA_CONFERENCIA:
            raise SystemExit(f"{modelo} em {conjunto} não confere: {valor(conjunto, modelo)} contra {esperado}.")
    print(f"Conferência OK: {len(esperados)} valores globais reproduzidos.")


def escrever_relatorio(erros: pd.DataFrame, diferencas: pd.DataFrame, tendencia: pd.DataFrame, resumo: pd.DataFrame, razao: float, pasta: Path) -> None:
    """Escreve o relatório do item com os números calculados nesta execução."""
    v = comum.virgula
    linhas = [
        "# Item 2 — Onde está o erro: 0,5 min contra o patamar", "",
        "Gerado por `erro_por_faixa_de_tempo.py`. Nenhum modelo foi treinado e nenhuma escolha foi feita com o teste cego.", "",
        f"Em 0,5 min a conversão medida já é, em média, {razao * 100:.0f}% da conversão em 15 min.", "",
        "## Erro por faixa de tempo", "",
        "RMSE de X_Zn; entre parênteses, o erro médio com sinal (previsto − medido). Modelos com sementes: média das 10 sementes.", "",
    ]
    for conjunto, titulo in (("CV", "Validação cruzada (13 ensaios)"), ("Teste cego", "Teste cego (3 ensaios; só descritivo)")):
        linhas += [f"### {titulo}", "", "| Faixa | n | " + " | ".join(NOME[m] for m in MODELOS) + " |", "| :-- | :-: |" + " :-: |" * len(MODELOS)]
        dados = erros[erros["conjunto"] == conjunto]
        for faixa in (*FAIXAS, TODOS):
            parte = dados[dados["faixa"] == faixa].set_index("modelo")
            celulas = [f"{v(parte.loc[m, 'RMSE'])} ({v(parte.loc[m, 'erro_medio_com_sinal'])})" for m in MODELOS]
            linhas.append(f"| {faixa} | {int(parte['n_pontos'].iloc[0])} | " + " | ".join(celulas) + " |")
        linhas.append("")

    linhas += [
        "## A v2 ganha em 0,5 min?", "",
        "Validação cruzada. Diferença negativa significa v2 melhor. O intervalo reamostra os 13 ensaios.", "",
        "| Faixa | Comparador | RMSE v2 | RMSE comparador | Diferença | IC 95% | Sementes em que a v2 ganha | Ensaios em que a v2 ganha |",
        "| :-- | :-- | :-: | :-: | :-: | :-: | :-: | :-: |",
    ]
    for d in diferencas.itertuples(index=False):
        linhas.append(f"| {d.faixa} | {NOME[d.comparador]} | {v(d.RMSE_v2)} | {v(d.RMSE_comparador)} | {v(d.diferenca_v2_menos_comparador)} | "
                      f"{v(d.IC95_inf)} a {v(d.IC95_sup)} | {d.sementes_v2_ganha} de 10 | {d.ensaios_v2_ganha} de {d.n_ensaios} |")

    linhas += ["", "## Leitura", ""]
    for d in diferencas[diferencas["faixa"] == FAIXAS[0]].itertuples(index=False):
        if d.IC_exclui_zero:
            lado = "menor" if d.diferenca_v2_menos_comparador < 0 else "maior"
            conclusao = f"o erro da v2 em 0,5 min é {lado}, e o intervalo não contém zero."
        else:
            conclusao = "o intervalo contém zero; com 13 ensaios, não dá para distinguir os dois em 0,5 min."
        linhas.append(f"- v2 × {NOME[d.comparador]}: {conclusao}")
    linhas += [
        "- Em 0,5 min há um único ponto por ensaio (13 na validação cruzada), o que limita a precisão do intervalo.",
        "", "## Efeito de C_A0 em 0,5 min", "",
        "Previsões fora da amostra: validação cruzada nos 13 ensaios de treino e comitê congelado nos 3 de teste cego. Modelos com sementes entram pela média das previsões.", "",
        "| η | C_A0 (mol/L) | Conjunto | Medição | " + " | ".join(NOME[m] for m in MODELOS) + " |",
        "| :-: | :-: | :-- | :-: |" + " :-: |" * len(MODELOS),
    ]
    for _, t in tendencia.iterrows():
        linhas.append(f"| {v(t['eta'], 1)} | {v(t['CA0_mol_L'], 1)} | {t['conjunto']} | {v(t['XZn_exp'], 3)} | " + " | ".join(v(t[m], 3) for m in MODELOS) + " |")

    colunas_subida = [c for c in resumo.columns if c.startswith("subida_eta_")]
    cabecalho = [f"η = {c.removeprefix('subida_eta_')}".replace(".", ",") for c in colunas_subida]
    linhas += [
        "", "### Resumo do efeito de C_A0", "",
        "Subida de X_Zn de C_A0 = 0,1 para a média de 0,5 e 1,0 mol/L. O \"erro no efeito\" compara o desvio de X_Zn em relação à média da própria η.", "",
        "| Fonte | " + " | ".join(cabecalho) + " | η com o sinal da medição | Erro no efeito de C_A0 | Correlação |",
        "| :-- |" + " :-: |" * (len(colunas_subida) + 3),
    ]
    nomes = {"XZn_exp": "Medição", **NOME}
    for _, r in resumo.iterrows():
        subidas = " | ".join(v(r[c], 3) for c in colunas_subida)
        if r["fonte"] == "XZn_exp":
            linhas.append(f"| {nomes[r['fonte']]} | {subidas} | — | — | — |")
        else:
            linhas.append(f"| {nomes[r['fonte']]} | {subidas} | {int(r['eta_com_mesmo_sinal_da_medicao'])} de {len(colunas_subida)} | {v(r['RMSE_desvio_CA0'])} | {v(r['correlacao_desvio_CA0'], 2)} |")
    linhas += ["", "A média por η não tem como representar C_A0. A correlação dela fica distorcida porque cada ensaio é retirado da própria média: ensaios acima da média recebem uma previsão mais baixa."]
    (pasta / "relatorio_item_2.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main() -> None:
    """Executa o Item 2 e grava tabelas, figuras e relatório."""
    pasta = comum.pasta_saida("item_2_erro_inicial_vs_patamar")
    medicoes = comum.carregar_medicoes()
    previsoes = montar_previsoes()
    erros = erro_por_faixa(previsoes)
    conferir(erros)
    diferencas = diferencas_v2(previsoes)
    tendencia = tabela_tendencia(previsoes, medicoes)
    resumo = resumo_tendencia(tendencia)

    erros.to_csv(pasta / "tabela_erro_por_faixa_de_tempo.csv", index=False)
    diferencas.to_csv(pasta / "tabela_diferenca_v2_por_faixa.csv", index=False)
    tendencia.to_csv(pasta / "tabela_tendencia_CA0_em_0_5min.csv", index=False)
    resumo.to_csv(pasta / "tabela_tendencia_CA0_resumo.csv", index=False)
    figura_erro_por_faixa(erros, pasta)
    figura_tendencia(tendencia, pasta)
    escrever_relatorio(erros, diferencas, tendencia, resumo, razao_inicial_final(medicoes), pasta)
    print(diferencas.to_string(index=False))
    print(resumo.to_string(index=False))
    print(f"Saídas em {pasta}")


if __name__ == "__main__":
    main()
