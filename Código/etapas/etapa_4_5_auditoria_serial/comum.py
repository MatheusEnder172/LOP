"""Etapa 4.5 — leitura de dados e métricas usadas pelos itens da auditoria.

Só lê arquivos já existentes. Toda escrita vai para
`Código/outputs/etapa_4_5_auditoria_serial/<item>/`.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

CODIGO_DIR = Path(__file__).resolve().parents[2]
BASE_DIR = CODIGO_DIR.parent
SPLITS = BASE_DIR / "Base de dados" / "processed" / "splits"
OUTPUTS = CODIGO_DIR / "outputs"
SUB326 = OUTPUTS / "etapa_3_2" / "subetapa_3_2_6_mlp_otimizacao"
E42 = OUTPUTS / "etapa_4_2_avaliacao_indomain"
SAIDA_ETAPA = OUTPUTS / "etapa_4_5_auditoria_serial"

ENSAIOS_TESTE = (7, 8, 14)
CONFIG_V2 = "B2 – tentativa 511"
PONTOS_POR_ENSAIO = 7


def pasta_saida(item: str) -> Path:
    """Cria (se preciso) e devolve a pasta de saída de um item da auditoria."""
    pasta = SAIDA_ETAPA / item
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def rmse(y_real: np.ndarray | pd.Series, y_prev: np.ndarray | pd.Series) -> float:
    """Raiz do erro quadrático médio de X_Zn (adimensional)."""
    erro = np.asarray(y_real, dtype=float) - np.asarray(y_prev, dtype=float)
    return float(np.sqrt(np.mean(erro**2)))


def carregar_medicoes() -> pd.DataFrame:
    """Lê as 112 medições de X_Zn (t ≥ 0,5 min) dos 16 ensaios.

    Returns:
        Tabela com ensaio, t_min, CA0_mol_L, eta (razão molar) e XZn_exp.
    """
    colunas = ["ensaio", "t_min", "CA0_mol_L", "razao_molar_eta", "XZn_exp"]
    tabela = pd.concat(
        [pd.read_csv(SPLITS / "train_exp.csv")[colunas], pd.read_csv(SPLITS / "test_exp.csv")[colunas]],
        ignore_index=True,
    ).rename(columns={"razao_molar_eta": "eta"})
    if len(tabela) != 16 * PONTOS_POR_ENSAIO:
        raise SystemExit(f"Esperadas 112 medições, encontradas {len(tabela)}.")
    return tabela.sort_values(["ensaio", "t_min"]).reset_index(drop=True)


def carregar_dobras() -> list[dict]:
    """Lê as 4 dobras da validação cruzada (mesmas usadas na v2)."""
    return json.loads((SPLITS / "cv_folds_info.json").read_text(encoding="utf-8"))


def carregar_oof_v2() -> pd.DataFrame:
    """Lê as previsões fora da dobra da v2 (10 sementes, 13 ensaios, 7 instantes)."""
    tabela = pd.read_csv(SUB326 / "fase_b2" / "finalistas_oof.csv")
    tabela = tabela[tabela["config"] == CONFIG_V2].copy()
    if len(tabela) != 10 * 13 * PONTOS_POR_ENSAIO:
        raise SystemExit(f"Previsões fora da dobra incompletas: {len(tabela)} linhas.")
    return tabela[["semente", "fold", "ensaio", "t_min", "XZn_pred", "XZn_exp"]]


def carregar_v2_teste_cego() -> pd.DataFrame:
    """Lê as previsões do comitê v2 congelado nos 21 pontos do teste cego."""
    tabela = pd.read_csv(E42 / "tabela_predicoes_detalhadas_16_ensaios.csv")
    tabela = tabela[tabela["ensaio"].isin(ENSAIOS_TESTE)]
    tabela = tabela[tabela["t_min"] >= 0.5].rename(columns={"XZn_Hibrido_MLP_v2": "XZn_pred"})
    if len(tabela) != 3 * PONTOS_POR_ENSAIO:
        raise SystemExit(f"Teste cego incompleto: {len(tabela)} pontos.")
    return tabela[["ensaio", "t_min", "XZn_pred", "XZn_exp"]]


def carregar_fenomenologico() -> pd.DataFrame:
    """Lê as previsões do fenomenológico puro nos 112 pontos experimentais."""
    tabela = pd.read_csv(E42 / "tabela_predicoes_detalhadas_16_ensaios.csv")
    tabela = tabela[tabela["t_min"] >= 0.5].rename(columns={"XZn_FPM": "XZn_pred"})
    if len(tabela) != 16 * PONTOS_POR_ENSAIO:
        raise SystemExit(f"Fenomenológico incompleto: {len(tabela)} pontos.")
    return tabela[["ensaio", "t_min", "XZn_pred", "XZn_exp"]]


def conferir_hashes_v2() -> None:
    """Interrompe se algum membro do comitê v2 diferir dos hashes registrados."""
    pasta = OUTPUTS / "models_saved" / "mlp_v2"
    for linha in (pasta / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if linha.strip():
            esperado, nome = linha.split(None, 1)
            nome = nome.strip().lstrip("*")
            if hashlib.sha256((pasta / nome).read_bytes()).hexdigest() != esperado:
                raise SystemExit(f"Hash diferente para {nome}: o comitê v2 foi alterado.")


def valor_oficial_cv_v2() -> float:
    """RMSE médio fora da dobra da v2, como gravado na Fase B2."""
    tabela = pd.read_csv(SUB326 / "fase_b2" / "tabela_fase_b2_finalistas.csv")
    return float(tabela.loc[tabela["config"] == CONFIG_V2, "RMSE_X_media"].iloc[0])


def valor_oficial_teste_v2() -> float:
    """RMSE do comitê v2 no teste cego, como gravado na Fase E."""
    tabela = pd.read_csv(SUB326 / "fase_e" / "tabela_fase_e_metricas_XZn.csv")
    filtro = (tabela["Particao"] == "Teste cego") & (tabela["Modelo"] == "MLP v2 (ensemble)")
    return float(tabela.loc[filtro, "RMSE"].iloc[0])


def virgula(valor: float, casas: int = 4) -> str:
    """Formata um número com vírgula decimal, como no relatório."""
    return f"{valor:.{casas}f}".replace(".", ",")


def estilo() -> None:
    """Aplica o padrão visual do projeto (Arial, eixos 11 pt, título 13 pt)."""
    plt.rcParams.update({
        "font.family": "Arial", "font.size": 10, "axes.labelsize": 11, "axes.titlesize": 13,
        "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 9, "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })


def salvar_figura(fig: plt.Figure, pasta: Path, nome: str) -> None:
    """Grava a figura em PNG e PDF (300 DPI) e fecha."""
    fig.savefig(pasta / f"{nome}.png", dpi=300)
    fig.savefig(pasta / f"{nome}.pdf", dpi=300)
    plt.close(fig)
