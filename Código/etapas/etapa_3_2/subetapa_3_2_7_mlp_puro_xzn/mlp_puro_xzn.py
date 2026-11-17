"""Subetapa 3.2.7 — MLP pura (caixa-preta direta): (C_A0, η, t) → X_Zn, sem PBM e sem física.

Objetivo: ter uma referência "puramente orientada a dados" para comparar depois com o white-box
e com o híbrido serial. Diferente das MLPs das Subetapas 3.2.1 e 3.2.6, que aprendem a taxa de
retração |ν| (alvo vindo do problema inverso, que usa o PBM), esta rede aprende X_Zn diretamente
dos pares experimentais.

Regras (as mesmas do protocolo da Subetapa 3.2.6):
1. Treino nos 13 ensaios de treino (91 pontos t > 0). Teste cego = ensaios 7, 8 e 14 (21 pontos):
   fora de toda seleção; avaliado uma única vez, com o comitê congelado.
2. Seleção da configuração por validação cruzada com as 4 dobras por ensaio da Etapa 3.1
   (`cv_folds_info.json`), 3 sementes, 2 ensaios internos (sem os vértices) só para a parada
   antecipada, nota = RMSE agrupado de X_Zn fora da dobra (91 pontos).
3. Entradas: [C_A0, η, ln t], padronizadas (mesma transformação em ln t do restante do projeto).
   Saída: X_Zn linear, SEM sigmoide, SEM teto min(1, η), SEM monotonia: é o modelo "puro".
   Os pontos t = 0 não entram (X_Zn(0) = 0 só é imposto no desenho das curvas).
4. Modelo final: comitê de 10 redes (sementes 42 a 51), cada uma nos 13 ensaios, com o número fixo
   de épocas (mediana das melhores épocas da CV). A previsão é a média; a faixa mín–máx mostra a
   variação entre membros (não é intervalo de confiança).
5. `treinar` recusa sobrescrever membros já salvos (impede ajuste depois de ver o teste).

Uso (a partir desta pasta):
    python mlp_puro_xzn.py buscar --trabalhadores 24
    python mlp_puro_xzn.py treinar --trabalhadores 10
    python mlp_puro_xzn.py avaliar
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np
import pandas as pd
import torch
from torch import nn

SUBETAPA_DIR = Path(__file__).resolve().parent
CODIGO_DIR = SUBETAPA_DIR.parents[2]
BASE_DIR = CODIGO_DIR.parent
SPLITS_DIR = BASE_DIR / "Base de dados" / "processed" / "splits"
RAW_DIR = BASE_DIR / "Base de dados" / "raw"
OUT = CODIGO_DIR / "outputs" / "etapa_3_2" / "subetapa_3_2_7_mlp_puro_xzn"
MODELOS_DIR = CODIGO_DIR / "outputs" / "models_saved" / "mlp_puro_xzn"
ETAPA_4_2 = CODIGO_DIR / "outputs" / "etapa_4_2_avaliacao_indomain"

ENSAIOS_TESTE = [7, 8, 14]
VERTICES = [1, 2, 5, 16]
SEMENTES_CV = (42, 43, 44)
SEMENTES_ENSEMBLE = tuple(range(42, 52))
FEATURES = ["CA0_mol_L", "razao_molar_eta"]  # + ln t


# --------------------------------------------------------------------------------------
# Dados
# --------------------------------------------------------------------------------------
def carregar() -> Dict[str, Any]:
    tr = pd.read_csv(SPLITS_DIR / "train_exp.csv")[["ensaio", "CA0_mol_L", "razao_molar_eta", "t_min", "XZn_exp"]]
    te = pd.read_csv(SPLITS_DIR / "test_exp.csv")[["ensaio", "CA0_mol_L", "razao_molar_eta", "t_min", "XZn_exp"]]
    folds = json.loads((SPLITS_DIR / "cv_folds_info.json").read_text(encoding="utf-8"))
    assert not set(tr["ensaio"]) & set(ENSAIOS_TESTE), "Ensaio de teste no treino."
    assert (tr["t_min"] > 0).all() and (te["t_min"] > 0).all()
    return {"train": tr.reset_index(drop=True), "test": te.reset_index(drop=True), "folds": folds}


def matriz(df: pd.DataFrame) -> np.ndarray:
    return np.column_stack([df["CA0_mol_L"].values, df["razao_molar_eta"].values, np.log(df["t_min"].values)]).astype(np.float64)


def ensaios_parada_interna(ensaios_treino: Sequence[int], fold: int, seed: int, n: int = 2) -> List[int]:
    """Mesmo sorteio fixo do protocolo da 3.2.6 (por dobra e semente, sem os vértices)."""
    candidatos = sorted(e for e in ensaios_treino if e not in VERTICES)
    rng = np.random.default_rng(1000 * seed + fold)
    return sorted(int(e) for e in rng.choice(candidatos, size=n, replace=False))


# --------------------------------------------------------------------------------------
# Modelo e treino
# --------------------------------------------------------------------------------------
class MLPPuro(nn.Module):
    def __init__(self, hidden_dims: Sequence[int], dropout: float = 0.0):
        super().__init__()
        camadas: List[nn.Module] = []
        d = 3
        for h in hidden_dims:
            camadas += [nn.Linear(d, h), nn.GELU()]
            if dropout > 0:
                camadas.append(nn.Dropout(dropout))
            d = h
        camadas.append(nn.Linear(d, 1))
        self.net = nn.Sequential(*camadas)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def padronizador(X: np.ndarray) -> Dict[str, List[float]]:
    return {"mean": X.mean(axis=0).tolist(), "std": X.std(axis=0).tolist()}


def aplicar(X: np.ndarray, sc: Dict[str, List[float]]) -> np.ndarray:
    return (X - np.asarray(sc["mean"])) / np.asarray(sc["std"])


def treinar_rede(Xtr: np.ndarray, ytr: np.ndarray, cfg: Dict[str, Any], seed: int,
                 Xes: np.ndarray | None = None, yes: np.ndarray | None = None,
                 epocas_fixas: int | None = None) -> tuple[MLPPuro, int]:
    """Treina com parada antecipada (se Xes dado) ou com número fixo de épocas."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    model = MLPPuro(cfg["hidden_dims"], cfg.get("dropout", 0.0)).double()
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=cfg["weight_decay"])
    Xt, yt = torch.tensor(Xtr), torch.tensor(ytr)
    bs = cfg.get("batch_size", 16)
    g = torch.Generator().manual_seed(seed)
    n = len(Xt)
    max_ep = epocas_fixas if epocas_fixas is not None else cfg.get("max_epochs", 800)
    best, best_ep, best_state, sem_melhora = np.inf, 0, None, 0
    for ep in range(1, max_ep + 1):
        model.train()
        perm = torch.randperm(n, generator=g)
        for i in range(0, n, bs):
            idx = perm[i:i + bs]
            opt.zero_grad()
            loss = torch.mean((model(Xt[idx]) - yt[idx]) ** 2)
            loss.backward()
            opt.step()
        if epocas_fixas is None:
            model.eval()
            with torch.no_grad():
                v = float(torch.mean((model(torch.tensor(Xes)) - torch.tensor(yes)) ** 2))
            if v < best - 1e-9:
                best, best_ep, sem_melhora = v, ep, 0
                best_state = {k: t.clone() for k, t in model.state_dict().items()}
            else:
                sem_melhora += 1
                if sem_melhora >= cfg.get("patience", 60):
                    break
    if epocas_fixas is None and best_state is not None:
        model.load_state_dict(best_state)
    else:
        best_ep = max_ep
    model.eval()
    return model, best_ep


def prever(model: MLPPuro, Xs: np.ndarray) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        return model(torch.tensor(Xs)).numpy()


def rmse(y: np.ndarray, p: np.ndarray) -> float:
    return float(np.sqrt(np.mean((np.asarray(y) - np.asarray(p)) ** 2)))


def metricas(y: np.ndarray, p: np.ndarray) -> Dict[str, float]:
    y, p = np.asarray(y), np.asarray(p)
    ss_res, ss_tot = np.sum((y - p) ** 2), np.sum((y - y.mean()) ** 2)
    return {"R2": float(1 - ss_res / ss_tot), "RMSE": rmse(y, p), "MAE": float(np.mean(np.abs(y - p)))}


# --------------------------------------------------------------------------------------
# Busca por validação cruzada
# --------------------------------------------------------------------------------------
def grade() -> List[Dict[str, Any]]:
    """Rodada 1 (parada antecipada, 8 configurações) + rodada 2 (redes maiores, épocas fixas, lr maior).

    A rodada 2 foi acrescentada depois de ver que a parada antecipada com 2 ensaios internos parava
    em ~30 épocas (subtreino, desvio alto entre sementes). Só a CV foi consultada (teste cego intacto).
    """
    cfgs = []
    for hd in ([32, 32], [64, 32], [64, 64], [128, 64]):
        for wd in (1e-4, 1e-3):
            cfgs.append({"modo": "es", "hidden_dims": hd, "lr": 3e-3, "weight_decay": wd, "batch_size": 16,
                         "patience": 60, "max_epochs": 800, "dropout": 0.0})
    for hd in ([64, 64], [128, 64], [128, 128], [90, 45, 22]):
        for lr in (3e-3, 1e-2):
            for ep in (150, 400, 900):
                cfgs.append({"modo": "fixas", "epocas": ep, "hidden_dims": hd, "lr": lr, "weight_decay": 1e-4,
                             "batch_size": 16, "dropout": 0.0})
    return cfgs


def _tarefa_cv(args: tuple) -> Dict[str, Any]:
    torch.set_num_threads(1)
    ic, cfg, seed, fold = args
    d = carregar()
    tr_all = d["train"]
    val = list(fold["val_ensaios"])
    treino = sorted(set(tr_all["ensaio"]) - set(val))
    fixas = cfg.get("modo", "es") == "fixas"
    es = [] if fixas else ensaios_parada_interna(treino, fold["fold"], seed)
    tr = [e for e in treino if e not in es]
    m = lambda lst: tr_all["ensaio"].isin(lst).values  # noqa: E731
    sc = padronizador(matriz(tr_all[m(tr)]))
    Xtr, ytr = aplicar(matriz(tr_all[m(tr)]), sc), tr_all.loc[m(tr), "XZn_exp"].values
    if fixas:
        model, ep = treinar_rede(Xtr, ytr, cfg, seed, epocas_fixas=cfg["epocas"])
    else:
        Xes, yes = aplicar(matriz(tr_all[m(es)]), sc), tr_all.loc[m(es), "XZn_exp"].values
        model, ep = treinar_rede(Xtr, ytr, cfg, seed, Xes, yes)
    dv = tr_all[m(val)]
    p = prever(model, aplicar(matriz(dv), sc))
    return {"cfg": ic, "seed": seed, "fold": fold["fold"], "melhor_epoca": ep,
            "oof": pd.DataFrame({"ensaio": dv["ensaio"].values, "t_min": dv["t_min"].values,
                                 "XZn_exp": dv["XZn_exp"].values, "XZn_pred": p, "semente": seed, "cfg": ic})}


def buscar(trabalhadores: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = carregar()
    cfgs = grade()
    tarefas = [(ic, c, s, f) for ic, c in enumerate(cfgs) for s in SEMENTES_CV for f in d["folds"]]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=trabalhadores, mp_context=mp.get_context("spawn")) as ex:
        res = list(ex.map(_tarefa_cv, tarefas))
    oof = pd.concat([r["oof"] for r in res], ignore_index=True)
    ep = pd.DataFrame([{k: r[k] for k in ("cfg", "seed", "fold", "melhor_epoca")} for r in res])
    linhas = []
    for ic, c in enumerate(cfgs):
        g = oof[oof["cfg"] == ic]
        por_sem = [rmse(h["XZn_exp"], h["XZn_pred"]) for _, h in g.groupby("semente")]
        linhas.append({"cfg": ic, "modo": c["modo"], "epocas_fixas": c.get("epocas", np.nan), "lr": c["lr"],
                       "hidden_dims": str(c["hidden_dims"]), "weight_decay": c["weight_decay"],
                       "RMSE_cv_medio": float(np.mean(por_sem)), "RMSE_cv_dp": float(np.std(por_sem, ddof=1)),
                       "melhor_epoca_mediana": float(ep[ep["cfg"] == ic]["melhor_epoca"].median())})
    tab = pd.DataFrame(linhas).sort_values("RMSE_cv_medio").reset_index(drop=True)
    tab.to_csv(OUT / "busca_cv_configuracoes.csv", index=False)
    oof.to_csv(OUT / "busca_cv_predicoes_fora_da_dobra.csv", index=False)
    melhor = tab.iloc[0]
    cfg_escolhida = dict(cfgs[int(melhor["cfg"])])
    cfg_escolhida["epocas_finais"] = (int(cfg_escolhida["epocas"]) if cfg_escolhida["modo"] == "fixas"
                                      else int(round(melhor["melhor_epoca_mediana"])))
    (OUT / "config_escolhida.json").write_text(json.dumps({
        "config": cfg_escolhida, "RMSE_cv_medio": melhor["RMSE_cv_medio"], "RMSE_cv_dp": melhor["RMSE_cv_dp"],
        "criterio": "menor RMSE de X_Zn fora da dobra (91 pontos, 4 dobras, 3 sementes); épocas = mediana das melhores épocas",
        "data": datetime.now().isoformat(timespec="seconds")}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(tab.to_string())
    print(f"\nEscolhida: {cfg_escolhida}\nTempo: {time.time()-t0:.0f}s")


# --------------------------------------------------------------------------------------
# Comitê final
# --------------------------------------------------------------------------------------
def _treinar_membro(seed: int) -> str:
    torch.set_num_threads(1)
    d = carregar()
    cfg = json.loads((OUT / "config_escolhida.json").read_text(encoding="utf-8"))["config"]
    tr = d["train"]
    sc = padronizador(matriz(tr))
    model, _ = treinar_rede(aplicar(matriz(tr), sc), tr["XZn_exp"].values, cfg, seed, epocas_fixas=cfg["epocas_finais"])
    torch.save(model.state_dict(), MODELOS_DIR / f"mlp_puro_membro_{seed}.pt")
    return f"membro {seed} ok"


def treinar(trabalhadores: int) -> None:
    MODELOS_DIR.mkdir(parents=True, exist_ok=True)
    if list(MODELOS_DIR.glob("*.pt")):
        raise SystemExit("Já existem membros salvos em models_saved/mlp_puro_xzn: não sobrescrevo (mova para old/ com README).")
    cfg = json.loads((OUT / "config_escolhida.json").read_text(encoding="utf-8"))["config"]
    d = carregar()
    sc = padronizador(matriz(d["train"]))
    (MODELOS_DIR / "mlp_puro_config.json").write_text(json.dumps(
        {"config": cfg, "scaler": sc, "features": FEATURES + ["ln_t_min"], "sementes": list(SEMENTES_ENSEMBLE),
         "treino_ensaios": sorted(int(e) for e in d["train"]["ensaio"].unique()),
         "data": datetime.now().isoformat(timespec="seconds")}, indent=2, ensure_ascii=False), encoding="utf-8")
    with ProcessPoolExecutor(max_workers=trabalhadores, mp_context=mp.get_context("spawn")) as ex:
        for msg in ex.map(_treinar_membro, SEMENTES_ENSEMBLE):
            print(msg)
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(MODELOS_DIR.glob("*.pt"))}
    (MODELOS_DIR / "SHA256SUMS.txt").write_text("\n".join(f"{h}  {n}" for n, h in hashes.items()) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------------------
# Avaliação (teste cego uma única vez, com o comitê congelado)
# --------------------------------------------------------------------------------------
def carregar_comite() -> tuple[List[MLPPuro], Dict[str, Any]]:
    conf = json.loads((MODELOS_DIR / "mlp_puro_config.json").read_text(encoding="utf-8"))
    membros = []
    for s in conf["sementes"]:
        m = MLPPuro(conf["config"]["hidden_dims"], conf["config"].get("dropout", 0.0)).double()
        m.load_state_dict(torch.load(MODELOS_DIR / f"mlp_puro_membro_{s}.pt", map_location="cpu", weights_only=True))
        m.eval()
        membros.append(m)
    return membros, conf


def prever_comite(membros: List[MLPPuro], conf: Dict[str, Any], df: pd.DataFrame) -> np.ndarray:
    Xs = aplicar(matriz(df), conf["scaler"])
    return np.stack([prever(m, Xs) for m in membros])  # (n_membros, n_pontos)


def avaliar() -> None:
    from matplotlib import pyplot as plt
    membros, conf = carregar_comite()
    d = carregar()
    full = pd.concat([d["train"].assign(particao="Treino"), d["test"].assign(particao="Teste Cego")], ignore_index=True)
    P = prever_comite(membros, conf, full)
    full["XZn_pred"], full["XZn_min"], full["XZn_max"] = P.mean(0), P.min(0), P.max(0)
    full["teto"] = np.minimum(1.0, full["razao_molar_eta"])
    full["viola_teto"] = full["XZn_pred"] > full["teto"] + 0.005
    full["negativo"] = full["XZn_pred"] < -0.005
    full.round(5).to_csv(OUT / "predicoes_pontos_experimentais.csv", index=False)

    # --- métricas globais, por partição e por ensaio
    linhas = []
    for nome, g in (("Treino (13 ensaios, 91 pts)", full[full["particao"] == "Treino"]),
                    ("Teste cego (3 ensaios, 21 pts)", full[full["particao"] == "Teste Cego"]),
                    ("Global (16 ensaios, 112 pts)", full)):
        linhas.append({"particao": nome, **metricas(g["XZn_exp"], g["XZn_pred"]),
                       "n_viola_teto": int(g["viola_teto"].sum()), "n_pontos": len(g)})
    tab_glob = pd.DataFrame(linhas)
    tab_glob.round(5).to_csv(OUT / "metricas_mlp_puro.csv", index=False)

    ref = pd.read_csv(ETAPA_4_2 / "tabela_metricas_indomain_hibrido_vs_fpm.csv")
    por_ens = []
    for e, g in full.groupby("ensaio"):
        r = ref[ref["ensaio"] == e].iloc[0]
        por_ens.append({"ensaio": int(e), "particao": g["particao"].iloc[0], "CA0_mol_L": g["CA0_mol_L"].iloc[0],
                        "eta": g["razao_molar_eta"].iloc[0], "RMSE_MLP_puro": rmse(g["XZn_exp"], g["XZn_pred"]),
                        "RMSE_WhiteBox_novo": r["RMSE_FPM"], "RMSE_Hibrido_v1": r["RMSE_Hibrido"],
                        "RMSE_Hibrido_v2": r["RMSE_Hibrido_v2"]})
    tab_ens = pd.DataFrame(por_ens)
    tab_ens.round(5).to_csv(OUT / "metricas_por_ensaio_vs_referencias.csv", index=False)

    # --- curvas densas: violações físicas
    # Dentro da faixa dos dados (t ≥ 0,5 min, primeira amostra experimental); abaixo disso é extrapolação.
    t_fino = np.linspace(0.5, 15.0, 300)
    t_extra = np.linspace(0.02, 0.5, 25)
    extra = {}
    meta = pd.concat([d["train"], d["test"]]).groupby("ensaio")[["CA0_mol_L", "razao_molar_eta"]].first()
    curvas, viol = {}, []
    for e, m in meta.iterrows():
        df = pd.DataFrame({"CA0_mol_L": m["CA0_mol_L"], "razao_molar_eta": m["razao_molar_eta"], "t_min": t_fino})
        P_e = prever_comite(membros, conf, df)
        media = P_e.mean(0)
        curvas[int(e)] = (P_e.min(0), media, P_e.max(0))
        dfx = df.iloc[:0].reindex(range(len(t_extra))).assign(CA0_mol_L=m["CA0_mol_L"], razao_molar_eta=m["razao_molar_eta"], t_min=t_extra)
        extra[int(e)] = prever_comite(membros, conf, dfx).mean(0)
        teto = min(1.0, m["razao_molar_eta"])
        viol.append({"ensaio": int(e), "particao": "Teste Cego" if e in ENSAIOS_TESTE else "Treino",
                     "eta": m["razao_molar_eta"], "X_max_curva": float(media.max()), "teto": teto,
                     "acima_do_teto_pp": float(max(0.0, media.max() - teto) * 100),
                     "X_min_curva": float(media.min()), "maior_queda_pp": float(max(0.0, -np.diff(media).min()) * 100),
                     "X_em_15min": float(media[-1])})
    tab_viol = pd.DataFrame(viol)
    tab_viol.round(4).to_csv(OUT / "violacoes_fisicas_curvas.csv", index=False)
    dense = pd.DataFrame([{"ensaio": e, "t_min": t, "XZn_min": a, "XZn_pred": b, "XZn_max": c}
                          for e, (lo, mid, hi) in curvas.items() for t, a, b, c in zip(t_fino, lo, mid, hi)])
    dense.round(5).to_csv(OUT / "curvas_densas_mlp_puro.csv", index=False)

    # --- figura 4x4
    COR = "#1B9E77"
    fig, axes = plt.subplots(4, 4, figsize=(17, 14), sharex=True, sharey=True)
    plt.rcParams.update({"axes.grid": True, "grid.alpha": 0.35, "grid.linestyle": "--"})
    for ax, e in zip(axes.flatten(), sorted(meta.index)):
        m = meta.loc[e]; lo, mid, hi = curvas[int(e)]
        pts = full[full["ensaio"] == e]
        cego = e in ENSAIOS_TESTE
        ax.axhline(min(1.0, m["razao_molar_eta"]), color="gray", lw=1.0, ls=":")
        ax.fill_between(t_fino, lo, hi, color=COR, alpha=0.22, lw=0)
        ax.plot(t_extra, extra[int(e)], color=COR, lw=1.4, ls=":", alpha=0.9)
        ax.plot(t_fino, mid, color=COR, lw=2.2)
        ax.plot(pts["t_min"], pts["XZn_exp"], "o", color="#222222", ms=5.5, mec="white", mew=0.6, zorder=5)
        r = rmse(pts["XZn_exp"], pts["XZn_pred"]) * 100
        ax.set_title(f"Ensaio {int(e):02d} — C_A0 = {m['CA0_mol_L']:.2f} M, η = {m['razao_molar_eta']:g}" + ("  [TESTE CEGO]" if cego else ""),
                     fontweight="bold", fontsize=9.6, color="#B22222" if cego else "black")
        ax.text(0.97, 0.06, f"RMSE: {r:.1f}%", transform=ax.transAxes, ha="right", va="bottom", fontsize=9.5, color=COR,
                fontweight="bold", bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=COR, lw=0.9))
        ax.set_xlim(-0.3, 15.5); ax.set_ylim(-0.05, 1.15)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    handles = [plt.Line2D([], [], marker="o", color="#222222", ls="none", ms=7, label="Experimental"),
               plt.Line2D([], [], color=COR, lw=2.4, label="MLP pura (média do comitê de 10)"),
               plt.Rectangle((0, 0), 1, 1, color=COR, alpha=0.22, label="Faixa mín–máx entre membros"),
               plt.Line2D([], [], color=COR, ls=":", lw=1.6, label="Extrapolação (t < 0,5 min, sem dados)"),
               plt.Line2D([], [], color="gray", ls=":", lw=1.2, label="Teto min(1, η) (não imposto)")]
    fig.legend(handles=handles, loc="upper center", ncol=5, frameon=False, fontsize=11, bbox_to_anchor=(0.5, 0.965))
    g_all, g_te = tab_glob.iloc[2], tab_glob.iloc[1]
    fig.suptitle(f"MLP pura (C_A0, η, t) → X_Zn, sem PBM — RMSE global {g_all['RMSE']*100:.2f}% | teste cego {g_te['RMSE']*100:.2f}%",
                 fontweight="bold", fontsize=14.5, y=0.995)
    fig.supxlabel("Tempo de reação, t (min)", fontweight="bold", fontsize=12, y=0.02)
    fig.supylabel("Conversão de zinco, X_Zn (−)", fontweight="bold", fontsize=12, x=0.01)
    fig.text(0.5, 0.0, "Rede sem sigmoide, sem teto e sem monotonia; treinada só com t ≥ 0,5 min. "
             "A faixa é variação entre membros, não intervalo de confiança.", ha="center", fontsize=9, style="italic")
    fig.tight_layout(rect=(0.015, 0.03, 1, 0.945))
    fig.savefig(OUT / "fig_mlp_puro_xzn_4x4.png", dpi=300)
    fig.savefig(OUT / "fig_mlp_puro_xzn_4x4.pdf")
    plt.close(fig)

    print(tab_glob.round(4).to_string())
    print(tab_ens.round(4).to_string())
    print(tab_viol.round(3).to_string())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["buscar", "treinar", "avaliar"])
    ap.add_argument("--trabalhadores", type=int, default=10)
    a = ap.parse_args()
    {"buscar": lambda: buscar(a.trabalhadores), "treinar": lambda: treinar(a.trabalhadores), "avaliar": avaliar}[a.cmd]()


if __name__ == "__main__":
    main()
