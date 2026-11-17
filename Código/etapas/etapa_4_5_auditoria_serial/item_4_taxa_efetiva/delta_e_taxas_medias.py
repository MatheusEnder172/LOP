"""Item 4 da Etapa 4.5 — o que a rede prevê: δ e taxas médias por intervalo.

O valor de ν em um nó só tem sentido junto com a regra de integração. As grandezas físicas que
os dados identificam são o encolhimento acumulado δ(t), obtido de X = g(δ), e a taxa média em
cada intervalo entre amostras, ν̄ = Δδ/Δt. Este script as calcula para a medição, para a v2 e
para o fenomenológico. Não treina nada e não altera modelos.

Saídas em `Código/outputs/etapa_4_5_auditoria_serial/item_4_taxa_efetiva/`:
    tabela_delta_exp_vs_previsto.csv      δ medido e previsto nos 112 pontos
    tabela_taxa_media_por_intervalo.csv   ν̄ medida e prevista nos 112 intervalos
    tabela_metricas_delta_e_taxa.csv      RMSE e erro com sinal por grandeza, conjunto e modelo
    tabela_pesos_quadratura.csv           peso de cada ν nodal em cada δ medido
    fig_i4_delta_16_ensaios, fig_i4_taxa_media_por_intervalo (.png e .pdf)
    relatorio_item_4.md

Uso: python delta_e_taxas_medias.py
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # não cria __pycache__ nas pastas do código existente

from pathlib import Path  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.optimize import brentq  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comum  # noqa: E402

for caminho in (comum.CODIGO_DIR, comum.CODIGO_DIR / "etapas" / "etapa_3_2" / "subetapa_3_2_6_mlp_otimizacao"):
    if str(caminho) not in sys.path:
        sys.path.insert(0, str(caminho))

from src.hybrid.serial_hybrid import SerialHybridModel  # noqa: E402
from src.physics.pbm_batch import BatchPBMSolver  # noqa: E402

T_NOS = np.linspace(0.25, 15.0, 60)
INSTANTES = np.array([0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 15.0])
INDICES_INSTANTES = np.rint(INSTANTES / 0.25).astype(int) - 1
ROTULOS_INTERVALOS = ("0 a 0,5", "0,5 a 1", "1 a 2", "2 a 3", "3 a 4", "4 a 5", "5 a 15")
LIMITE_X_DETERMINADO = 0.99
MEIA_RESOLUCAO_X = 0.005
TODOS = "Todos"
TREINO, CV, TESTE = "Treino (ajuste)", "Validação cruzada", "Teste cego"
NOME_MODELO = {"v2_comite": "v2 (comitê)", "v2_fora_da_dobra": "v2 (fora da dobra)", "fenomenologico": "Fenomenológico"}
UNIDADE = {"delta": "µm", "taxa": "µm/min"}
COR_V2, COR_FPM, COR_MEDIDA = "#2E6DA4", "#94761A", "#1F3A5F"


def inverter_g(x: float, solver: BatchPBMSolver) -> float:
    """Devolve δ (µm) tal que g(δ) = X, ou NaN se X não estiver em (0, 1).

    Args:
        x: conversão de zinco (adimensional).
        solver: resolvedor que contém a função crescente g fixada pela granulometria.
    """
    if not 0.0 < x < 1.0:
        return float("nan")
    return float(brentq(lambda d: solver.compute_conversion_from_delta(float(d)) - x, 0.0, solver.d_max, xtol=1e-7))


def taxas_por_intervalo(deltas: np.ndarray) -> np.ndarray:
    """Calcula ν̄ = Δδ/Δt nos 7 intervalos, partindo de δ(0) = 0.

    Args:
        deltas: δ (µm) nos 7 instantes experimentais; NaN onde não houver valor.

    Returns:
        Taxa média (µm/min) em cada intervalo; NaN se uma das pontas for NaN.
    """
    return np.diff(np.concatenate([[0.0], deltas])) / np.diff(np.concatenate([[0.0], INSTANTES]))


def pesos_quadratura(solver: BatchPBMSolver) -> pd.DataFrame:
    """Extrai do próprio solver o peso de cada ν nodal em cada δ medido.

    A integração é linear em ν, então cada coluna vem de um perfil unitário no nó.

    Returns:
        Tabela com t_medicao, t_no e peso (min), só com pesos não nulos.
    """
    linhas = []
    for indice, t_no in enumerate(T_NOS):
        perfil = np.zeros_like(T_NOS)
        perfil[indice] = -1.0
        deltas = solver.simulate_with_v_profile(t_eval=T_NOS, v_profile=perfil)["delta"]
        for t_medicao, posicao in zip(INSTANTES, INDICES_INSTANTES):
            if deltas[posicao] != 0.0:
                linhas.append({"t_medicao": float(t_medicao), "t_no": float(t_no), "peso": float(deltas[posicao])})
    return pd.DataFrame(linhas).sort_values(["t_medicao", "t_no"]).reset_index(drop=True)


def rotular_conjunto(ensaio: int) -> str:
    """Nomeia a partição do ensaio para o comitê congelado."""
    return TESTE if int(ensaio) in comum.ENSAIOS_TESTE else TREINO


def simular_ensaios(modelo: SerialHybridModel, solver: BatchPBMSolver, medicoes: pd.DataFrame) -> dict[int, dict]:
    """Simula comitê, membros e fenomenológico em todos os nós de cada ensaio."""
    resultados: dict[int, dict] = {}
    for ensaio, grupo in medicoes.groupby("ensaio"):
        ca0, eta = float(grupo["CA0_mol_L"].iloc[0]), float(grupo["eta"].iloc[0])
        comite = modelo.simulate(ca0=ca0, eta=eta, t_eval=T_NOS)
        membros = [SerialHybridModel(ddm_model=m, scaler_X=modelo.scaler_X, solver=modelo.solver).simulate(ca0=ca0, eta=eta, t_eval=T_NOS)
                   for m in modelo.model.membros]
        fenomenologico = solver.simulate(ca0=ca0, eta=eta, t_eval=T_NOS, alpha=0.0)
        resultados[int(ensaio)] = {
            "delta_comite": comite["delta"], "x_comite": comite["XZn"],
            "delta_membros": np.vstack([r["delta"] for r in membros]), "x_membros": np.vstack([r["XZn"] for r in membros]),
            "delta_fpm": fenomenologico["delta"], "x_fpm": fenomenologico["XZn"],
        }
    return resultados


def delta_medido(medicoes: pd.DataFrame, solver: BatchPBMSolver) -> pd.DataFrame:
    """Inverte g nas 112 medições e marca os pontos em que δ é mal determinado.

    Returns:
        `medicoes` com delta_exp_um, faixa de δ devida à resolução de X (±0,005) e bem_determinado.
    """
    tabela = medicoes.copy()
    tabela["delta_exp_um"] = [inverter_g(x, solver) for x in tabela["XZn_exp"]]
    tabela["delta_exp_inf_um"] = [inverter_g(x - MEIA_RESOLUCAO_X, solver) for x in tabela["XZn_exp"]]
    tabela["delta_exp_sup_um"] = [inverter_g(x + MEIA_RESOLUCAO_X, solver) for x in tabela["XZn_exp"]]
    tabela["bem_determinado"] = (tabela["XZn_exp"] < LIMITE_X_DETERMINADO) & tabela["delta_exp_um"].notna()
    tabela["conjunto"] = tabela["ensaio"].map(rotular_conjunto)
    return tabela


def limitar_simulacoes(simulacoes: dict[int, dict], delta_limite: float) -> dict[int, dict]:
    """Limita δ previsto a g⁻¹(0,99), acima do qual δ não é identificável por X.

    O limite vale para todos os modelos. Sem ele, o fenomenológico acumula δ depois de X chegar
    a 1 (sobra ácido, então a EDO continua) e o erro de δ passaria a medir só esse excesso.
    """
    limitadas = {}
    for ensaio, sim in simulacoes.items():
        limitadas[ensaio] = {**sim, **{chave: np.minimum(sim[chave], delta_limite) for chave in ("delta_comite", "delta_membros", "delta_fpm")}}
    return limitadas


def delta_fora_da_dobra(solver: BatchPBMSolver, delta_limite: float) -> pd.DataFrame:
    """Obtém δ fora da dobra invertendo g nas conversões previstas, com o mesmo limite de δ."""
    oof = comum.carregar_oof_v2().copy()
    invertido = pd.Series([inverter_g(x, solver) for x in oof["XZn_pred"]], index=oof.index)
    oof["delta_oof_um"] = np.minimum(invertido.fillna(delta_limite), delta_limite)
    return oof[["semente", "ensaio", "t_min", "delta_oof_um"]]


def tabela_delta(medidas: pd.DataFrame, simulacoes: dict[int, dict], oof: pd.DataFrame) -> pd.DataFrame:
    """Monta a tabela de δ medido e previsto nos instantes experimentais."""
    tabela = medidas.copy().sort_values(["ensaio", "t_min"]).reset_index(drop=True)
    colunas: dict[str, list[float]] = {"delta_v2_um": [], "delta_v2_min_um": [], "delta_v2_max_um": [], "delta_fenomenologico_um": []}
    for ensaio, grupo in tabela.groupby("ensaio", sort=True):
        sim = simulacoes[int(ensaio)]
        membros = sim["delta_membros"][:, INDICES_INSTANTES]
        colunas["delta_v2_um"].extend(sim["delta_comite"][INDICES_INSTANTES])
        colunas["delta_v2_min_um"].extend(membros.min(axis=0))
        colunas["delta_v2_max_um"].extend(membros.max(axis=0))
        colunas["delta_fenomenologico_um"].extend(sim["delta_fpm"][INDICES_INSTANTES])
    for nome, valores in colunas.items():
        tabela[nome] = valores
    media_oof = oof.groupby(["ensaio", "t_min"], as_index=False)["delta_oof_um"].mean()
    return tabela.merge(media_oof, on=["ensaio", "t_min"], how="left")


def tabela_taxas(deltas: pd.DataFrame, simulacoes: dict[int, dict], oof: pd.DataFrame) -> pd.DataFrame:
    """Monta a tabela de ν̄ medida e prevista nos 7 intervalos de cada ensaio."""
    linhas = []
    for ensaio, grupo in deltas.groupby("ensaio", sort=True):
        grupo = grupo.sort_values("t_min")
        sim = simulacoes[int(ensaio)]
        exp = grupo["delta_exp_um"].where(grupo["bem_determinado"]).to_numpy()
        membros = np.vstack([taxas_por_intervalo(d[INDICES_INSTANTES]) for d in sim["delta_membros"]])
        v2 = taxas_por_intervalo(sim["delta_comite"][INDICES_INSTANTES])
        fpm = taxas_por_intervalo(sim["delta_fpm"][INDICES_INSTANTES])
        taxa_exp = taxas_por_intervalo(exp)
        oof_ensaio = oof[oof["ensaio"] == ensaio]
        oof_taxa = (np.vstack([taxas_por_intervalo(g.sort_values("t_min")["delta_oof_um"].to_numpy()) for _, g in oof_ensaio.groupby("semente")]).mean(axis=0)
                    if not oof_ensaio.empty else np.full(7, np.nan))
        for i, rotulo in enumerate(ROTULOS_INTERVALOS):
            linhas.append({
                "ensaio": int(ensaio), "conjunto": grupo["conjunto"].iloc[0], "eta": grupo["eta"].iloc[0], "CA0_mol_L": grupo["CA0_mol_L"].iloc[0],
                "intervalo_min": rotulo, "taxa_exp_um_min": taxa_exp[i], "bem_determinado": bool(np.isfinite(taxa_exp[i])),
                "taxa_v2_um_min": v2[i], "taxa_v2_min_um_min": membros[:, i].min(), "taxa_v2_max_um_min": membros[:, i].max(),
                "taxa_oof_um_min": oof_taxa[i], "taxa_fenomenologico_um_min": fpm[i],
            })
    return pd.DataFrame(linhas)


def pares_longos(deltas: pd.DataFrame, taxas: pd.DataFrame, oof: pd.DataFrame) -> pd.DataFrame:
    """Reúne pares medido e previsto, só nos pontos bem determinados.

    Returns:
        Tabela com grandeza, conjunto, grupo (instante ou intervalo), modelo, semente, ensaio,
        medido e previsto.
    """
    d_ok = deltas[deltas["bem_determinado"]]
    t_ok = taxas[taxas["bem_determinado"]]
    grupo_delta = d_ok["t_min"].map(lambda t: f"{t:g} min".replace(".", ","))
    partes = []

    def adicionar(grandeza: str, base: pd.DataFrame, grupo: pd.Series, medido: str, previsto: str, conjunto: pd.Series | str, modelo: str) -> None:
        partes.append(pd.DataFrame({
            "grandeza": grandeza, "conjunto": conjunto, "grupo": grupo.to_numpy(), "modelo": modelo, "semente": 0,
            "ensaio": base["ensaio"].to_numpy(), "medido": base[medido].to_numpy(), "previsto": base[previsto].to_numpy(),
        }))

    treino_delta, treino_taxa = d_ok[d_ok["conjunto"] == TREINO], t_ok[t_ok["conjunto"] == TREINO]
    adicionar("delta", d_ok, grupo_delta, "delta_exp_um", "delta_v2_um", d_ok["conjunto"].to_numpy(), "v2_comite")
    adicionar("delta", d_ok, grupo_delta, "delta_exp_um", "delta_fenomenologico_um", d_ok["conjunto"].to_numpy(), "fenomenologico")
    adicionar("taxa", t_ok, t_ok["intervalo_min"], "taxa_exp_um_min", "taxa_v2_um_min", t_ok["conjunto"].to_numpy(), "v2_comite")
    adicionar("taxa", t_ok, t_ok["intervalo_min"], "taxa_exp_um_min", "taxa_fenomenologico_um_min", t_ok["conjunto"].to_numpy(), "fenomenologico")
    adicionar("delta", treino_delta, grupo_delta.loc[treino_delta.index], "delta_exp_um", "delta_fenomenologico_um", CV, "fenomenologico")
    adicionar("taxa", treino_taxa, treino_taxa["intervalo_min"], "taxa_exp_um_min", "taxa_fenomenologico_um_min", CV, "fenomenologico")

    medidas_delta = d_ok[["ensaio", "t_min", "delta_exp_um"]]
    por_semente_delta = oof.merge(medidas_delta, on=["ensaio", "t_min"])
    partes.append(pd.DataFrame({
        "grandeza": "delta", "conjunto": CV, "grupo": por_semente_delta["t_min"].map(lambda t: f"{t:g} min".replace(".", ",")).to_numpy(),
        "modelo": "v2_fora_da_dobra", "semente": por_semente_delta["semente"].to_numpy(), "ensaio": por_semente_delta["ensaio"].to_numpy(),
        "medido": por_semente_delta["delta_exp_um"].to_numpy(), "previsto": por_semente_delta["delta_oof_um"].to_numpy(),
    }))

    medidas_taxa = t_ok.set_index(["ensaio", "intervalo_min"])["taxa_exp_um_min"]
    for (semente, ensaio), grupo in oof.groupby(["semente", "ensaio"]):
        taxas_oof = taxas_por_intervalo(grupo.sort_values("t_min")["delta_oof_um"].to_numpy())
        for rotulo, valor in zip(ROTULOS_INTERVALOS, taxas_oof):
            if (int(ensaio), rotulo) in medidas_taxa.index:
                partes.append(pd.DataFrame([{"grandeza": "taxa", "conjunto": CV, "grupo": rotulo, "modelo": "v2_fora_da_dobra", "semente": int(semente),
                                             "ensaio": int(ensaio), "medido": medidas_taxa.loc[(int(ensaio), rotulo)], "previsto": valor}]))
    return pd.concat(partes, ignore_index=True).dropna(subset=["medido", "previsto"])


def metricas(pares: pd.DataFrame) -> pd.DataFrame:
    """Calcula RMSE e erro médio com sinal (previsto − medido), com média entre sementes."""
    linhas = []
    for (grandeza, conjunto, modelo), dados in pares.groupby(["grandeza", "conjunto", "modelo"]):
        for grupo in (*dict.fromkeys(dados["grupo"]), TODOS):
            parte = dados if grupo == TODOS else dados[dados["grupo"] == grupo]
            por_semente = parte.groupby("semente")
            rmse_semente = por_semente[["medido", "previsto"]].apply(lambda g: comum.rmse(g["medido"], g["previsto"]))
            vies_semente = (parte["previsto"] - parte["medido"]).groupby(parte["semente"]).mean()
            linhas.append({"grandeza": grandeza, "conjunto": conjunto, "grupo": grupo, "modelo": modelo, "n_pontos": int(por_semente.size().iloc[0]),
                           "RMSE": rmse_semente.mean(), "RMSE_dp_sementes": rmse_semente.std(ddof=1), "erro_medio_com_sinal": vies_semente.mean()})
    return pd.DataFrame(linhas)


def conferir(simulacoes: dict[int, dict], medidas: pd.DataFrame, solver: BatchPBMSolver) -> None:
    """Interrompe se X_Zn não reproduzir as previsões oficiais da Etapa 4.2 ou se g⁻¹ falhar."""
    oficial = pd.read_csv(comum.E42 / "tabela_predicoes_detalhadas_16_ensaios.csv")
    oficial = oficial[oficial["t_min"] >= 0.5].sort_values(["ensaio", "t_min"])
    x_comite, x_min, x_max, x_fpm = [], [], [], []
    for ensaio in sorted(simulacoes):
        sim = simulacoes[ensaio]
        membros = sim["x_membros"][:, INDICES_INSTANTES]
        x_comite.extend(sim["x_comite"][INDICES_INSTANTES])
        x_min.extend(membros.min(axis=0))
        x_max.extend(membros.max(axis=0))
        x_fpm.extend(sim["x_fpm"][INDICES_INSTANTES])
    verificacoes = {
        "X do comitê": (x_comite, "XZn_Hibrido_MLP_v2", 1e-5), "X mínimo dos membros": (x_min, "XZn_Hibrido_MLP_v2_min", 1e-5),
        "X máximo dos membros": (x_max, "XZn_Hibrido_MLP_v2_max", 1e-5), "X do fenomenológico": (x_fpm, "XZn_FPM", 1e-4),
    }
    for nome, (calculado, coluna, tolerancia) in verificacoes.items():
        diferenca = float(np.max(np.abs(np.asarray(calculado) - oficial[coluna].to_numpy())))
        if diferenca > tolerancia:
            raise SystemExit(f"{nome} não confere com a Etapa 4.2: diferença máxima {diferenca:.2e}.")
        print(f"Conferência OK: {nome} (diferença máxima {diferenca:.1e}).")
    validos = medidas.dropna(subset=["delta_exp_um"])
    ida_volta = np.abs(validos["delta_exp_um"].map(solver.compute_conversion_from_delta) - validos["XZn_exp"]).max()
    if ida_volta > 1e-5:
        raise SystemExit(f"Inversão de g imprecisa: diferença {ida_volta:.2e}.")
    print(f"Conferência OK: inversão de g (diferença máxima {ida_volta:.1e}).")


def _ordenar_paineis(deltas: pd.DataFrame) -> tuple[list[float], list[float], dict[tuple[float, float], int]]:
    """Devolve η (linhas), C_A0 (colunas) e o ensaio de cada combinação."""
    info = deltas.drop_duplicates("ensaio")
    etas, ca0s = sorted(info["eta"].unique()), sorted(info["CA0_mol_L"].unique())
    return etas, ca0s, {(float(l.eta), float(l.CA0_mol_L)): int(l.ensaio) for l in info.itertuples()}


def figura_delta(deltas: pd.DataFrame, simulacoes: dict[int, dict], delta_limite: float, pasta: Path) -> None:
    """Desenha δ(t) nos 16 ensaios: linhas para η e colunas para C_A0."""
    comum.estilo()
    etas, ca0s, ensaios = _ordenar_paineis(deltas)
    fig, eixos = plt.subplots(4, 4, figsize=(11.5, 9.4), sharex=True, sharey="row")
    for i, eta in enumerate(etas):
        for j, ca0 in enumerate(ca0s):
            eixo, ensaio = eixos[i, j], ensaios[(eta, ca0)]
            sim = simulacoes[ensaio]
            pontos = deltas[deltas["ensaio"] == ensaio]
            bons, ruins = pontos[pontos["bem_determinado"]], pontos[~pontos["bem_determinado"]]
            if max(sim["delta_fpm"].max(), sim["delta_membros"].max()) >= delta_limite * 0.999:
                eixo.axhline(delta_limite, color="#8C8C8C", linewidth=0.9, linestyle=":", zorder=1)
            eixo.fill_between(T_NOS, sim["delta_membros"].min(axis=0), sim["delta_membros"].max(axis=0), color=COR_V2, alpha=0.22, linewidth=0, label="Faixa dos membros")
            eixo.plot(T_NOS, sim["delta_comite"], color=COR_V2, linewidth=1.8, label="v2 (comitê)")
            eixo.plot(T_NOS, sim["delta_fpm"], color=COR_FPM, linewidth=1.8, linestyle="--", label="Fenomenológico")
            eixo.scatter(bons["t_min"], bons["delta_exp_um"], s=26, color=COR_MEDIDA, zorder=4, label="$g^{-1}$(medição)")
            eixo.scatter(ruins["t_min"], ruins["delta_exp_um"], s=26, facecolor="white", edgecolor=COR_MEDIDA, linewidth=1.1, zorder=4, label="$X \\geq 0{,}99$ (mal determinado)")
            eixo.set_xscale("log")
            eixo.set_xticks([0.5, 1, 2, 5, 15], ["0,5", "1", "2", "5", "15"])
            eixo.minorticks_off()
            eixo.set_xlim(0.25, 16)
            sufixo = " (teste)" if ensaio in comum.ENSAIOS_TESTE else ""
            eixo.set_title(f"Ensaio {ensaio}{sufixo}", loc="left", fontsize=10)
            eixo.grid(color="#E3E3E3", linewidth=0.7)
            eixo.set_axisbelow(True)
            eixo.spines[["top", "right"]].set_visible(False)
        eixos[i, 0].set_ylabel(f"η = {eta:.1f}\nδ (µm)".replace(".", ","))
    for j, ca0 in enumerate(ca0s):
        eixos[0, j].annotate(f"$C_{{A0}}$ = {ca0:.1f} mol·L$^{{-1}}$".replace(".", ","), xy=(0.5, 1.22), xycoords="axes fraction", ha="center", fontsize=11)
        eixos[-1, j].set_xlabel("t (min)")
    identificadores, rotulos = eixos[0, 0].get_legend_handles_labels()
    identificadores.append(plt.Line2D([], [], color="#8C8C8C", linewidth=0.9, linestyle=":"))
    rotulos.append("Limite de δ ($X = 0{,}99$)")
    fig.legend(identificadores, rotulos, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.06))
    fig.tight_layout()
    comum.salvar_figura(fig, pasta, "fig_i4_delta_16_ensaios")


def figura_taxas(taxas: pd.DataFrame, pasta: Path) -> None:
    """Desenha ν̄ por intervalo nos 16 ensaios, em escala simétrica-logarítmica."""
    comum.estilo()
    etas, ca0s, ensaios = _ordenar_paineis(taxas)
    fig, eixos = plt.subplots(4, 4, figsize=(11.5, 9.4), sharex=True, sharey="row")
    x = np.arange(len(ROTULOS_INTERVALOS))
    for i, eta in enumerate(etas):
        for j, ca0 in enumerate(ca0s):
            eixo, ensaio = eixos[i, j], ensaios[(eta, ca0)]
            dados = taxas[taxas["ensaio"] == ensaio].set_index("intervalo_min").loc[list(ROTULOS_INTERVALOS)]
            inferior = (dados["taxa_v2_um_min"] - dados["taxa_v2_min_um_min"]).clip(lower=0)
            superior = (dados["taxa_v2_max_um_min"] - dados["taxa_v2_um_min"]).clip(lower=0)
            eixo.errorbar(x - 0.15, dados["taxa_v2_um_min"], yerr=[inferior, superior], fmt="o", markersize=4.8, color=COR_V2, elinewidth=1.1, label="v2 (comitê, com faixa dos membros)")
            eixo.scatter(x + 0.15, dados["taxa_fenomenologico_um_min"], marker="v", s=28, color=COR_FPM, label="Fenomenológico")
            eixo.scatter(x, dados["taxa_exp_um_min"], s=30, color=COR_MEDIDA, zorder=4, label="Taxa média medida")
            eixo.set_yscale("symlog", linthresh=0.1)
            eixo.set_xticks(x, ROTULOS_INTERVALOS, rotation=60, ha="right", fontsize=8)
            sufixo = " (teste)" if ensaio in comum.ENSAIOS_TESTE else ""
            eixo.set_title(f"Ensaio {ensaio}{sufixo}", loc="left", fontsize=10)
            eixo.grid(axis="y", color="#E3E3E3", linewidth=0.7)
            eixo.set_axisbelow(True)
            eixo.spines[["top", "right"]].set_visible(False)
            eixo.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
        eixos[i, 0].set_ylabel(f"η = {eta:.1f}\n$\\bar{{\\nu}}$ (µm·min$^{{-1}}$)".replace(".", ","))
    for j, ca0 in enumerate(ca0s):
        eixos[0, j].annotate(f"$C_{{A0}}$ = {ca0:.1f} mol·L$^{{-1}}$".replace(".", ","), xy=(0.5, 1.22), xycoords="axes fraction", ha="center", fontsize=11)
        eixos[-1, j].set_xlabel("Intervalo (min)")
    identificadores, rotulos = eixos[0, 0].get_legend_handles_labels()
    fig.legend(identificadores, rotulos, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.03))
    fig.tight_layout()
    comum.salvar_figura(fig, pasta, "fig_i4_taxa_media_por_intervalo")


def escrever_relatorio(tabela: pd.DataFrame, deltas: pd.DataFrame, taxas: pd.DataFrame, pesos: pd.DataFrame, delta_limite: float, n_acima_dmax: int, pasta: Path) -> None:
    """Escreve o relatório do item com os números calculados nesta execução."""
    v = comum.virgula
    mal = deltas[~deltas["bem_determinado"]]
    faixa = (deltas["delta_exp_sup_um"] - deltas["delta_exp_inf_um"])[deltas["bem_determinado"]]
    linhas = [
        "# Item 4 — O que a rede prevê: δ e taxas médias por intervalo", "",
        "Gerado por `delta_e_taxas_medias.py`. Nenhum modelo foi treinado.", "",
        "## O que é físico e o que não é", "",
        "- δ(t) é identificado pelas medições: X = g(δ) é crescente e fixada pela granulometria.",
        "- ν̄ = Δδ/Δt entre amostras também é física e, em princípio, não depende da malha (o Item 5 testa isso).",
        "- O valor de ν em um nó não é identificado: cada medição fixa só uma combinação dos ν nodais (tabela de pesos abaixo).", "",
        "## Medições usadas", "",
        f"- Pontos bem determinados: {int(deltas['bem_determinado'].sum())} de {len(deltas)}. Foram excluídos {len(mal)} pontos com X ≥ 0,99, em que g fica plana ou X ≥ 1 não tem inversa.",
        f"- Intervalos bem determinados: {int(taxas['bem_determinado'].sum())} de {len(taxas)}.",
        f"- {int((taxas['taxa_exp_um_min'] < 0).sum())} das {int(taxas['bem_determinado'].sum())} taxas medidas são negativas, o que é fisicamente impossível, porque δ não diminui. Elas vêm de flutuações de X entre amostras, e por isso o RMSE de ν̄ inclui o ruído da medição, principalmente nos intervalos finais.",
        f"- Como X foi medido com duas casas decimais, a largura mediana da faixa de δ correspondente a ± 0,005 em X é {v(float(faixa.median()), 2)} µm (máxima: {v(float(faixa.max()), 2)} µm).",
        f"- δ previsto foi limitado a g⁻¹(0,99) = {v(delta_limite, 1)} µm em todos os modelos, porque acima disso X não determina δ. Sem o limite, o fenomenológico continua acumulando δ depois de X chegar a 1: em {n_acima_dmax} dos 112 pontos ele passa do diâmetro máximo da distribuição (297 µm), valor sem significado físico.", "",
        "## RMSE de δ e de ν̄ (pontos bem determinados)", "",
        "Entre parênteses, o erro médio com sinal (previsto − medido). No treino, o comitê mostra ajuste; a coluna fora da dobra e o teste cego mostram previsão.", "",
        "| Grandeza | Conjunto | n | v2 (comitê) | v2 (fora da dobra) | Fenomenológico |", "| :-- | :-- | :-: | :-: | :-: | :-: |",
    ]
    todos = tabela[tabela["grupo"] == TODOS]
    for grandeza in ("delta", "taxa"):
        nome_grandeza = f"{'δ' if grandeza == 'delta' else 'ν̄'} ({UNIDADE[grandeza]})"
        for conjunto in (TREINO, CV, TESTE):
            parte = todos[(todos["grandeza"] == grandeza) & (todos["conjunto"] == conjunto)].set_index("modelo")
            if parte.empty:
                continue
            celulas = [f"{v(parte.loc[m, 'RMSE'], 3)} ({v(parte.loc[m, 'erro_medio_com_sinal'], 3)})" if m in parte.index else "—" for m in NOME_MODELO]
            linhas.append(f"| {nome_grandeza} | {conjunto} | {int(parte['n_pontos'].iloc[0])} | " + " | ".join(celulas) + " |")

    linhas += ["", "## RMSE de ν̄ por intervalo", "", "Em µm/min. Validação cruzada (fora da dobra) e teste cego.", "",
               "| Intervalo (min) | n (CV) | v2 fora da dobra | Fenomenológico (CV) | n (teste) | v2 comitê (teste) | Fenomenológico (teste) |",
               "| :-: | :-: | :-: | :-: | :-: | :-: | :-: |"]
    def celula(conjunto: str, modelo: str, grupo: str, coluna: str = "RMSE") -> pd.Series:
        return tabela[(tabela["grandeza"] == "taxa") & (tabela["conjunto"] == conjunto) & (tabela["modelo"] == modelo) & (tabela["grupo"] == grupo)][coluna]

    for rotulo in ROTULOS_INTERVALOS:
        def texto(c: str, m: str) -> str:
            valor = celula(c, m, rotulo)
            return v(float(valor.iloc[0]), 3) if not valor.empty else "—"

        def n_texto(c: str, m: str) -> str:
            valor = celula(c, m, rotulo, "n_pontos")
            return str(int(valor.iloc[0])) if not valor.empty else "0"

        linhas.append(f"| {rotulo} | {n_texto(CV, 'v2_fora_da_dobra')} | {texto(CV, 'v2_fora_da_dobra')} | {texto(CV, 'fenomenologico')} | {n_texto(TESTE, 'v2_comite')} | {texto(TESTE, 'v2_comite')} | {texto(TESTE, 'fenomenologico')} |")

    linhas += ["", "## Pesos de ν nodal em cada δ medido", "",
               "Extraídos do solver por perfis unitários. A soma dos pesos de cada linha é o próprio tempo (min). Sete medições fixam sete combinações dos 60 valores nodais.", "",
               "| t (min) | Nós envolvidos | Peso de ν(0,25) | Peso de cada nó intermediário | Peso do último nó | Soma |", "| :-: | :-: | :-: | :-: | :-: | :-: |"]
    for t, grupo in pesos.groupby("t_medicao"):
        grupo = grupo.sort_values("t_no")
        intermediarios = sorted({round(float(p), 6) for p in grupo["peso"].iloc[1:-1]}) if len(grupo) > 2 else []
        meio = " e ".join(v(p, 3) for p in intermediarios) if intermediarios else "—"
        linhas.append(f"| {v(float(t), 1)} | {len(grupo)} | {v(float(grupo['peso'].iloc[0]), 3)} | {meio} | {v(float(grupo['peso'].iloc[-1]), 3)} | {v(float(grupo['peso'].sum()), 3)} |")

    linhas += ["", "## Pontos mal determinados", "", "| Ensaio | t (min) | X_Zn medido |", "| :-: | :-: | :-: |"]
    for m in mal.sort_values(["ensaio", "t_min"]).itertuples(index=False):
        linhas.append(f"| {int(m.ensaio)} | {m.t_min:g} | {v(float(m.XZn_exp), 2)} |".replace(".", ","))
    (pasta / "relatorio_item_4.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main() -> None:
    """Executa o Item 4 e grava tabelas, figuras e relatório."""
    comum.conferir_hashes_v2()
    pasta = comum.pasta_saida("item_4_taxa_efetiva")
    medicoes = comum.carregar_medicoes()
    modelo = SerialHybridModel(model_type="mlp_v2")
    solver = BatchPBMSolver()

    simulacoes = simular_ensaios(modelo, solver, medicoes)
    medidas = delta_medido(medicoes, solver)
    conferir(simulacoes, medidas, solver)

    delta_limite = inverter_g(LIMITE_X_DETERMINADO, solver)
    n_acima_dmax = sum(int((sim["delta_fpm"][INDICES_INSTANTES] > solver.d_max).sum()) for sim in simulacoes.values())
    simulacoes = limitar_simulacoes(simulacoes, delta_limite)
    oof = delta_fora_da_dobra(solver, delta_limite)
    deltas = tabela_delta(medidas, simulacoes, oof)
    taxas = tabela_taxas(deltas, simulacoes, oof)
    tabela = metricas(pares_longos(deltas, taxas, oof))
    pesos = pesos_quadratura(solver)

    deltas.to_csv(pasta / "tabela_delta_exp_vs_previsto.csv", index=False)
    taxas.to_csv(pasta / "tabela_taxa_media_por_intervalo.csv", index=False)
    tabela.to_csv(pasta / "tabela_metricas_delta_e_taxa.csv", index=False)
    pesos.to_csv(pasta / "tabela_pesos_quadratura.csv", index=False)
    figura_delta(deltas, simulacoes, delta_limite, pasta)
    figura_taxas(taxas, pasta)
    escrever_relatorio(tabela, deltas, taxas, pesos, delta_limite, n_acima_dmax, pasta)
    print(f"Limite de δ: {delta_limite:.2f} µm; pontos do fenomenológico acima de d_max: {n_acima_dmax}.")
    print(tabela[tabela["grupo"] == TODOS].to_string(index=False))
    print(f"Saídas em {pasta}")


if __name__ == "__main__":
    main()
