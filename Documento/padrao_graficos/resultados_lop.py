"""Modelo de gráficos da parte de Resultados: cada integrante gera os gráficos da sua modelagem contra o white-box.

O que sai, para cada modelagem (PINN, híbrido paralelo, híbrido serial), sempre com os 16 ensaios (13 de treino +
3 de teste cego: 7, 8 e 14) e só com o painel principal (cinética de 0 a 15 min):
  - 16 gráficos individuais   fig_<chave>_ensaio_XX
  - 4 gráficos 2x2            fig_<chave>_2x2_ensaios_XX_YY       (ensaios 1-4, 5-8, 9-12, 13-16)
  - 1 gráfico 4x4             fig_<chave>_4x4_todos                (os 16 ensaios numa única imagem)
  - tabelas: metricas_por_ensaio.csv, metricas_resumo.csv (treino, teste cego, global), dados_plotados.csv e
    curvas_<chave>.csv (a curva densa da modelagem, para juntar com as dos colegas depois).

Cada gráfico tem: pontos experimentais; curva do white-box NOVO (RRB ÷ D³ e α = 0, em azul); curva da modelagem na cor
FIXA dela (pg.MODELOS); e a linha pontilhada do limite estequiométrico, min(1, η).

Como a comparação final funciona: as funções aceitam um dicionário {chave: curvas}. Hoje com 2 chaves ({"novo", "pinn"});
na comparação, com 4 ({"novo", "pinn", "par", "hib"}), e as cores já são as mesmas. Veja `juntar_curvas`.

Contrato do seu modelo (o único código que você escreve): uma função
    prever(ca0, eta, t) -> array com X_Zn     # ca0 em mol/L, eta (adimensional), t = array de tempos em min, T = 40 °C
ou, se o seu modelo roda fora do Python, um CSV de curvas densas com colunas  ensaio, t_min, XZn  (passo <= 0,05 min
no 1º minuto; use a grade de `T_DENSO`).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import padrao_graficos_lop as pg  # noqa: E402

RAIZ = AQUI.parents[1]                 # Codigo_v4
CODIGO = RAIZ / "Código"
RAW = RAIZ / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv"
ENSAIOS_TESTE = (7, 8, 14)
T_DENSO = np.unique(np.concatenate([np.linspace(0, 2, 201), np.linspace(2, 15, 131)]))   # grade das curvas (min)
YMAX = 1.2
T_FISICA = np.arange(0.0, 15.0 + 1e-9, 0.25)   # malha comum (61 nós) da checagem de consistência física
TOL_FISICA = 1e-6                               # tolerância numérica, em fração de conversão
ENSAIOS_FIGURA_TEXTO = (1, 7, 8, 14)            # figura do texto de Resultados: um ensaio de treino e os três de teste cego
# Ensaios novos de bancada (07/11/2026): C_A0 (mol/L) e η. Medições já convertidas em X_Zn, com os rótulos E2 e E3
# trocados em relação à planilha do laboratório (hipótese do grupo; ver etapa_4_3_previsao_novos_ensaios).
ENSAIOS_NOVOS = {"E1": (0.25, 0.75), "E2": (0.75, 1.25), "E3": (0.75, 2.25), "E4": (0.25, 0.40)}
MEDICOES_NOVOS = RAIZ / "Base de dados" / "Experimentos novos" / "medicoes_XZn_ensaios_novos_E2_E3_trocados.csv"
NOME_PASTA = {"pinn": "pinn", "par": "paralelo", "hib": "serial"}   # nomes que o grupo usa nas pastas e nos arquivos
NOME_PASTA_REFERENCIA = {"puro": "mlp_pura"}   # linha de base black-box: mesmas saídas, mas fora da comparação automática
CURTO = {"novo": "white-box", "fab": "white-box (Fabrício)", "puro": "MLP pura", "pinn": "PINN", "par": "paralelo", "hib": "serial"}


@dataclass
class Curva:
    """Previsão de um modelo para um ensaio: curva densa (t, x) e valores nos instantes experimentais (x_pts)."""

    t: np.ndarray
    x: np.ndarray
    x_pts: np.ndarray


# ----------------------------------------------------------------------------------------------
# Dados e curvas
# ----------------------------------------------------------------------------------------------
def carregar_experimentos() -> pd.DataFrame:
    """Os 112 pontos experimentais (t > 0) dos 16 ensaios, com a partição (treino / teste cego)."""
    d = pd.read_csv(RAW)
    d = d[d["t_min"] > 0].sort_values(["ensaio", "t_min"]).reset_index(drop=True)
    d["particao"] = np.where(d["ensaio"].isin(ENSAIOS_TESTE), "teste cego", "treino")
    return d


def _condicoes(exp: pd.DataFrame, e: int) -> tuple[float, float]:
    d = exp[exp["ensaio"] == e]
    return float(d["CA0_mol_L"].iloc[0]), float(d["razao_molar_eta"].iloc[0])


def curvas_de_funcao(prever, exp: pd.DataFrame, t_inicio: float = 0.0) -> dict[int, Curva]:
    """Roda `prever(ca0, eta, t)` em cada ensaio: na grade densa (a partir de t_inicio) e nos tempos experimentais.

    t_inicio > 0 só se o seu modelo não aceita t = 0 (ex.: usa ln t); a curva então começa nesse tempo.
    """
    saida = {}
    for e in sorted(exp["ensaio"].unique()):
        ca0, eta = _condicoes(exp, e)
        t_exp = exp.loc[exp["ensaio"] == e, "t_min"].to_numpy(float)
        t = T_DENSO[T_DENSO >= t_inicio]
        x = np.asarray(prever(ca0, eta, t), float).ravel()
        xp = np.asarray(prever(ca0, eta, t_exp), float).ravel()
        if x.shape != t.shape or xp.shape != t_exp.shape or not (np.isfinite(x).all() and np.isfinite(xp).all()):
            raise ValueError(f"Ensaio {e}: prever() deve devolver um array finito do mesmo tamanho de t (recebeu {x.shape} para {t.shape}).")
        saida[e if isinstance(e, str) else int(e)] = Curva(t, x, xp)
    return saida


def curvas_de_csv(caminho, exp: pd.DataFrame) -> dict[int, Curva]:
    """Lê curvas densas de um CSV (colunas ensaio, t_min, XZn). Os valores nos pontos experimentais saem por interpolação linear."""
    d = pd.read_csv(caminho)
    col = "XZn" if "XZn" in d.columns else "XZn_pred"
    saida = {}
    for e in sorted(exp["ensaio"].unique()):
        s = d[d["ensaio"] == e].sort_values("t_min")
        if s.empty:
            raise ValueError(f"O CSV não tem o ensaio {e}.")
        t_exp = exp.loc[exp["ensaio"] == e, "t_min"].to_numpy(float)
        if t_exp.max() > s["t_min"].max() + 1e-9 or t_exp.min() < s["t_min"].min() - 1e-9:
            raise ValueError(f"Ensaio {e}: a curva do CSV não cobre os tempos experimentais ({t_exp.min()} a {t_exp.max()} min).")
        saida[int(e)] = Curva(s["t_min"].to_numpy(float), s[col].to_numpy(float), np.interp(t_exp, s["t_min"], s[col]))
    return saida


def curvas_whitebox_novo(exp: pd.DataFrame) -> dict[int, Curva]:
    """White-box NOVO: RRB em número ÷ D³ e α = 0 (o mesmo para todos; não mexa)."""
    sys.path.insert(0, str(CODIGO))
    from src.physics.granulometry import RosinRammlerBennet
    from src.physics.kinetics import LeachingKinetics
    from src.physics.pbm_batch import BatchPBMSolver

    solver = BatchPBMSolver(granulometry=RosinRammlerBennet(use_number_density_d3=True),
                            kinetics=LeachingKinetics(alpha_nominal=0.0), n_mesh_points=5000)
    return curvas_de_funcao(lambda ca0, eta, t: solver.simulate(ca0=ca0, eta=eta, t_eval=t)["XZn"], exp)


def salvar_curvas_csv(curvas: dict[int, Curva], caminho) -> None:
    """Grava a curva densa de uma modelagem (ensaio, t_min, XZn) para juntar com as dos colegas na comparação."""
    linhas = [{"ensaio": e, "t_min": t, "XZn": x} for e, c in curvas.items() for t, x in zip(c.t, c.x)]
    pd.DataFrame(linhas).to_csv(caminho, index=False)


PASTA_RESULTADOS = CODIGO / "outputs" / "resultados_por_modelagem"


def modelagens_disponiveis(pasta_resultados=PASTA_RESULTADOS) -> list[str]:
    """Chaves ('pinn', 'par', 'hib') das modelagens que já entregaram curvas_<nome>.csv, na ordem do padrão."""
    return [k for k, n in NOME_PASTA.items() if (Path(pasta_resultados) / n / f"curvas_{n}.csv").exists()]


def juntar_curvas(pasta_resultados=PASTA_RESULTADOS, chaves=None, exp: pd.DataFrame | None = None, wb: dict | None = None) -> dict:
    """Comparação final: lê curvas_<nome>.csv de cada colega e devolve {chave: curvas}, com o white-box novo na frente.

    chaves: modelagens a juntar (padrão: todas as que já entregaram, na ordem do padrão). Os valores nos pontos
    experimentais vêm de dados_plotados.csv (exatos) quando existir; senão, de interpolação da curva densa.
    Passe o resultado para grafico_2x2(...), grafico_4x4(...) e companhia.
    """
    exp = carregar_experimentos() if exp is None else exp
    chaves = modelagens_disponiveis(pasta_resultados) if chaves is None else [pg.resolver(k) for k in chaves]
    out = {"novo": wb if wb is not None else curvas_whitebox_novo(exp)}
    for k in chaves:
        n = NOME_PASTA[k]
        base = Path(pasta_resultados) / n
        cv = curvas_de_csv(base / f"curvas_{n}.csv", exp)
        dp = base / "dados_plotados.csv"
        if dp.exists():   # valores exatos nos pontos experimentais (a interpolação só aproxima)
            d = pd.read_csv(dp)
            for e in cv:
                cv[e].x_pts = d.loc[d["ensaio"] == e, f"XZn_{n}"].to_numpy(float)
        out[k] = cv
    return out


def curvas_whitebox_fabricio(exp: pd.DataFrame) -> dict[int, Curva]:
    """Referência: white-box ORIGINAL do Fabrício (RRB em massa, α = 5500 µm/min). Só para comparação; não é o white-box do grupo."""
    sys.path.insert(0, str(CODIGO))
    from src.physics.granulometry import RosinRammlerMassaAntiga
    from src.physics.kinetics import LeachingKinetics
    from src.physics.pbm_batch import BatchPBMSolver

    solver = BatchPBMSolver(granulometry=RosinRammlerMassaAntiga(), kinetics=LeachingKinetics(alpha_nominal=5500.0), n_mesh_points=5000)
    return curvas_de_funcao(lambda ca0, eta, t: solver.simulate(ca0=ca0, eta=eta, t_eval=t)["XZn"], exp)


def curvas_mlp_pura(exp: pd.DataFrame) -> dict[int, Curva]:
    """Referência: MLP pura da Subetapa 3.2.7 (X_Zn direto de C_A0, η, t), lida dos CSV congelados. A curva começa em 0,5 min."""
    pasta = CODIGO / "outputs" / "etapa_3_2" / "subetapa_3_2_7_mlp_puro_xzn"
    dens = pd.read_csv(pasta / "curvas_densas_mlp_puro.csv")
    pts = pd.read_csv(pasta / "predicoes_pontos_experimentais.csv").sort_values(["ensaio", "t_min"])
    out = {}
    for e in sorted(exp["ensaio"].unique()):
        d = dens[dens["ensaio"] == e].sort_values("t_min")
        out[int(e)] = Curva(d["t_min"].to_numpy(), d["XZn_pred"].to_numpy(), pts.loc[pts["ensaio"] == e, "XZn_pred"].to_numpy())
    return out


# ----------------------------------------------------------------------------------------------
# Métricas
# ----------------------------------------------------------------------------------------------
def inconsistencia_fisica(c: Curva, eta: float) -> tuple[int, int]:
    """(nós inconsistentes, nós avaliados) da curva de um ensaio na malha comum de 0,25 min.

    Um nó é inconsistente se a conversão diminui em relação ao nó anterior ou se passa do limite estequiométrico
    min(1, η) (Seção 4.2.3). A checagem é feita na curva do modelo, e não só nos 7 instantes medidos, para pegar
    violações entre as medições. TOL_FISICA evita contar ruído numérico.
    """
    t = T_FISICA[(T_FISICA >= c.t.min() - 1e-9) & (T_FISICA <= c.t.max() + 1e-9)]
    x = np.interp(t, c.t, c.x)
    diminui = np.r_[False, np.diff(x) < -TOL_FISICA]
    passa_do_limite = x > min(1.0, eta) + TOL_FISICA
    return int((diminui | passa_do_limite).sum()), len(t)


def metricas(exp: pd.DataFrame, curvas: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(por ensaio, resumo por partição) para cada modelo em `curvas`. Erros em pontos percentuais (p.p.) de X_Zn.

    Métricas comuns do grupo: R2 (só no resumo, com os pontos da partição juntos), RMSE, MAE, erro máximo absoluto e
    inconsistência física (% dos nós da malha de 0,25 min; ver `inconsistencia_fisica`).
    """
    por, res = [], []
    for k, cv in curvas.items():
        pred = np.concatenate([cv[int(e)].x_pts for e in sorted(exp["ensaio"].unique())])
        d = exp.sort_values(["ensaio", "t_min"]).assign(pred=pred)
        d["erro"] = d["pred"] - d["XZn"]
        nome = pg.estilo_de(k).nome
        fis = {int(e): inconsistencia_fisica(cv[int(e)], _condicoes(exp, e)[1]) for e in exp["ensaio"].unique()}
        for e, s in d.groupby("ensaio"):
            por.append({"modelo": nome, "ensaio": e, "particao": s["particao"].iloc[0], "n": len(s),
                        "RMSE_pp": 100 * np.sqrt((s["erro"] ** 2).mean()), "MAE_pp": 100 * s["erro"].abs().mean(),
                        "Emax_pp": 100 * s["erro"].abs().max(), "incons_fis_pct": 100 * fis[int(e)][0] / fis[int(e)][1]})
        for nome_p, s in (("Treino", d[d["particao"] == "treino"]), ("Teste cego", d[d["particao"] == "teste cego"]), ("Global", d)):
            sst = ((s["XZn"] - s["XZn"].mean()) ** 2).sum()
            ruins, nos = (sum(fis[int(e)][i] for e in s["ensaio"].unique()) for i in (0, 1))
            res.append({"modelo": nome, "particao": nome_p, "n_ensaios": s["ensaio"].nunique(), "n_pontos": len(s),
                        "RMSE_pp": 100 * np.sqrt((s["erro"] ** 2).mean()), "MAE_pp": 100 * s["erro"].abs().mean(),
                        "R2": 1 - (s["erro"] ** 2).sum() / sst, "Emax_pp": 100 * s["erro"].abs().max(),
                        "incons_fis_pct": 100 * ruins / nos})
    return pd.DataFrame(por), pd.DataFrame(res)


def carregar_ensaios_novos() -> pd.DataFrame:
    """Medições (t > 0) dos 4 ensaios novos, no mesmo formato de `carregar_experimentos` (ensaio = 'E1'..'E4')."""
    d = pd.read_csv(MEDICOES_NOVOS)
    d = d[d["t_min"] > 0].sort_values(["ensaio", "t_min"]).reset_index(drop=True)
    d["CA0_mol_L"] = d["ensaio"].map(lambda e: ENSAIOS_NOVOS[e][0])
    d["razao_molar_eta"] = d["ensaio"].map(lambda e: ENSAIOS_NOVOS[e][1])
    d["particao"] = "ensaio novo"
    return d


def metricas_ensaios_novos(exp: pd.DataFrame, curvas: dict) -> pd.DataFrame:
    """Métricas por ensaio novo, no conjunto dos quatro e sem o E1 (dado com erro experimental). Erros em p.p.

    vies_pp = média de (medido - previsto); medido_acima_limite_pct = % das medições acima de min(1, η).
    """
    linhas = []
    for k, cv in curvas.items():
        d = exp.sort_values(["ensaio", "t_min"]).copy()
        d["pred"] = np.concatenate([cv[e].x_pts for e in sorted(exp["ensaio"].unique())])
        d["erro"] = d["pred"] - d["XZn"]
        d["acima"] = d["XZn"] > np.minimum(1.0, d["razao_molar_eta"]) + TOL_FISICA
        grupos = [(e, s) for e, s in d.groupby("ensaio")] + [("Todos", d), ("Sem E1", d[d["ensaio"] != "E1"])]
        for nome_g, s in grupos:
            fis = [inconsistencia_fisica(cv[e], ENSAIOS_NOVOS[e][1]) for e in s["ensaio"].unique()]
            linhas.append({"modelo": pg.estilo_de(k).nome, "ensaio": nome_g, "n": len(s),
                           "RMSE_pp": 100 * np.sqrt((s["erro"] ** 2).mean()), "MAE_pp": 100 * s["erro"].abs().mean(),
                           "Emax_pp": 100 * s["erro"].abs().max(), "vies_pp": -100 * s["erro"].mean(),
                           "incons_fis_pct": 100 * sum(f[0] for f in fis) / sum(f[1] for f in fis),
                           "medido_acima_limite_pct": 100 * s["acima"].mean()})
    return pd.DataFrame(linhas)


def gerar_ensaios_novos(chave: str, prever, pasta=None, t_inicio: float = 0.0) -> Path:
    """Sua modelagem (já treinada, sem novo ajuste) contra os 4 ensaios novos: figura 2x2, métricas e curvas.

    Saída em Código/outputs/resultados_por_modelagem/<pinn|paralelo|serial>/ensaios_novos/.
    """
    chave = pg.resolver(chave)
    nome = {**NOME_PASTA, **NOME_PASTA_REFERENCIA}[chave]
    pasta = Path(pasta) if pasta else CODIGO / "outputs" / "resultados_por_modelagem" / nome / "ensaios_novos"
    pasta.mkdir(parents=True, exist_ok=True)
    exp = carregar_ensaios_novos()
    wb, meu = curvas_whitebox_novo(exp), curvas_de_funcao(prever, exp, t_inicio)
    curvas = {"novo": wb, chave: meu}
    pg.salvar(grafico_2x2(list(ENSAIOS_NOVOS), exp, curvas), pasta / f"fig_{nome}_2x2_ensaios_novos")
    metricas_ensaios_novos(exp, curvas).round(4).to_csv(pasta / "metricas_ensaios_novos.csv", index=False)
    salvar_curvas_csv(meu, pasta / f"curvas_{nome}_ensaios_novos.csv")
    linhas = []
    for e in ENSAIOS_NOVOS:
        for i, (_, r) in enumerate(exp[exp["ensaio"] == e].iterrows()):
            linhas.append({"ensaio": e, "CA0_mol_L": r["CA0_mol_L"], "eta": r["razao_molar_eta"],
                           "limite_estequiometrico": min(1.0, r["razao_molar_eta"]), "t_min": r["t_min"], "XZn_exp": r["XZn"],
                           "XZn_whitebox_novo": wb[e].x_pts[i], f"XZn_{nome}": meu[e].x_pts[i]})
    pd.DataFrame(linhas).to_csv(pasta / "dados_plotados_ensaios_novos.csv", index=False)
    return pasta


def _rmse_pp(exp_e: pd.DataFrame, c: Curva) -> float:
    return 100 * float(np.sqrt(np.mean((c.x_pts - exp_e["XZn"].to_numpy()) ** 2)))


# ----------------------------------------------------------------------------------------------
# Desenho
# ----------------------------------------------------------------------------------------------
def _legenda(fig, chaves) -> None:
    lim = pg.Estilo("", pg.COR_REFERENCIA, pg.LS_REFERENCIA, "", "", pg.LW_REFERENCIA + 0.2)
    pg.legenda_topo(fig, chaves=list(chaves), extras=(("Limite estequiométrico, min(1; η)", lim),))


def _painel(ax, e: int, exp: pd.DataFrame, curvas: dict, escala: float, modo: str) -> None:
    """Um quadro de ensaio. modo: 'individual' | 'grade' (2x2) | 'compacto' (4x4)."""
    exp_e = exp[exp["ensaio"] == e]
    ca0, eta = _condicoes(exp, e)
    cego = e in ENSAIOS_TESTE
    pg.linha_referencia(ax, y=min(1.0, eta))
    pg.marcador_t0(ax)
    for k, cv in curvas.items():   # a ordem do dicionário é a ordem de desenho: white-box primeiro, modelagens por cima
        est = pg.estilo_de(k)
        pg.linha_modelo(ax, cv[e].t, cv[e].x, k, lw=est.lw * escala)
    pg.pontos_exp(ax, exp_e["t_min"], exp_e["XZn"], ms=5.5 * escala, mew=0.9 * escala)
    ax.set_xlim(-0.3, 15.5)
    ax.set_ylim(0, YMAX)

    titulo = f"Ensaio {e} (teste cego)" if (modo == "individual" and cego) else f"Ensaio {e} (treino)" if modo == "individual" else f"Ensaio {e}{'*' if cego else ''}"
    ax.text(0.03, 0.965, titulo, transform=ax.transAxes, fontweight="bold", va="top", ha="left", fontsize=10 * escala, zorder=10)
    cond = f"$C_{{\\mathrm{{A0}}}}$ = {pg.num(ca0)} mol/L, η = {pg.num(eta)}" if modo != "compacto" else f"$C_{{\\mathrm{{A0}}}}$ = {pg.num(ca0)}; η = {pg.num(eta)}"
    linhas = [cond]
    if modo != "compacto" and len(curvas) <= 2:
        linhas.append("RMSE (p.p.): " + "; ".join(f"{CURTO[pg.resolver(k)]} {pg.num(_rmse_pp(exp_e, cv[e]), 1)}" for k, cv in curvas.items()))
    ax.text(0.965, 0.04, "\n".join(linhas), transform=ax.transAxes, ha="right", va="bottom", fontsize=(8.5 if modo != "compacto" else 9) * escala,
            linespacing=1.35)


def grafico_individual(e: int, exp: pd.DataFrame, curvas: dict, largura_cm: float = pg.LARGURA_CM, altura_cm: float = 8.0):
    """Um ensaio, painel único (sem rótulo (a)). Devolve a figura; grave com pg.salvar."""
    fig, gs = pg.nova_figura(altura_cm=altura_cm, largura_cm=largura_cm, n_linhas_legenda=pg.linhas_legenda(len(curvas) + 2))
    ax = fig.add_subplot(gs[0, 0])
    _painel(ax, e, exp, curvas, 1.0, "individual")
    ax.set_xlabel(pg.ROTULOS["t"])
    ax.set_ylabel(pg.ROTULOS["XZn"])
    _legenda(fig, curvas)
    return fig


def _malha(ensaios, exp, curvas, nlin, ncol, altura_cm, escala, modo, hspace, wspace, xticks, yticks, bottom_cm=1.55, y_em_todos=False):
    fig, gs = pg.nova_figura(altura_cm=altura_cm, nlin=nlin, ncol=ncol, escala_fonte=escala, hspace=hspace, wspace=wspace,
                             n_linhas_legenda=pg.linhas_legenda(len(curvas) + 2),
                             left=1.75 / pg.LARGURA_CM, bottom=bottom_cm / altura_cm)
    primeiro, eixos = None, []
    for i, e in enumerate(ensaios):
        ax = fig.add_subplot(gs[i // ncol, i % ncol], sharex=primeiro, sharey=primeiro)
        primeiro = primeiro or ax
        _painel(ax, e, exp, curvas, escala, modo)
        ax.set_xticks(xticks)
        ax.set_yticks(yticks)
        ax.label_outer()
        if y_em_todos:   # pedido do orientador: números do eixo y em todos os quadros, não só na coluna da esquerda
            ax.tick_params(labelleft=True, labelbottom=True)   # idem para o eixo x
        eixos.append(ax)
    rot = matplotlib.rcParams["axes.labelsize"]
    fig.supxlabel(pg.ROTULOS["t"], fontsize=rot, y=0.15 / altura_cm)
    fig.supylabel(pg.ROTULOS["XZn"], fontsize=rot, x=0.2 / pg.LARGURA_CM)
    _legenda(fig, curvas)
    return fig


def grafico_2x2(ensaios, exp: pd.DataFrame, curvas: dict):
    """Até 4 ensaios em malha 2x2, eixos compartilhados. Ex.: grafico_2x2([1, 2, 3, 4], ...)."""
    if not 1 <= len(ensaios) <= 4:
        raise ValueError("grafico_2x2 aceita de 1 a 4 ensaios.")
    return _malha(list(ensaios), exp, curvas, 2, 2, 12.6, 0.9, "grade", 0.3, 0.2, [0, 5, 10, 15], [0, 0.2, 0.4, 0.6, 0.8, 1.0], y_em_todos=True)


def grafico_4x4(exp: pd.DataFrame, curvas: dict, ensaios=range(1, 17)):
    """Os 16 ensaios numa única imagem (4x4). O asterisco marca teste cego: use pg.NOTA_TESTE_CEGO na legenda do Word."""
    ensaios = list(ensaios)
    if not 1 <= len(ensaios) <= 16:
        raise ValueError("grafico_4x4 aceita de 1 a 16 ensaios.")
    return _malha(ensaios, exp, curvas, 4, 4, 17.8, 0.72, "compacto", 0.32, 0.30, [0, 5, 10, 15], [0, 0.5, 1.0], bottom_cm=1.2, y_em_todos=True)


# ----------------------------------------------------------------------------------------------
# Tudo de uma vez
# ----------------------------------------------------------------------------------------------
def gerar_figuras(curvas: dict, exp: pd.DataFrame, pasta, prefixo: str) -> list[Path]:
    """Grava os 16 individuais, os 4 gráficos 2x2, o 2x2 do texto (Ensaios 3, 9, 7* e 14*) e o 4x4, em PNG + PDF.

    Devolve os caminhos dos PNG.
    """
    pasta = Path(pasta)
    feitos = []
    nome_texto = "_".join(f"{e:02d}" for e in ENSAIOS_FIGURA_TEXTO)
    feitos += pg.salvar(grafico_2x2(ENSAIOS_FIGURA_TEXTO, exp, curvas), pasta / f"fig_{prefixo}_2x2_texto_ensaios_{nome_texto}")[:1]
    for e in range(1, 17):
        feitos += pg.salvar(grafico_individual(e, exp, curvas), pasta / f"fig_{prefixo}_ensaio_{e:02d}")[:1]
    for ini in (1, 5, 9, 13):
        feitos += pg.salvar(grafico_2x2(range(ini, ini + 4), exp, curvas), pasta / f"fig_{prefixo}_2x2_ensaios_{ini:02d}_{ini + 3:02d}")[:1]
    feitos += pg.salvar(grafico_4x4(exp, curvas), pasta / f"fig_{prefixo}_4x4_todos")[:1]
    return feitos


def gerar_do_modelo(chave: str, prever=None, csv=None, pasta=None, t_inicio: float = 0.0, wb: dict | None = None) -> Path:
    """Fluxo completo de UMA modelagem contra o white-box novo. Passe `prever` (função) OU `csv` (curvas densas).

    chave: 'pinn', 'paralelo' ou 'serial' (ou 'par', 'hib'). Saída em Código/outputs/resultados_por_modelagem/<pinn|paralelo|serial>/.
    """
    if (prever is None) == (csv is None):
        raise ValueError("Passe exatamente um: prever=<função> ou csv=<caminho das curvas>.")
    chave = pg.resolver(chave)
    pastas = {**NOME_PASTA, **NOME_PASTA_REFERENCIA}
    if chave not in pastas:
        raise ValueError("Esta função é para as modelagens do grupo ('pinn', 'paralelo', 'serial') ou para a MLP pura ('puro').")
    nome = pastas[chave]
    pasta = Path(pasta) if pasta else CODIGO / "outputs" / "resultados_por_modelagem" / nome
    pasta.mkdir(parents=True, exist_ok=True)
    exp = carregar_experimentos()
    wb = wb if wb is not None else curvas_whitebox_novo(exp)
    meu = curvas_de_funcao(prever, exp, t_inicio) if prever is not None else curvas_de_csv(csv, exp)
    curvas = {"novo": wb, chave: meu}

    gerar_figuras(curvas, exp, pasta, nome)
    por, res = metricas(exp, curvas)
    por.round(4).to_csv(pasta / "metricas_por_ensaio.csv", index=False)
    res.round(4).to_csv(pasta / "metricas_resumo.csv", index=False)
    salvar_curvas_csv(meu, pasta / f"curvas_{nome}.csv")
    linhas = []
    for e in sorted(exp["ensaio"].unique()):
        d = exp[exp["ensaio"] == e]
        for i, (_, r) in enumerate(d.iterrows()):
            linhas.append({"ensaio": e, "particao": r["particao"], "CA0_mol_L": r["CA0_mol_L"], "eta": r["razao_molar_eta"],
                           "limite_estequiometrico": min(1.0, r["razao_molar_eta"]), "t_min": r["t_min"], "XZn_exp": r["XZn"],
                           "XZn_whitebox_novo": wb[int(e)].x_pts[i], f"XZn_{nome}": meu[int(e)].x_pts[i]})
    pd.DataFrame(linhas).to_csv(pasta / "dados_plotados.csv", index=False)
    print(res.round(3).to_string(index=False))
    print("saída:", pasta)
    return pasta
