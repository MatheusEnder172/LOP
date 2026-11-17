"""Gera a v27 a partir da `RELATÓRIO FINAL LOP_v26_limpo.docx` (que não é alterada).

Pedido de 15/11/2026 (noite), depois da revisão completa da v26 (`revisao_v26/REVISAO_COMPLETA_V26.md`): aplicar as
correções da parte do Matheus que não dependem do grupo, na Revisão, em Métodos, nos Resultados e nos Apêndices,
com as marcas de sempre (VERMELHO TACHADO = sai; AZUL = entra).

Fica de fora, por decisão do usuário: numeração de figuras, tabelas e equações e as remissões (Seção 3 da revisão).
Fica de fora, por depender do grupo: PINN na seção comum, convenção de η e Seção 5.4 (paralelo), números do
white-box nos ensaios novos, lista de referências, Seção 3.1.2, Introdução e objetivos.

Como a base é a versão limpa da v26, as marcas da v27 mostram só o que é novo em relação à v26.

Saídas: `RELATÓRIO FINAL LOP_v27.docx` (com as marcas) e `RELATÓRIO FINAL LOP_v27_limpo.docx` (aceita).
Uso: python correcoes_v27.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adequar_grupo4_v24 as v24  # noqa: E402
import marcar_grupo_v21 as m  # noqa: E402

DOC_DIR = v24.DOC_DIR
BASE = DOC_DIR / "RELATÓRIO FINAL LOP_v26_limpo.docx"
DESTINO = DOC_DIR / "RELATÓRIO FINAL LOP_v27.docx"
LIMPO = DOC_DIR / "RELATÓRIO FINAL LOP_v27_limpo.docx"
W_P, W_TBL, W_R, W_T, M_T, M_R = v24.W_P, v24.W_TBL, v24.W_R, v24.W_T, v24.M_T, v24.M_R
texto, cor_de, VERMELHO, AZUL, qn, feito = v24.texto, v24.cor_de, v24.VERMELHO, v24.AZUL, v24.qn, v24.feito


def tr(p, antigo: str, novo: str) -> None:
    """Troca marcada. Dentro de um único run, mantém a formatação do trecho; senão, usa a troca longa."""
    try:
        v24.troca(p, antigo, novo)
    except AssertionError:
        v24.troca_longa(p, antigo, novo)


def main() -> None:
    doc = m.abrir(BASE)
    body = doc.element.body
    m.garantir_rpr(body)
    cores = {cor_de(r) for r in body.iter(W_R)}
    assert VERMELHO not in cores and AZUL not in cores, "a base já tem marcas"
    comentarios = v24.ids_de_comentario(body)
    G = [el for el in body if el.tag in (W_P, W_TBL)]

    def pos(comeco: str, a: int = 0, b: int | None = None, exato: bool = False) -> int:
        alvo = m.sem_espaco(comeco)
        for i in range(a, len(G) if b is None else b):
            t = m.sem_espaco(texto(G[i]))
            if G[i].tag == W_P and (t == alvo if exato else t.startswith(alvo)):
                return i
        raise AssertionError(f"parágrafo não encontrado: {comeco!r}")

    i_rev = pos("REVISÃO BIBLIOGRÁFICA", exato=True)
    i_met = pos("MATERIAIS E MÉTODOS", exato=True)
    i_res = pos("RESULTADOS E DISCUSSÃO", exato=True)
    i_fim = pos("CONCLUSÕES", i_res, exato=True)
    i_apa = pos("APÊNDICE A - DETALHAMENTO DO MODELO HÍBRIDO SERIAL", i_fim)
    i_apb = pos("APÊNDICE B - RESULTADOS COMPLEMENTARES", i_apa)
    i_apc = pos("APÊNDICE C", i_apb)
    i_bb = pos("MODELO PURAMENTE ORIENTADO A DADOS (BLACK-BOX)", i_met, i_res, exato=True)
    i_pinn = pos("MODELAGEM HÍBRIDA: REDES NEURAIS INFORMADAS PELA FÍSICA (PINN)", i_bb, i_res)
    i_ser = pos("MODELAGEM HÍBRIDA SERIAL", i_pinn, i_res, exato=True)
    i_r52 = pos("MODELO PURAMENTE ORIENTADO A DADOS (BLACK-BOX)", i_res, i_fim, exato=True)
    i_r53 = pos("MODELAGEM HÍBRIDA VIA REDES NEURAIS INFORMADAS PELA FÍSICA", i_r52, i_fim)
    i_r55 = pos("MODELAGEM HÍBRIDA SERIAL", i_r53, i_fim, exato=True)

    def rev(c): return G[pos(c, i_rev, i_met)]
    def com(c): return G[pos(c, i_met, i_bb)]          # seção comum (4.1)
    def bbm(c): return G[pos(c, i_bb, i_pinn)]         # black-box, Métodos
    def ser(c): return G[pos(c, i_ser, i_res)]         # serial, Métodos
    def r52(c): return G[pos(c, i_r52, i_r53)]
    def r55(c): return G[pos(c, i_r55, i_fim)]
    def apa(c): return G[pos(c, i_apa, i_apb)]
    def apb(c): return G[pos(c, i_apb, i_apc)]

    # ================================================================== REVISÃO (trechos da nossa parte)
    p = rev("No treinamento, os pesos são ajustados pela retropropagação do erro")
    tr(p, ", na qual a cada passagem completa", ", em que cada passagem completa")
    tr(p, "Ba, 2017", "Ba, 2015")
    tr(rev("Dessa maneira, com o intuito de uniformizar a influência das variáveis"), ".Para redes", ". Para redes")

    # ================================================================== MÉTODOS, seção comum (4.1)
    # C96 (Rodrigo): o trecho dos critérios dependia de uma figura que só aparece na seção do serial
    v24.inserir(com("Os dados utilizados foram extraídos das Tabelas A1.1 e A1.4"), "em um total de 128 observações.",
                " O planejamento combina quatro concentrações iniciais de ácido (0,10; 0,50; 1,00 e 1,50 mol/L) e "
                "quatro razões molares (0,5; 1,0; 1,5 e 3,1).")
    p = com("A escolha desses três ensaios seguiu três critérios")
    v24.sai_trecho(p, " (Figura 4.XX.9(a))")
    v24.inserir(p, "(i) os quatro vértices do planejamento",
                " ($C_{A0}$ de 0,10 e 1,50 mol/L com $\\eta$ de 0,5 e 3,1)")
    v24.acrescentar(p, " A partição é ilustrada na Figura 4.XX.9(a).")

    # C109 (Rodrigo): δ ainda não foi definido neste ponto
    p = com("(i) condição inicial:")
    total = texto(p)
    a, b = total.index("X(0)=0") + len("X(0)=0"), total.index("CA(0)=CA0")
    assert "δ(0)=0" in total[a:b], total[a:b]
    m.retirar_trecho(p, total[a:b], total[a:b])
    v24.inserir(p, total[a:b], " e ")
    feito.append("− δ(0)=0 na condição inicial")

    # frase invertida
    tr(com("(ii) irreversibilidade:"), "é deve ser negativa, pois corresponderia",
       "não pode ser negativa, pois isso corresponderia")

    v24.sai_trecho(com("O desempenho de todos os modelos é quantificado pelo coeficiente de determinação"),
                   " de conversão")
    # C115 (Rodrigo): faltava dizer como a condição inicial é verificada
    v24.acrescentar(com("Por sua vez, o atendimento às restrições da Seção 4.1.3 é verificado"),
                    " Já a condição inicial é verificada pelo valor previsto em $t=0$, exceto no black-box, que "
                    "recebe o tempo como $\\ln t$ e não fornece previsão nesse instante (Seção 4.3.1).")

    # ================================================================== MÉTODOS, black-box (4.3)
    tr(bbm("Com o gradiente fornecido pelo backpropagation"), "Ba, 2017", "Ba, 2015")
    p = bbm("Após o treinamento, os pesos sinápticos (W) e vieses (b) otimizados")
    tr(p, "Nessa etapa de validação", "Nessa etapa de avaliação")
    tr(p, "nos ensaios de validação", "nos ensaios de teste cego")

    # ================================================================== MÉTODOS, serial (4.6)
    tr(ser("Para que a taxa estimada pela rede seja convertida em conversão de zinco"),
       "acumulada, a conversão e o balanço", "acumulada e a conversão, e o balanço")
    tr(ser("Por esse motivo, a relação"), "Por esse motivo, a relação",
       "Como depende apenas da distribuição granulométrica inicial, a relação")
    v24.troca_longa(ser("No modelo fenomenológico, essa função é dada pela lei cinética"),
                    "essa função é dada", "a taxa $\\nu(t)$ é dada")
    p = ser("Com os parâmetros definidos, calcularam-se")
    tr(p, "epara os sete", "para os sete")
    tr(p, "que foi usada para verificar", "usados para verificar")
    tr(p, "que foi usada no treinamento", "usados no treinamento")
    tr(ser("Os valores de"), ".A base com", ". A base com")
    tr(ser("A escolha da configuração da rede e a decisão de quando interromper"), "Apêndic A", "Apêndice A")

    # símbolos do texto iguais aos da Equação 4.XX.11 e da Seção A.5
    p = G[pos("Em que", pos("A rede recebe as três entradas padronizadas", i_ser, i_res), i_res)]
    total = texto(p)
    assert total.startswith("Em que") and "são a média e o desvio-padrão de" in total, total[:80]
    simbolos = total[len("Em que"):total.index("são a média")].strip()
    assert "μ" in simbolos and "σ" in simbolos, simbolos
    v24.troca_longa(p, simbolos, "$m_{\\tau}$ e $s_{\\tau}$")

    tr(ser("As camadas ocultas são três blocos residuais"), "correção não linear..", "correção não linear.")
    tr(ser("A minimização foi feita por descida de gradiente em mini-lotes"), "Ba, 2017", "Ba, 2015")
    tr(ser("Primeiramente, é escolhida a malha"), "malha canônica", "malha temporal")
    tr(ser("Como discutido anteriormente, a rede só é avaliada"),
       "dados de treino e como a integração", "dados de treino. Como a integração")
    tr(ser("A primeira operação garante que a conversão não diminua"),
       "ao longo do tempo, mesmo que", "ao longo do tempo. Como")
    p = ser("A segunda operação reforça que relação")
    tr(p, "reforça que relação", "é necessária porque a relação")
    v24.troca_longa(p, "fazendo que a retração acumulada seja mantida constante..",
                    "de modo que a retração acumulada é mantida constante.")

    # ================================================================== RESULTADOS, black-box (5.2)
    tr(r52("Tabela 5.2.1 – Desempenho do modelo black-box"), "(MAE)e erro", "(MAE) e erro")
    tr(r52("A Figura 5.X.1 compara as curvas previstas com as medições"),
       "de cerca de 0,87, e os dados contêm a informação", "de cerca de 0,87. Os dados contêm, portanto, a informação")
    tr(r52("O segundo motivo é que nada obriga a curva prevista"), "Noo Ensaio", "No Ensaio")
    tr(r52("Para os quatro ensaios novos, descritos na Seção 4.1.2, as previsões foram calculadas"),
       "(0,117 e 0,072) e o ensaio E4 expõe a limitação mais séria desta modelagem, na qual com razão molar",
       "(0,117 e 0,072). Já o ensaio E4 expõe a limitação mais séria desta modelagem, pois, com razão molar")

    # ================================================================== RESULTADOS, serial (5.5)
    tr(r55("O erro em E2 e E3 foi inferior ao do modelo white-box"),
       "as previsões do modelo superam", "as conversões medidas superam")
    tr(r55("Por tanto, o modelo híbrido serial superou"), "Por tanto", "Portanto")
    p = G[next(i for i in range(i_r55, i_fim) if G[i].tag == W_P
               and re.match(r"Tabela 5\.\d\.2 – Ensaios novos: condições", texto(G[i])))]
    tr(p, "Ensaios novos: condições, limite estequiométrico, conversão de zinco medida e prevista pelo modelo híbrido "
          "serial em 15 min e erros da previsão nos seis instantes de amostragem",
       "Desempenho do modelo híbrido serial nos ensaios novos: RMSE, erro absoluto médio (MAE) e erro máximo nos "
       "seis instantes de amostragem")

    # ================================================================== APÊNDICE A
    tr(apa("Com os parâmetros ótimos de cada ensaio, a conversão reconstruída reproduz"),
       "e serve de teto de referência nas Seções B.1 e B.2",
       "e é tratado como teto de desempenho, isto é, o menor erro alcançável, nas Seções B.1 a B.3")
    v24.inserir(apa("Em 12 dos 16 ensaios, algum parâmetro ficou no limite superior"), "regularização adicional.",
                " Nos Ensaios 2, 6 e 7, os dois termos exponenciais trocaram de papel ($b_1<b_2$), o que a forma "
                "da taxa permite por ser simétrica nos dois termos, e, nos Ensaios 6 e 7, é a etapa rápida que fica "
                "limitada por $b_2=4$ min⁻¹.")
    v24.acrescentar(apa("As entradas foram padronizadas pela Equação"),
                    " Como a padronização envolve apenas as três entradas, cujos valores são fixados pelo "
                    "planejamento e pela malha temporal, nenhuma informação da resposta dos ensaios de validação "
                    "entra no treinamento.")

    # ================================================================== APÊNDICE B (rótulos internos do desenvolvimento)
    def tabela_apos(legenda: str):
        tbl = G[pos(legenda, i_apb, i_apc) + 1]
        assert tbl.tag == W_TBL
        return tbl

    n = 0
    for pc in tabela_apos("Tabela B.3 – Segundo estágio").iter(W_P):
        t = texto(pc)
        if t.startswith("Tentativa B2 "):
            m.retirar_trecho(pc, "B2 ", "B2 ")
            n += 1
        elif t.startswith("Fase B (Tentativa 211)"):
            tr(pc, "Fase B (Tentativa 211)", "Primeiro estágio (tentativa 211)")
            n += 1
    assert n == 6, n
    feito.append("Tabela B.3: 'B2' e 'Fase B' retirados dos rótulos")
    pc = next(pc for pc in tabela_apos("Tabela B.8 – Variantes testadas").iter(W_P)
              if texto(pc).startswith("Ajuste fino ponta a ponta (Fase D)"))
    v24.sai_trecho(pc, " (Fase D)")

    # ------------------------------------------------------------------ conferência e gravação
    def vivo(el) -> str:
        return "".join((x.text or "") for r in el.iter() if r.tag in (W_R, M_R) and cor_de(r) != VERMELHO
                       for x in r if x.tag in (W_T, M_T))
    resto = "".join(vivo(el) for el in G if el.getparent() is not None)
    ruins = r"Noo |Por tanto|Apêndic A| epara |é deve ser|Ba, 2017|Fase [BD]\b|Tentativa B2|malha canônica"
    achados = re.findall(r".{40}(?:" + ruins + r").{20}", resto)
    # o que sobra fora da nossa parte fica listado, sem impedir a gravação
    for a in achados:
        print("  [fora da nossa parte]", a)
    assert v24.ids_de_comentario(body) == comentarios, "marca de comentário perdida"
    doc.save(DESTINO)
    print(f"{len(feito)} alterações; gravado: {DESTINO.name}")
    for linha in feito:
        print("  ", linha)
    print("versão limpa:", v24.aceitar(body))
    assert v24.ids_de_comentario(body) == comentarios, "marca de comentário perdida na versão limpa"
    doc.save(LIMPO)
    print("gravado:", LIMPO.name)


if __name__ == "__main__":
    main()
