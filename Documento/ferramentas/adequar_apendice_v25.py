"""Gera a v25 a partir da versão 5 do grupo (`RELATÓRIO FINAL LOP - GRUPO-5.docx`, que não é alterada).

Pedido de 15/11/2026 (noite). O usuário passou para o arquivo do grupo as Seções 5.2 e 5.5 no padrão novo, mas os
Apêndices A e B ainda estão na forma antiga (o Apêndice B segue em p.p. e com a inconsistência física). Este script
mexe só nos apêndices:

0. Aceita as marcas que já estavam no arquivo do grupo (vermelho apagado, azul vira preto), como na v24. Daí em
   diante, VERMELHO TACHADO = sai; AZUL = entra.
1. Apêndice B na forma da v24: erros na escala da conversão (três casas, valores brutos dos CSV) nas Tabelas B.10,
   B.13, B.14 e B.17 e no texto das Seções B.5 a B.8; sem a inconsistência física; malhas 4x4 no visual atual.
2. Decisão de 15/11: o texto não cita mais que os rótulos de E2 e E3 foram trocados (Seção B.6 e legendas das
   Tabelas B.12 e B.16). Os dados continuam os mesmos.
3. Cabeçalhos das tabelas dos dois apêndices sem a unidade adimensional "(–)" e sem "(p.p.)", como nas tabelas
   dos Resultados (RMSE, MAE, Erro máximo, η, R²). As unidades com dimensão ficam.
4. Redação no estilo que o usuário deu às Seções 5.2 e 5.5: os dois-pontos que explicam viram conectivos
   ("pois", "e", "já que"); os que abrem enumeração ou equação ficam.
5. Remissões: métricas pela Seção 4.1.4 (as equações da revisão ainda vão ser renumeradas), Kingma e Ba com o ano
   da lista (2015), Thompson e Kramer (1994) retirado (não está na lista; comentário do Rodrigo), auto-remissões
   da Seção A.7 e da Seção B.1 desfeitas, comparação com o black-box nas Seções 5.2 e 5.5.

Saídas: `RELATÓRIO FINAL LOP_v25.docx` (com as marcas) e `RELATÓRIO FINAL LOP_v25_limpo.docx` (aceita).
Uso: python adequar_apendice_v25.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adequar_grupo4_v24 as v24  # noqa: E402
import adequar_resultados_v23 as v23  # noqa: E402
import marcar_grupo_v21 as m  # noqa: E402

DOC_DIR = v24.DOC_DIR
GRUPO = DOC_DIR / "RELATÓRIO FINAL LOP - GRUPO-5.docx"
DESTINO = DOC_DIR / "RELATÓRIO FINAL LOP_v25.docx"
LIMPO = DOC_DIR / "RELATÓRIO FINAL LOP_v25_limpo.docx"
W_P, W_TBL, W_R, W_T, M_T, M_R = v24.W_P, v24.W_TBL, v24.W_R, v24.W_T, v24.M_T, v24.M_R
texto, cor_de, VERMELHO = v24.texto, v24.cor_de, v24.VERMELHO
feito = v24.feito
qn = v24.qn


# cabeçalho reescrito pela v23 sem unidade (lá virava "(–)")
def _tabela_de_csv_sem_unidade(tbl, colunas, chave=lambda s: s) -> int:
    n = _tabela_de_csv_original(tbl, colunas, chave)
    cab = tbl.findall(qn("w:tr"))[0].findall(qn("w:tc"))
    for tc in cab:
        if texto(tc).strip().endswith(" (–)") and cor_de(next(r for r in tc.iter(W_R) if texto(r))) == v24.AZUL:
            v23.escrever_celula(tc, texto(tc).strip()[:-4])
    return n


_tabela_de_csv_original = v23.tabela_de_csv
v23.tabela_de_csv = _tabela_de_csv_sem_unidade


def tirar_unidade_do_cabecalho(tbl) -> int:
    """Marca para sair o ' (–)' dos rótulos da tabela (cabeçalho e, na Tabela A.9, a coluna das variáveis)."""
    n = 0
    for tc in tbl.iter(qn("w:tc")):
        for p in tc.iter(W_P):
            vivo = "".join(texto(r) for r in p.iter(W_R) if cor_de(r) != VERMELHO)
            if " (–)" in vivo:
                m.retirar_trecho(p, " (–)", " (–)")
                n += 1
    return n


def main(destino: Path = DESTINO, limpo: Path = LIMPO, extra=None) -> None:
    """`extra(doc, G, pos, marcos)` permite que versões seguintes acrescentem mudanças antes da gravação."""
    doc = m.abrir(GRUPO)
    body = doc.element.body
    print("sdt removidos:", m.desembrulhar(body))
    print("marcas de comentário repetidas retiradas:", v23.consertar_comentarios(body))
    m.garantir_rpr(body)
    comentarios = v24.ids_de_comentario(body)
    assert comentarios["commentRangeStart"] == comentarios["commentRangeEnd"] == comentarios["commentReference"]
    print("marcas do arquivo do grupo aceitas:", v24.aceitar(body))
    assert v24.ids_de_comentario(body) == comentarios, "marca de comentário perdida"
    G = [el for el in body if el.tag in (W_P, W_TBL)]

    def pos(comeco: str, a: int = 0, b: int | None = None, exato: bool = False) -> int:
        alvo = m.sem_espaco(comeco)
        for i in range(a, len(G) if b is None else b):
            t = m.sem_espaco(texto(G[i]))
            if G[i].tag == W_P and (t == alvo if exato else t.startswith(alvo)):
                return i
        raise AssertionError(f"parágrafo não encontrado: {comeco!r}")

    i_fim = pos("CONCLUSÕES", pos("RESULTADOS E DISCUSSÃO", exato=True), exato=True)
    i_apa = pos("APÊNDICE A - DETALHAMENTO DO MODELO HÍBRIDO SERIAL", i_fim)
    i_apb = pos("APÊNDICE B - RESULTADOS COMPLEMENTARES", i_apa)
    i_apc = pos("APÊNDICE C", i_apb)

    def par(comeco: str, a: int = i_apa):
        return G[pos(comeco, a, i_apc)]

    def tabela_apos(legenda: str):
        tbl = G[pos(legenda, i_apb, i_apc) + 1]
        assert tbl.tag == W_TBL
        return tbl

    F = v24.fatos()
    S, B = F["N"]["serial"], F["N"]["mlp_pura"]
    ERROS = {"RMSE (p.p.)": "RMSE_pp", "MAE (p.p.)": "MAE_pp", "Erro máximo (p.p.)": "Emax_pp"}

    def colunas(tabela, extras=None) -> dict:
        return {cab: tabela[col] for cab, col in ERROS.items()} | (extras or {})

    def por_ensaio(rotulo: str) -> int:
        return int(rotulo.rstrip("*"))

    troca = v24.troca_longa

    # ------------------------------------------------------------------ 1. Apêndice B na forma da v24
    troca(par("Este apêndice reúne os resultados da seleção da configuração", i_apb),
          "Nas Seções B.5 a B.8, os erros estão em pontos percentuais (p.p.) de conversão.", "Os erros estão " + v24.ESCALA + ".")
    v23.trocar_imagem(doc, G[pos("Figura B.11 – Conversão de zinco medida e prevista pelo modelo híbrido serial", i_apb) - 1],
                      v24.FIG_RES / "fig_serial_4x4_todos.png")
    v23.trocar_imagem(doc, G[pos("Figura B.12 – Conversão de zinco medida e prevista pelo modelo black-box", i_apb) - 1],
                      v24.FIG_RES / "fig_mlp_pura_4x4_todos.png")
    v24.sai_trecho(par("A Figura B.12 apresenta as curvas previstas pelo modelo black-box nos 16 ensaios", i_apb),
                   " e a fração dos nós da curva fisicamente inconsistentes")
    v24.sai_trecho(par("Tabela B.17 – Métricas do modelo black-box nos ensaios novos", i_apb),
                   " e inconsistência física das curvas previstas")
    v24.coluna_sai(tabela_apos("Tabela B.14 – Métricas do modelo black-box"), "Inconsistência física")
    v24.coluna_sai(tabela_apos("Tabela B.17 – Métricas do modelo black-box nos ensaios novos"), "Inconsistência física")
    n_cel = v23.tabela_de_csv(tabela_apos("Tabela B.10 – Métricas do modelo híbrido serial"), colunas(S["por"], {
        "RMSE na validação cruzada (p.p.)": S["vc"], "RMSE do white-box (p.p.)": S["por_wb"]["RMSE_pp"]}), por_ensaio)
    n_cel += v23.tabela_de_csv(tabela_apos("Tabela B.13 – Métricas do modelo híbrido serial nos ensaios novos"), colunas(S["nov"], {
        "Desvio médio (p.p.)": S["nov"]["vies_pp"], "RMSE do white-box (p.p.)": S["nov_wb"]["RMSE_pp"]}))
    n_cel += v23.tabela_de_csv(tabela_apos("Tabela B.14 – Métricas do modelo black-box"), colunas(B["por"], {
        "RMSE na validação cruzada (p.p.)": B["vc"]}), por_ensaio)
    n_cel += v23.tabela_de_csv(tabela_apos("Tabela B.17 – Métricas do modelo black-box nos ensaios novos"), colunas(B["nov"], {
        "Desvio médio (p.p.)": B["nov"]["vies_pp"]}))
    assert n_cel == (16 * 5 - 3) + 6 * 5 + (16 * 4 - 3) + 6 * 4, n_cel
    for el in G[pos("B.5 Modelo híbrido serial: ensaios do planejamento original", i_apb):i_apc]:
        if el.tag == W_P and el.getparent() is not None:
            v24.sem_pp(el, S["fontes"] + B["fontes"])
    feito.append(f"Apêndice B: {n_cel} valores de tabela na escala da conversão")

    # ------------------------------------------------------------------ 2. sem citar a troca dos rótulos de E2 e E3
    v24.sai_trecho(par("As medições dos quatro ensaios novos (condições na Tabela B.9)", i_apb),
                   ", com os rótulos dos Ensaios E2 e E3 trocados em relação à planilha do laboratório")
    troca(par("A Tabela B.12 lista a conversão medida e a prevista em cada instante", i_apb),
          "o que não é possível com as condições nominais, de modo que o desvio nesses ensaios não pode ser atribuído ao "
          "modelo antes de o dado ser esclarecido.",
          "o que não é possível com as condições nominais e indica erro experimental (Seção 5.1), de modo que o desvio "
          "nesses ensaios não pode ser atribuído ao modelo.")
    troca(par("A Tabela B.16 lista a conversão prevista pelo modelo black-box", i_apb),
          "A conversão das medições e as hipóteses adotadas são as da Seção B.6.",
          "A conversão das medições é a mesma da Seção B.6.")
    for leg in ("Tabela B.12 – Conversão de zinco medida e prevista pelo modelo híbrido serial",
                "Tabela B.16 – Conversão de zinco medida e prevista pelo modelo black-box"):
        v24.sai_trecho(par(leg, i_apb), " (rótulos de E2 e E3 trocados em relação à planilha)")

    # ------------------------------------------------------------------ 3. cabeçalhos sem "(–)"
    n_cab = sum(tirar_unidade_do_cabecalho(t) for t in G[i_apa:i_apc] if t.tag == W_TBL)
    feito.append(f"cabeçalhos: {n_cab} unidades '(–)' retiradas")

    # ------------------------------------------------------------------ 4. dois-pontos explicativos
    troca(par("O coeficiente de determinação por ensaio varia de"),
          "não deve ser lido isoladamente: em ensaios", "não deve ser lido isoladamente, pois, em ensaios")
    p = par("Em 12 dos 16 ensaios algum parâmetro ficou no limite superior")
    troca(p, "Em 12 dos 16 ensaios algum", "Em 12 dos 16 ensaios, algum")
    troca(p, "de sua faixa: ", "de sua faixa, com ")
    troca(p, "(15 min); isso sugere", "(15 min), o que sugere")
    troca(par("A busca foi realizada em dois estágios"), "(Seção B.1): como as melhores", "(Seção B.1). Como as melhores")
    troca(par("A busca foi realizada em dois estágios"), "as duas estratégias de parada (Seção A.7)", "as duas estratégias de parada")
    troca(par("Este apêndice reúne os resultados da seleção da configuração", i_apb),
          "(Seções B.5 a B.8): as curvas", "(Seções B.5 a B.8), com as curvas")
    p = par("O resultado mostra que a nota em", i_apb)
    troca(p, "que não foram separados: ele remove", "que não foram separados, já que ele remove")
    troca(p, "A Seção B.1 mostra que treinar com todos os ensaios de cada dobra, por número fixo de épocas, reduz muito "
             "esse erro: com a mesma", "Treinar com todos os ensaios de cada dobra, por número fixo de épocas, reduz muito "
             "esse erro e, com a mesma")
    troca(par("No primeiro estágio, foram realizadas 423 tentativas", i_apb),
          "o fator mais decisivo: a mediana", "o fator mais decisivo, e a mediana")
    troca(par("O segundo estágio teve 523 tentativas", i_apb), "não ajudaram: a mediana", "não ajudaram, e a mediana")
    troca(par("O comitê de dez redes foi avaliado uma única vez", i_apb),
          "composição das dobras: a primeira", "composição das dobras, pois a primeira")
    troca(par("O modelo final foi melhor que a referência nos Ensaios 8 e 14", i_apb),
          "grandeza de interesse: a diferença", "grandeza de interesse, e a diferença")
    troca(par("Com a configuração final fixa, testou-se", i_apb),
          "daquele instante: como a retração", "daquele instante, pois, como a retração")
    troca(par("Nenhuma variante teve ganho claro.", i_apb),
          "otimista: as sementes 42 a 44", "otimista, já que as sementes 42 a 44")
    p = par("A D2 (", i_apb)
    troca(p, "a forma das curvas: a fração", "a forma das curvas, pois a fração")
    troca(p, "da Seção A.5: no comitê final", "da Seção A.5. No comitê final")
    troca(par("O ajuste fino reduziu o erro de", i_apb), "(Figura B.9): as redes", "(Figura B.9), e as redes")
    p = par("A configuração final (comitê de dez redes da Seção A.8) foi mantida", i_apb)
    troca(p, "ganho confiável sobre ela: a D1", "ganho confiável sobre ela, pois a D1")
    troca(p, "o teste cego foi usado: todas as escolhas", "o teste cego foi usado, e todas as escolhas")

    # ------------------------------------------------------------------ 5. remissões e citações
    troca(par("A atualização dos parâmetros seguiu o algoritmo AdamW"), "(Kingma; Ba, 2017)", "(Kingma; Ba, 2015)")
    v24.sai_trecho(par("Em vez de apenas imitar as taxas do problema inverso", i_apb), "; Thompson; Kramer, 1994")
    p = par("O desempenho do modelo híbrido foi quantificado")
    troca(p, "conforme as Equações 3.25 a 3.27 da revisão bibliográfica (Chicco; Warrens; Jurman, 2021)",
          "conforme a Seção 4.1.4 (Chicco; Warrens; Jurman, 2021)")
    troca(p, "pelo motivo já discutido na Seção 4.1.4.", "pelo motivo discutido na mesma seção.")
    troca(par("Para situar o desempenho do modelo híbrido, foram utilizadas"),
          "é apresentada na Seção 5.", "é apresentada nas Seções 5.2 e 5.5.")

    # ------------------------------------------------------------------ 7. figuras soltas no fim do Apêndice B
    # Duas figuras sem legenda, versões antigas da previsão a priori, com "E2 e E3 trocados" no título. Na versão
    # marcada, uma nota vermelha tachada avisa que saem; na limpa, são retiradas.
    i_b17 = pos("Tabela B.17 – Métricas do modelo black-box nos ensaios novos", i_apb, i_apc)
    soltas = [el for el in G[i_b17 + 1:i_apc] if el.tag == W_P and el.find(".//" + v24.A_BLIP) is not None]
    assert len(soltas) == 2, len(soltas)
    nota = v24.novo_par(G[i_b17 + 2], G[i_b17 + 2],
                        "[As duas figuras a seguir, sem legenda, saem: são versões antigas da previsão a priori dos "
                        "ensaios novos e citam a troca dos rótulos de E2 e E3 no título.]")
    for r in nota.iter(W_R):
        v24.v19.pintar_run(r, VERMELHO)
        v24.v19.tachar_run(r)

    # ------------------------------------------------------------------ 6. fonte "Gungsuh" herdada do Google Docs
    n_fonte = 0
    for el in G[i_apa:i_apc]:
        for rf in list(el.iter(qn("w:rFonts"))):
            if "Gungsuh" in rf.attrib.values():
                rf.getparent().remove(rf)
                n_fonte += 1
    todos = sum("Gungsuh" in rf.attrib.values() for rf in body.iter(qn("w:rFonts")))
    feito.append(f"fonte Gungsuh retirada de {n_fonte} trechos dos apêndices ({todos} restam no resto do documento)")

    if extra is not None:
        extra(doc, G, pos, {"fim": i_fim, "apa": i_apa, "apb": i_apb, "apc": i_apc})

    # ------------------------------------------------------------------ conferência final e gravação
    def vivo(el) -> str:
        return "".join((x.text or "") for r in el.iter() if r.tag in (W_R, M_R) and cor_de(r) != VERMELHO
                       for x in r if x.tag in (W_T, M_T))
    atual = [el for el in body if el.tag in (W_P, W_TBL)]
    resto = "".join(vivo(el) for el in atual[atual.index(G[i_apa]):atual.index(G[i_apc])])
    assert not re.search(r"p\.p\.|percentuais|[Ii]nconsist|trocad|planilha|\(–\)|Thompson|Equações 3\.", resto), \
        re.findall(r".{40}(?:p\.p\.|percentuais|[Ii]nconsist|trocad|planilha|\(–\)|Thompson|Equações 3\.).{20}", resto)
    doc.save(destino)
    print(f"{len(feito)} alterações; gravado: {destino.name}")
    for linha in feito:
        print("  ", linha)
    assert v24.ids_de_comentario(body) == comentarios, "marca de comentário perdida"
    print("versão limpa:", v24.aceitar(body))
    for p in soltas:
        p.getparent().remove(p)
    assert v24.ids_de_comentario(body) == comentarios, "marca de comentário perdida na versão limpa"
    doc.save(limpo)
    print("gravado:", limpo.name)


if __name__ == "__main__":
    main()
