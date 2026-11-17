"""Gera a v26: a v25 (apêndices no padrão do GRUPO-5) mais dois pedidos de 15/11/2026 (noite).

1. A troca dos rótulos de E2 e E3 deixa de ser citada também fora do apêndice: parágrafo da Seção 4.1.2 (fica só a
   verificação da unidade g/L) e legendas das Figuras 5.1.2, 5.X.2 e 5.4.2. Os dados não mudam.
2. Figuras nossas com remissões numeradas desenhadas dentro da imagem, que não poderiam ser corrigidas depois:
   Figura A.10 ("Figura 4.X.14"), Figura A.11 ("Seção 4.X") e Figura 4.XX.17 ("Eq. 4.X.6", "Eq. 4.X.3" e
   "Eq. 4.X.4"). As três foram regeradas sem essas remissões por `figuras_metodologia/gerar_figuras_hibrido_serial.py`
   (que também passou a dizer "Malha temporal" em vez de "Malha canônica", dúvida do Daniel). A imagem é trocada no
   mesmo lugar, com o mesmo tamanho; imagem não tem cor, então a troca não aparece marcada.

Saídas: `RELATÓRIO FINAL LOP_v26.docx` (marcado) e `RELATÓRIO FINAL LOP_v26_limpo.docx` (aceito).
Uso: python ../figuras_metodologia/gerar_figuras_hibrido_serial.py fig_busca_hiperparametros fig_comite_redes \
         fig_algoritmo_simulacao && python remissoes_figuras_v26.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adequar_apendice_v25 as v25  # noqa: E402

v24, v23 = v25.v24, v25.v23
DOC_DIR = v25.DOC_DIR
DESTINO = DOC_DIR / "RELATÓRIO FINAL LOP_v26.docx"
LIMPO = DOC_DIR / "RELATÓRIO FINAL LOP_v26_limpo.docx"
FIG_MET = DOC_DIR / "figuras_metodologia"
TROCA = ", com os rótulos de E2 e E3 trocados em relação à planilha do laboratório"


def extra(doc, G, pos, k) -> None:
    i_met = pos("MATERIAIS E MÉTODOS", exato=True)
    i_res = pos("RESULTADOS E DISCUSSÃO", exato=True)

    # 1. Seção 4.1.2 e legendas dos Resultados
    p = G[pos("No tratamento dos dados, duas verificações de consistência foram realizadas", i_met, i_res)]
    v24.troca_longa(p, "duas verificações de consistência foram realizadas. A primeira é que os valores",
                    "verificou-se que os valores")
    v24.sai_trecho(p, " Além disso, constatou-se que as concentrações atribuídas aos Ensaios E2 e E3 só são compatíveis "
                      "com a massa de sólido do outro ensaio, o que indica a troca dos rótulos no registro do procedimento. "
                      "Portanto, mantida a atribuição original, a conversão do E3 atingiria 1,69, sendo fisicamente "
                      "impossível. Os rótulos foram, por isso, corrigidos antes do cálculo das conversões.")
    legendas = [i for i in range(i_res, k["fim"]) if G[i].tag == v25.W_P
                and v25.texto(G[i]).startswith("Figura") and TROCA in v25.texto(G[i])]
    assert len(legendas) == 3, [v25.texto(G[i])[:30] for i in legendas]
    for i in legendas:
        v24.sai_trecho(G[i], TROCA)

    # 2. figuras com remissões desenhadas
    for legenda, a, b, arquivo in (
            ("Figura A.10 – Busca de hiperparâmetros", k["apa"], k["apb"], "fig_hs_15_busca_hiperparametros.png"),
            ("Figura A.11 – Modelo final: comitê de dez redes", k["apa"], k["apb"], "fig_hs_16_comite_redes.png"),
            ("Figura 4.XX.17 – Algoritmo de simulação do modelo híbrido serial", i_met, i_res,
             "fig_hs_17_algoritmo_simulacao.png")):
        i = pos(legenda, a, b)
        fig = next(el for el in reversed(G[i - 3:i]) if el.find(".//" + v24.A_BLIP) is not None)
        v23.trocar_imagem(doc, fig, FIG_MET / arquivo)

    # conferência: nenhuma menção à troca no documento inteiro
    vivo = "".join(x.text or "" for el in G if el.getparent() is not None for r in el.iter(v25.W_R)
                   if v25.cor_de(r) != v25.VERMELHO for x in r if x.tag == v25.W_T)
    assert not re.search(r"trocad|troca dos rótulos|rótulos de E2|sem trocar", vivo), \
        re.findall(r".{60}(?:trocad|troca dos rótulos|rótulos de E2|sem trocar).{30}", vivo)


if __name__ == "__main__":
    v25.main(DESTINO, LIMPO, extra)
