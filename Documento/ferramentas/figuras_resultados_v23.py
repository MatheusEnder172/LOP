"""Figuras da v23 do relatório: serial e black-box (MLP pura) no visual atual do grupo.

Pedido de 14/11/2026: adequar os Resultados e o apêndice da serial e do black-box às seções novas dos colegas.
Nas figuras, isso significa (i) números dos eixos x e y em todos os quadros e traço em t = 0, que o módulo
`resultados_lop.py` já faz desde 11/11, (ii) o white-box aparecer na legenda só como "White-box", como na
figura da Seção 5.1: o relatório tem um único white-box, e "(novo)" era um nome interno do grupo, e (iii) o RMSE
anotado em cada quadro sair na escala da conversão (0 a 1), sem "p.p.", como o grupo combinou em 13/11.

Nada é treinado nem recalculado: as curvas dos modelos são lidas dos CSV congelados em
`Código/outputs/resultados_por_modelagem/` e só o white-box (solução do balanço populacional) é simulado de novo.
O nome do white-box e a anotação do RMSE são trocados aqui, em tempo de execução; `padrao_graficos_lop.py` e
`resultados_lop.py` não são alterados (se o grupo quiser, a mudança pode ir para os módulos depois).

Saída: Documento/figuras_v23/  (PNG + PDF)
Uso:   python figuras_resultados_v23.py            # gera as seis figuras
       python figuras_resultados_v23.py --conferir # antes, confere que o desenho a partir dos CSV reproduz os PNG de 11/11
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DOC_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DOC_DIR / "padrao_graficos"))
import padrao_graficos_lop as pg  # noqa: E402
import resultados_lop as rl  # noqa: E402

SAIDA = DOC_DIR / "figuras_v23"
PASTAS = {"hib": "serial", "puro": "mlp_pura"}


def curvas_16(chave: str, exp: pd.DataFrame) -> dict:
    """Curvas densas e valores nos instantes medidos (exatos, de dados_plotados.csv) dos 16 ensaios."""
    nome = PASTAS[chave]
    base = rl.PASTA_RESULTADOS / nome
    cv = rl.curvas_de_csv(base / f"curvas_{nome}.csv", exp)
    d = pd.read_csv(base / "dados_plotados.csv")
    for e in cv:
        cv[e].x_pts = d.loc[d["ensaio"] == e, f"XZn_{nome}"].to_numpy(float)
    return cv


def curvas_novos(chave: str, exp: pd.DataFrame) -> dict:
    """Idem, para os quatro ensaios novos (E1 a E4)."""
    nome = PASTAS[chave]
    base = rl.PASTA_RESULTADOS / nome / "ensaios_novos"
    dens = pd.read_csv(base / f"curvas_{nome}_ensaios_novos.csv")
    pts = pd.read_csv(base / "dados_plotados_ensaios_novos.csv")
    out = {}
    for e in rl.ENSAIOS_NOVOS:
        s = dens[dens["ensaio"] == e].sort_values("t_min")
        p = pts[pts["ensaio"] == e].sort_values("t_min")
        assert len(s) > 0 and len(p) == int((exp["ensaio"] == e).sum()), e
        out[e] = rl.Curva(s["t_min"].to_numpy(float), s["XZn"].to_numpy(float), p[f"XZn_{nome}"].to_numpy(float))
    return out


def conferir_whitebox(wb: dict, chave: str, novos: bool) -> None:
    """O white-box simulado agora coincide com o gravado junto das curvas de cada modelagem."""
    nome = PASTAS[chave]
    arq = rl.PASTA_RESULTADOS / nome / ("ensaios_novos/dados_plotados_ensaios_novos.csv" if novos else "dados_plotados.csv")
    d = pd.read_csv(arq)
    for e, c in wb.items():
        ref = d.loc[d["ensaio"] == e, "XZn_whitebox_novo"].to_numpy(float)
        assert np.abs(c.x_pts - ref).max() < 1e-9, f"white-box diferente do gravado: ensaio {e}"


def gerar(pasta: Path) -> list[Path]:
    exp, exp_n = rl.carregar_experimentos(), rl.carregar_ensaios_novos()
    wb, wb_n = rl.curvas_whitebox_novo(exp), rl.curvas_whitebox_novo(exp_n)
    feitos = []
    for chave, nome in PASTAS.items():
        conferir_whitebox(wb, chave, novos=False)
        conferir_whitebox(wb_n, chave, novos=True)
        c16 = {"novo": wb, chave: curvas_16(chave, exp)}
        cn = {"novo": wb_n, chave: curvas_novos(chave, exp_n)}
        feitos += pg.salvar(rl.grafico_2x2(rl.ENSAIOS_FIGURA_TEXTO, exp, c16), pasta / f"fig_{nome}_2x2_texto_ensaios_01_07_08_14")[:1]
        feitos += pg.salvar(rl.grafico_2x2(list(rl.ENSAIOS_NOVOS), exp_n, cn), pasta / f"fig_{nome}_2x2_ensaios_novos")[:1]
        feitos += pg.salvar(rl.grafico_4x4(exp, c16), pasta / f"fig_{nome}_4x4_todos")[:1]
    return feitos


def conferir_reproducao() -> None:
    """Com o nome antigo do white-box, o desenho a partir dos CSV dá os mesmos pixels dos PNG gravados em 11/11."""
    from PIL import Image

    tmp = SAIDA / "_conferencia"
    for p in gerar(tmp):
        nome = next(n for n in PASTAS.values() if p.name.startswith(f"fig_{n}_"))
        antigo = rl.PASTA_RESULTADOS / nome / ("ensaios_novos" if "ensaios_novos" in p.name else "") / p.name
        a, b = np.asarray(Image.open(p).convert("RGB"), int), np.asarray(Image.open(antigo).convert("RGB"), int)
        dif = float(np.abs(a - b).mean()) if a.shape == b.shape else float("nan")
        print(f"  {p.name}: {a.shape[1]}x{a.shape[0]} | diferença média por pixel = {dif:.4f}")
        assert a.shape == b.shape and dif < 0.05, p.name
    for p in tmp.iterdir():
        p.unlink()
    tmp.rmdir()


def rmse_sem_pp() -> None:
    """Anotação de cada quadro com o RMSE na escala da conversão (0 a 1), como na figura da Seção 5.1.

    "RMSE (p.p.): white-box 3,4; serial 1,0" passa a "RMSE: white-box 0,034; serial 0,010" (mesmos algarismos).
    """
    original = rl._painel

    def painel(ax, e, exp, curvas, escala, modo):
        original(ax, e, exp, curvas, escala, modo)
        exp_e = exp[exp["ensaio"] == e]
        for t in ax.texts:
            linhas = t.get_text().split("\n")
            if linhas[-1].startswith("RMSE (p.p.)"):
                linhas[-1] = "RMSE: " + "; ".join(f"{rl.CURTO[pg.resolver(k)]} {pg.num(rl._rmse_pp(exp_e, cv[e]) / 100, 3)}"
                                                  for k, cv in curvas.items())
                t.set_text("\n".join(linhas))

    rl._painel = painel


if __name__ == "__main__":
    if "--conferir" in sys.argv:
        conferir_reproducao()
    pg.MODELOS["novo"] = dataclasses.replace(pg.MODELOS["novo"], nome="White-box")
    rmse_sem_pp()
    for p in gerar(SAIDA):
        print("gravado:", p.relative_to(DOC_DIR))
