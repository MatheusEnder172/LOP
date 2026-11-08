"""Fase B2 (Subetapa 3.2.6): busca ampliada de hiperparâmetros a partir do que a Fase B mostrou.

A Fase B terminou com as melhores redes no limite do espaço (4 camadas) e com o modo de parada
"épocas fixas" claramente melhor. A B2 refina e amplia a busca:

- profundidade de 2 a 8 camadas ocultas, largura de 8 a 96;
- até 4000 épocas fixas (o modo com parada interna sai da busca, pela evidência da Fase B);
- conexões residuais (úteis em redes mais profundas);
- inicialização de Glorot (Glorot; Bengio, 2010) com o ganho de Tanh, além da padrão do PyTorch;
- entrada temporal em t ou em ln t (`KineticsMLPLogT`): ν cai várias ordens de grandeza nos
  primeiros minutos, e ln t espalha melhor os instantes iniciais.

As configurações escolhida e empatada da Fase B (tentativas 211 e 354) são enfileiradas no novo
espaço, como referência e ponto de partida. Protocolo, finalistas (10 sementes) e regra de um
erro-padrão iguais aos da Fase B.

Uso:
    python fase_b2_busca_ampliada.py buscar --tentativas 500 --trabalhadores 24
    python fase_b2_busca_ampliada.py finalistas --trabalhadores 24
    python fase_b2_busca_ampliada.py figuras
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
from typing import Any, Dict

import numpy as np
import pandas as pd

import fase_b_optuna_hpo as fb
from protocolo_cv import CONFIG_V1, OUTPUTS_DIR

OUT = Path(os.environ.get("FASE_B2_OUT", OUTPUTS_DIR / "fase_b2"))
JOURNAL = OUT / "estudo_optuna_fase_b2.log"
NOME_ESTUDO = "mlp_v2_fase_b2_busca_ampliada"
SEMENTES_BUSCA = fb.SEMENTES_BUSCA
SEMENTES_FINALISTAS = fb.SEMENTES_FINALISTAS


def sugerir_config(trial) -> Dict[str, Any]:
    n = trial.suggest_int("n_camadas", 2, 8)
    largura = trial.suggest_int("largura", 8, 96, log=True)
    forma = trial.suggest_categorical("forma", ["constante", "afunilada"])
    return {
        "hidden_dims": fb.camadas(n, largura, forma),
        "activation": trial.suggest_categorical("activation", ["GELU", "SiLU", "Tanh"]),
        "use_layer_norm": trial.suggest_categorical("use_layer_norm", [True, False]),
        "use_residual": trial.suggest_categorical("use_residual", [False, True]),
        "inicializacao": trial.suggest_categorical("inicializacao", ["padrao", "xavier"]),
        "entrada_log_t": trial.suggest_categorical("entrada_log_t", [False, True]),
        "dropout_rate": trial.suggest_float("dropout_rate", 0.0, 0.3),
        "lr": trial.suggest_float("lr", 1e-4, 1e-2, log=True),
        "weight_decay": trial.suggest_float("weight_decay", 1e-6, 1e-1, log=True),
        "batch_size": trial.suggest_categorical("batch_size", [16, 32, 64, 128, 256]),
        "modo_parada": "epocas_fixas",
        "patience": 0,
        "max_epochs": trial.suggest_int("max_epochs", 200, 4000, log=True),
        "mono_lambda": 0.0,
    }


def config_de_params(p: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "hidden_dims": fb.camadas(p["n_camadas"], p["largura"], p["forma"]),
        "activation": p["activation"], "use_layer_norm": p["use_layer_norm"], "use_residual": p["use_residual"],
        "inicializacao": p["inicializacao"], "entrada_log_t": p["entrada_log_t"],
        "dropout_rate": p["dropout_rate"], "lr": p["lr"], "weight_decay": p["weight_decay"],
        "batch_size": p["batch_size"], "modo_parada": "epocas_fixas", "patience": 0,
        "max_epochs": p["max_epochs"], "mono_lambda": 0.0,
    }


def params_da_fase_b(numero: int) -> Dict[str, Any]:
    """Parâmetros de uma tentativa da Fase B escritos no espaço da B2."""
    t = fb.carregar_estudo().trials[numero]
    p = t.params
    return {
        "n_camadas": p["n_camadas"], "largura": p["largura"], "forma": p.get("forma", "constante"),
        "activation": p["activation"], "use_layer_norm": p["use_layer_norm"], "use_residual": False,
        "inicializacao": "padrao", "entrada_log_t": False, "dropout_rate": p["dropout_rate"], "lr": p["lr"],
        "weight_decay": p["weight_decay"], "batch_size": p["batch_size"], "max_epochs": p["max_epochs_fixas"],
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
    study = optuna.load_study(
        study_name=NOME_ESTUDO, storage=_storage(),
        sampler=optuna.samplers.TPESampler(multivariate=True, group=True, seed=1042 + wid, n_startup_trials=40),
        pruner=optuna.pruners.MedianPruner(n_startup_trials=40, n_warmup_steps=1),
    )

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
        trial.set_user_attr("R2_X_medio", float(res.por_semente["R2_X"].mean()))
        trial.set_user_attr("R2_nu_medio", float(res.por_dobra["R2_nu"].mean()))
        trial.set_user_attr("hidden_dims", cfg["hidden_dims"])
        trial.set_user_attr("n_parametros", fb.n_parametros(cfg["hidden_dims"]))
        trial.set_user_attr("segundos", time.time() - t0)
        return res.objetivo

    study.optimize(objetivo, callbacks=[MaxTrialsCallback(total, states=(TrialState.COMPLETE, TrialState.PRUNED))],
                   catch=(RuntimeError, ValueError))


def buscar(total: int, n_trab: int) -> None:
    import optuna

    OUT.mkdir(parents=True, exist_ok=True)
    study = optuna.create_study(study_name=NOME_ESTUDO, storage=_storage(), direction="minimize", load_if_exists=True)
    if len(study.trials) == 0:
        for numero in (211, 354):
            study.enqueue_trial(params_da_fase_b(numero))
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
    df.to_csv(OUT / "tabela_fase_b2_tentativas.csv", index=False)
    return df


def finalistas(n_top: int, n_trab: int) -> None:
    from optuna.trial import TrialState

    completas = sorted([t for t in carregar_estudo().trials if t.state == TrialState.COMPLETE], key=lambda t: t.value)
    melhor_b = json.loads((fb.OUT / "melhor_config_fase_b.json").read_text(encoding="utf-8"))
    candidatos: Dict[str, Dict[str, Any]] = {
        "v1 (MLP-B, parada interna)": dict(CONFIG_V1, modo_parada="interna"),
        f"Fase B ({melhor_b['origem']})": melhor_b["config"],
    }
    for t in completas[:n_top]:
        candidatos[f"B2 – tentativa {t.number}"] = config_de_params(t.params)

    jobs = [(nome, cfg, s) for nome, cfg in candidatos.items() for s in SEMENTES_FINALISTAS]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=n_trab, mp_context=mp.get_context("spawn")) as ex:
        saidas = list(ex.map(fb._avaliar_semente, jobs))
    print(f"Finalistas avaliados em {(time.time() - t0) / 60:.1f} min")
    for chave in ("por_dobra", "por_semente", "oof", "curvas"):
        pd.concat([s[chave] for s in saidas], ignore_index=True).to_csv(OUT / f"finalistas_{chave}.csv", index=False)

    ps = pd.concat([s["por_semente"] for s in saidas], ignore_index=True)
    resumo = ps.groupby("config").agg(RMSE_X_media=("RMSE_X", "mean"), RMSE_X_dp=("RMSE_X", "std"),
                                      R2_X_media=("R2_X", "mean"), MAE_X_media=("MAE_X", "mean")).reset_index()
    resumo["RMSE_X_ep"] = resumo["RMSE_X_dp"] / np.sqrt(len(SEMENTES_FINALISTAS))
    resumo["n_parametros"] = [fb.n_parametros(candidatos[c]["hidden_dims"]) for c in resumo["config"]]
    resumo["config_json"] = [json.dumps(candidatos[c]) for c in resumo["config"]]
    resumo = resumo.sort_values("RMSE_X_media").reset_index(drop=True)

    # Regra de um erro-padrão entre as configurações da busca (B e B2); a v1 fica só como referência
    busca = resumo[~resumo["config"].str.startswith("v1")]
    melhor = busca.iloc[0]
    limite = melhor["RMSE_X_media"] + melhor["RMSE_X_ep"]
    escolhida = busca[busca["RMSE_X_media"] <= limite].sort_values("n_parametros").iloc[0]
    resumo["dentro_de_1_EP"] = resumo["RMSE_X_media"] <= limite
    resumo["escolhida"] = resumo["config"] == escolhida["config"]
    resumo.to_csv(OUT / "tabela_fase_b2_finalistas.csv", index=False)
    with open(OUT / "melhor_config_fase_b2.json", "w", encoding="utf-8") as f:
        json.dump({"origem": escolhida["config"], "config": candidatos[escolhida["config"]],
                   "RMSE_X_media_10_sementes": float(escolhida["RMSE_X_media"]),
                   "RMSE_X_dp_10_sementes": float(escolhida["RMSE_X_dp"])}, f, indent=2, ensure_ascii=False)
    print(resumo[["config", "RMSE_X_media", "RMSE_X_dp", "n_parametros", "dentro_de_1_EP", "escolhida"]])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("etapa", choices=["buscar", "finalistas", "figuras"])
    ap.add_argument("--tentativas", type=int, default=500)
    ap.add_argument("--trabalhadores", type=int, default=24)
    ap.add_argument("--top", type=int, default=5)
    a = ap.parse_args()
    if a.etapa == "buscar":
        buscar(a.tentativas, a.trabalhadores)
    elif a.etapa == "finalistas":
        finalistas(a.top, a.trabalhadores)
    else:
        from figuras_fase_b2 import gerar_tudo

        gerar_tudo()


if __name__ == "__main__":
    main()
