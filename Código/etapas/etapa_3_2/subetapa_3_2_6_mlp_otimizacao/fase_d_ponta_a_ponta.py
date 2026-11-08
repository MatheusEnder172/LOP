"""Fase D (Subetapa 3.2.6): ajuste fino ponta a ponta através do PBM.

Em vez de só imitar os alvos ν do problema inverso, a rede pré-treinada na Fase C é ajustada
diretamente no X_Zn experimental, passando ν pela integração e pela curva X(δ) dentro do PyTorch
(`src/hybrid/pbm_torch.py`; Psichogios; Ungar, 1992; Thompson; Kramer, 1994). A perda do ajuste fino é

    MSE(X_Zn experimental) + λ_ν · MSE_log(ν, ν_alvo) + λ_D2 · penalidade de monotonia,

com λ_D2 herdado da variante da Fase C. O termo de âncora λ_ν impede que ν perca a forma física,
já que sobram cerca de 70 pontos de X por dobra. Ajuste em lote completo, número fixo de épocas,
rede em modo de avaliação (sem dropout, para a perda ser determinística).

Pré-treino: a variante da Fase C com menor RMSE em 10 sementes (`melhor_config_fase_c.json`); as redes
de cada (semente, dobra) são salvas em `fase_d/pretreino/` e reaproveitadas na busca e na comparação
final, de modo que a comparação com a Fase C seja pareada e use exatamente as mesmas redes de partida.

Uso:
    python fase_d_ponta_a_ponta.py pretreinar --trabalhadores 28
    python fase_d_ponta_a_ponta.py buscar --tentativas 60 --trabalhadores 28
    python fase_d_ponta_a_ponta.py finais --trabalhadores 28
    python fase_d_ponta_a_ponta.py figuras
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
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import torch

from protocolo_cv import OUTPUTS_DIR, TARGET, Dados

OUT = Path(os.environ.get("FASE_D_OUT", OUTPUTS_DIR / "fase_d"))
PRE = OUT / "pretreino"
JOURNAL = OUT / "estudo_optuna_fase_d.log"
NOME_ESTUDO = "mlp_v2_fase_d_ponta_a_ponta"
FASE_C = OUTPUTS_DIR / "fase_c"
SEMENTES_BUSCA = (42, 43, 44)
SEMENTES_FINAIS = tuple(range(42, 52))


def base_da_fase_c() -> Dict[str, Any]:
    """Configuração e γ da variante da Fase C que serve de pré-treino."""
    arq = Path(os.environ.get("FASE_D_BASE", FASE_C / "melhor_config_fase_c.json"))
    j = json.loads(arq.read_text(encoding="utf-8"))
    return {"config": j["config_base_fase_d"], "gamma": float(j["gamma_base_fase_d"]), "variante": j["variante_menor_RMSE"]}


def _pesos(dados: Dados, gamma: float) -> np.ndarray:
    from fase_c_perdas_fisicas import pesos_sensibilidade

    return pesos_sensibilidade(dados, gamma)


def fold_do_treino(dados: Dados, tr: List[int]) -> int:
    for fold in dados.folds:
        if sorted(set(dados.train_df["ensaio"]) - set(fold["val_ensaios"])) == sorted(tr):
            return int(fold["fold"])
    raise ValueError("Conjunto de treino não corresponde a nenhuma dobra.")


# ----------------------------------------------------------------------------------------------
# Pré-treino (rede da Fase C por semente e dobra)
# ----------------------------------------------------------------------------------------------
def _pretreinar(semente: int) -> int:
    torch.set_num_threads(1)
    from protocolo_cv import carregar_dados, rodar_cv

    dados = carregar_dados()
    base = base_da_fase_c()
    res = rodar_cv(base["config"], dados, sementes=(semente,), pesos=_pesos(dados, base["gamma"]))
    for (s, f), model in res.modelos.items():
        torch.save(model.state_dict(), PRE / f"s{s}_f{f}.pt")
    res.por_dobra.to_csv(PRE / f"por_dobra_s{semente}.csv", index=False)
    res.oof.to_csv(PRE / f"oof_s{semente}.csv", index=False)
    return semente


def pretreinar(n_trab: int, sementes=SEMENTES_FINAIS) -> None:
    PRE.mkdir(parents=True, exist_ok=True)
    pend = [s for s in sementes if not all((PRE / f"s{s}_f{f}.pt").exists() for f in range(4))]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=n_trab, mp_context=mp.get_context("spawn")) as ex:
        list(ex.map(_pretreinar, pend))
    print(f"Pré-treino de {len(pend)} sementes em {(time.time() - t0) / 60:.1f} min")


# ----------------------------------------------------------------------------------------------
# Ajuste fino ponta a ponta
# ----------------------------------------------------------------------------------------------
def x_experimental(dados: Dados, ensaios: List[int]) -> torch.Tensor:
    linhas = [dados.exp_df[dados.exp_df["ensaio"] == e].sort_values("t_min")["XZn"].values for e in ensaios]
    return torch.tensor(np.stack(linhas), dtype=torch.float64)


def ajuste_fino(model, dados: Dados, tr: List[int], cfg: Dict[str, Any], w_all: np.ndarray,
                lr: float, epocas: int, lambda_nu: float, seed: int) -> Dict[str, List[float]]:
    """Ajusta `model` (in-place) no X_Zn experimental dos ensaios `tr`, passando ν pelo PBM em torch."""
    from modelo_mlp_v2 import MLPTrainerV2
    from src.hybrid.pbm_torch import PBMTorch, montar_lote, nu_da_rede

    pbm = PBMTorch(dados.solver)
    ens = sorted(tr)
    x_lote, eta = montar_lote(dados.scaler_X, dados.meta, ens)
    x_exp = x_experimental(dados, ens)
    m = dados.mascara(ens)
    x_d = torch.tensor(dados.X_train_s[m], dtype=torch.float32)
    y_d = torch.tensor(np.log1p(dados.y_train[m]), dtype=torch.float32).view(-1, 1)
    w_d = torch.tensor(w_all[m], dtype=torch.float32).view(-1, 1)
    lam_mono = float(cfg.get("mono_lambda", 0.0))
    gen = torch.Generator().manual_seed(seed)
    trainer = None
    if lam_mono > 0.0:
        from protocolo_cv import criar_trainer

        trainer = criar_trainer(cfg, dados, seed)

    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=float(cfg["weight_decay"]))
    model.eval()
    hist: Dict[str, List[float]] = {"train_loss": [], "loss_X": [], "loss_ancora": [], "best_epoch": [epocas]}
    for _ in range(epocas):
        opt.zero_grad()
        x_pred = pbm(nu_da_rede(model, x_lote), eta)
        loss_x = torch.mean((x_pred - x_exp) ** 2)
        loss_a = torch.mean(w_d * (model.forward_log(x_d) - y_d) ** 2)
        loss = loss_x + lambda_nu * loss_a
        if trainer is not None:
            loss = loss + lam_mono * MLPTrainerV2.penalidade_monotonia(model, trainer._pontos_colocacao(gen))
        loss.backward()
        opt.step()
        hist["train_loss"].append(float(loss.item()))
        hist["loss_X"].append(float(loss_x.item()))
        hist["loss_ancora"].append(float(loss_a.item()))
    model.eval()
    return hist


def criar_callback(params: Dict[str, float], registro: Optional[list] = None):
    """Função `treinar` do `rodar_cv`: carrega a rede pré-treinada e faz o ajuste fino."""
    base = base_da_fase_c()
    cfg, gamma = base["config"], base["gamma"]

    def treinar(config, dados: Dados, s: int, tr: List[int], es: List[int]):
        from protocolo_cv import criar_trainer

        f = fold_do_treino(dados, tr)
        model = criar_trainer(cfg, dados, s).build_model()
        model.load_state_dict(torch.load(PRE / f"s{s}_f{f}.pt", weights_only=True))
        if registro is not None:
            registro.append(("antes", s, f, _nu_todos(model, dados)))
        hist = ajuste_fino(model, dados, tr, cfg, _pesos(dados, gamma), params["lr_ft"], int(params["epocas_ft"]),
                           params["lambda_nu"], seed=s + 100 * f)
        if registro is not None:
            registro.append(("depois", s, f, _nu_todos(model, dados)))
        return model, hist

    return treinar


def _nu_todos(model, dados: Dados) -> pd.DataFrame:
    from src.hybrid.pbm_torch import T_MALHA, montar_lote, nu_da_rede

    ens = sorted(dados.meta["ensaio"].tolist())
    x_lote, _ = montar_lote(dados.scaler_X, dados.meta, ens)
    with torch.no_grad():
        nu = nu_da_rede(model, x_lote).numpy()
    return pd.DataFrame({"ensaio": np.repeat(ens, len(T_MALHA)), "t_min": np.tile(T_MALHA, len(ens)), "nu": nu.ravel()})


# ----------------------------------------------------------------------------------------------
# Busca (Optuna) e comparação final
# ----------------------------------------------------------------------------------------------
def sugerir(trial) -> Dict[str, float]:
    return {
        "lr_ft": trial.suggest_float("lr_ft", 1e-5, 3e-3, log=True),
        "epocas_ft": trial.suggest_int("epocas_ft", 10, 600, log=True),
        "lambda_nu": trial.suggest_float("lambda_nu", 1e-3, 100.0, log=True),
    }


def _storage():
    import optuna
    from optuna.storages.journal import JournalFileBackend, JournalFileOpenLock

    return optuna.storages.JournalStorage(JournalFileBackend(str(JOURNAL), lock_obj=JournalFileOpenLock(str(JOURNAL))))


def _trabalhador(total: int, wid: int) -> None:
    import optuna
    from optuna.study import MaxTrialsCallback
    from optuna.trial import TrialState

    torch.set_num_threads(1)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    from protocolo_cv import carregar_dados, rodar_cv

    dados = carregar_dados()
    study = optuna.load_study(
        study_name=NOME_ESTUDO, storage=_storage(),
        sampler=optuna.samplers.TPESampler(multivariate=True, seed=3042 + wid, n_startup_trials=20),
        pruner=optuna.pruners.MedianPruner(n_startup_trials=20, n_warmup_steps=1),
    )

    def objetivo(trial) -> float:
        p = sugerir(trial)

        def ao_fim(k: int, parcial: float) -> None:
            trial.report(parcial, k)
            if trial.should_prune():
                raise optuna.TrialPruned()

        t0 = time.time()
        res = rodar_cv(base_da_fase_c()["config"], dados, sementes=SEMENTES_BUSCA, treinar=criar_callback(p),
                       ao_fim_da_dobra=ao_fim)
        if not math.isfinite(res.objetivo):
            return 1.0
        trial.set_user_attr("rmse_X_dp_sementes", res.objetivo_std)
        trial.set_user_attr("segundos", time.time() - t0)
        return res.objetivo

    study.optimize(objetivo, callbacks=[MaxTrialsCallback(total, states=(TrialState.COMPLETE, TrialState.PRUNED))],
                   catch=(RuntimeError, ValueError))


def buscar(total: int, n_trab: int) -> None:
    import optuna

    OUT.mkdir(parents=True, exist_ok=True)
    study = optuna.create_study(study_name=NOME_ESTUDO, storage=_storage(), direction="minimize", load_if_exists=True)
    if len(study.trials) == 0:
        # referência: ajuste fino praticamente nulo (deve reproduzir a Fase C) e um ajuste moderado
        study.enqueue_trial({"lr_ft": 1e-5, "epocas_ft": 10, "lambda_nu": 1.0})
        study.enqueue_trial({"lr_ft": 3e-4, "epocas_ft": 100, "lambda_nu": 1.0})
    t0 = time.time()
    ctx = mp.get_context("spawn")
    procs = [ctx.Process(target=_trabalhador, args=(total, w)) for w in range(n_trab)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    print(f"Busca concluída em {(time.time() - t0) / 60:.1f} min")
    carregar_estudo().trials_dataframe(attrs=("number", "value", "state", "params", "user_attrs", "duration")).to_csv(
        OUT / "tabela_fase_d_tentativas.csv", index=False)


def carregar_estudo():
    import optuna

    return optuna.load_study(study_name=NOME_ESTUDO, storage=_storage())


def _avaliar_final(args) -> Dict[str, Any]:
    params, semente = args
    torch.set_num_threads(1)
    from protocolo_cv import carregar_dados, rodar_cv

    dados = carregar_dados()
    registro: list = []
    res = rodar_cv(base_da_fase_c()["config"], dados, sementes=(semente,), treinar=criar_callback(params, registro))
    for df in (res.por_dobra, res.por_semente, res.oof):
        df["config"] = "Fase D (ponta a ponta)"
    nu = []
    for quando, s, f, d in registro:
        d = d.copy()
        d["quando"], d["semente"], d["fold"] = quando, s, f
        nu.append(d)
    return {"por_dobra": res.por_dobra, "por_semente": res.por_semente, "oof": res.oof,
            "nu": pd.concat(nu, ignore_index=True)}


def finais(n_trab: int) -> None:
    from scipy import stats
    from optuna.trial import TrialState

    completas = [t for t in carregar_estudo().trials if t.state == TrialState.COMPLETE]
    melhor = min(completas, key=lambda t: t.value)
    params = dict(melhor.params)
    pretreinar(n_trab)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=n_trab, mp_context=mp.get_context("spawn")) as ex:
        saidas = list(ex.map(_avaliar_final, [(params, s) for s in SEMENTES_FINAIS]))
    print(f"Comparação final em {(time.time() - t0) / 60:.1f} min")
    for chave in ("por_dobra", "por_semente", "oof", "nu"):
        pd.concat([s[chave] for s in saidas], ignore_index=True).to_csv(OUT / f"finais_{chave}.csv", index=False)
    d = pd.concat([s["por_semente"] for s in saidas], ignore_index=True).sort_values("semente")["RMSE_X"].values

    abl = pd.read_csv(FASE_C / "ablacao_por_semente.csv")
    base = base_da_fase_c()
    nomes = {"B2 (referência)": "B2", base["variante"]: f"Fase C ({base['variante']})"}
    linhas = []
    for nome_c, rotulo in nomes.items():
        ref = abl[abl["config"] == nome_c].sort_values("semente")["RMSE_X"].values
        dif = ref - d
        ep = dif.std(ddof=1) / np.sqrt(len(dif))
        linhas.append({
            "referencia": rotulo, "RMSE_ref_media": ref.mean(), "RMSE_D_media": d.mean(), "RMSE_D_dp": d.std(ddof=1),
            "ganho_medio": dif.mean(), "ep_ganho_pareado": ep, "ganho_claro": bool(dif.mean() > ep),
            "p_t_pareado": float(stats.ttest_rel(ref, d).pvalue), "p_wilcoxon": float(stats.wilcoxon(ref, d).pvalue),
            "n_D_melhor_de_10": int((dif > 0).sum()),
        })
    tab = pd.DataFrame(linhas)
    tab.to_csv(OUT / "tabela_fase_d_comparacao.csv", index=False)
    (OUT / "melhor_config_fase_d.json").write_text(json.dumps({
        "tentativa_optuna": melhor.number, "valor_3_sementes": melhor.value, "params": params,
        "base_pretreino": base["variante"], "RMSE_X_media_10_sementes": float(d.mean()),
        "RMSE_X_dp_10_sementes": float(d.std(ddof=1)),
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(tab.to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("etapa", choices=["pretreinar", "buscar", "finais", "figuras"])
    ap.add_argument("--tentativas", type=int, default=60)
    ap.add_argument("--trabalhadores", type=int, default=28)
    a = ap.parse_args()
    if a.etapa == "pretreinar":
        pretreinar(a.trabalhadores)
    elif a.etapa == "buscar":
        buscar(a.tentativas, a.trabalhadores)
    elif a.etapa == "finais":
        finais(a.trabalhadores)
    else:
        from figuras_fase_d import gerar_tudo

        gerar_tudo()


if __name__ == "__main__":
    main()
