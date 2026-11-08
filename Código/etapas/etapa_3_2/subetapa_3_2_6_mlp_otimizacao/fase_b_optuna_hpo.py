"""Fase B (Subetapa 3.2.6): busca de hiperparâmetros da MLP com Optuna, objetivo RMSE de X_Zn.

Etapas (subcomandos):
    buscar      Estudo Optuna (amostrador TPE multivariado + poda pela mediana), com vários
                processos trabalhando sobre o mesmo armazenamento em arquivo (journal).
    finalistas  Reavalia as 5 melhores configurações e a v1 com 10 sementes cada, para separar
                o efeito da configuração do efeito da semente, e escolhe a configuração pela
                regra de um erro-padrão (Hastie; Tibshirani; Friedman, 2009).
    figuras     Gera figuras, tabelas e o relatório da fase.

Uso:
    python fase_b_optuna_hpo.py buscar --tentativas 400 --trabalhadores 20
    python fase_b_optuna_hpo.py finalistas --trabalhadores 20
    python fase_b_optuna_hpo.py figuras

Cada tentativa é avaliada no protocolo comum (protocolo_cv.py): 4 dobras por ensaio, 3 sementes,
nota = RMSE de X_Zn fora da dobra nos 91 pontos experimentais, teste cego intocado.
Base bibliográfica: Goodfellow, Bengio e Courville (2016, seção 11.4); Bergstra et al. (2011, TPE);
Akiba et al. (2019, Optuna).
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
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from protocolo_cv import CONFIG_V1, OUTPUTS_DIR

# FASE_B_OUT permite rodar um teste rápido em outra pasta sem tocar nas saídas oficiais
OUT = Path(os.environ.get("FASE_B_OUT", OUTPUTS_DIR / "fase_b"))
JOURNAL = OUT / "estudo_optuna_fase_b.log"
NOME_ESTUDO = "mlp_v2_fase_b_rmse_XZn"
SEMENTES_BUSCA = (42, 43, 44)
SEMENTES_FINALISTAS = tuple(range(42, 52))
T_CURVA = np.arange(0.0, 15.0 + 1e-9, 0.25)

# Parâmetros da v1 escritos no espaço de busca (primeira tentativa enfileirada)
PARAMS_V1 = {
    "n_camadas": 2, "largura": 64, "forma": "afunilada", "activation": "GELU",
    "use_layer_norm": True, "dropout_rate": 0.0, "lr": 3e-3, "weight_decay": 1e-4,
    "batch_size": 32, "modo_parada": "interna", "patience": 60, "max_epochs_interna": 350,
}


# --------------------------------------------------------------------------- espaço de busca
def camadas(n: int, largura: int, forma: str) -> List[int]:
    if forma == "afunilada":
        return [max(8, largura // (2 ** i)) for i in range(n)]
    return [largura] * n


def sugerir_config(trial) -> Dict[str, Any]:
    """Espaço de busca da Fase B (ver README e relatório)."""
    n = trial.suggest_int("n_camadas", 1, 4)
    largura = trial.suggest_int("largura", 8, 256, log=True)
    forma = trial.suggest_categorical("forma", ["constante", "afunilada"]) if n > 1 else "constante"
    modo = trial.suggest_categorical("modo_parada", ["interna", "epocas_fixas"])
    cfg = {
        "hidden_dims": camadas(n, largura, forma),
        "activation": trial.suggest_categorical("activation", ["GELU", "SiLU", "Tanh"]),
        "use_layer_norm": trial.suggest_categorical("use_layer_norm", [True, False]),
        "dropout_rate": trial.suggest_float("dropout_rate", 0.0, 0.2),
        "lr": trial.suggest_float("lr", 1e-4, 1e-2, log=True),
        "weight_decay": trial.suggest_float("weight_decay", 1e-6, 1e-1, log=True),
        "batch_size": trial.suggest_categorical("batch_size", [16, 32, 64, 128, 256]),
        "modo_parada": modo,
        "mono_lambda": 0.0,
    }
    if modo == "interna":
        cfg["patience"] = trial.suggest_int("patience", 20, 200)
        cfg["max_epochs"] = trial.suggest_int("max_epochs_interna", 300, 2000, log=True)
    else:
        cfg["patience"] = 0
        cfg["max_epochs"] = trial.suggest_int("max_epochs_fixas", 50, 2000, log=True)
    return cfg


def config_de_params(p: Dict[str, Any]) -> Dict[str, Any]:
    """Reconstrói a configuração a partir dos parâmetros gravados de uma tentativa."""
    n = p["n_camadas"]
    modo = p["modo_parada"]
    return {
        "hidden_dims": camadas(n, p["largura"], p.get("forma", "constante") if n > 1 else "constante"),
        "activation": p["activation"], "use_layer_norm": p["use_layer_norm"],
        "dropout_rate": p["dropout_rate"], "lr": p["lr"], "weight_decay": p["weight_decay"],
        "batch_size": p["batch_size"], "modo_parada": modo, "mono_lambda": 0.0,
        "patience": p.get("patience", 0) if modo == "interna" else 0,
        "max_epochs": p["max_epochs_interna"] if modo == "interna" else p["max_epochs_fixas"],
    }


def n_parametros(hidden: List[int]) -> int:
    dims = [3] + list(hidden) + [1]
    return sum(a * b + b for a, b in zip(dims[:-1], dims[1:]))


# --------------------------------------------------------------------------- busca
def _storage():
    import optuna
    from optuna.storages.journal import JournalFileBackend, JournalFileOpenLock

    return optuna.storages.JournalStorage(JournalFileBackend(str(JOURNAL), lock_obj=JournalFileOpenLock(str(JOURNAL))))


def _trabalhador(total: int, wid: int) -> None:
    import optuna
    import torch

    torch.set_num_threads(1)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    from protocolo_cv import carregar_dados, rodar_cv

    dados = carregar_dados()
    study = optuna.load_study(study_name=NOME_ESTUDO, storage=_storage(),
                              sampler=optuna.samplers.TPESampler(multivariate=True, group=True, seed=42 + wid,
                                                                 n_startup_trials=30),
                              pruner=optuna.pruners.MedianPruner(n_startup_trials=30, n_warmup_steps=1))

    def objetivo(trial) -> float:
        cfg = sugerir_config(trial)

        def ao_fim(k: int, parcial: float) -> None:
            trial.report(parcial, k)
            if trial.should_prune():
                raise optuna.TrialPruned()

        t0 = time.time()
        res = rodar_cv(cfg, dados, sementes=SEMENTES_BUSCA, ao_fim_da_dobra=ao_fim)
        if not math.isfinite(res.objetivo):
            return 1.0
        trial.set_user_attr("rmse_X_dp_sementes", res.objetivo_std)
        trial.set_user_attr("rmse_X_por_semente", res.por_semente["RMSE_X"].tolist())
        trial.set_user_attr("R2_X_medio", float(res.por_semente["R2_X"].mean()))
        trial.set_user_attr("R2_nu_medio", float(res.por_dobra["R2_nu"].mean()))
        trial.set_user_attr("R2_log_nu_medio", float(res.por_dobra["R2_log_nu"].mean()))
        trial.set_user_attr("epocas_medias", float(res.por_dobra["epocas_rodadas"].mean()))
        trial.set_user_attr("hidden_dims", cfg["hidden_dims"])
        trial.set_user_attr("n_parametros", n_parametros(cfg["hidden_dims"]))
        trial.set_user_attr("segundos", time.time() - t0)
        return res.objetivo

    from optuna.study import MaxTrialsCallback
    from optuna.trial import TrialState

    study.optimize(objetivo, callbacks=[MaxTrialsCallback(total, states=(TrialState.COMPLETE, TrialState.PRUNED))],
                   catch=(RuntimeError, ValueError))


def buscar(total: int, n_trab: int) -> None:
    import optuna

    OUT.mkdir(parents=True, exist_ok=True)
    study = optuna.create_study(study_name=NOME_ESTUDO, storage=_storage(), direction="minimize",
                                load_if_exists=True)
    if len(study.trials) == 0:
        study.enqueue_trial(PARAMS_V1)  # v1 como ponto de partida, no mesmo protocolo
        study.enqueue_trial({**{k: v for k, v in PARAMS_V1.items() if k not in ("patience", "max_epochs_interna")},
                             "modo_parada": "epocas_fixas", "max_epochs_fixas": 350})
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
    df = carregar_estudo().trials_dataframe(attrs=("number", "value", "state", "params", "user_attrs",
                                                   "duration", "intermediate_values"))
    df.to_csv(OUT / "tabela_fase_b_tentativas.csv", index=False)
    return df


# --------------------------------------------------------------------------- finalistas
def _avaliar_semente(args) -> Dict[str, Any]:
    nome, cfg, s = args
    import torch

    torch.set_num_threads(1)
    from protocolo_cv import carregar_dados, rodar_cv, simular_X

    dados = carregar_dados()
    res = rodar_cv(cfg, dados, sementes=(s,))
    curvas = []
    for (sem, f), model in res.modelos.items():
        val = next(fd["val_ensaios"] for fd in dados.folds if fd["fold"] == f)
        c = simular_X(model, dados, val, t_eval=T_CURVA)
        c["semente"] = sem
        curvas.append(c)
    for df in (res.por_dobra, res.por_semente, res.oof):
        df["config"] = nome
    curvas = pd.concat(curvas, ignore_index=True)
    curvas["config"] = nome
    return {"por_dobra": res.por_dobra, "por_semente": res.por_semente, "oof": res.oof, "curvas": curvas}


def finalistas(n_top: int, n_trab: int) -> None:
    from optuna.trial import TrialState

    study = carregar_estudo()
    completas = sorted([t for t in study.trials if t.state == TrialState.COMPLETE], key=lambda t: t.value)
    candidatos: Dict[str, Dict[str, Any]] = {"v1 (MLP-B, parada interna)": dict(CONFIG_V1, modo_parada="interna")}
    for t in completas[:n_top]:
        candidatos[f"Tentativa {t.number}"] = config_de_params(t.params)

    jobs = [(nome, cfg, s) for nome, cfg in candidatos.items() for s in SEMENTES_FINALISTAS]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=n_trab, mp_context=mp.get_context("spawn")) as ex:
        saidas = list(ex.map(_avaliar_semente, jobs))
    print(f"Finalistas avaliados em {(time.time() - t0) / 60:.1f} min")

    for chave in ("por_dobra", "por_semente", "oof", "curvas"):
        pd.concat([s[chave] for s in saidas], ignore_index=True).to_csv(
            OUT / f"finalistas_{chave}.csv", index=False)

    ps = pd.concat([s["por_semente"] for s in saidas], ignore_index=True)
    resumo = ps.groupby("config").agg(RMSE_X_media=("RMSE_X", "mean"), RMSE_X_dp=("RMSE_X", "std"),
                                      R2_X_media=("R2_X", "mean"), MAE_X_media=("MAE_X", "mean")).reset_index()
    resumo["RMSE_X_ep"] = resumo["RMSE_X_dp"] / np.sqrt(len(SEMENTES_FINALISTAS))
    resumo["n_parametros"] = [n_parametros(candidatos[c]["hidden_dims"]) for c in resumo["config"]]
    resumo["config_json"] = [json.dumps(candidatos[c]) for c in resumo["config"]]
    resumo = resumo.sort_values("RMSE_X_media").reset_index(drop=True)

    # Regra de um erro-padrão: entre as configurações dentro de 1 EP da melhor, fica a de menos parâmetros
    so_busca = resumo[~resumo["config"].str.startswith("v1")]
    melhor = so_busca.iloc[0]
    limite = melhor["RMSE_X_media"] + melhor["RMSE_X_ep"]
    escolhida = so_busca[so_busca["RMSE_X_media"] <= limite].sort_values("n_parametros").iloc[0]
    resumo["dentro_de_1_EP"] = resumo["RMSE_X_media"] <= limite
    resumo["escolhida"] = resumo["config"] == escolhida["config"]
    resumo.to_csv(OUT / "tabela_fase_b_finalistas.csv", index=False)
    cfg_escolhida = candidatos[escolhida["config"]]
    with open(OUT / "melhor_config_fase_b.json", "w", encoding="utf-8") as f:
        json.dump({"origem": escolhida["config"], "config": cfg_escolhida,
                   "RMSE_X_media_10_sementes": float(escolhida["RMSE_X_media"]),
                   "RMSE_X_dp_10_sementes": float(escolhida["RMSE_X_dp"])}, f, indent=2, ensure_ascii=False)
    print(resumo[["config", "RMSE_X_media", "RMSE_X_dp", "n_parametros", "dentro_de_1_EP", "escolhida"]])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("etapa", choices=["buscar", "finalistas", "figuras"])
    ap.add_argument("--tentativas", type=int, default=400)
    ap.add_argument("--trabalhadores", type=int, default=20)
    ap.add_argument("--top", type=int, default=5)
    a = ap.parse_args()
    if a.etapa == "buscar":
        buscar(a.tentativas, a.trabalhadores)
    elif a.etapa == "finalistas":
        finalistas(a.top, a.trabalhadores)
    else:
        from figuras_fase_b import gerar_tudo

        gerar_tudo()


if __name__ == "__main__":
    main()
