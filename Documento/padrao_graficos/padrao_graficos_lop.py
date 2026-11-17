"""Padrão de gráficos do grupo LOP para a seção de Resultados (estilo C).

Estilo C: fonte serifada (Times New Roman, a mesma do Word), caixa completa, grade pontilhada leve,
paleta Okabe-Ito (segura para daltonismo) e REDUNDÂNCIA: além da cor, cada modelo tem linha, marcador e
hachura próprios, então a figura continua legível em impressão preto e branco.

Uso mínimo:

    import padrao_graficos_lop as pg

    fig, gs = pg.nova_figura(altura_cm=9, nlin=1, ncol=2)
    a, b = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    pg.linha_modelo(a, t, x_hib, "hib")
    pg.pontos_exp(a, t_exp, x_exp)
    a.set_xlabel(pg.ROTULOS["t"]); a.set_ylabel(pg.ROTULOS["XZn"])
    pg.rotular_paineis([a, b])
    pg.legenda_topo(fig)
    pg.salvar(fig, "caminho/fig_R1_cinetica")      # grava .png (300 DPI) e .pdf

Regras que o módulo aplica sozinho: largura 16 cm, 300 DPI, sem título dentro da figura (a legenda vai no Word),
vírgula como separador decimal nos eixos, rótulos de painel (a), (b), (c) e cores fixas por modelo.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import ScalarFormatter

# ----------------------------------------------------------------------------------------------
# Tamanhos e saída
# ----------------------------------------------------------------------------------------------
LARGURA_CM = 16.0        # coluna A4 inteira
LARGURA_MEIA_CM = 7.8    # meia coluna (figura pequena, lado a lado no Word)
DPI = 300
_CM = 1 / 2.54

# ----------------------------------------------------------------------------------------------
# Paleta (Okabe-Ito) — NÃO trocar cores. Amarelo fica de fora (pouco contraste no fundo branco).
# ----------------------------------------------------------------------------------------------
OKABE_ITO = {
    "laranja": "#E69F00",
    "azul_claro": "#56B4E9",
    "verde": "#009E73",
    "azul": "#0072B2",
    "vermelhao": "#D55E00",
    "roxo": "#CC79A7",
    "preto": "#000000",
}
COR_EXPERIMENTAL = "#000000"   # pontos experimentais: círculo preto com miolo branco
COR_REFERENCIA = "#555555"     # linhas de referência (diagonal y = x, teto físico, zero)
LS_REFERENCIA = (0, (1, 2.2))  # pontos finos e espaçados: não se confunde com a curva pontilhada grossa do white-box novo
LW_REFERENCIA = 0.9
COR_GRADE = "#000000"          # grade com transparência 0,25 (ver aplicar_estilo)


@dataclass(frozen=True)
class Estilo:
    """Identidade visual de uma série: nome na legenda, cor, tipo de linha, marcador, hachura e espessura."""

    nome: str
    cor: str
    ls: object
    marcador: str
    hachura: str
    lw: float


# Modelos da seção de Resultados. A ordem de MODELOS é a ordem da legenda e das barras.
#   Modelagens do grupo:  novo (white-box, referência de todos), pinn, par (híbrido paralelo) e hib (híbrido serial).
#   Referências extras:   fab (white-box original do Fabrício) e puro (MLP pura, caixa-preta).
MODELOS: dict[str, Estilo] = {
    "fab": Estilo("White-box (Fabrício)", OKABE_ITO["laranja"], "--", "s", "///", 1.6),
    "novo": Estilo("White-box (novo)", OKABE_ITO["azul"], ":", "^", "...", 1.9),
    "puro": Estilo("MLP pura", OKABE_ITO["verde"], "-.", "D", "xxx", 1.6),
    "pinn": Estilo("PINN", OKABE_ITO["vermelhao"], (0, (5, 1, 1, 1, 1, 1)), "v", "\\\\\\", 2.0),
    "par": Estilo("Híbrido paralelo", OKABE_ITO["azul_claro"], (0, (8, 2)), "P", "++", 2.0),
    "hib": Estilo("Híbrido serial", OKABE_ITO["roxo"], "-", "o", "", 2.2),
}
# Apelidos aceitos em qualquer função (o nome interno do híbrido serial é "hib" por história do projeto).
ALIAS = {"serial": "hib", "paralelo": "par", "whitebox": "novo", "white-box": "novo", "fabricio": "fab", "mlp": "puro"}
# Os quatro da primeira comparação (legenda e barras padrão). Para PINN e paralelo, passe chaves=... explicitamente.
ORDEM_LEGENDA_PADRAO = ("fab", "novo", "puro", "hib")

# Séries que NÃO são modelos (níveis de η, temperaturas, variantes), na ordem de uso. Só sobrou uma cor reservada.
EXTRAS: list[Estilo] = [
    Estilo("", "#6E6E6E", (0, (1, 1)), "X", "||", 1.6),
]

# Rótulos padrão. Use sempre estes (nada de "Xzn", "X_Zn" ou "conversão" solto).
ROTULOS = {
    "t": "Tempo de reação, $t$ (min)",
    "XZn": r"Conversão de zinco, $X_{\mathrm{Zn}}$ (–)",
    "XZn_exp": r"$X_{\mathrm{Zn}}$ experimental (–)",
    "XZn_mod": r"$X_{\mathrm{Zn}}$ do modelo (–)",
    "RMSE": r"RMSE de $X_{\mathrm{Zn}}$ (p.p.)",
    "CA0": r"$C_{\mathrm{A0}}$ (mol/L)",
    "eta": "η (–)",
    "ensaio": "Ensaio",
}
NOTA_TESTE_CEGO = "* ensaio de teste cego"   # texto para a legenda da figura no Word
LEGENDA_EXPERIMENTAL = "Experimental"


def serie_extra(i: int) -> Estilo:
    """i-ésima série extra (0, 1, 2). Esgotou? Fale com o grupo antes de inventar outra cor."""
    if i >= len(EXTRAS):
        raise ValueError(f"Só há {len(EXTRAS)} séries extras no padrão; combine com o grupo antes de criar outra.")
    return EXTRAS[i]


def registrar_modelo(chave: str, estilo: Estilo) -> None:
    """Acrescenta um modelo novo ao padrão, recusando cor repetida (cada modelo = uma cor, em todo o relatório)."""
    usadas = {e.cor.lower() for e in MODELOS.values()} | {e.cor.lower() for e in EXTRAS}
    if estilo.cor.lower() in usadas:
        raise ValueError(f"A cor {estilo.cor} já pertence a outra série do padrão.")
    MODELOS[chave] = estilo


def resolver(chave):
    """Chave canônica de MODELOS a partir de um apelido ('serial' -> 'hib'); índices inteiros (extras) passam direto."""
    if isinstance(chave, int):
        return chave
    c = ALIAS.get(str(chave).lower(), chave)
    if c not in MODELOS:
        raise KeyError(f"Modelo '{chave}' desconhecido. Opções: {sorted(MODELOS)} e apelidos {sorted(ALIAS)}.")
    return c


def estilo_de(chave) -> Estilo:
    """Estilo de um modelo (chave de MODELOS ou apelido) ou de uma série extra (por índice inteiro)."""
    c = resolver(chave)
    return serie_extra(c) if isinstance(c, int) else MODELOS[c]


_REFERENCIAS = ("fab", "novo", "puro")   # desenhadas por baixo; as modelagens do grupo ficam por cima


# ----------------------------------------------------------------------------------------------
# Fonte e estilo global
# ----------------------------------------------------------------------------------------------
def _fonte_serifada() -> str | None:
    for nome in ("Times New Roman", "Liberation Serif", "Nimbus Roman", "TeX Gyre Termes"):
        try:
            font_manager.findfont(nome, fallback_to_default=False)
            return nome
        except ValueError:
            continue
    return None


def aplicar_estilo(escala: float = 1.0) -> None:
    """Configura o matplotlib com o estilo C. É chamada por nova_figura(); pode ser chamada à mão também.

    escala: multiplica os tamanhos de fonte (use 0,7 a 0,85 em figuras com muitos painéis, como a malha 4x4).
    A legenda não encolhe.
    """
    fonte = _fonte_serifada()
    rc: dict = {
        "font.size": 10 * escala,
        "axes.labelsize": 10 * escala,
        "xtick.labelsize": 9 * escala,
        "ytick.labelsize": 9 * escala,
        "legend.fontsize": 8.2,
        "axes.linewidth": 0.8,
        "axes.spines.top": True,
        "axes.spines.right": True,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": ":",
        "grid.color": COR_GRADE,
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "axes.titlesize": 10,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
        "hatch.linewidth": 0.5,
        "lines.solid_capstyle": "round",
        "figure.dpi": 100,
        "savefig.dpi": DPI,
        "pdf.fonttype": 42,   # fonte embutida no PDF (texto selecionável, sem Type 3)
        "ps.fonttype": 42,
        "axes.unicode_minus": True,
    }
    if fonte is not None:
        rc |= {
            "font.family": "serif",
            "font.serif": [fonte],
            "mathtext.fontset": "custom",
            "mathtext.rm": fonte,
            "mathtext.it": f"{fonte}:italic",
            "mathtext.bf": f"{fonte}:bold",
            "mathtext.default": "it",
        }
    else:
        warnings.warn("Times New Roman não encontrada; usando STIX (parecida). Instale a fonte para o padrão exato.")
        rc |= {"font.family": "serif", "font.serif": ["STIXGeneral"], "mathtext.fontset": "stix"}
    matplotlib.rcParams.update(rc)


class FormatadorVirgula(ScalarFormatter):
    """Igual ao formatador numérico padrão, mas com vírgula decimal (português)."""

    def __call__(self, x, pos=None):
        return super().__call__(x, pos).replace(".", ",")

    def get_offset(self):
        return super().get_offset().replace(".", ",")


def num(valor: float, casas: int = 2) -> str:
    """Número em texto com vírgula decimal: num(0.0657, 3) -> '0,066'. Use em anotações e rótulos."""
    return f"{valor:.{casas}f}".replace(".", ",")


# ----------------------------------------------------------------------------------------------
# Figura, painéis e legenda
# ----------------------------------------------------------------------------------------------
def linhas_legenda(n_itens: int) -> int:
    """Quantas linhas a legenda do topo ocupa: 1 linha até 4 itens, 2 linhas de 5 a 8."""
    return 1 if n_itens <= 4 else 2


def nova_figura(altura_cm: float, nlin: int = 1, ncol: int = 1, largura_cm: float = LARGURA_CM, legenda_no_topo: bool = True,
                escala_fonte: float = 1.0, n_linhas_legenda: int = 1, **gridspec):
    """Cria a figura na largura padrão e devolve (fig, gs). Adicione painéis com fig.add_subplot(gs[i, j]).

    legenda_no_topo=True reserva a faixa de cima para legenda_topo(); passe False se a figura não tiver legenda.
    escala_fonte: veja aplicar_estilo (0,7 a 0,85 para malhas com muitos painéis).
    n_linhas_legenda: 2 quando a legenda tem mais de 4 itens (use linhas_legenda(n)); reserva mais margem no topo.
    gridspec aceita left, right, top, bottom, hspace, wspace, height_ratios, width_ratios.
    """
    aplicar_estilo(escala_fonte)
    fig = plt.figure(figsize=(largura_cm * _CM, altura_cm * _CM))
    # Margens em cm (não em fração), para o rótulo do eixo x não ser cortado em figuras baixas.
    kw = {"left": 1.6 / largura_cm, "right": 1 - 0.35 / largura_cm,
          "top": 1 - ((1.4 + 0.5 * (n_linhas_legenda - 1)) if legenda_no_topo else 0.35) / altura_cm, "bottom": 1.5 / altura_cm, "hspace": 0.48, "wspace": 0.32}
    kw.update(gridspec)
    gs = GridSpec(nlin, ncol, figure=fig, **kw)
    return fig, gs


def rotular_paineis(eixos, x: float = 0.03, y: float = 0.95) -> None:
    """Escreve (a), (b), (c)... em negrito no canto superior esquerdo de cada painel, na ordem dada."""
    for i, ax in enumerate(eixos):
        ax.text(x, y, f"({chr(ord('a') + i)})", transform=ax.transAxes, fontweight="bold", va="top", ha="left", zorder=10)


def legenda_topo(fig, chaves=None, experimental: bool = True, extras: tuple = (), y: float = 0.995, ncol: int | None = None, barras: bool = False):
    """Legenda numa linha só acima de todos os painéis, com linha+marcador de cada série.

    chaves: modelos a mostrar, na ordem dada (padrão: ORDEM_LEGENDA_PADRAO = fab, novo, puro, hib). Aceita apelidos.
    extras: tuplas (nome, Estilo) para séries que não são modelos, ex.: (("η = 0,5", serie_extra(0)),).
    barras: True quando a figura é só de barras: a legenda mostra o quadrado com cor + hachura em vez de linha + marcador.
            Se a figura mistura curvas e barras, deixe False (e a hachura repete a identificação das barras).
    """
    chaves = list(ORDEM_LEGENDA_PADRAO) if chaves is None else list(chaves)
    itens = [(estilo_de(k).nome, estilo_de(k)) for k in chaves] + list(extras)
    if barras:
        proxies = [Patch(facecolor=e.cor, edgecolor="black", hatch=e.hachura, linewidth=0.5, label=nome) for nome, e in itens]
    else:
        proxies = [Line2D([], [], color=e.cor, ls=e.ls, lw=e.lw, marker=e.marcador, ms=4.5, label=nome) for nome, e in itens]
    if experimental:
        proxies.append(Line2D([], [], color=COR_EXPERIMENTAL, ls="none", marker="o", ms=5, mfc="white", mec=COR_EXPERIMENTAL, label=LEGENDA_EXPERIMENTAL))
    n = len(proxies)
    ncol = ncol or (n if n <= 4 else -(-n // 2))
    nlin = -(-n // ncol)
    # matplotlib preenche a legenda por colunas; reordena para a leitura ser da esquerda para a direita, linha a linha
    ordem = [r * ncol + c for c in range(ncol) for r in range(nlin) if r * ncol + c < n]
    return fig.legend(handles=[proxies[i] for i in ordem], loc="upper center", ncol=ncol, frameon=False, bbox_to_anchor=(0.54, y),
                      handlelength=2.2, columnspacing=1.0)


# ----------------------------------------------------------------------------------------------
# Elementos de gráfico
# ----------------------------------------------------------------------------------------------
def linha_modelo(ax, x, y, chave, **kw):
    """Curva de um modelo com a cor, o tipo de linha e a espessura do padrão."""
    e = estilo_de(chave)
    args = {"color": e.cor, "ls": e.ls, "lw": e.lw, "zorder": 3 if resolver(chave) in _REFERENCIAS else 4} | kw
    return ax.plot(x, y, **args)


def pontos_exp(ax, x, y, **kw):
    """Pontos experimentais: círculo preto com miolo branco, sempre por cima das curvas."""
    args = {"marker": "o", "ls": "none", "color": COR_EXPERIMENTAL, "ms": 5.5, "mec": COR_EXPERIMENTAL, "mfc": "white", "mew": 0.9, "zorder": 6} | kw
    return ax.plot(x, y, **args)


def dispersao_modelo(ax, x, y, chave, **kw):
    """Gráfico de paridade: pontos de um modelo com o marcador e a cor do padrão."""
    e = estilo_de(chave)
    ref = resolver(chave) in _REFERENCIAS
    args = {"s": 11 if ref else 14, "marker": e.marcador, "facecolors": e.cor, "edgecolors": e.cor, "linewidths": 0.6, "alpha": 0.85, "zorder": 3 if ref else 4} | kw
    return ax.scatter(x, y, **args)


def diagonal_paridade(ax, lo: float, hi: float) -> None:
    """Reta y = x tracejada e eixos quadrados com a mesma faixa."""
    ax.plot([lo, hi], [lo, hi], color=COR_REFERENCIA, lw=LW_REFERENCIA, ls=LS_REFERENCIA, zorder=1)
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal")


def linha_referencia(ax, y: float | None = None, x: float | None = None) -> None:
    """Linha de referência pontilhada (teto físico min(1, η), zero, valor-alvo)."""
    if y is not None:
        ax.axhline(y, color=COR_REFERENCIA, lw=LW_REFERENCIA, ls=LS_REFERENCIA, zorder=1)
    if x is not None:
        ax.axvline(x, color=COR_REFERENCIA, lw=LW_REFERENCIA, ls=LS_REFERENCIA, zorder=1)


def marcador_t0(ax) -> None:
    """Traço de t = 0 no eixo x, igual aos de 5, 10 e 15 min (pequeno, para dentro, embaixo e em cima).

    O traço que o matplotlib desenha em t = 0 fica escondido porque as curvas nascem ali; este é redesenhado por cima.
    """
    kw = {"ls": "none", "color": "black", "ms": matplotlib.rcParams["xtick.major.size"], "mew": matplotlib.rcParams["xtick.major.width"],
          "clip_on": False, "zorder": 7, "transform": ax.get_xaxis_transform()}
    ax.plot([0], [0], marker=matplotlib.markers.TICKUP, **kw)
    ax.plot([0], [1], marker=matplotlib.markers.TICKDOWN, **kw)


def rotulos_ensaio(ensaios, cegos=()) -> list[str]:
    """Rótulos de eixo para ensaios, com asterisco nos de teste cego: rotulos_ensaio([6, 7, 8], cegos=[7, 8]) -> ['6', '7*', '8*'].
    Explique o asterisco na legenda do Word com pg.NOTA_TESTE_CEGO."""
    return [f"{e}*" if e in set(cegos) else str(e) for e in ensaios]


def barras_agrupadas(ax, categorias, valores: dict, largura: float | None = None, alpha: float = 1.0):
    """Barras agrupadas por categoria, uma barra por série, com cor + hachura do padrão (cor exata, alpha 1).

    valores: {chave_do_modelo (ou índice extra): [valor por categoria]}, na ordem em que as barras devem aparecer.
    largura: de cada barra; por padrão 0,8 dividido pelo número de séries (grupo ocupa 80% da categoria).
    O eixo x é ajustado para não sobrar margem; defina ylim (começando em 0) depois.
    """
    chaves = list(valores)
    largura = largura or 0.8 / len(chaves)
    xs = np.arange(len(categorias))
    for i, k in enumerate(chaves):
        e = estilo_de(k)
        ax.bar(xs + (i - (len(chaves) - 1) / 2) * largura, valores[k], largura, facecolor=e.cor, edgecolor="black", hatch=e.hachura, linewidth=0.5, alpha=alpha, zorder=3)
    ax.set_xticks(xs)
    ax.set_xticklabels(categorias)
    ax.set_xlim(-0.6, len(categorias) - 0.4)
    ax.grid(axis="x", visible=False)


def inserto_zoom(ax, xlim, ylim, retangulo=(0.40, 0.14, 0.50, 0.42)):
    """Quadro ampliado dentro do painel (ex.: o primeiro minuto da cinética). Plote as mesmas séries no eixo devolvido.

    retangulo = (x0, y0, largura, altura) em fração do painel. Use onde não haja curva passando.
    """
    ins = ax.inset_axes(list(retangulo))
    ins.set_xlim(*xlim)
    ins.set_ylim(*ylim)
    ins.tick_params(labelsize=7.5)
    caixa = ax.indicate_inset_zoom(ins, edgecolor=COR_REFERENCIA, lw=0.7, alpha=0.9)
    for conector in caixa.connectors:   # só a caixa da região ampliada; as linhas de ligação cortariam as curvas
        conector.set_visible(False)
    return ins


# ----------------------------------------------------------------------------------------------
# Acabamento e gravação
# ----------------------------------------------------------------------------------------------
def finalizar(fig) -> None:
    """Ajustes finais obrigatórios: vírgula decimal nos eixos numéricos e nenhum título dentro da figura."""
    todos = [a for ax in fig.axes for a in (ax, *ax.child_axes)]   # inclui quadros ampliados (inserto_zoom)
    for ax in todos:
        ax.set_title("")
        for eixo in (ax.xaxis, ax.yaxis):
            if type(eixo.get_major_formatter()) is ScalarFormatter:   # não mexe em rótulos de texto nem em escala log
                eixo.set_major_formatter(FormatadorVirgula())


def salvar(fig, caminho_sem_extensao) -> list[Path]:
    """Grava PNG (300 DPI) e PDF com o mesmo nome base e devolve os caminhos. Não use bbox_inches='tight' (muda a largura)."""
    finalizar(fig)
    base = Path(caminho_sem_extensao)
    base.parent.mkdir(parents=True, exist_ok=True)
    saidas = []
    for ext in (".png", ".pdf"):
        p = base.with_suffix(ext)
        fig.savefig(p, dpi=DPI)
        saidas.append(p)
    plt.close(fig)
    return saidas
