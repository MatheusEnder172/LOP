"""Testes da Subetapa 3.2.6 (otimização da MLP).

Verifica:
1. Disjunção entre treino, parada interna, validação e teste cego em todas as dobras e sementes.
2. Determinismo do sorteio dos ensaios de parada interna e ausência dos vértices.
3. Não-negatividade e formato da taxa do `KineticsMLPEnsemble`.
4. Penalidade de monotonia nula para uma rede que não depende do tempo.
5. Treino curto do `MLPTrainerV2` (com penalidade) sem erro e com pesos restaurados da melhor época.
"""

import sys
from pathlib import Path

import numpy as np
import pytest
import torch

SUBETAPA_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SUBETAPA_DIR))

from modelo_mlp_v2 import KineticsMLP, KineticsMLPEnsemble, MLPTrainerV2  # noqa: E402
from protocolo_cv import ENSAIOS_TESTE, VERTICES, carregar_dados, ensaios_parada_interna  # noqa: E402


@pytest.fixture(scope="module")
def dados():
    return carregar_dados()


def test_particoes_disjuntas(dados) -> None:
    todos = set(dados.train_df["ensaio"])
    assert not todos & set(ENSAIOS_TESTE)
    for fold in dados.folds:
        val = set(fold["val_ensaios"])
        treino = sorted(todos - val)
        for s in (42, 43, 44):
            es = set(ensaios_parada_interna(treino, fold["fold"], s))
            tr = set(treino) - es
            assert len(es) == 2
            assert not (tr & val) and not (es & val) and not (tr & es)
            assert not es & set(VERTICES)
            assert tr | es | val == todos


def test_sorteio_deterministico() -> None:
    a = ensaios_parada_interna([3, 4, 6, 9, 10, 12, 13, 15], 2, 42)
    b = ensaios_parada_interna([3, 4, 6, 9, 10, 12, 13, 15], 2, 42)
    assert a == b


def test_ensemble_nao_negativo() -> None:
    membros = [KineticsMLP(input_dim=3, hidden_dims=[16, 8]) for _ in range(3)]
    ens = KineticsMLPEnsemble(membros)
    x = torch.randn(50, 3) * 10
    out = ens(x)
    assert out.shape == (50, 1)
    assert (out >= 0).all()
    assert ens.forward_membros(x).shape == (3, 50, 1)


def test_penalidade_nula_sem_tempo(dados) -> None:
    model = KineticsMLP(input_dim=3, hidden_dims=[8])
    with torch.no_grad():
        model.network[0].weight[:, 2] = 0.0  # rede independente de t
    x = torch.randn(64, 3, requires_grad=True)
    assert float(MLPTrainerV2.penalidade_monotonia(model, x)) == pytest.approx(0.0, abs=1e-12)


def test_espaco_de_busca_reconstrucao() -> None:
    """A configuração reconstruída dos parâmetros gravados é igual à sugerida na tentativa."""
    import optuna

    from fase_b_optuna_hpo import PARAMS_V1, config_de_params, sugerir_config

    for params in (PARAMS_V1, {**PARAMS_V1, "n_camadas": 3, "forma": "constante", "modo_parada": "epocas_fixas",
                               "max_epochs_fixas": 120}):
        p = {k: v for k, v in params.items() if not (params["modo_parada"] == "epocas_fixas"
                                                     and k in ("patience", "max_epochs_interna"))}
        cfg = sugerir_config(optuna.trial.FixedTrial(p))
        assert cfg == config_de_params(p)
    assert config_de_params(PARAMS_V1)["hidden_dims"] == [64, 32]


def test_epocas_fixas_curto(dados) -> None:
    tr = MLPTrainerV2(hidden_dims=[16], max_epochs=3, batch_size=128, seed=0)
    m = dados.mascara([1, 2, 3])
    model, hist = tr.fit_epocas_fixas(dados.X_train_s[m], dados.y_train[m])
    assert len(hist["train_loss"]) == 3 and np.isfinite(hist["train_loss"]).all()


def test_treino_curto_v2(dados) -> None:
    tr = MLPTrainerV2(hidden_dims=[16, 8], mono_lambda=1.0, scaler_X=dados.scaler_X,
                      max_epochs=5, patience=3, batch_size=64, seed=0)
    m = dados.mascara([1, 2, 3, 4, 5, 6])
    e = dados.mascara([9, 10])
    model, hist = tr.fit_parada_interna(dados.X_train_s[m], dados.y_train[m],
                                        dados.X_train_s[e], dados.y_train[e])
    assert 1 <= hist["best_epoch"][0] <= 5
    assert np.isfinite(hist["train_loss"]).all()
    assert hist["mono_loss"][0] >= 0.0
