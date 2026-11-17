"""Gera a v17 a partir da v16 (sem alterá-la): Métodos passa a descrever o black-box realmente usado nos Resultados.

Pedido do usuário em 10/11/2026. As Seções 4.1.4 a 4.1.7 descreviam uma rede de 4 camadas de 64 neurônios, tanh,
saída sigmoide, normalização Min-Max e 3.000 épocas, que é a rede-base da PINN. O black-box dos Resultados é a MLP
pura da Subetapa 3.2.7: entradas C_A0, η e ln t padronizadas pelo escore Z, camadas de 90, 45 e 22 neurônios, GELU,
saída linear, AdamW, 900 épocas fixas, configuração escolhida por validação cruzada e comitê de dez redes.

O que muda:
- 4.1.4 a 4.1.7 são reescritas para a MLP pura (mantendo a explicação geral de alimentação direta e de
  backpropagation, que a seção da PINN cita);
- a função de perda, que era uma imagem, vira equação nativa (4.1.7.1);
- a descrição da rede da PINN (o que saiu daqui) vira um parágrafo no início da seção da PINN, com a figura da
  arquitetura que a acompanhava. Esse parágrafo usa só o que o texto anterior já afirmava e precisa da conferência do
  integrante responsável pela PINN.

Texto novo em AZUL (0070C0), a legenda de "texto novo ou reescrito" do documento de sugestões do grupo, porque são
seções de outros integrantes. Números lidos do `config_escolhida.json` e do `mlp_puro_config.json`.
Uso: python ajustar_metodos_blackbox_v17.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import docx
import pandas as pd
from docx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docx_utils import SectionWriter, pintar  # noqa: E402
from reescrever_resultados_v13 import estilo, texto, v  # noqa: E402
from reescrever_serial_v11 import trocar  # noqa: E402

DOC_DIR = Path(__file__).resolve().parents[1]
ORIGEM = DOC_DIR / "RELATÓRIO FINAL LOP_v16.docx"
DESTINO = DOC_DIR / "RELATÓRIO FINAL LOP_v17.docx"
OUT = DOC_DIR.parent / "Código" / "outputs"
S327 = OUT / "etapa_3_2" / "subetapa_3_2_7_mlp_puro_xzn"
AZUL = "0070C0"
W_P = qn("w:p")


def main() -> None:
    cfg = json.loads((S327 / "config_escolhida.json").read_text(encoding="utf-8"))["config"]
    comite = json.loads((OUT / "models_saved" / "mlp_puro_xzn" / "mlp_puro_config.json").read_text(encoding="utf-8"))
    busca = pd.read_csv(S327 / "busca_cv_configuracoes.csv")   # as 32 configurações avaliadas (8 da rodada 1 e 24 da rodada 2)
    assert cfg["hidden_dims"] == [90, 45, 22] and cfg["lr"] == 0.01 and cfg["weight_decay"] == 1e-4 and cfg["batch_size"] == 16
    assert cfg["epocas_finais"] == 900 and cfg.get("dropout", 0.0) == 0.0 and list(comite["sementes"]) == list(range(42, 52))
    camadas = [3] + cfg["hidden_dims"] + [1]
    n_par = sum(a * b + b for a, b in zip(camadas, camadas[1:]))
    n_cfg = int(busca["cfg"].nunique())
    assert n_cfg == len(busca) == 32 and busca.sort_values("RMSE_cv_medio").iloc[0]["hidden_dims"] == "[90, 45, 22]"

    with open(ORIGEM, "rb") as f:
        doc = docx.Document(io.BytesIO(f.read()))
    body = doc.element.body
    els = list(body.iterchildren())

    def achar(pred, inicio=0):
        return next(i for i, e in enumerate(els) if i >= inicio and e.tag == W_P and pred(e))

    a = achar(lambda e: estilo(e) == "Heading3" and texto(e).strip() == "DESENVOLVIMENTO DO MODELO HÍBRIDO E APRENDIZADO DE MÁQUINA")
    h_pre = achar(lambda e: estilo(e) == "Heading3" and texto(e).strip() == "Pré-processamento e partição dos dados", a)
    h_arq = achar(lambda e: estilo(e) == "Heading3" and texto(e).strip() == "Arquitetura da rede neural", h_pre)
    h_tre = achar(lambda e: estilo(e) == "Heading3" and texto(e).strip() == "Treinamento e otimização da rede neural", h_arq)
    b = achar(lambda e: estilo(e) == "Heading3" and texto(e).strip().startswith("MODELAGEM HÍBRIDA: REDES NEURAIS INFORMADAS"), h_tre)
    h_col = achar(lambda e: estilo(e) == "Heading3" and texto(e).strip() == "Pontos de colocação", b)
    assert a + 1 == h_pre and h_col == b + 1 and b - a < 30

    # figura da arquitetura (imagem, legenda e fonte): acompanha a rede da PINN
    i_leg = achar(lambda e: texto(e).strip().startswith("Figura") and "arquitetura da rede neural MLP" in texto(e), h_tre)
    figura = els[i_leg - 1:i_leg + 2]
    assert figura[0].findall(".//" + qn("w:drawing")) and texto(figura[2]).strip().startswith("Fonte")
    cabecalhos = {a, h_pre, h_arq, h_tre}
    antigos = [els[i] for i in range(a, b) if i not in cabecalhos and els[i] not in figura]
    ancoras_perdidas = sum(len(e.findall(".//" + qn("w:commentRangeStart"))) + len(e.findall(".//" + qn("w:commentReference"))) for e in antigos)

    i_serial = achar(lambda e: estilo(e) == "Heading3" and texto(e).strip() == "MODELAGEM HÍBRIDA SERIAL")
    i_cap = achar(lambda e: texto(e).strip().startswith("Figura 4.5.1 –"), i_serial)
    refs = {"body": els[achar(lambda e: texto(e).startswith("Com essa escolha, a rede neural fica responsável"), i_serial)],
            "figure": els[i_cap - 1], "caption": els[i_cap], "source": els[i_cap + 1]}
    novos = []

    def escrever(ancora, paragrafos):
        w = SectionWriter(doc, refs, ancora)
        for item in paragrafos:
            if isinstance(item, tuple):
                w.equation(*item)
            else:
                w.paragraph(item)
        novos.extend(w.inserted)

    # ------------------------------------------------------------------ títulos
    trocar(els[a], "DESENVOLVIMENTO DO MODELO HÍBRIDO E APRENDIZADO DE MÁQUINA", "Modelo puramente orientado a dados (black box)")
    trocar(els[h_pre], "Pré-processamento e partição dos dados", "Pré-processamento dos dados")

    # ------------------------------------------------------------------ 4.1.5 pré-processamento
    escrever(els[h_arq], [
        r"O modelo puramente orientado a dados (*black-box*) estima a conversão de zinco diretamente a partir das condições "
        r"do ensaio, sem o balanço populacional, e serve de linha de base para as abordagens híbridas (Seção 4.2.4). Os "
        r"dados foram extraídos das Tabelas A1.1 e A1.4 (Apêndice A1) da dissertação de Bortot Coelho (2017), que reúnem 16 "
        r"ensaios em batelada monitorados em oito instantes (0; 0,5; 1; 2; 3; 4; 5 e 15 min), num total de 128 observações.",
        r"Como a temperatura (40 °C) e a agitação (1000 rpm) foram mantidas constantes, as entradas da rede são a "
        r"concentração inicial de ácido sulfúrico ($C_{A0}$), a razão molar estequiométrica ($\eta$) e o tempo de reação "
        r"($t$), e a saída é a conversão de zinco ($X_{\mathrm{Zn}}$). O tempo entra na rede como $\ln t$, pois a maior "
        r"parte da conversão ocorre nos primeiros minutos; por isso, o instante $t=0$, em que a conversão é nula por "
        r"definição, não participa do treinamento.",
        r"Como as três entradas têm escalas diferentes, elas foram padronizadas pelo escore Z, isto é, subtraídas da média e "
        r"divididas pelo desvio-padrão, calculados apenas com os pontos de treino (LeCun et al., 1998). Seguindo a partição "
        r"comum a todas as abordagens (Seção 4.2.1), 13 ensaios (91 pontos com $t>0$) foram destinados ao treinamento, e os "
        r"Ensaios 7, 8 e 14 (21 pontos) foram reservados para o teste cego (Kapoor; Narayanan, 2023).",
    ])

    # comentário do orientador ancorado no parágrafo antigo da partição ("por que 13/3 e por que esses 3"):
    # reancora no parágrafo novo equivalente, para não se perder
    alvo = next(e for e in novos if e.tag == W_P and texto(e).startswith("Como as três entradas têm escalas diferentes"))
    reancorados = 0
    for e in antigos:
        for ini in list(e.iter(qn("w:commentRangeStart"))):
            ppr = alvo.find(qn("w:pPr"))
            (ppr.addnext(ini) if ppr is not None else alvo.insert(0, ini))
            reancorados += 1
        for fim in list(e.iter(qn("w:commentRangeEnd"))):
            alvo.append(fim)
        for ref in list(e.iter(qn("w:commentReference"))):
            alvo.append(ref.getparent())   # o run que carrega a referência do comentário
    assert reancorados == 1

    # ------------------------------------------------------------------ 4.1.6 arquitetura
    escrever(els[h_tre], [
        r"O modelo *black-box* é uma rede neural MLP de alimentação direta, com 3 neurônios de entrada ($C_{A0}$, $\eta$ e "
        r"$\ln t$ padronizados), três camadas ocultas com " + f"{camadas[1]}, {camadas[2]} e {camadas[3]}" + r" neurônios e 1 "
        r"neurônio de saída, que fornece a conversão de zinco, num total de " + f"{n_par:,}".replace(",", ".") + r" parâmetros. "
        r"Essa configuração, que tem as mesmas larguras de camada da rede do modelo híbrido serial (Seção 4.5.3), foi a "
        r"escolhida pela validação cruzada descrita na Seção 4.1.7.",
        r"Na alimentação direta, os dados propagam-se camada a camada até a saída: cada neurônio calcula a soma ponderada "
        r"das suas entradas pelos pesos sinápticos ($W$), acrescida de um termo de viés ($b$), conforme a Equação (3.24). "
        r"Após a soma ponderada de cada camada oculta, aplica-se a função de ativação GELU (*Gaussian Error Linear Unit*; "
        r"Hendrycks; Gimpel, 2016), que introduz a não linearidade necessária para representar a curva de conversão.",
        r"A camada de saída é linear, sem função de ativação que limite o valor previsto. O modelo *black-box* não tem, "
        r"portanto, nenhuma restrição física: a conversão prevista não é obrigada a ficar entre 0 e 1, a respeitar o limite "
        r"estequiométrico nem a crescer com o tempo (Seção 4.2.3), o que permite medir o que o aprendizado de máquina "
        r"alcança sem informação do processo.",
    ])

    # ------------------------------------------------------------------ 4.1.7 treinamento
    escrever(els[b], [
        r"O treinamento é guiado pelo erro quadrático médio (MSE) entre as conversões previstas pela rede e as medidas no "
        r"conjunto de treinamento:",
        (r"L_{data}=\frac{1}{N_d}\sum_{i=1}^{N_d}{\left[X_{\mathrm{Zn},i}^{pred}-X_{\mathrm{Zn},i}^{exp}\right]^2}", "4.1.7.1"),
        r"Em que $N_d$ é o número de pontos considerados no cálculo. O objetivo do treinamento é encontrar os pesos ($W$) e "
        r"os vieses ($b$) que minimizam $L_{data}$ nos 91 pontos dos 13 ensaios de treinamento.",
        r"Para esse ajuste, utiliza-se o algoritmo de *backpropagation* (Rumelhart; Hinton; Williams, 1986). Calculada a "
        r"função de perda na saída, o erro é propagado no sentido inverso da rede pela regra da cadeia, por meio da "
        r"diferenciação automática da biblioteca PyTorch, o que fornece o gradiente da perda em relação a cada peso e viés e "
        r"indica a direção em que eles devem ser ajustados.",
        r"Os parâmetros são atualizados na direção oposta ao gradiente pelo otimizador AdamW (Loshchilov; Hutter, 2019), "
        r"variação do Adam (Kingma; Ba, 2017) com penalização dos pesos, em mini-lotes de " + str(cfg["batch_size"])
        + r" pontos. A configuração da rede foi escolhida pela validação cruzada por ensaio, com as mesmas quatro dobras do "
        r"modelo serial (Seção 4.5.2), entre " + (f"{n_cfg} " if n_cfg else "") + r"combinações de arquitetura, taxa de "
        r"aprendizado, penalização dos pesos e número de épocas, adotando-se a de menor erro na conversão fora da dobra: taxa "
        r"de aprendizado de $10^{-2}$, penalização dos pesos de $10^{-4}$ e " + str(cfg["epocas_finais"]) + r" épocas fixas, "
        r"sem parada antecipada.",
        r"O modelo final é a média das previsões de dez redes treinadas com essa configuração e sementes diferentes (42 a "
        r"51), como no modelo serial. Após o treinamento, os pesos e os vieses são fixados e a rede passa a operar apenas "
        r"por alimentação direta. A qualidade do ajuste e a capacidade de generalização são quantificadas por $R^2$, RMSE e "
        r"MAE, conforme a Seção 4.2.4.",
    ])

    # ------------------------------------------------------------------ rede da PINN: parágrafo no início da seção dela
    escrever(els[h_col], [
        r"A PINN utiliza uma rede própria, também do tipo MLP de alimentação direta, com 3 neurônios de entrada ($t$, "
        r"$C_{A0}$ e $\eta$, convertidos para o intervalo de −1 a 1 pela normalização *Min-Max*; Jayalakshmi; Santhakumaran, "
        r"2011), quatro camadas ocultas com 64 neurônios cada e 1 neurônio de saída. Antes do treinamento, os vieses são "
        r"inicializados em zero e os pesos são sorteados pela inicialização de Xavier (Datta, 2020). Nas camadas ocultas, "
        r"adotou-se a tangente hiperbólica (tanh), contínua e diferenciável em todos os pontos, requisito para que a saída "
        r"da rede seja derivada em relação ao tempo por diferenciação automática (Raissi et al., 2019); na camada de saída, "
        r"a função sigmoide restringe o valor ao intervalo (0, 1). A Figura 4.XX.X ilustra essa arquitetura e o ciclo de "
        r"treinamento, cujo mecanismo é o descrito na Seção 4.1.7.",
    ])
    for e in figura:   # a figura da arquitetura vai para depois do parágrafo da PINN
        els[h_col].addprevious(e)

    for e in antigos:
        body.remove(e)
    pintar(novos + [els[a], els[h_pre]], AZUL)

    # conferências
    atuais = list(body.iterchildren())
    ia, ib = atuais.index(els[a]), atuais.index(els[b])
    bloco = "\n".join(texto(e) for e in atuais[ia:ib])
    for proibido in ("sigmoide", "tanh", "Min-Max", "3.000", "64 neurônios", "104 pontos"):
        assert proibido not in bloco, f"sobrou '{proibido}' na descrição do black-box"
    assert "(4.1.7.1)" in bloco and [estilo(e) for e in atuais[ia:ib]].count("Heading3") == 4
    n_anc = len(body.findall(".//" + qn("w:commentRangeStart")))
    assert n_anc == len(body.findall(".//" + qn("w:commentReference"))) == 38, n_anc   # nenhum comentário do Word perdido
    doc.save(str(DESTINO))
    print(f"{DESTINO.name} gravada a partir da {ORIGEM.name}")
    print(f"black-box em Métodos: {len(antigos)} blocos antigos retirados, {len(novos)} novos (azul); {n_par} parâmetros; "
          f"{n_cfg} configurações na busca; comentários reancorados no texto novo: {reancorados}")


if __name__ == "__main__":
    main()
