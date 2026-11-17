"""Item 5 da Etapa 4.5 — diagnóstico: problema inverso com integração exata de δ(t).

Refaz a otimização da Etapa 2.1 em duas versões: a original (malha de 0,25 min) e uma cópia em
que δ(t) é a integral analítica da bi-exponencial. Serve para ver o que muda: δ e ν̄ ou só o valor
pontual de ν. Os alvos novos NÃO são salvos em `Base de dados/processed/` nem usados em treino.

Saídas em `Código/outputs/etapa_4_5_auditoria_serial/item_5_malha_fina_problema_inverso/`:
    parametros_inverso_malha_fina.csv            parâmetros θ nas duas integrações
    tabela_malha_025_vs_exata.csv                resumo por ensaio
    tabela_delta_e_taxa_malha_vs_exata.csv       δ e ν̄ por instante e intervalo
    fig_i5_nu_pontual_vs_taxa_media (.png e .pdf)
    relatorio_item_5.md

Uso: python problema_inverso_malha_fina.py --trabalhadores 8
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # não cria __pycache__ nas pastas do código existente

import argparse  # noqa: E402
import multiprocessing as mp  # noqa: E402
from concurrent.futures import ProcessPoolExecutor  # noqa: E402
from pathlib import Path  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import LogLocator, NullFormatter  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.optimize import minimize  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comum  # noqa: E402

for caminho in (comum.CODIGO_DIR, comum.CODIGO_DIR / "etapas" / "etapa_2_1_otimizacao_alvos_v"):
    if str(caminho) not in sys.path:
        sys.path.insert(0, str(caminho))

import otimizar_alvos_v as etapa21  # noqa: E402
from src.physics.granulometry import RosinRammlerBennet  # noqa: E402
from src.physics.pbm_batch import BatchPBMSolver  # noqa: E402

T_DENSO = np.linspace(0.25, 15.0, 60)
INSTANTES = np.array([0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 15.0])
INDICES = np.rint(INSTANTES / 0.25).astype(int) - 1
ROTULOS_INTERVALOS = ("0 a 0,5", "0,5 a 1", "1 a 2", "2 a 3", "3 a 4", "4 a 5", "5 a 15")
NOMES_PARAMETROS = ("a1", "b1", "a2", "b2", "c")
LIMITE_X_DETERMINADO = 0.99
TOLERANCIA_LIMITE = 1e-3
TOLERANCIA_REPRODUCAO_RMSE = 1e-4
COR_PONTO = "#2E6DA4"

# Cópia literal dos valores de `optimize_single_experiment` (Etapa 2.1); o teste compara com o original.
LIMITES = [(0.0, 250.0), (0.2, 8.0), (0.0, 80.0), (0.02, 4.0), (0.0, 0.03)]
PONTOS_DE_PARTIDA = [
    [20.0, 3.0, 4.0, 0.4, 0.0],
    [50.0, 5.0, 10.0, 0.8, 0.0],
    [10.0, 1.5, 2.0, 0.2, 0.0],
    [100.0, 6.0, 15.0, 1.0, 0.0],
    [35.0, 4.0, 6.0, 0.5, 0.0],
    [150.0, 7.5, 8.0, 0.3, 0.0],
]


def criar_solver() -> BatchPBMSolver:
    """Cria o solver com a mesma granulometria da Etapa 2.1."""
    return BatchPBMSolver(granulometry=RosinRammlerBennet(use_number_density_d3=True))


def perfil_exato(parametros: np.ndarray, t: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Calcula δ(t) (integral analítica desde t = 0) e |ν(t)| da bi-exponencial.

    Args:
        parametros: θ = (a1, b1, a2, b2, c).
        t: instantes (min).

    Returns:
        δ (µm) e |ν| (µm/min).
    """
    a1, b1, a2, b2, c = parametros
    taxa = a1 * np.exp(-b1 * t) + a2 * np.exp(-b2 * t) + c
    delta = (a1 / b1) * (1.0 - np.exp(-b1 * t)) + (a2 / b2) * (1.0 - np.exp(-b2 * t)) + c * t
    return delta, taxa


def perda_exata(parametros: np.ndarray, solver: BatchPBMSolver, x_exp: np.ndarray) -> float:
    """Calcula a perda da Etapa 2.1 trocando apenas a integração de δ pela forma analítica."""
    a1, b1, _, _, _ = parametros
    delta, taxa = perfil_exato(parametros, T_DENSO)
    x_pred = np.clip(solver.compute_conversion_from_delta(delta), 0.0, 1.0)[INDICES]
    ajuste = float(np.sum((x_pred - x_exp) ** 2))
    penal_cauda = 1e-4 * (float(taxa[-1]) ** 2)
    penal_delta = 1e-4 * (max(0.0, float(delta[-1]) - 140.0) ** 2)
    penal_suave = 1e-7 * (a1**2) + 1e-6 * ((b1 - 4.0) ** 2)
    return ajuste + penal_cauda + penal_delta + penal_suave


def otimizar_exato(solver: BatchPBMSolver, x_exp: np.ndarray) -> tuple[np.ndarray, float]:
    """Otimiza θ com integração exata, com os mesmos limites e pontos de partida da Etapa 2.1."""
    melhor_theta, melhor_perda = None, float("inf")
    for inicial in PONTOS_DE_PARTIDA:
        resultado = minimize(perda_exata, inicial, args=(solver, x_exp), method="L-BFGS-B", bounds=LIMITES, tol=1e-10)
        if resultado.fun < melhor_perda:
            melhor_theta, melhor_perda = resultado.x, resultado.fun
    return melhor_theta, melhor_perda


def ajustar_ensaio(argumentos: tuple[int, np.ndarray]) -> dict:
    """Ajusta um ensaio nas duas integrações (executado em processo separado)."""
    ensaio, x_exp = argumentos
    solver = criar_solver()
    theta_malha, perda_malha = etapa21.optimize_single_experiment(solver, T_DENSO, INSTANTES, x_exp)
    theta_exato, perda_ex = otimizar_exato(solver, x_exp)
    return {"ensaio": ensaio, "theta_malha": theta_malha, "theta_exato": theta_exato, "perda_malha": perda_malha, "perda_exata": perda_ex}


def parametros_no_limite(theta: np.ndarray) -> list[str]:
    """Lista os parâmetros que ficaram encostados em um limite da faixa."""
    nomes = []
    for nome, valor, (inferior, superior) in zip(NOMES_PARAMETROS, theta, LIMITES):
        margem = TOLERANCIA_LIMITE * (superior - inferior)
        if valor <= inferior + margem or valor >= superior - margem:
            nomes.append(nome)
    return nomes


def taxas_medias(delta_instantes: np.ndarray) -> np.ndarray:
    """Calcula ν̄ = Δδ/Δt nos 7 intervalos, partindo de δ(0) = 0."""
    return np.diff(np.concatenate([[0.0], delta_instantes])) / np.diff(np.concatenate([[0.0], INSTANTES]))


def comparar_ensaio(ajuste: dict, medicoes: pd.DataFrame, solver: BatchPBMSolver) -> tuple[dict, pd.DataFrame]:
    """Compara as duas integrações em um ensaio.

    Returns:
        Linha-resumo do ensaio e tabela com δ e ν̄ por instante e intervalo.
    """
    x_exp = medicoes["XZn_exp"].to_numpy()
    theta_malha, theta_exato = ajuste["theta_malha"], ajuste["theta_exato"]
    delta_malha, _, taxa_malha, x_malha = etapa21.evaluate_profiles_on_positive_grid(solver, theta_malha, T_DENSO)
    delta_exato, taxa_exata = perfil_exato(theta_exato, T_DENSO)
    x_exato = np.clip(solver.compute_conversion_from_delta(delta_exato), 0.0, 1.0)
    delta_cruzado, _ = perfil_exato(theta_malha, T_DENSO)
    x_cruzado = np.clip(solver.compute_conversion_from_delta(delta_cruzado), 0.0, 1.0)

    bom = x_exp < LIMITE_X_DETERMINADO
    d_malha, d_exato = delta_malha[INDICES], delta_exato[INDICES]
    nubar_malha, nubar_exata = taxas_medias(d_malha), taxas_medias(d_exato)
    intervalo_bom = bom & np.concatenate([[True], bom[:-1]])
    dif_delta, dif_taxa = (d_exato - d_malha)[bom], (nubar_exata - nubar_malha)[intervalo_bom]

    def relativo(novo: float, antigo: float) -> float:
        return abs(novo - antigo) / abs(antigo) if antigo != 0 else float("nan")

    resumo = {
        "ensaio": int(ajuste["ensaio"]), "eta": medicoes["eta"].iloc[0], "CA0_mol_L": medicoes["CA0_mol_L"].iloc[0],
        "RMSE_X_malha": comum.rmse(x_exp, x_malha[INDICES]), "RMSE_X_exata": comum.rmse(x_exp, x_exato[INDICES]),
        "RMSE_X_theta_malha_integrado_exato": comum.rmse(x_exp, x_cruzado[INDICES]),
        "delta_dif_rmse_um": float(np.sqrt(np.mean(dif_delta**2))), "delta_dif_max_um": float(np.abs(dif_delta).max()),
        "delta_0_5_malha_um": d_malha[0], "delta_0_5_exata_um": d_exato[0],
        "taxa_dif_rmse_um_min": float(np.sqrt(np.mean(dif_taxa**2))), "taxa_dif_max_um_min": float(np.abs(dif_taxa).max()),
        "nubar_0_0_5_malha": nubar_malha[0], "nubar_0_0_5_exata": nubar_exata[0],
        "nu_0_25_malha": taxa_malha[0], "nu_0_25_exata": taxa_exata[0], "nu_0_50_malha": taxa_malha[1], "nu_0_50_exata": taxa_exata[1],
        "mudanca_rel_delta_0_5": relativo(d_exato[0], d_malha[0]), "mudanca_rel_nubar_0_0_5": relativo(nubar_exata[0], nubar_malha[0]),
        "mudanca_rel_nu_0_25": relativo(taxa_exata[0], taxa_malha[0]), "mudanca_rel_nu_0_50": relativo(taxa_exata[1], taxa_malha[1]),
        "limites_malha": ",".join(parametros_no_limite(theta_malha)), "limites_exata": ",".join(parametros_no_limite(theta_exato)),
    }
    detalhe = pd.DataFrame({
        "ensaio": int(ajuste["ensaio"]), "t_min": INSTANTES, "intervalo_min": ROTULOS_INTERVALOS, "XZn_exp": x_exp,
        "delta_bem_determinado": bom, "delta_malha_um": d_malha, "delta_exata_um": d_exato,
        "intervalo_bem_determinado": intervalo_bom, "taxa_media_malha_um_min": nubar_malha, "taxa_media_exata_um_min": nubar_exata,
    })
    return resumo, detalhe


def conferir_reproducao(ajustes: list[dict], resumo: pd.DataFrame) -> dict[str, float]:
    """Interrompe se a malha de 0,25 min não reproduzir os resultados gravados da Etapa 2.1."""
    gravado = pd.read_csv(comum.BASE_DIR / "Base de dados" / "processed" / "parametros_otimizacao_inversa.csv").set_index("ensaio")
    diferenca_rmse = (resumo.set_index("ensaio")["RMSE_X_malha"] - gravado["RMSE"]).abs().max()
    if diferenca_rmse > TOLERANCIA_REPRODUCAO_RMSE:
        raise SystemExit(f"A malha de 0,25 min não reproduz o RMSE gravado: diferença máxima {diferenca_rmse:.2e}.")
    diferenca_theta = max(float(np.abs(np.asarray(a["theta_malha"]) - gravado.loc[a["ensaio"], list(NOMES_PARAMETROS)].to_numpy(dtype=float)).max()) for a in ajustes)
    print(f"Conferência OK: RMSE por ensaio (diferença máxima {diferenca_rmse:.1e}); parâmetros (diferença máxima {diferenca_theta:.1e}).")
    return {"rmse": float(diferenca_rmse), "theta": diferenca_theta}


def figura_parciais(resumo: pd.DataFrame, pasta: Path) -> None:
    """Desenha malha × exata para δ(0,5), ν̄(0 a 0,5), ν(0,25) e ν(0,5)."""
    comum.estilo()
    paineis = (("delta_0_5_malha_um", "delta_0_5_exata_um", "δ em 0,5 min (µm)", "mudanca_rel_delta_0_5"),
               ("nubar_0_0_5_malha", "nubar_0_0_5_exata", "$\\bar{\\nu}$ de 0 a 0,5 min (µm·min$^{-1}$)", "mudanca_rel_nubar_0_0_5"),
               ("nu_0_25_malha", "nu_0_25_exata", "ν nodal em 0,25 min (µm·min$^{-1}$)", "mudanca_rel_nu_0_25"),
               ("nu_0_50_malha", "nu_0_50_exata", "ν nodal em 0,5 min (µm·min$^{-1}$)", "mudanca_rel_nu_0_50"))
    fig, eixos = plt.subplots(2, 2, figsize=(8.8, 8.4))
    for eixo, (x_col, y_col, titulo, mudanca) in zip(eixos.ravel(), paineis):
        x, y = resumo[x_col].to_numpy(), resumo[y_col].to_numpy()
        inferior, superior = min(x.min(), y.min()) * 0.75, max(x.max(), y.max()) * 1.3
        eixo.plot([inferior, superior], [inferior, superior], color="#8C8C8C", linewidth=1.0, linestyle="--", zorder=1)
        eixo.scatter(x, y, s=46, color=COR_PONTO, edgecolor="white", linewidth=0.6, zorder=3)
        eixo.set_xscale("log")
        eixo.set_yscale("log")
        eixo.set_xlim(inferior, superior)
        eixo.set_ylim(inferior, superior)
        eixo.set_aspect("equal")
        formato = plt.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))
        for eixo_xy in (eixo.xaxis, eixo.yaxis):
            eixo_xy.set_major_locator(LogLocator(base=10, subs=(1.0, 2.0, 5.0)))
            eixo_xy.set_major_formatter(formato)
            eixo_xy.set_minor_formatter(NullFormatter())
        eixo.set_title(titulo, loc="left", fontsize=11)
        eixo.set_xlabel("Malha de 0,25 min")
        eixo.set_ylabel("Integração exata")
        eixo.grid(color="#E3E3E3", linewidth=0.7)
        eixo.set_axisbelow(True)
        eixo.spines[["top", "right"]].set_visible(False)
        mediana = f"{resumo[mudanca].median() * 100:.1f}".replace(".", ",")
        eixo.text(0.97, 0.05, f"mudança mediana: {mediana}%", transform=eixo.transAxes, ha="right", va="bottom", color="#333333", fontsize=9.5)
    fig.tight_layout()
    comum.salvar_figura(fig, pasta, "fig_i5_nu_pontual_vs_taxa_media")


def escrever_relatorio(resumo: pd.DataFrame, detalhe: pd.DataFrame, conferencia: dict[str, float], pasta: Path) -> None:
    """Escreve o relatório do item com os números calculados nesta execução."""
    v = comum.virgula
    def pct(coluna: str) -> str:
        return f"{v(float(resumo[coluna].median() * 100), 1)}% (máx. {v(float(resumo[coluna].max() * 100), 1)}%)"

    def potencia(valor: float) -> str:
        return f"{valor:.1e}".replace(".", ",").replace("e-0", " × 10^-").replace("e-", " × 10^-")

    def contar_limites(coluna: str, incluir_c: bool) -> int:
        return int(resumo[coluna].map(lambda s: any(p and (incluir_c or p != "c") for p in s.split(","))).sum())

    bons = detalhe[detalhe["delta_bem_determinado"]]
    bons_taxa = detalhe[detalhe["intervalo_bem_determinado"]]
    d_rmse = comum.rmse(bons["delta_malha_um"], bons["delta_exata_um"])
    t_rmse = comum.rmse(bons_taxa["taxa_media_malha_um_min"], bons_taxa["taxa_media_exata_um_min"])
    item_4 = pd.read_csv(comum.SAIDA_ETAPA / "item_4_taxa_efetiva" / "tabela_metricas_delta_e_taxa.csv")
    filtro_4 = (item_4["grupo"] == "Todos") & (item_4["conjunto"] == "Validação cruzada") & (item_4["modelo"] == "v2_fora_da_dobra")
    erro_4 = item_4[filtro_4].set_index("grandeza")["RMSE"]
    linhas = [
        "# Item 5 — Problema inverso com integração exata", "",
        "Gerado por `problema_inverso_malha_fina.py`. Os alvos novos não foram salvos em `Base de dados/processed/` nem usados em treino.", "",
        "## Conferência", "",
        f"A malha de 0,25 min reproduz a Etapa 2.1: diferença máxima de {potencia(conferencia['rmse'])} no RMSE por ensaio e de {potencia(conferencia['theta'])} nos parâmetros (os gravados têm 4 casas).", "",
        "## O que muda ao trocar a integração", "",
        "Mudança relativa |exata − malha|/|malha| nos 16 ensaios (mediana; máximo).", "",
        "| Grandeza | Mudança |", "| :-- | :-: |",
        f"| δ em 0,5 min | {pct('mudanca_rel_delta_0_5')} |",
        f"| ν̄ de 0 a 0,5 min | {pct('mudanca_rel_nubar_0_0_5')} |",
        f"| ν nodal em 0,25 min | {pct('mudanca_rel_nu_0_25')} |",
        f"| ν nodal em 0,5 min | {pct('mudanca_rel_nu_0_50')} |", "",
        f"Em todos os pontos bem determinados: RMSE entre as duas versões de δ = {v(d_rmse, 3)} µm ({len(bons)} pontos); de ν̄ = {v(t_rmse, 3)} µm/min ({len(bons_taxa)} intervalos). Para comparação, o erro fora da dobra da v2 (Item 4) é de {v(float(erro_4['delta']), 2)} µm em δ e {v(float(erro_4['taxa']), 2)} µm/min em ν̄.", "",
        "De 0 a 0,5 min, ν̄ é δ(0,5)/0,5; por isso a mudança relativa é a mesma nas duas primeiras linhas da tabela.", "",
        "## Reconstrução de X_Zn", "",
        f"- Malha de 0,25 min: RMSE global de {v(float(np.sqrt((resumo['RMSE_X_malha']**2).mean())))}.",
        f"- Integração exata, reajustada: RMSE global de {v(float(np.sqrt((resumo['RMSE_X_exata']**2).mean())))}.",
        f"- Parâmetros da malha integrados de forma exata, sem reajuste: RMSE global de {v(float(np.sqrt((resumo['RMSE_X_theta_malha_integrado_exato']**2).mean())))}. Mostra que θ só vale junto com a regra de integração.",
        f"- Ensaios com a1, b1, a2 ou b2 no limite da faixa: {contar_limites('limites_malha', False)} de 16 na malha e {contar_limites('limites_exata', False)} de 16 na integração exata. Contando também c, cuja faixa é estreita (0 a 0,03): {contar_limites('limites_malha', True)} e {contar_limites('limites_exata', True)} de 16.", "",
        "## Por ensaio", "",
        "| Ensaio | η | C_A0 | RMSE X malha | RMSE X exata | RMSE X θ malha + exata | Dif. δ máx. (µm) | Dif. ν̄ máx. (µm/min) | ν(0,25) malha | ν(0,25) exata | ν̄(0 a 0,5) malha | ν̄(0 a 0,5) exata | Limites malha | Limites exata |",
        "| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-- | :-- |",
    ]
    for r in resumo.sort_values("ensaio").itertuples(index=False):
        linhas.append(
            f"| {r.ensaio} | {v(r.eta, 1)} | {v(r.CA0_mol_L, 1)} | {v(r.RMSE_X_malha)} | {v(r.RMSE_X_exata)} | {v(r.RMSE_X_theta_malha_integrado_exato)} | "
            f"{v(r.delta_dif_max_um, 2)} | {v(r.taxa_dif_max_um_min, 2)} | {v(r.nu_0_25_malha, 1)} | {v(r.nu_0_25_exata, 1)} | {v(r.nubar_0_0_5_malha, 1)} | {v(r.nubar_0_0_5_exata, 1)} | "
            f"{r.limites_malha or '—'} | {r.limites_exata or '—'} |"
        )
    linhas += ["", "**Fora do escopo:** retreinar a rede com os alvos novos, o que exigiria refazer a busca, o comitê e consultar o teste cego de novo."]
    (pasta / "relatorio_item_5.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main() -> None:
    """Executa o Item 5: ajusta, confere a reprodução e compara as duas integrações."""
    analisador = argparse.ArgumentParser()
    analisador.add_argument("--trabalhadores", type=int, default=8)
    trabalhadores = analisador.parse_args().trabalhadores

    pasta = comum.pasta_saida("item_5_malha_fina_problema_inverso")
    medicoes = comum.carregar_medicoes()
    tarefas = [(int(e), g.sort_values("t_min")["XZn_exp"].to_numpy()) for e, g in medicoes.groupby("ensaio")]
    with ProcessPoolExecutor(max_workers=trabalhadores, mp_context=mp.get_context("spawn")) as executor:
        ajustes = list(executor.map(ajustar_ensaio, tarefas))

    solver = criar_solver()
    partes = [comparar_ensaio(a, medicoes[medicoes["ensaio"] == a["ensaio"]].sort_values("t_min"), solver) for a in ajustes]
    resumo = pd.DataFrame([p[0] for p in partes])
    detalhe = pd.concat([p[1] for p in partes], ignore_index=True)
    conferencia = conferir_reproducao(ajustes, resumo)

    parametros = pd.DataFrame([{"ensaio": a["ensaio"], "integracao": nome, **dict(zip(NOMES_PARAMETROS, a[chave])), "perda": a[perda]}
                               for a in ajustes for nome, chave, perda in (("malha_0_25", "theta_malha", "perda_malha"), ("exata", "theta_exato", "perda_exata"))])
    parametros.to_csv(pasta / "parametros_inverso_malha_fina.csv", index=False)
    resumo.to_csv(pasta / "tabela_malha_025_vs_exata.csv", index=False)
    detalhe.to_csv(pasta / "tabela_delta_e_taxa_malha_vs_exata.csv", index=False)
    figura_parciais(resumo, pasta)
    escrever_relatorio(resumo, detalhe, conferencia, pasta)
    print(resumo[["ensaio", "RMSE_X_malha", "RMSE_X_exata", "RMSE_X_theta_malha_integrado_exato", "mudanca_rel_delta_0_5", "mudanca_rel_nubar_0_0_5", "mudanca_rel_nu_0_25", "mudanca_rel_nu_0_50", "limites_malha", "limites_exata"]].round(4).to_string(index=False))
    print(f"Saídas em {pasta}")


if __name__ == "__main__":
    main()
