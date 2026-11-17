"""Testes da Subetapa 3.2.7 (MLP pura em X_Zn): integridade do comitê e reprodução das métricas gravadas."""

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mlp_puro_xzn as mp  # noqa: E402


def test_teste_cego_fora_do_treino():
    d = mp.carregar()
    assert not set(d["train"]["ensaio"]) & set(mp.ENSAIOS_TESTE)
    assert sorted(d["test"]["ensaio"].unique()) == mp.ENSAIOS_TESTE
    assert len(d["train"]) == 91 and len(d["test"]) == 21
    assert (d["train"]["t_min"] > 0).all()


def test_hashes_do_comite_conferem():
    linhas = (mp.MODELOS_DIR / "SHA256SUMS.txt").read_text(encoding="utf-8").strip().splitlines()
    assert len(linhas) == 10
    for ln in linhas:
        h, nome = ln.split("  ")
        assert hashlib.sha256((mp.MODELOS_DIR / nome).read_bytes()).hexdigest() == h, nome


def test_metricas_gravadas_sao_reproduzidas():
    membros, conf = mp.carregar_comite()
    d = mp.carregar()
    gravado = pd.read_csv(mp.OUT / "metricas_mlp_puro.csv").set_index("particao")
    for nome, df in (("Teste cego (3 ensaios, 21 pts)", d["test"]), ("Treino (13 ensaios, 91 pts)", d["train"])):
        p = mp.prever_comite(membros, conf, df).mean(0)
        assert abs(mp.rmse(df["XZn_exp"], p) - gravado.loc[nome, "RMSE"]) < 1e-4


def test_comite_finito_e_dentro_de_faixa_razoavel():
    membros, conf = mp.carregar_comite()
    t = np.linspace(0.5, 15, 50)
    df = pd.DataFrame({"CA0_mol_L": 0.8, "razao_molar_eta": 2.0, "t_min": t})
    P = mp.prever_comite(membros, conf, df)
    assert P.shape == (10, 50) and np.isfinite(P).all()
    assert -0.05 < P.min() and P.max() < 1.1
