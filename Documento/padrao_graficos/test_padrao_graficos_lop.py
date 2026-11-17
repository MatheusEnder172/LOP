"""Testes do padrão de gráficos LOP: tamanho, DPI, vírgula decimal, sem título, cores únicas, PNG + PDF."""

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import padrao_graficos_lop as pg  # noqa: E402


def _figura_simples():
    fig, gs = pg.nova_figura(altura_cm=8, nlin=1, ncol=2)
    a, b = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    t = np.linspace(0, 15, 50)
    pg.linha_modelo(a, t, 1 - np.exp(-t), "hib")
    pg.pontos_exp(a, [1, 5, 10], [0.6, 0.99, 1.0])
    a.set_title("não deve aparecer")
    a.set_ylim(0, 1.0)
    pg.dispersao_modelo(b, [0.4, 0.8], [0.45, 0.78], "novo")
    pg.barras_agrupadas(b.inset_axes([0.5, 0.1, 0.4, 0.3]), ["A", "B"], {"fab": [1, 2], "puro": [2, 1]})
    pg.rotular_paineis([a, b])
    pg.legenda_topo(fig)
    return fig, a


def test_saida_png_pdf_16cm_300dpi(tmp_path):
    fig, _ = _figura_simples()
    png, pdf = pg.salvar(fig, tmp_path / "sub" / "fig_teste")
    assert png.exists() and pdf.exists() and pdf.stat().st_size > 1000
    w, h = Image.open(png).size
    assert abs(w - round(16 / 2.54 * 300)) <= 1
    assert abs(h - round(8 / 2.54 * 300)) <= 1


def test_virgula_decimal_e_sem_titulo(tmp_path):
    fig, a = _figura_simples()
    pg.finalizar(fig)
    fig.canvas.draw()
    rotulos = [t.get_text() for t in a.get_yticklabels() if t.get_text()]
    assert rotulos and all("." not in r for r in rotulos) and any("," in r for r in rotulos)
    assert a.get_title() == ""
    assert pg.num(0.0657, 3) == "0,066"


def test_inserto_tambem_recebe_virgula():
    fig, gs = pg.nova_figura(altura_cm=6)
    a = fig.add_subplot(gs[0, 0])
    a.plot([0, 1], [0, 1])
    ins = pg.inserto_zoom(a, (0, 0.5), (0, 0.5))
    ins.plot([0, 0.5], [0, 0.5])
    pg.finalizar(fig)
    fig.canvas.draw()
    assert any("," in t.get_text() for t in ins.get_xticklabels())


def test_cores_unicas_e_registro():
    cores = [e.cor.lower() for e in list(pg.MODELOS.values()) + pg.EXTRAS]
    assert len(cores) == len(set(cores))
    with pytest.raises(ValueError):
        pg.registrar_modelo("copia", pg.Estilo("Cópia", pg.MODELOS["hib"].cor, "-", "o", "", 1.0))
    with pytest.raises(ValueError):
        pg.serie_extra(len(pg.EXTRAS))


def test_ordem_nomes_e_cores_dos_modelos():
    assert list(pg.MODELOS) == ["fab", "novo", "puro", "pinn", "par", "hib"]
    assert [pg.MODELOS[k].nome for k in ("fab", "novo", "puro", "pinn", "par", "hib")] == [
        "White-box (Fabrício)", "White-box (novo)", "MLP pura", "PINN", "Híbrido paralelo", "Híbrido serial"]
    assert pg.MODELOS["hib"].cor == "#CC79A7" and pg.MODELOS["fab"].cor == "#E69F00" and pg.MODELOS["novo"].cor == "#0072B2"
    assert pg.MODELOS["pinn"].cor == "#D55E00" and pg.MODELOS["par"].cor == "#56B4E9"


def test_apelidos():
    assert pg.resolver("serial") == "hib" and pg.resolver("Paralelo") == "par" and pg.resolver("whitebox") == "novo"
    assert pg.estilo_de("serial") is pg.MODELOS["hib"]
    with pytest.raises(KeyError):
        pg.resolver("inexistente")


def test_rotulo_x_nao_e_cortado_em_figura_baixa():
    fig, gs = pg.nova_figura(altura_cm=7)
    a = fig.add_subplot(gs[0, 0])
    pg.barras_agrupadas(a, pg.rotulos_ensaio(range(1, 17), cegos=[7, 8, 14]), {k: np.arange(16) + i for i, k in enumerate(("fab", "novo", "puro", "hib"))})
    a.set_xlabel(pg.ROTULOS["ensaio"])
    pg.legenda_topo(fig, experimental=False)
    pg.finalizar(fig)
    fig.canvas.draw()
    caixa_fig = fig.bbox
    for artista in (a.xaxis.label, a.yaxis.label, *fig.legends):
        bb = artista.get_window_extent()
        assert bb.x0 >= caixa_fig.x0 and bb.y0 >= caixa_fig.y0 and bb.x1 <= caixa_fig.x1 and bb.y1 <= caixa_fig.y1


def test_rotulos_ensaio_marca_teste_cego():
    assert pg.rotulos_ensaio([6, 7, 8], cegos=[7, 8]) == ["6", "7*", "8*"]
