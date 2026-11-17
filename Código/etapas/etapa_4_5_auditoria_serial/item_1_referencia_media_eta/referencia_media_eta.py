"""Item 1 da Etapa 4.5 — referências sem modelo: média por η e interpolação em C_A0.

Pergunta: a v2 prevê melhor do que a média das curvas medidas com a mesma razão molar?
Não treina nada e não escolhe nada com o teste cego.

Saídas em `Código/outputs/etapa_4_5_auditoria_serial/item_1_referencia_media_eta/`:
    tabela_referencias.csv                  RMSE por modelo, global e por ensaio
    tabela_diferenca_v2_vs_referencia.csv   diferença, intervalo por ensaio e contagem de sementes
    previsoes_referencias.csv               previsões das duas referências, ponto a ponto
    fig_i1_rmse_por_ensaio (.png e .pdf)
    relatorio_item_1.md

Uso: python referencia_media_eta.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comum  # noqa: E402

N_REPLICAS = 10_000
SEMENTE_BOOTSTRAP = 2026
TOLERANCIA_CONFERENCIA = 1e-6
COR = {"v2": "#2E6DA4", "media_eta": "#D9822B", "interp_CA0": "#2A9D8F"}
MARCADOR = {"v2": "o", "media_eta": "s", "interp_CA0": "D"}
ROTULO = {"v2": "v2", "media_eta": "Média por η", "interp_CA0": "Interpolação em $C_{A0}$"}


def prever_referencias(alvos: pd.DataFrame, treino: pd.DataFrame) -> pd.DataFrame:
    """Prevê X_Zn dos ensaios-alvo só com medições de ensaios de treino de mesma η.

    Args:
        alvos: medições a prever (ensaio, t_min, CA0_mol_L, eta, XZn_exp).
        treino: medições disponíveis, sem os ensaios-alvo.

    Returns:
        `alvos` com as colunas `media_eta` e `interp_CA0`. A interpolação é linear em
        C_A0 entre vizinhos de mesma η; só com vizinho de um lado, usa o mais próximo.

    Raises:
        ValueError: se um ensaio-alvo estiver no treino ou não houver vizinho de mesma η.
    """
    if set(alvos["ensaio"]) & set(treino["ensaio"]):
        raise ValueError("Ensaio-alvo presente no treino.")
    linhas = []
    for linha in alvos.itertuples(index=False):
        vizinhos = treino[np.isclose(treino["eta"], linha.eta) & np.isclose(treino["t_min"], linha.t_min)]
        if vizinhos.empty:
            raise ValueError(f"Sem vizinho de mesma η para o ensaio {linha.ensaio}, t = {linha.t_min}.")
        vizinhos = vizinhos.sort_values("CA0_mol_L")
        linhas.append({
            **linha._asdict(),
            "media_eta": float(vizinhos["XZn_exp"].mean()),
            "interp_CA0": float(np.interp(linha.CA0_mol_L, vizinhos["CA0_mol_L"], vizinhos["XZn_exp"])),
        })
    return pd.DataFrame(linhas)


def referencias_cv(medicoes: pd.DataFrame, dobras: list[dict]) -> pd.DataFrame:
    """Calcula as referências fora da dobra nas mesmas 4 dobras da v2."""
    partes = []
    for dobra in dobras:
        alvos = medicoes[medicoes["ensaio"].isin(dobra["val_ensaios"])]
        treino = medicoes[medicoes["ensaio"].isin(dobra["train_ensaios"])]
        partes.append(prever_referencias(alvos, treino).assign(fold=dobra["fold"], conjunto="CV"))
    return pd.concat(partes, ignore_index=True)


def referencias_teste(medicoes: pd.DataFrame) -> pd.DataFrame:
    """Calcula as referências no teste cego usando os 13 ensaios de treino."""
    alvos = medicoes[medicoes["ensaio"].isin(comum.ENSAIOS_TESTE)]
    treino = medicoes[~medicoes["ensaio"].isin(comum.ENSAIOS_TESTE)]
    return prever_referencias(alvos, treino).assign(fold=0, conjunto="Teste cego")


def sse_por_ensaio(tabela: pd.DataFrame, coluna: str, ensaios: list[int]) -> np.ndarray:
    """Soma dos erros quadráticos de cada ensaio, na ordem de `ensaios`."""
    erro2 = (tabela["XZn_exp"] - tabela[coluna]) ** 2
    return erro2.groupby(tabela["ensaio"]).sum().reindex(ensaios).to_numpy()


def bootstrap_diferenca(sse_v2: np.ndarray, sse_ref: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    """Intervalo de 95% para RMSE(v2) − RMSE(referência), reamostrando ensaios.

    Args:
        sse_v2: somas por ensaio, forma (n_sementes, n_ensaios).
        sse_ref: somas por ensaio da referência, forma (n_ensaios,).
        rng: gerador de números aleatórios.

    Returns:
        Limites inferior e superior do intervalo percentil.
    """
    n_ensaios = sse_ref.size
    n_pontos = n_ensaios * comum.PONTOS_POR_ENSAIO
    pesos = rng.multinomial(n_ensaios, np.full(n_ensaios, 1 / n_ensaios), size=N_REPLICAS)
    rmse_v2 = np.sqrt(pesos @ sse_v2.T / n_pontos).mean(axis=1)
    rmse_ref = np.sqrt(pesos @ sse_ref / n_pontos)
    return tuple(np.percentile(rmse_v2 - rmse_ref, [2.5, 97.5]))


def montar_tabela_referencias(
    cv: pd.DataFrame, teste: pd.DataFrame, oof: pd.DataFrame, curva_media: pd.DataFrame, v2_teste: pd.DataFrame,
) -> pd.DataFrame:
    """Reúne o RMSE global e por ensaio de cada modelo em formato longo."""
    info = pd.concat([cv, teste]).drop_duplicates("ensaio").set_index("ensaio")[["eta", "CA0_mol_L"]]
    linhas: list[dict] = []

    def registrar(conjunto: str, ensaio: int | str, modelo: str, valor: float, dp: float = np.nan) -> None:
        n_pontos = comum.PONTOS_POR_ENSAIO if ensaio != "global" else {"CV": 91, "Teste cego": 21}[conjunto]
        eta, ca0 = (info.loc[ensaio, "eta"], info.loc[ensaio, "CA0_mol_L"]) if ensaio != "global" else (np.nan, np.nan)
        linhas.append({"conjunto": conjunto, "ensaio": ensaio, "eta": eta, "CA0_mol_L": ca0, "n_pontos": n_pontos,
                       "modelo": modelo, "RMSE": valor, "dp_sementes": dp})

    for tabela, nome in ((cv, "CV"), (teste, "Teste cego")):
        for ref in ("media_eta", "interp_CA0"):
            registrar(nome, "global", ref, comum.rmse(tabela["XZn_exp"], tabela[ref]))
            for ensaio, grupo in tabela.groupby("ensaio"):
                registrar(nome, int(ensaio), ref, comum.rmse(grupo["XZn_exp"], grupo[ref]))

    por_semente = oof.groupby("semente")[["XZn_exp", "XZn_pred"]].apply(lambda g: comum.rmse(g["XZn_exp"], g["XZn_pred"]))
    registrar("CV", "global", "v2", float(por_semente.mean()), float(por_semente.std(ddof=1)))
    for ensaio, grupo in oof.groupby("ensaio"):
        valores = grupo.groupby("semente")[["XZn_exp", "XZn_pred"]].apply(lambda g: comum.rmse(g["XZn_exp"], g["XZn_pred"]))
        registrar("CV", int(ensaio), "v2", float(valores.mean()), float(valores.std(ddof=1)))

    registrar("CV", "global", "v2_curva_media", comum.rmse(curva_media["XZn_exp"], curva_media["XZn_pred"]))
    for ensaio, grupo in curva_media.groupby("ensaio"):
        registrar("CV", int(ensaio), "v2_curva_media", comum.rmse(grupo["XZn_exp"], grupo["XZn_pred"]))

    registrar("Teste cego", "global", "v2", comum.rmse(v2_teste["XZn_exp"], v2_teste["XZn_pred"]))
    for ensaio, grupo in v2_teste.groupby("ensaio"):
        registrar("Teste cego", int(ensaio), "v2", comum.rmse(grupo["XZn_exp"], grupo["XZn_pred"]))
    return pd.DataFrame(linhas)


def montar_tabela_diferencas(
    cv: pd.DataFrame, oof: pd.DataFrame, curva_media: pd.DataFrame, tabela: pd.DataFrame,
) -> pd.DataFrame:
    """Compara a v2 com cada referência: diferença, intervalo e contagens."""
    rng = np.random.default_rng(SEMENTE_BOOTSTRAP)
    ensaios = sorted(int(e) for e in cv["ensaio"].unique())
    sementes = sorted(oof["semente"].unique())
    cv_ord = cv.sort_values(["ensaio", "t_min"])
    sse_sementes = np.vstack([sse_por_ensaio(oof[oof["semente"] == s], "XZn_pred", ensaios) for s in sementes])
    sse_curva = sse_por_ensaio(curva_media, "XZn_pred", ensaios)[np.newaxis, :]
    rmse_sementes = np.sqrt(sse_sementes.sum(axis=1) / 91)

    def valor(conjunto: str, ensaio: int | str, modelo: str) -> float:
        filtro = (tabela["conjunto"] == conjunto) & (tabela["ensaio"] == ensaio) & (tabela["modelo"] == modelo)
        return float(tabela.loc[filtro, "RMSE"].iloc[0])

    linhas = []
    for ref in ("media_eta", "interp_CA0"):
        sse_ref = sse_por_ensaio(cv_ord, ref, ensaios)
        rmse_ref = float(np.sqrt(sse_ref.sum() / 91))
        for modelo, sse_v2 in (("v2", sse_sementes), ("v2_curva_media", sse_curva)):
            inferior, superior = bootstrap_diferenca(sse_v2, sse_ref, rng)
            rmse_v2 = valor("CV", "global", modelo)
            vence_ensaios = sum(valor("CV", e, modelo) < valor("CV", e, ref) for e in ensaios)
            linhas.append({
                "conjunto": "CV", "versao_v2": modelo, "referencia": ref, "RMSE_v2": rmse_v2, "RMSE_referencia": rmse_ref,
                "diferenca_v2_menos_ref": rmse_v2 - rmse_ref, "IC95_inf": inferior, "IC95_sup": superior,
                "IC_exclui_zero": bool(inferior > 0 or superior < 0),
                "sementes_v2_ganha": int((rmse_sementes < rmse_ref).sum()) if modelo == "v2" else np.nan,
                "ensaios_v2_ganha": vence_ensaios, "n_ensaios": len(ensaios),
            })
        rmse_v2 = valor("Teste cego", "global", "v2")
        rmse_ref_teste = valor("Teste cego", "global", ref)
        linhas.append({
            "conjunto": "Teste cego", "versao_v2": "v2", "referencia": ref, "RMSE_v2": rmse_v2, "RMSE_referencia": rmse_ref_teste,
            "diferenca_v2_menos_ref": rmse_v2 - rmse_ref_teste, "IC95_inf": np.nan, "IC95_sup": np.nan, "IC_exclui_zero": np.nan,
            "sementes_v2_ganha": np.nan,
            "ensaios_v2_ganha": sum(valor("Teste cego", e, "v2") < valor("Teste cego", e, ref) for e in comum.ENSAIOS_TESTE),
            "n_ensaios": 3,
        })
    return pd.DataFrame(linhas)


def figura_por_ensaio(tabela: pd.DataFrame, pasta: Path) -> None:
    """Desenha o RMSE por ensaio, agrupado por η e ordenado por C_A0."""
    comum.estilo()
    por_ensaio = tabela[tabela["ensaio"] != "global"].copy()
    por_ensaio["ensaio"] = por_ensaio["ensaio"].astype(int)
    ordem = por_ensaio.drop_duplicates("ensaio").sort_values(["eta", "CA0_mol_L"])
    posicao = {int(e): i for i, e in enumerate(ordem["ensaio"])}

    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    deslocamento = {"v2": -0.2, "media_eta": 0.0, "interp_CA0": 0.2}
    for modelo in ("v2", "media_eta", "interp_CA0"):
        dados = por_ensaio[por_ensaio["modelo"] == modelo]
        ax.scatter([posicao[e] + deslocamento[modelo] for e in dados["ensaio"]], dados["RMSE"], s=46,
                   marker=MARCADOR[modelo], color=COR[modelo], edgecolor="white", linewidth=0.6, label=ROTULO[modelo], zorder=3)

    rotulos = [f"{int(e)}*" if int(e) in comum.ENSAIOS_TESTE else f"{int(e)}" for e in ordem["ensaio"]]
    ax.set_xticks(range(len(ordem)), rotulos)
    ax.set_xlim(-0.6, len(ordem) - 0.4)
    ax.set_ylim(0, por_ensaio["RMSE"].max() * 1.16)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.2f}".replace(".", ",")))
    ax.set_xlabel("Ensaio (* = teste cego); dentro de cada η, em ordem crescente de $C_{A0}$")
    ax.set_ylabel("RMSE de $X_{Zn}$ (−)")
    ax.set_title("Erro por ensaio: v2 e referências sem modelo", loc="left")
    ax.grid(axis="y", color="#E3E3E3", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)

    limite_y = ax.get_ylim()[1]
    for eta, grupo in ordem.groupby("eta"):
        indices = [posicao[int(e)] for e in grupo["ensaio"]]
        ax.text(np.mean(indices), limite_y * 0.97, f"η = {eta:.1f}".replace(".", ","), ha="center", va="top", color="#444444")
        if max(indices) < len(ordem) - 1:
            ax.axvline(max(indices) + 0.5, color="#BDBDBD", linewidth=0.8)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=3, frameon=False)
    comum.salvar_figura(fig, pasta, "fig_i1_rmse_por_ensaio")


def escrever_relatorio(tabela: pd.DataFrame, diferencas: pd.DataFrame, pasta: Path) -> None:
    """Escreve o relatório do item com os números calculados nesta execução."""
    nomes = {"media_eta": "Média por η", "interp_CA0": "Interpolação em C_A0"}
    versoes = {"v2": "v2 (média das 10 sementes)", "v2_curva_media": "v2 (curva média das 10 sementes)"}
    v = comum.virgula
    linhas = [
        "# Item 1 — Referências sem modelo", "",
        "Gerado por `referencia_media_eta.py`. Nenhum modelo foi treinado e nenhuma escolha foi feita com o teste cego.", "",
        "## Diferença entre a v2 e as referências", "",
        "RMSE de X_Zn. Diferença negativa significa v2 melhor. O intervalo reamostra os 13 ensaios (10.000 réplicas).", "",
        "| Conjunto | Versão | Referência | RMSE v2 | RMSE ref. | Diferença | IC 95% | Sementes em que a v2 ganha | Ensaios em que a v2 ganha |",
        "| :-- | :-- | :-- | :-: | :-: | :-: | :-: | :-: | :-: |",
    ]
    for d in diferencas.itertuples(index=False):
        ic = f"{v(d.IC95_inf)} a {v(d.IC95_sup)}" if not np.isnan(d.IC95_inf) else "não calculado (3 ensaios)"
        sementes = f"{int(d.sementes_v2_ganha)} de 10" if not np.isnan(d.sementes_v2_ganha) else "—"
        versao = versoes[d.versao_v2] if d.conjunto == "CV" else "v2 (comitê)"
        linhas.append(f"| {d.conjunto} | {versao} | {nomes[d.referencia]} | {v(d.RMSE_v2)} | {v(d.RMSE_referencia)} | "
                      f"{v(d.diferenca_v2_menos_ref)} | {ic} | {sementes} | {d.ensaios_v2_ganha} de {d.n_ensaios} |")

    linhas += ["", "## Leitura", ""]
    for d in diferencas[diferencas["conjunto"] == "CV"].itertuples(index=False):
        if d.IC_exclui_zero:
            lado = "melhor" if d.diferenca_v2_menos_ref < 0 else "pior"
            texto = f"o intervalo não contém zero: a v2 é {lado} que a referência nesta comparação."
        else:
            texto = "o intervalo contém zero: com 13 ensaios, a v2 não é distinguível da referência nesta comparação."
        linhas.append(f"- {versoes[d.versao_v2]} × {nomes[d.referencia]}: {texto}")
    linhas += [
        "- Teste cego: 3 ensaios não sustentam um intervalo por reamostragem; a diferença é só descritiva.",
        "- A \"curva média\" tira a média de X_Zn entre as 10 sementes de cada dobra. É uma aproximação do comitê (que tira a média das taxas antes do balanço populacional), por isso não substitui a avaliação do comitê no teste cego.",
        "- O RMSE global é dominado pelo patamar (6 dos 7 pontos de cada ensaio). O Item 2 separa o ponto de 0,5 min.",
        "", "## RMSE por ensaio", "",
        "| Conjunto | Ensaio | η | C_A0 (mol/L) | v2 | Média por η | Interpolação em C_A0 |",
        "| :-- | :-: | :-: | :-: | :-: | :-: | :-: |",
    ]
    largura = tabela[tabela["ensaio"] != "global"].pivot(index=["conjunto", "ensaio", "eta", "CA0_mol_L"], columns="modelo", values="RMSE").reset_index()
    largura["ensaio"] = largura["ensaio"].astype(int)
    for l in largura.sort_values(["conjunto", "ensaio"]).itertuples(index=False):
        linhas.append(f"| {l.conjunto} | {l.ensaio} | {v(l.eta, 1)} | {v(l.CA0_mol_L, 1)} | {v(l.v2)} | {v(l.media_eta)} | {v(l.interp_CA0)} |")
    (pasta / "relatorio_item_1.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def conferir(tabela: pd.DataFrame) -> None:
    """Interrompe se os números da v2 não reproduzirem os valores já gravados."""
    filtro = (tabela["ensaio"] == "global") & (tabela["modelo"] == "v2")
    cv = float(tabela.loc[filtro & (tabela["conjunto"] == "CV"), "RMSE"].iloc[0])
    teste = float(tabela.loc[filtro & (tabela["conjunto"] == "Teste cego"), "RMSE"].iloc[0])
    if abs(cv - comum.valor_oficial_cv_v2()) > TOLERANCIA_CONFERENCIA:
        raise SystemExit(f"CV da v2 não confere: {cv} contra {comum.valor_oficial_cv_v2()}.")
    if abs(teste - comum.valor_oficial_teste_v2()) > TOLERANCIA_CONFERENCIA:
        raise SystemExit(f"Teste cego da v2 não confere: {teste} contra {comum.valor_oficial_teste_v2()}.")
    print(f"Conferência OK: CV {cv:.6f}; teste cego {teste:.6f}.")


def main() -> None:
    """Executa o Item 1 e grava tabelas, figura e relatório."""
    pasta = comum.pasta_saida("item_1_referencia_media_eta")
    medicoes = comum.carregar_medicoes()
    cv = referencias_cv(medicoes, comum.carregar_dobras())
    teste = referencias_teste(medicoes)
    oof = comum.carregar_oof_v2()
    curva_media = oof.groupby(["ensaio", "t_min"], as_index=False).agg(XZn_pred=("XZn_pred", "mean"), XZn_exp=("XZn_exp", "first"))
    v2_teste = comum.carregar_v2_teste_cego()

    tabela = montar_tabela_referencias(cv, teste, oof, curva_media, v2_teste)
    conferir(tabela)
    diferencas = montar_tabela_diferencas(cv, oof, curva_media, tabela)

    pd.concat([cv, teste], ignore_index=True).to_csv(pasta / "previsoes_referencias.csv", index=False)
    tabela.to_csv(pasta / "tabela_referencias.csv", index=False)
    diferencas.to_csv(pasta / "tabela_diferenca_v2_vs_referencia.csv", index=False)
    figura_por_ensaio(tabela[tabela["modelo"].isin(["v2", "media_eta", "interp_CA0"])], pasta)
    escrever_relatorio(tabela, diferencas, pasta)
    print(diferencas.to_string(index=False))
    print(f"Saídas em {pasta}")


if __name__ == "__main__":
    main()
