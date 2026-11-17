"""Gráficos e métricas da parte de Resultados da MLP PURA (black-box) contra o white-box novo.

Mesmo fluxo do híbrido serial (`gerar_resultados_serial.py`), para a linha de base puramente orientada a dados da
Subetapa 3.2.7: comitê de 10 redes (sementes 42 a 51) que prevê X_Zn direto de (C_A0, η, ln t), sem balanço
populacional e sem restrições físicas. Só leitura do comitê congelado (hashes conferidos); nada é treinado.

As curvas começam em 0,5 min, primeiro instante com medição: a rede usa ln t e não recebe a condição inicial.
Saída: Código/outputs/resultados_por_modelagem/mlp_pura/ (16 ensaios) e .../mlp_pura/ensaios_novos/ (E1 a E4).
"""

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "Documento" / "padrao_graficos"))
sys.path.insert(0, str(RAIZ / "Código" / "etapas" / "etapa_3_2" / "subetapa_3_2_7_mlp_puro_xzn"))
import mlp_puro_xzn as mp  # noqa: E402
import resultados_lop as rl  # noqa: E402

T_INICIO = 0.5
OUT_327 = RAIZ / "Código" / "outputs" / "etapa_3_2" / "subetapa_3_2_7_mlp_puro_xzn"


def conferir_hashes() -> None:
    """Os dez arquivos do comitê são os mesmos gravados em 08/11/2026 (antes das medições dos ensaios novos)."""
    gravados = dict(reversed(l.split(maxsplit=1)) for l in (mp.MODELOS_DIR / "SHA256SUMS.txt").read_text().splitlines() if l.strip())
    gravados = {k.strip().lstrip("*"): h for k, h in gravados.items()}
    pts = sorted(mp.MODELOS_DIR.glob("*.pt"))
    assert len(pts) == 10
    for p in pts:
        assert gravados[p.name] == hashlib.sha256(p.read_bytes()).hexdigest(), f"hash diferente: {p.name}"


membros, conf = mp.carregar_comite()


def prever_membros(ca0, eta, t) -> np.ndarray:
    df = pd.DataFrame({"CA0_mol_L": ca0, "razao_molar_eta": eta, "t_min": np.asarray(t, float)})
    return mp.prever_comite(membros, conf, df)   # (10, n)


def prever(ca0, eta, t):
    return prever_membros(ca0, eta, t).mean(axis=0)


if __name__ == "__main__":
    conferir_hashes()
    pasta = rl.gerar_do_modelo("puro", prever=prever, t_inicio=T_INICIO)

    # confere com as previsões congeladas da Subetapa 3.2.7 (CSV com 5 casas)
    novo = pd.read_csv(pasta / "dados_plotados.csv")
    antigo = pd.read_csv(OUT_327 / "predicoes_pontos_experimentais.csv")
    junto = novo.merge(antigo[["ensaio", "t_min", "XZn_pred"]], on=["ensaio", "t_min"], validate="one_to_one")
    assert len(junto) == 112 and (junto["XZn_mlp_pura"] - junto["XZn_pred"]).abs().max() < 1e-5

    # cada rede isolada no teste cego e dispersão entre as redes nos 112 pontos
    exp = rl.carregar_experimentos()
    linhas, faixa = [], []
    por_membro = {s: [] for s in conf["sementes"]}
    for e in sorted(exp["ensaio"].unique()):
        d = exp[exp["ensaio"] == e]
        ca0, eta = rl._condicoes(exp, e)
        pm = prever_membros(ca0, eta, d["t_min"].to_numpy(float))
        faixa.extend(pm.max(axis=0) - pm.min(axis=0))
        if e in rl.ENSAIOS_TESTE:
            for s, linha in zip(conf["sementes"], pm):
                por_membro[s].extend(linha - d["XZn"].to_numpy(float))
    pd.DataFrame([{"semente": s, "RMSE_teste_cego": float(np.sqrt(np.mean(np.square(v))))} for s, v in por_membro.items()]) \
        .to_csv(pasta / "membros_teste_cego.csv", index=False)
    pd.DataFrame({"faixa_entre_membros": faixa}).to_csv(pasta / "faixa_entre_membros_112_pontos.csv", index=False)

    # 4 ensaios novos: mesmo comitê, sem novo ajuste
    pasta_n = rl.gerar_ensaios_novos("puro", prever=prever, t_inicio=T_INICIO)
    print(pd.read_csv(pasta / "metricas_resumo.csv").to_string(index=False))
    print(pd.read_csv(pasta / "membros_teste_cego.csv")["RMSE_teste_cego"].describe().round(5).to_string())
    print(pd.read_csv(pasta_n / "metricas_ensaios_novos.csv").to_string(index=False))
    print(pd.read_csv(pasta_n / "dados_plotados_ensaios_novos.csv").pivot(index="t_min", columns="ensaio", values="XZn_mlp_pura").round(3).to_string())
