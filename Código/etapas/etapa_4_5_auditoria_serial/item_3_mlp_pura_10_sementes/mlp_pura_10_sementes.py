"""Item 3 da Etapa 4.5 — MLP pura com as mesmas 10 sementes da v2 na validação cruzada.

A MLP pura foi avaliada com 3 sementes (42 a 44) e a v2 com 10. Este script roda a configuração
já escolhida, sem nova busca, nas mesmas 4 dobras e nas sementes 42 a 51. Não usa o teste cego
e não grava nada nas pastas da Subetapa 3.2.7.

Saídas em `Código/outputs/etapa_4_5_auditoria_serial/item_3_mlp_pura_10_sementes/`:
    cv_mlp_pura_10_sementes.csv           RMSE por semente (MLP pura e v2)
    oof_mlp_pura_10_sementes.csv          previsões fora da dobra (usadas pelo Item 2)
    tabela_v2_vs_mlp_pura.csv             média, desvio, testes pareados e intervalo por ensaio
    tabela_v2_vs_mlp_pura_por_ensaio.csv  RMSE por ensaio dos dois modelos
    relatorio_item_3.md

Uso: python mlp_pura_10_sementes.py --trabalhadores 8
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # não cria __pycache__ na pasta da Subetapa 3.2.7

import argparse  # noqa: E402
import json  # noqa: E402
import multiprocessing as mp  # noqa: E402
from concurrent.futures import ProcessPoolExecutor  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comum  # noqa: E402

sys.path.insert(0, str(comum.CODIGO_DIR / "etapas" / "etapa_3_2" / "subetapa_3_2_7_mlp_puro_xzn"))
import mlp_puro_xzn as mlp327  # noqa: E402

SEMENTES_ORIGINAIS = (42, 43, 44)
SEMENTES_NOVAS = tuple(range(45, 52))
TOLERANCIA_REPRODUCAO = 5e-5
N_REPLICAS = 10_000
SEMENTE_BOOTSTRAP = 2026
MIN_SEMENTES_TESTE = 6


def treinar_sementes(sementes: tuple[int, ...], cfg: dict, dobras: list[dict], trabalhadores: int) -> pd.DataFrame:
    """Treina a MLP pura em cada dobra e devolve as previsões fora da dobra.

    Args:
        sementes: sementes de inicialização.
        cfg: configuração gravada em `config_escolhida.json`.
        dobras: as 4 dobras da validação cruzada.
        trabalhadores: número de processos.

    Returns:
        Tabela com semente, fold, ensaio, t_min, XZn_exp e XZn_pred.
    """
    tarefas = [(0, cfg, semente, dobra) for semente in sementes for dobra in dobras]
    with ProcessPoolExecutor(max_workers=trabalhadores, mp_context=mp.get_context("spawn")) as executor:
        resultados = list(executor.map(mlp327._tarefa_cv, tarefas))
    partes = [r["oof"].assign(fold=r["fold"]) for r in resultados]
    colunas = ["semente", "fold", "ensaio", "t_min", "XZn_exp", "XZn_pred"]
    return pd.concat(partes, ignore_index=True)[colunas].sort_values(["semente", "ensaio", "t_min"]).reset_index(drop=True)


def rmse_por_semente(oof: pd.DataFrame) -> pd.Series:
    """RMSE global de X_Zn fora da dobra (91 pontos) de cada semente."""
    return oof.groupby("semente")[["XZn_exp", "XZn_pred"]].apply(lambda g: comum.rmse(g["XZn_exp"], g["XZn_pred"]))


def conferir_reproducao(rmse_medio: float, oficial: float) -> None:
    """Interrompe se a média das sementes 42 a 44 não reproduzir o valor gravado."""
    if abs(rmse_medio - oficial) > TOLERANCIA_REPRODUCAO:
        raise SystemExit(f"Sementes 42 a 44 não reproduzem o valor gravado: {rmse_medio:.6f} contra {oficial:.6f}.")


def diferenca_maxima_pontual(oof: pd.DataFrame) -> float:
    """Maior diferença absoluta entre as previsões atuais e as gravadas na busca original."""
    pasta = mlp327.OUT
    melhor = int(pd.read_csv(pasta / "busca_cv_configuracoes.csv").iloc[0]["cfg"])
    gravado = pd.read_csv(pasta / "busca_cv_predicoes_fora_da_dobra.csv")
    gravado = gravado[gravado["cfg"] == melhor][["semente", "ensaio", "t_min", "XZn_pred"]]
    unido = oof.merge(gravado, on=["semente", "ensaio", "t_min"], suffixes=("", "_gravado"), validate="one_to_one")
    if len(unido) != len(oof):
        raise SystemExit("As previsões gravadas não cobrem os mesmos pontos.")
    return float((unido["XZn_pred"] - unido["XZn_pred_gravado"]).abs().max())


def matriz_sse(oof: pd.DataFrame, sementes: list[int], ensaios: list[int]) -> np.ndarray:
    """Soma dos erros quadráticos, com forma (n_sementes, n_ensaios)."""
    erro2 = (oof["XZn_exp"] - oof["XZn_pred"]) ** 2
    tabela = erro2.groupby([oof["semente"], oof["ensaio"]]).sum().unstack("ensaio")
    return tabela.loc[sementes, ensaios].to_numpy()


def bootstrap_por_ensaio(sse_a: np.ndarray, sse_b: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    """Intervalo de 95% para a diferença de RMSE médio (A − B), reamostrando ensaios."""
    n_ensaios = sse_a.shape[1]
    n_pontos = n_ensaios * comum.PONTOS_POR_ENSAIO
    pesos = rng.multinomial(n_ensaios, np.full(n_ensaios, 1 / n_ensaios), size=N_REPLICAS)
    rmse_a = np.sqrt(pesos @ sse_a.T / n_pontos).mean(axis=1)
    rmse_b = np.sqrt(pesos @ sse_b.T / n_pontos).mean(axis=1)
    return tuple(np.percentile(rmse_a - rmse_b, [2.5, 97.5]))


def comparar(rotulo: str, v2: np.ndarray, pura: np.ndarray, sse_v2: np.ndarray, sse_pura: np.ndarray, rng: np.random.Generator) -> dict:
    """Compara v2 e MLP pura em um conjunto de sementes.

    Args:
        rotulo: nome do conjunto de sementes.
        v2: RMSE da v2 por semente.
        pura: RMSE da MLP pura nas mesmas sementes.
        sse_v2: somas por semente e ensaio da v2.
        sse_pura: somas por semente e ensaio da MLP pura.
        rng: gerador de números aleatórios.

    Returns:
        Linha da tabela de comparação. A diferença é v2 − MLP pura (negativa: v2 melhor).
    """
    n = len(v2)
    diferenca = v2 - pura
    t_estat, p_t, w_estat, p_w = (np.nan, np.nan, np.nan, np.nan)
    if n >= MIN_SEMENTES_TESTE:
        t_estat, p_t = stats.ttest_rel(v2, pura)
        w_estat, p_w = stats.wilcoxon(v2, pura)
    inferior, superior = bootstrap_por_ensaio(sse_v2, sse_pura, rng)
    return {
        "sementes": rotulo, "n_sementes": n,
        "RMSE_v2_media": v2.mean(), "RMSE_v2_dp": v2.std(ddof=1), "RMSE_v2_ep": v2.std(ddof=1) / np.sqrt(n),
        "RMSE_pura_media": pura.mean(), "RMSE_pura_dp": pura.std(ddof=1), "RMSE_pura_ep": pura.std(ddof=1) / np.sqrt(n),
        "diferenca_media_v2_menos_pura": diferenca.mean(), "sementes_v2_ganha": int((diferenca < 0).sum()),
        "t_pareado": t_estat, "p_t_pareado": p_t, "W_wilcoxon": w_estat, "p_wilcoxon": p_w,
        "IC95_ensaios_inf": inferior, "IC95_ensaios_sup": superior,
        "IC_ensaios_exclui_zero": bool(inferior > 0 or superior < 0),
    }


def tabela_por_ensaio(oof_pura: pd.DataFrame, oof_v2: pd.DataFrame) -> pd.DataFrame:
    """RMSE por ensaio (média das sementes) da v2 e da MLP pura."""
    def media(oof: pd.DataFrame) -> pd.Series:
        rmse_semente = oof.groupby(["ensaio", "semente"])[["XZn_exp", "XZn_pred"]].apply(lambda g: comum.rmse(g["XZn_exp"], g["XZn_pred"]))
        return rmse_semente.groupby("ensaio").mean()

    info = comum.carregar_medicoes().drop_duplicates("ensaio").set_index("ensaio")[["eta", "CA0_mol_L"]]
    tabela = info.join(media(oof_v2).rename("RMSE_v2"), how="inner").join(media(oof_pura).rename("RMSE_mlp_pura"))
    tabela["diferenca_v2_menos_pura"] = tabela["RMSE_v2"] - tabela["RMSE_mlp_pura"]
    return tabela.reset_index()


def referencias_item_1() -> dict[str, float] | None:
    """Lê o RMSE de validação cruzada das referências do Item 1, se já existir."""
    arquivo = comum.SAIDA_ETAPA / "item_1_referencia_media_eta" / "tabela_referencias.csv"
    if not arquivo.exists():
        return None
    tabela = pd.read_csv(arquivo)
    filtro = (tabela["conjunto"] == "CV") & (tabela["ensaio"] == "global")
    return dict(zip(tabela.loc[filtro, "modelo"], tabela.loc[filtro, "RMSE"]))


def escrever_relatorio(comparacao: pd.DataFrame, por_ensaio: pd.DataFrame, reproducao: dict[str, float], pasta: Path) -> None:
    """Escreve o relatório do item com os números calculados nesta execução."""
    v = comum.virgula

    def p_texto(valor: float) -> str:
        if np.isnan(valor):
            return "—"
        return "< 0,0001" if valor < 1e-4 else v(valor, 4)

    linhas = [
        "# Item 3 — MLP pura com 10 sementes", "",
        "Gerado por `mlp_pura_10_sementes.py`. Sem nova busca e sem uso do teste cego.", "",
        "## Reprodução do valor antigo", "",
        f"- Sementes 42 a 44, RMSE médio: {v(reproducao['reproduzido'], 6)} (gravado: {v(reproducao['oficial'], 6)}).",
        f"- Maior diferença ponto a ponto contra as previsões gravadas: {reproducao['pontual']:.1e}.".replace(".", ",", 1).replace("e-", " × 10^-") + "", "",
        "## Comparação pareada (RMSE de X_Zn fora da dobra, 91 pontos)", "",
        "Diferença negativa significa v2 melhor.", "",
        "| Sementes | v2 (média ± dp) | MLP pura (média ± dp) | Diferença | Sementes em que a v2 ganha | p (t pareado) | p (Wilcoxon) | IC 95% reamostrando ensaios |",
        "| :-- | :-: | :-: | :-: | :-: | :-: | :-: | :-: |",
    ]
    for c in comparacao.itertuples(index=False):
        linhas.append(
            f"| {c.sementes} | {v(c.RMSE_v2_media)} ± {v(c.RMSE_v2_dp)} | {v(c.RMSE_pura_media)} ± {v(c.RMSE_pura_dp)} | "
            f"{v(c.diferenca_media_v2_menos_pura)} | {c.sementes_v2_ganha} de {c.n_sementes} | {p_texto(c.p_t_pareado)} | "
            f"{p_texto(c.p_wilcoxon)} | {v(c.IC95_ensaios_inf)} a {v(c.IC95_ensaios_sup)} |"
        )

    total = comparacao.iloc[0]
    if total["IC_ensaios_exclui_zero"]:
        lado = "melhor" if total["diferenca_media_v2_menos_pura"] < 0 else "pior"
        leitura_ic = f"o intervalo por ensaios não contém zero: a v2 é {lado} que a MLP pura também quando se considera a variação entre ensaios."
    else:
        leitura_ic = "o intervalo por ensaios contém zero: com 13 ensaios, a diferença entre v2 e MLP pura não é distinguível quando se considera a variação entre ensaios."
    linhas += [
        "", "## Leitura", "",
        f"- Com as 10 sementes, {leitura_ic}",
        "- Os testes pareados por semente mantêm os 13 ensaios fixos. Eles medem se a diferença supera a variação de treinamento, não se ela se repetiria com outros ensaios.",
        "- O pareamento é só pelo número da semente: as duas redes não compartilham inicialização.",
        "- As sementes 42 a 44 foram usadas para escolher a configuração da MLP pura; as sementes 45 a 51 não foram vistas nessa escolha.",
        "- A assimetria de busca permanece: cerca de 950 tentativas para a v2 e 32 configurações para a MLP pura.",
    ]
    referencias = referencias_item_1()
    if referencias:
        linhas += ["", "## Contexto: referências sem modelo (Item 1)", "",
                   f"Média por η: {v(referencias['media_eta'])}. Interpolação em C_A0: {v(referencias['interp_CA0'])}."]
    linhas += ["", "## RMSE por ensaio (média das 10 sementes)", "",
               "| Ensaio | η | C_A0 (mol/L) | v2 | MLP pura | Diferença |", "| :-: | :-: | :-: | :-: | :-: | :-: |"]
    for e in por_ensaio.itertuples(index=False):
        linhas.append(f"| {e.ensaio} | {v(e.eta, 1)} | {v(e.CA0_mol_L, 1)} | {v(e.RMSE_v2)} | {v(e.RMSE_mlp_pura)} | {v(e.diferenca_v2_menos_pura)} |")
    (pasta / "relatorio_item_3.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main() -> None:
    """Executa o Item 3: confere a reprodução, completa as sementes e compara com a v2."""
    argumentos = argparse.ArgumentParser()
    argumentos.add_argument("--trabalhadores", type=int, default=8)
    trabalhadores = argumentos.parse_args().trabalhadores

    pasta = comum.pasta_saida("item_3_mlp_pura_10_sementes")
    escolhida = json.loads((mlp327.OUT / "config_escolhida.json").read_text(encoding="utf-8"))
    dobras = comum.carregar_dobras()

    oof_originais = treinar_sementes(SEMENTES_ORIGINAIS, escolhida["config"], dobras, trabalhadores)
    reproduzido = float(rmse_por_semente(oof_originais).mean())
    conferir_reproducao(reproduzido, float(escolhida["RMSE_cv_medio"]))
    reproducao = {"reproduzido": reproduzido, "oficial": float(escolhida["RMSE_cv_medio"]), "pontual": diferenca_maxima_pontual(oof_originais)}
    print(f"Reprodução OK: {reproduzido:.6f} (gravado {reproducao['oficial']:.6f}); maior diferença pontual {reproducao['pontual']:.2e}.")

    oof_pura = pd.concat([oof_originais, treinar_sementes(SEMENTES_NOVAS, escolhida["config"], dobras, trabalhadores)], ignore_index=True)
    oof_v2 = comum.carregar_oof_v2()
    rmse_pura, rmse_v2 = rmse_por_semente(oof_pura), rmse_por_semente(oof_v2)
    ensaios = sorted(int(e) for e in oof_v2["ensaio"].unique())

    rng = np.random.default_rng(SEMENTE_BOOTSTRAP)
    linhas = []
    for rotulo, sementes in (("42 a 51 (todas)", list(range(42, 52))),
                             ("42 a 44 (usadas na escolha)", list(SEMENTES_ORIGINAIS)),
                             ("45 a 51 (não vistas)", list(SEMENTES_NOVAS))):
        linhas.append(comparar(rotulo, rmse_v2.loc[sementes].to_numpy(), rmse_pura.loc[sementes].to_numpy(),
                               matriz_sse(oof_v2, sementes, ensaios), matriz_sse(oof_pura, sementes, ensaios), rng))
    comparacao = pd.DataFrame(linhas)
    por_ensaio = tabela_por_ensaio(oof_pura, oof_v2)

    oof_pura.to_csv(pasta / "oof_mlp_pura_10_sementes.csv", index=False)
    pd.DataFrame({"semente": rmse_pura.index, "RMSE_mlp_pura": rmse_pura.to_numpy(), "RMSE_v2": rmse_v2.loc[rmse_pura.index].to_numpy()}).to_csv(
        pasta / "cv_mlp_pura_10_sementes.csv", index=False)
    comparacao.to_csv(pasta / "tabela_v2_vs_mlp_pura.csv", index=False)
    por_ensaio.to_csv(pasta / "tabela_v2_vs_mlp_pura_por_ensaio.csv", index=False)
    escrever_relatorio(comparacao, por_ensaio, reproducao, pasta)
    print(comparacao.T.to_string())
    print(f"Saídas em {pasta}")


if __name__ == "__main__":
    main()
