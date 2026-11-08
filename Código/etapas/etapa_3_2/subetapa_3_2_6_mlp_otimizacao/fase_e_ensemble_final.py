"""Fase E mínima (Subetapa 3.2.6): modelo final em ensemble e avaliação única no teste cego.

Versão mínima pedida pelo usuário em 26/10/2026, sem as Fases C e D (pausadas):

1. Configuração: a escolhida na Fase B2 (tentativa 511), lida de `melhor_config_fase_b2.json`.
2. Ensemble: 10 membros, um por semente (42 a 51), cada um treinado nos 13 ensaios de treino
   (780 registros) com o número fixo de épocas da B2, sem reserva de ensaios. A predição do ensemble
   é a média de ν entre os membros, que depois passa pelo PBM (Lakshminarayanan et al., 2017).
   A faixa de incerteza de X_Zn vem de integrar cada membro separadamente.
3. Teste cego (ensaios 7, 8 e 14, 21 pontos t > 0) avaliado uma única vez, depois de o modelo
   estar congelado (Kapoor; Narayanan, 2023). Para impedir ajustes depois de ver o teste,
   `treinar` recusa sobrescrever membros já salvos.
4. Referências na mesma avaliação: a v1 (`mlp_kinetics_v1.pt`, pipeline oficial) e o modelo
   fenomenológico puro (valores da Etapa 4.2).

Não altera o `SerialHybridModel`, a Etapa 4.2 nem o campeão; a v1 continua sendo a do `main`.

Uso:
    python fase_e_ensemble_final.py treinar --trabalhadores 10
    python fase_e_ensemble_final.py avaliar
    python fase_e_ensemble_final.py figuras
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import torch

from modelo_mlp_v2 import KineticsMLPEnsemble
from protocolo_cv import (CODIGO_DIR, ENSAIOS_TESTE, OUTPUTS_DIR, TARGET, carregar_dados, criar_trainer,
                          metricas, metricas_nu, simular_X)

OUT = OUTPUTS_DIR / "fase_e"
MODELOS_DIR = CODIGO_DIR / "outputs" / "models_saved" / "mlp_v2"
ETAPA_4_2 = CODIGO_DIR / "outputs" / "etapa_4_2_avaliacao_indomain"
SEMENTES_ENSEMBLE = tuple(range(42, 52))
T_CURVA = np.arange(0.0, 15.0 + 1e-9, 0.25)


def carregar_config() -> Dict[str, Any]:
    b2 = json.loads((OUTPUTS_DIR / "fase_b2" / "melhor_config_fase_b2.json").read_text(encoding="utf-8"))
    return b2


def _treinar_membro(semente: int) -> Dict[str, Any]:
    torch.set_num_threads(1)
    dados = carregar_dados()
    cfg = carregar_config()["config"]
    t0 = time.time()
    trainer = criar_trainer(cfg, dados, semente)
    model, hist = trainer.fit_epocas_fixas(dados.X_train_s, dados.y_train)
    return {"semente": semente, "estado": {k: v.cpu() for k, v in model.state_dict().items()},
            "perda_final": hist["train_loss"][-1], "segundos": time.time() - t0}


def treinar(n_trab: int) -> None:
    existentes = sorted(MODELOS_DIR.glob("membro_semente_*.pt"))
    if existentes:
        raise SystemExit(f"Já existem {len(existentes)} membros em {MODELOS_DIR}. Para retreinar, mova-os para "
                         "uma pasta old/ com README (o teste cego já pode ter sido visto).")
    MODELOS_DIR.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    b2 = carregar_config()
    dados = carregar_dados()
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=n_trab, mp_context=mp.get_context("spawn")) as ex:
        saidas = list(ex.map(_treinar_membro, SEMENTES_ENSEMBLE))
    for s in saidas:
        torch.save(s["estado"], MODELOS_DIR / f"membro_semente_{s['semente']}.pt")
    pd.DataFrame([{k: s[k] for k in ("semente", "perda_final", "segundos")} for s in saidas]).to_csv(
        OUT / "tabela_fase_e_treino_membros.csv", index=False)
    info = {
        "descricao": "Ensemble da MLP v2 (Subetapa 3.2.6, Fase E mínima): média de ν entre os membros.",
        "origem_config": f"Fase B2 – {b2['origem']}",
        "config": b2["config"],
        "sementes": list(SEMENTES_ENSEMBLE),
        "arquivos_membros": [f"membro_semente_{s}.pt" for s in SEMENTES_ENSEMBLE],
        "ensaios_treino": sorted(int(e) for e in dados.train_df["ensaio"].unique()),
        "n_registros_treino": int(len(dados.train_df)),
        "ensaios_teste_cego": ENSAIOS_TESTE,
        "scaler": "Base de dados/processed/splits/scalers.joblib (scaler_X)",
        "como_carregar": "criar_trainer(config, dados, semente).build_model(); load_state_dict(membro); "
                         "KineticsMLPEnsemble(membros)",
        "RMSE_X_fora_da_dobra_B2_10_sementes": b2["RMSE_X_media_10_sementes"],
        "data_treino": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    (MODELOS_DIR / "mlp_v2_config.json").write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(saidas)} membros treinados em {(time.time() - t0) / 60:.1f} min -> {MODELOS_DIR}")


def carregar_membros(dados) -> List[torch.nn.Module]:
    info = json.loads((MODELOS_DIR / "mlp_v2_config.json").read_text(encoding="utf-8"))
    membros = []
    for s, arq in zip(info["sementes"], info["arquivos_membros"]):
        m = criar_trainer(info["config"], dados, s).build_model()
        m.load_state_dict(torch.load(MODELOS_DIR / arq, weights_only=True))
        m.eval()
        membros.append(m)
    return membros


def carregar_v1(dados) -> torch.nn.Module:
    from src.hybrid.serial_hybrid import SerialHybridModel

    return SerialHybridModel(model_type="mlp", solver=dados.solver).model


def _linha(modelo: str, particao: str, df: pd.DataFrame) -> Dict[str, Any]:
    erro = np.abs(df["XZn_exp"] - df["XZn_pred"])
    return {"Particao": particao, "Modelo": modelo, "n_pontos": len(df),
            **metricas(df["XZn_exp"].values, df["XZn_pred"].values), "MaxErro": float(erro.max())}


def avaliar() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    dados = carregar_dados()
    membros = carregar_membros(dados)
    ens = KineticsMLPEnsemble(membros).eval()
    v1 = carregar_v1(dados)
    treino = sorted(int(e) for e in dados.train_df["ensaio"].unique())
    todos = sorted(treino + ENSAIOS_TESTE)
    particao = {e: ("Teste cego" if e in ENSAIOS_TESTE else "Treino") for e in todos}

    # X_Zn nos pontos experimentais (t > 0): ensemble, v1 e cada membro
    pred = {"MLP v2 (ensemble)": simular_X(ens, dados, todos), "MLP v1": simular_X(v1, dados, todos)}
    por_membro = []
    for s, m in zip(SEMENTES_ENSEMBLE, membros):
        px = simular_X(m, dados, todos)
        px["semente"] = s
        por_membro.append(px)
    por_membro = pd.concat(por_membro, ignore_index=True)

    # Modelo fenomenológico puro (Etapa 4.2), nos mesmos pontos
    det = pd.read_csv(ETAPA_4_2 / "tabela_predicoes_detalhadas_16_ensaios.csv")
    fpm = det[["ensaio", "t_min", "XZn_exp", "XZn_FPM"]].rename(columns={"XZn_FPM": "XZn_pred"})
    pred["Fenomenológico puro"] = fpm

    linhas, por_ensaio = [], []
    for nome, df in pred.items():
        df = df.copy()
        df["particao"] = df["ensaio"].map(particao)
        for part in ("Treino", "Teste cego"):
            linhas.append(_linha(nome, part, df[df["particao"] == part]))
        linhas.append(_linha(nome, "Global", df))
        for e, g in df.groupby("ensaio"):
            por_ensaio.append({"ensaio": e, "particao": particao[e], "Modelo": nome,
                               **metricas(g["XZn_exp"].values, g["XZn_pred"].values)})
    # Membros isolados no teste cego (distribuição do RMSE de um único modelo)
    mt = por_membro[por_membro["ensaio"].isin(ENSAIOS_TESTE)]
    rm = mt.groupby("semente").apply(lambda g: metricas(g["XZn_exp"].values, g["XZn_pred"].values)["RMSE"],
                                     include_groups=False)
    tab = pd.DataFrame(linhas)
    tab.to_csv(OUT / "tabela_fase_e_metricas_XZn.csv", index=False)
    pd.DataFrame(por_ensaio).to_csv(OUT / "tabela_fase_e_rmse_por_ensaio.csv", index=False)
    rm.rename("RMSE_teste_cego").reset_index().to_csv(OUT / "tabela_fase_e_membros_teste_cego.csv", index=False)

    saida = pred["MLP v2 (ensemble)"][["ensaio", "t_min", "XZn_exp", "XZn_pred"]].rename(
        columns={"XZn_pred": "XZn_v2_ensemble"})
    saida["XZn_v1"] = pred["MLP v1"]["XZn_pred"].values
    saida = saida.merge(fpm.rename(columns={"XZn_pred": "XZn_FPM"})[["ensaio", "t_min", "XZn_FPM"]],
                        on=["ensaio", "t_min"], how="left")
    faixa = por_membro.groupby(["ensaio", "t_min"])["XZn_pred"].agg(["min", "max", "std"]).reset_index()
    saida = saida.merge(faixa.rename(columns={"min": "XZn_v2_membro_min", "max": "XZn_v2_membro_max",
                                              "std": "XZn_v2_membro_dp"}), on=["ensaio", "t_min"])
    saida["particao"] = saida["ensaio"].map(particao)
    saida.to_csv(OUT / "predicoes_fase_e_pontos_experimentais.csv", index=False)

    # Curvas densas (X_Zn e ν) dos ensaios de teste, para as figuras
    curvas = []
    for nome, mod in [("v2_ensemble", ens), ("v1", v1)] + [(f"membro_{s}", m) for s, m in zip(SEMENTES_ENSEMBLE, membros)]:
        c = simular_X(mod, dados, ENSAIOS_TESTE, t_eval=T_CURVA)
        c["modelo"] = nome
        curvas.append(c)
    pd.concat(curvas, ignore_index=True).to_csv(OUT / "curvas_fase_e_teste_cego.csv", index=False)

    # Métricas de ν no teste cego (malha densa, alvos do problema inverso)
    X_te = dados.scaler_X.transform(dados.test_df[["CA0_mol_L", "razao_molar_eta", "t_min"]].values)
    y_te = dados.test_df[TARGET].values
    nu = pd.DataFrame([{"Modelo": "MLP v2 (ensemble)", **metricas_nu(ens, X_te, y_te)},
                       {"Modelo": "MLP v1", **metricas_nu(v1, X_te, y_te)}])
    nu.to_csv(OUT / "tabela_fase_e_metricas_nu_teste_cego.csv", index=False)

    resumo = {
        "data_avaliacao": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "RMSE_teste_cego_membros_media": float(rm.mean()), "RMSE_teste_cego_membros_dp": float(rm.std(ddof=1)),
        "RMSE_teste_cego_membros_min": float(rm.min()), "RMSE_teste_cego_membros_max": float(rm.max()),
    }
    (OUT / "resumo_fase_e.json").write_text(json.dumps(resumo, indent=2, ensure_ascii=False), encoding="utf-8")
    print(tab.to_string(index=False))
    print(nu.to_string(index=False))
    print(resumo)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("etapa", choices=["treinar", "avaliar", "figuras"])
    ap.add_argument("--trabalhadores", type=int, default=10)
    a = ap.parse_args()
    if a.etapa == "treinar":
        treinar(a.trabalhadores)
    elif a.etapa == "avaliar":
        avaliar()
    else:
        from figuras_fase_e import gerar_tudo

        gerar_tudo()


if __name__ == "__main__":
    main()
