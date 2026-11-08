"""Fase C (Subetapa 3.2.6): perdas com informação física sobre a configuração da B2.

A rede é a da B2 (tentativa 511); só a função de perda muda:

- D1, perda ponderada pela sensibilidade. O peso de ν(tᵢ) é a soma, nos tempos experimentais tₖ ≥ tᵢ,
  de X′(δₖ)·∂δₖ/∂νᵢ·(1 + νᵢ), calculada uma vez na trajetória-alvo de cada ensaio. X′ é a derivada da
  PCHIP do `BatchPBMSolver` (zero quando X atinge min(1, η)); ∂δₖ/∂νᵢ vem do esquema de integração do
  acoplamento serial (δ(t₁) = ν(t₁)·t₁ e trapézio depois); o fator (1 + νᵢ) aparece porque a perda está
  em ln(1 + ν). O peso é normalizado para média 1 e elevado a um expoente γ (γ = 0 é o treino atual).
- D2, monotonia. Penalidade λ·média(ReLU(∂ν/∂t)²) em pontos de colocação sorteados no domínio
  (já implementada no `MLPTrainerV2`; Raissi et al., 2019; von Stosch et al., 2014).

Como o teste cego (ensaios 7, 8 e 14) já foi visto uma vez, a escolha é feita só pela validação cruzada
do protocolo comum (4 dobras, nota em X_Zn fora da dobra) e pela regra de ganho claro: diferença média
pareada por semente (B2 − variante, 10 sementes) maior que 1 erro-padrão da própria diferença.

Uso:
    python fase_c_perdas_fisicas.py buscar --tentativas 80 --trabalhadores 26
    python fase_c_perdas_fisicas.py ablacao --trabalhadores 26
    python fase_c_perdas_fisicas.py figuras
"""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import os
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from protocolo_cv import OUTPUTS_DIR, TARGET, Dados

OUT = Path(os.environ.get("FASE_C_OUT", OUTPUTS_DIR / "fase_c"))
JOURNAL = OUT / "estudo_optuna_fase_c.log"
NOME_ESTUDO = "mlp_v2_fase_c_perdas_fisicas"
SEMENTES_BUSCA = (42, 43, 44)
SEMENTES_ABLACAO = tuple(range(42, 52))
T_EXP = np.array([0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 15.0])
PISO_PESO = 1e-3  # peso mínimo relativo à média, para não zerar trechos saturados


def config_b2() -> Dict[str, Any]:
    return json.loads((OUTPUTS_DIR / "fase_b2" / "melhor_config_fase_b2.json").read_text(encoding="utf-8"))["config"]


def matriz_dos_deltas(t_grid: np.ndarray) -> np.ndarray:
    """Matriz A (n × n), A[j, i] = ∂δ(t_j)/∂ν(t_i), no esquema do `SerialHybridModel`.

    δ(t₁) = ν(t₁)·t₁ (t = 0 é a condição inicial) e, depois, δ(t_j) = δ(t_{j-1}) + ½(ν_j + ν_{j-1})·Δt.
    O esquema é linear em ν, então A é a imagem da base canônica.
    """
    n = len(t_grid)
    A = np.zeros((n, n))
    for i in range(n):
        nu = np.zeros(n)
        nu[i] = 1.0
        d = np.zeros(n)
        d[0] = nu[0] * t_grid[0]
        for j in range(1, n):
            d[j] = d[j - 1] + 0.5 * (nu[j] + nu[j - 1]) * (t_grid[j] - t_grid[j - 1])
        A[:, i] = d
    return A


def pesos_brutos(dados: Dados) -> np.ndarray:
    """Pesos de sensibilidade (sem normalização), alinhados às linhas de `train_df`."""
    deriv = dados.solver._interpolator.derivative()
    assert (dados.train_df.index.values == np.arange(len(dados.train_df))).all()
    bruto = np.zeros(len(dados.train_df))
    for e, sub in dados.train_df.groupby("ensaio"):
        sub = sub.sort_values("t_min")
        t = sub["t_min"].values
        nu = sub[TARGET].values
        eta = float(sub["razao_molar_eta"].iloc[0])
        delta = dados.solver.simulate_with_v_profile(t, -nu)["delta"]
        x_raw = dados.solver.compute_conversion_from_delta(delta)
        dx = deriv(np.clip(delta, 0.0, dados.solver.d_max))
        dx = np.where(x_raw >= min(1.0, eta) - 1e-7, 0.0, dx)
        idx_k = np.array([int(np.argmin(np.abs(t - tk))) for tk in T_EXP])
        A = matriz_dos_deltas(t)
        sens = (dx[idx_k][:, None] * A[idx_k, :]).sum(axis=0)  # soma sobre k; A é causal (tₖ ≥ tᵢ)
        bruto[sub.index.values] = sens * (1.0 + nu)
    return bruto


def pesos_sensibilidade(dados: Dados, gamma: float, bruto: Optional[np.ndarray] = None) -> np.ndarray:
    """Pesos D1 com média 1: (w/média)^γ, com piso relativo `PISO_PESO`. γ = 0 devolve pesos unitários."""
    if gamma == 0.0:
        return np.ones(len(dados.train_df))
    w = pesos_brutos(dados) if bruto is None else bruto
    w = np.maximum(w / w.mean(), PISO_PESO) ** gamma
    return w / w.mean()


# ----------------------------------------------------------------------------------------------
# Busca (Optuna) e ablação
# ----------------------------------------------------------------------------------------------
def config_da_tentativa(p: Dict[str, Any]) -> Dict[str, Any]:
    cfg = dict(config_b2())
    cfg["lr"] = p["lr"]
    cfg["max_epochs"] = p["max_epochs"]
    ml = float(p.get("mono_lambda", 0.0))
    cfg["mono_lambda"] = ml if p.get("usar_mono", ml > 0) else 0.0
    return cfg


def sugerir(trial) -> Dict[str, Any]:
    b2 = config_b2()
    usar = trial.suggest_categorical("usar_mono", [False, True])
    return {
        "gamma": trial.suggest_float("gamma", 0.0, 2.0),
        "usar_mono": usar,
        "mono_lambda": trial.suggest_float("mono_lambda", 1e-4, 10.0, log=True) if usar else 0.0,
        "lr": trial.suggest_float("lr", 0.4 * b2["lr"], 2.5 * b2["lr"], log=True),
        "max_epochs": trial.suggest_int("max_epochs", 500, 1500),
    }


def _storage():
    import optuna
    from optuna.storages.journal import JournalFileBackend, JournalFileOpenLock

    return optuna.storages.JournalStorage(JournalFileBackend(str(JOURNAL), lock_obj=JournalFileOpenLock(str(JOURNAL))))


def _trabalhador(total: int, wid: int) -> None:
    import optuna
    import torch
    from optuna.study import MaxTrialsCallback
    from optuna.trial import TrialState

    torch.set_num_threads(1)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    from protocolo_cv import carregar_dados, rodar_cv

    dados = carregar_dados()
    bruto = pesos_brutos(dados)
    study = optuna.load_study(
        study_name=NOME_ESTUDO, storage=_storage(),
        sampler=optuna.samplers.TPESampler(multivariate=True, group=True, seed=2042 + wid, n_startup_trials=24),
        pruner=optuna.pruners.MedianPruner(n_startup_trials=24, n_warmup_steps=1),
    )

    def objetivo(trial) -> float:
        p = sugerir(trial)
        cfg = config_da_tentativa(p)
        pesos = pesos_sensibilidade(dados, p["gamma"], bruto)

        def ao_fim(k: int, parcial: float) -> None:
            trial.report(parcial, k)
            if trial.should_prune():
                raise optuna.TrialPruned()

        t0 = time.time()
        res = rodar_cv(cfg, dados, sementes=SEMENTES_BUSCA, pesos=pesos, ao_fim_da_dobra=ao_fim)
        if not math.isfinite(res.objetivo):
            return 1.0
        trial.set_user_attr("rmse_X_dp_sementes", res.objetivo_std)
        trial.set_user_attr("R2_X_medio", float(res.por_semente["R2_X"].mean()))
        trial.set_user_attr("segundos", time.time() - t0)
        return res.objetivo

    study.optimize(objetivo, callbacks=[MaxTrialsCallback(total, states=(TrialState.COMPLETE, TrialState.PRUNED))],
                   catch=(RuntimeError, ValueError))


def buscar(total: int, n_trab: int) -> None:
    import optuna

    OUT.mkdir(parents=True, exist_ok=True)
    study = optuna.create_study(study_name=NOME_ESTUDO, storage=_storage(), direction="minimize", load_if_exists=True)
    if len(study.trials) == 0:
        b2 = config_b2()
        base = {"lr": b2["lr"], "max_epochs": b2["max_epochs"]}
        # Referências na fila: a própria B2, só D1, só D2 e as duas juntas
        study.enqueue_trial({**base, "gamma": 0.0, "usar_mono": False})
        study.enqueue_trial({**base, "gamma": 1.0, "usar_mono": False})
        study.enqueue_trial({**base, "gamma": 0.0, "usar_mono": True, "mono_lambda": 0.1})
        study.enqueue_trial({**base, "gamma": 1.0, "usar_mono": True, "mono_lambda": 0.1})
    t0 = time.time()
    ctx = mp.get_context("spawn")
    procs = [ctx.Process(target=_trabalhador, args=(total, w)) for w in range(n_trab)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    print(f"Busca concluída em {(time.time() - t0) / 60:.1f} min")
    exportar_tentativas()


def carregar_estudo():
    import optuna

    return optuna.load_study(study_name=NOME_ESTUDO, storage=_storage())


def exportar_tentativas() -> pd.DataFrame:
    df = carregar_estudo().trials_dataframe(attrs=("number", "value", "state", "params", "user_attrs", "duration"))
    df.to_csv(OUT / "tabela_fase_c_tentativas.csv", index=False)
    return df


def fracao_nao_monotona(model, dados: Dados, n: int = 4000, seed: int = 0) -> float:
    """Fração de pontos do domínio físico (sorteio uniforme) com ∂ν/∂t > 0, por autograd."""
    import torch
    from modelo_mlp_v2 import DOMINIO_FISICO

    rng = np.random.default_rng(seed)
    x_fis = DOMINIO_FISICO[:, 0] + rng.random((n, 3)) * (DOMINIO_FISICO[:, 1] - DOMINIO_FISICO[:, 0])
    x = torch.tensor(dados.scaler_X.transform(x_fis), dtype=torch.float32, requires_grad=True)
    model.eval()
    y = model.forward_log(x)
    g = torch.autograd.grad(y.sum(), x)[0][:, 2]
    return float((g > 1e-9).float().mean())


def curva_sem_ensaio(model, dados: Dados, ca0: float = 0.75, eta: float = 2.0) -> pd.DataFrame:
    """ν(t) e X_Zn(t) em uma condição que não é ensaio (C_A0 = 0,75 mol/L e η = 2)."""
    from protocolo_cv import SerialHybridModel

    t = np.arange(0.25, 15.0 + 1e-9, 0.25)
    res = SerialHybridModel(ddm_model=model, scaler_X=dados.scaler_X, solver=dados.solver).simulate(
        ca0=ca0, eta=eta, t_eval=t)
    return pd.DataFrame({"t_min": t, "nu": res["abs_v"], "XZn": res["XZn"]})


def _avaliar_variante(args) -> Dict[str, Any]:
    nome, cfg, gamma, semente = args
    import torch

    torch.set_num_threads(1)
    from protocolo_cv import carregar_dados, rodar_cv

    dados = carregar_dados()
    res = rodar_cv(cfg, dados, sementes=(semente,), pesos=pesos_sensibilidade(dados, gamma))
    mono, curvas = [], []
    for (sem, f), model in res.modelos.items():
        mono.append({"config": nome, "semente": sem, "fold": f, "frac_dnu_dt_positivo": fracao_nao_monotona(model, dados)})
        c = curva_sem_ensaio(model, dados)
        c["config"], c["semente"], c["fold"] = nome, sem, f
        curvas.append(c)
    for df in (res.por_dobra, res.por_semente, res.oof):
        df["config"] = nome
    return {"por_dobra": res.por_dobra, "por_semente": res.por_semente, "oof": res.oof,
            "mono": pd.DataFrame(mono), "curvas": pd.concat(curvas, ignore_index=True)}


def ablacao(n_trab: int) -> None:
    from optuna.trial import TrialState

    estudo = carregar_estudo()
    completas = [t for t in estudo.trials if t.state == TrialState.COMPLETE]
    melhor = min(completas, key=lambda t: t.value)
    p = dict(melhor.params)
    p.setdefault("usar_mono", p.get("mono_lambda", 0.0) > 0)
    b2 = config_b2()
    ajustada = config_da_tentativa({**p})
    gamma, lam = float(p["gamma"]), float(ajustada["mono_lambda"])
    base_aj = dict(ajustada, mono_lambda=0.0)
    mono_aj = dict(ajustada, mono_lambda=lam if lam > 0 else 0.1)
    variantes = {
        "B2 (referência)": (b2, 0.0),
        "B2 reajustada (lr, épocas)": (base_aj, 0.0),
        "+ D1": (base_aj, gamma),
        "+ D2": (mono_aj, 0.0),
        "+ D1 + D2": (mono_aj, gamma),
    }
    jobs = [(nome, cfg, g, s) for nome, (cfg, g) in variantes.items() for s in SEMENTES_ABLACAO]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=n_trab, mp_context=mp.get_context("spawn")) as ex:
        saidas = list(ex.map(_avaliar_variante, jobs))
    print(f"Ablação em {(time.time() - t0) / 60:.1f} min")
    for chave in ("por_dobra", "por_semente", "oof", "mono", "curvas"):
        pd.concat([s[chave] for s in saidas], ignore_index=True).to_csv(OUT / f"ablacao_{chave}.csv", index=False)
    ps = pd.concat([s["por_semente"] for s in saidas], ignore_index=True)

    ref = ps[ps["config"] == "B2 (referência)"].sort_values("semente")["RMSE_X"].values
    linhas = []
    for nome in variantes:
        v = ps[ps["config"] == nome].sort_values("semente")["RMSE_X"].values
        dif = ref - v  # positivo = variante melhor que a B2
        ep = dif.std(ddof=1) / np.sqrt(len(dif))
        from scipy import stats

        linhas.append({
            "variante": nome, "RMSE_X_media": v.mean(), "RMSE_X_dp": v.std(ddof=1),
            "ganho_medio_vs_B2": dif.mean(), "ep_ganho_pareado": ep,
            "ganho_claro": bool(nome != "B2 (referência)" and dif.mean() > ep),
            "p_t_pareado": float(stats.ttest_rel(ref, v).pvalue) if nome != "B2 (referência)" else np.nan,
            "p_wilcoxon": float(stats.wilcoxon(ref, v).pvalue) if nome != "B2 (referência)" else np.nan,
            "n_melhor_que_B2_de_10": int((dif > 0).sum()),
            "gamma": variantes[nome][1], "mono_lambda": variantes[nome][0]["mono_lambda"],
            "lr": variantes[nome][0]["lr"], "max_epochs": variantes[nome][0]["max_epochs"],
        })
    tab = pd.DataFrame(linhas)
    tab.to_csv(OUT / "tabela_fase_c_ablacao.csv", index=False)
    escolhida = tab.iloc[1:].sort_values("RMSE_X_media").iloc[0]
    resumo = {
        "melhor_tentativa_optuna": melhor.number, "valor_3_sementes": melhor.value, "params": melhor.params,
        "variante_menor_RMSE": escolhida["variante"], "RMSE_X_media_10_sementes": float(escolhida["RMSE_X_media"]),
        "ganho_claro": bool(escolhida["ganho_claro"]),
        "config_base_fase_d": dict(variantes[escolhida["variante"]][0]),
        "gamma_base_fase_d": float(variantes[escolhida["variante"]][1]),
    }
    (OUT / "melhor_config_fase_c.json").write_text(json.dumps(resumo, indent=2, ensure_ascii=False), encoding="utf-8")
    print(tab.to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("etapa", choices=["buscar", "ablacao", "figuras"])
    ap.add_argument("--tentativas", type=int, default=80)
    ap.add_argument("--trabalhadores", type=int, default=26)
    a = ap.parse_args()
    if a.etapa == "buscar":
        buscar(a.tentativas, a.trabalhadores)
    elif a.etapa == "ablacao":
        ablacao(a.trabalhadores)
    else:
        from figuras_fase_c import gerar_tudo

        gerar_tudo()


if __name__ == "__main__":
    main()
