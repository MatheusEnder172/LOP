"""Testes da Subetapa 4.3 (previsão a priori dos 4 ensaios novos)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prever_novos_ensaios as pn  # noqa: E402

OFICIAL = pn.OUT


def test_hashes_do_comite_conferem():
    h = pn.conferir_modelo()
    assert len(h) == 11 and all(len(v) == 64 for v in h.values())


def test_previsao_oficial_gravada_e_integra():
    integ = json.loads((OFICIAL / "INTEGRIDADE_previsao_a_priori.json").read_text(encoding="utf-8"))
    for nome, h in integ["sha256_previsoes"].items():
        assert pn.sha256(OFICIAL / nome) == h, f"{nome} foi alterado depois da gravação"
    assert integ["sha256_modelo"] == pn.conferir_modelo()


def test_previsao_oficial_respeita_fisica():
    t = pd.read_csv(OFICIAL / "previsao_a_priori_instantes_amostrados.csv")
    assert set(t["ensaio"]) == {"E1", "E2", "E3", "E4"} and len(t) == 28
    assert np.allclose(sorted(t["t_min"].unique()), [0.5, 1, 2, 3, 4, 5, 15])
    assert (t["XZn_v2_comite"] <= t["limite_min_1_eta"] + 1e-9).all()
    assert (t["XZn_v2_membro_min"] <= t["XZn_v2_membro_max"]).all()
    assert (t["CAf_v2_mol_L"] >= 0).all()
    assert t[t["ensaio"] == "E4"]["extrapolacao_eta"].all() and not t[t["ensaio"] != "E4"]["extrapolacao_eta"].any()
    for e in ("E1", "E2", "E3", "E4"):  # X não decresce com o tempo
        assert (np.diff(t[t["ensaio"] == e]["XZn_v2_comite"]) >= -1e-9).all()


def test_gera_comparacao_e_recusa_refazer(tmp_path, monkeypatch):
    monkeypatch.setattr(pn, "OUT", tmp_path)
    pn.prever()
    with pytest.raises(SystemExit):
        pn.prever()  # não refaz a previsão já gravada
    tab = pd.read_csv(tmp_path / "previsao_a_priori_instantes_amostrados.csv")
    med = tab[["ensaio", "t_min"]].assign(XZn_medido=tab["XZn_v2_comite"] + 0.01)
    med.to_csv(tmp_path / "med.csv", index=False)
    pn.comparar(tmp_path / "med.csv")
    res = pd.read_csv(tmp_path / "tabela_comparacao_medicoes.csv")
    assert abs(res[res["ensaio"] == "Todos"]["RMSE_v2"].iloc[0] - 0.01) < 1e-9
    assert (tmp_path / "fig_ne_05_painel_com_medicoes.png").exists()
    # arquivo adulterado depois da gravação: a comparação aborta
    tab.assign(XZn_v2_comite=tab["XZn_v2_comite"] * 0.5).to_csv(tmp_path / "previsao_a_priori_instantes_amostrados.csv", index=False)
    with pytest.raises(SystemExit):
        pn.comparar(tmp_path / "med.csv")
