# Padrão de gráficos do grupo — seção de Resultados (estilo C)

Escolhido em 09/11/2026 entre quatro candidatos (A clássico P&B, B moderno colorido, C serifado colorido com
redundância, D minimalista). O C ganhou porque usa a mesma fonte do Word, tem cor para a tela e continua legível
impresso em preto e branco ou por quem tem daltonismo.

Arquivos desta pasta:

| Arquivo | Para que serve |
| :--- | :--- |
| `padrao_graficos_lop.py` | O módulo. Fonte da verdade de cores, tamanhos e funções. Não editar sem avisar o grupo. |
| `exemplo_figura_padrao.py` | Figura-modelo (cinética + paridade + RMSE) feita só com o módulo. |
| `exemplos/figura_padrao_exemplo.png/.pdf` | Como a figura deve parecer. |
| `exemplos/paleta_lop.png/.pdf` | Folha da paleta: cor, linha, marcador, hachura, versão P&B e simulações de daltonismo. |
| `PROMPT_PARA_COLEGAS.md` | Dois prompts para colar no Claude Code: (A) uma figura qualquer no padrão; (B) a minha parte de Resultados. |
| `resultados_lop.py` | Modelo da parte de Resultados: 16 individuais, 4 gráficos 2x2 e o 4x4, métricas e curvas, para qualquer modelagem. |
| `template_resultados_meu_modelo.py` | Template em branco: o colega só preenche `carregar_meu_modelo()` e `prever()`. |
| `Código/etapas/etapa_4_2_avaliacao_indomain/gerar_resultados_serial.py` | O template já preenchido para o híbrido serial (exemplo funcionando). |
| `test_padrao_graficos_lop.py`, `test_resultados_lop.py` | 16 testes (16 cm, 300 DPI, vírgula, sem título, cores únicas, 16 ensaios, 91/21/112 pontos, métricas). |
| `exemplos_estilos.py`, `exemplos/estilo_*.png` | Registro histórico dos 4 candidatos. |

## Paleta oficial: Okabe-Ito

Foi desenhada por Okabe e Ito (2008) para ser distinguível por quem tem as formas mais comuns de daltonismo, e é a
recomendação de várias revistas científicas. Usamos 7 das 8 cores. O **amarelo (#F0E442) fica de fora**: tem pouco
contraste no fundo branco.

| Uso | Cor | Hex | Linha | Marcador | Hachura |
| :--- | :--- | :--- | :---: | :---: | :---: |
| White-box (Fabrício) | laranja | `#E69F00` | tracejada `--` | quadrado | `///` |
| White-box (novo) | azul | `#0072B2` | pontilhada `:` | triângulo | `...` |
| MLP pura | verde | `#009E73` | traço-ponto `-.` | losango | `xxx` |
| Híbrido serial | rosa (roxo avermelhado) | `#CC79A7` | sólida, mais grossa | círculo | sem |
| PINN | vermelhão | `#D55E00` | traço-ponto-ponto | triângulo p/ baixo | `\\\` |
| Híbrido paralelo | azul-claro | `#56B4E9` | traço longo | cruz cheia | `++` |
| Extra (η, T, variante) | cinza | `#6E6E6E` | pontilhada fina | X | `\|\|` |
| Experimental | preto | `#000000` | – | círculo vazado (miolo branco) | – |
| Linhas de referência (y = x, teto físico) | cinza escuro | `#555555` | pontilhada | – | – |

As modelagens do grupo são **white-box novo (azul), PINN (vermelhão), híbrido paralelo (azul-claro) e híbrido serial
(rosa)**; o white-box do Fabrício (laranja) e a MLP pura (verde) são referências. Cada integrante só precisa conhecer a
chave da própria modelagem (`"pinn"`, `"paralelo"` ou `"serial"`); o módulo já traz a cor.

Regras da paleta:

1. **Um modelo, uma cor, no relatório inteiro.** O leitor aprende que laranja é o white-box do Fabrício e não precisa
   reler a legenda em cada figura.
2. **A cor nunca trabalha sozinha.** Cada série tem também linha, marcador e hachura próprios. Medi a luminância: MLP pura
   e híbrido (a dupla mais próxima) diferem só 0,036 em tons de cinza, e o laranja e o azul-claro quase empatam. No preto e
   branco quem separa as séries é a linha, o marcador e a hachura.
3. **Ordem fixa** na legenda e nas barras: Fabrício, novo, MLP pura, híbrido.
4. **Não inventar cor.** Precisa de mais de 7 séries? Provavelmente o gráfico está carregado demais; divida em painéis.
5. Mapas de calor ou variável contínua (concentração, tempo): usar `viridis` (uniforme e seguro para daltonismo), nunca
   `jet` ou `rainbow`.

## Decisões de formato (valem para toda figura)

| Item | Decisão |
| :--- | :--- |
| Largura | 16 cm (coluna inteira) ou 7,8 cm (meia coluna) |
| Resolução e formatos | 300 DPI, PNG **e** PDF |
| Fonte | Times New Roman, 10 pt nos rótulos, 9 pt nos números dos eixos, 8,2 pt na legenda |
| Título dentro da figura | **Não.** "Figura N – título" e "Fonte:" ficam no Word (ABNT) |
| Separador decimal | Vírgula (`0,85`), nos eixos e em qualquer número escrito na figura |
| Painéis | (a), (b), (c) em negrito, canto superior esquerdo. Exceção: malhas de ensaios (2x2, 4x4) identificam o quadro por "Ensaio N" dentro dele, sem letras |
| Legenda | Uma linha no topo, fora dos painéis |
| Moldura | Caixa completa, ticks para dentro, grade pontilhada alpha 0,25 |
| Símbolos | `$X_{\mathrm{Zn}}$`, `$C_{\mathrm{A0}}$` (índice em texto reto); gregas em Unicode (η) |
| Eixos nas malhas | Números dos eixos x e y em **todos** os quadros (pedido do orientador, 11/11/2026), mais um traço em t = 0 igual aos de 5, 10 e 15 (`pg.marcador_t0`, desenhado por cima das curvas) |
| Eixo do tempo | Linear, 0–15 min. Se a cinética se concentra no 1º minuto, usar o quadro ampliado (`pg.inserto_zoom`) |
| Rótulos padrão | Sempre de `pg.ROTULOS` (tempo, X_Zn experimental, X_Zn do modelo, RMSE em p.p.) |

## Parte de Resultados por modelagem (cada um faz a sua)

Cada integrante gera, para a sua modelagem contra o white-box novo (RRB ÷ D³, α = 0), os **16 ensaios (13 de treino +
3 de teste cego: 7, 8, 14)** em três formatos, todos só com a cinética de 0 a 15 min (sem painel de zoom):

| Formato | Arquivo | Tamanho |
| :--- | :--- | :--- |
| Individual (16) | `fig_<modelagem>_ensaio_XX` | 16 x 8 cm |
| 2x2 (4: ensaios 1-4, 5-8, 9-12, 13-16) | `fig_<modelagem>_2x2_ensaios_XX_YY` | 16 x 12,6 cm |
| 4x4 (os 16 numa imagem) | `fig_<modelagem>_4x4_todos` | 16 x 17,8 cm |

Em cada gráfico: pontos experimentais, white-box novo (azul pontilhado), a modelagem na sua cor fixa e o limite
estequiométrico min(1; η) em pontilhado fino. Saída em `Código/outputs/resultados_por_modelagem/<pinn|paralelo|serial>/`,
com `metricas_resumo.csv` (treino, teste cego e global), `metricas_por_ensaio.csv`, `dados_plotados.csv` e
`curvas_<modelagem>.csv`. Esse último é o que permite **juntar as modelagens depois**:

```bash
python "Código/etapas/etapa_4_2_avaliacao_indomain/gerar_comparacao_final_2x2.py"                 # white-box novo + quem já entregou
python "Código/etapas/etapa_4_2_avaliacao_indomain/gerar_comparacao_final_2x2.py" --referencias   # + white-box do Fabrício e MLP pura
```

### Atualização de 10/11/2026: métricas comuns, figura do texto e ensaios novos

- `metricas_resumo.csv` e `metricas_por_ensaio.csv` trazem agora também `Emax_pp` (erro máximo absoluto) e
  `incons_fis_pct` (inconsistência física: % dos nós da curva do modelo, em malha comum de 0,25 min, com conversão
  decrescente ou acima de min(1; η); tolerância de 1e-6). O R² fica só no resumo, com os pontos da partição juntos.
- `gerar_figuras` grava também `fig_<modelagem>_2x2_texto_ensaios_01_07_08_14`: a figura do texto de Resultados
  (Ensaio 1, de treino, e os três de teste cego).
- `rl.gerar_ensaios_novos("<modelagem>", prever=prever)` compara a modelagem, sem novo ajuste, com os 4 ensaios novos
  (E1 a E4): figura 2x2, `metricas_ensaios_novos.csv`, curvas e pontos em `<modelagem>/ensaios_novos/`. As medições vêm
  de `Base de dados/Experimentos novos/medicoes_XZn_ensaios_novos_E2_E3_trocados.csv` (rótulos E2 e E3 trocados em
  relação à planilha: hipótese do grupo, a confirmar com o laboratório).

### Figura de comparação final: 2x2 por ensaio (decidido em 09/11/2026)

A comparação entre modelagens nos Resultados usa o formato **2x2 por ensaio**: 4 figuras com 4 ensaios cada (1-4, 5-8, 9-12,
13-16), cobrindo os 16. Cada quadro mostra os pontos experimentais, o limite estequiométrico e uma curva por modelo, nas cores
fixas. O script acima lê sozinho as modelagens que já entregaram `curvas_<nome>.csv` (white-box novo entra sempre) e grava em
`Código/outputs/resultados_por_modelagem/comparacao/` (ou `comparacao_com_referencias/`). Com 3 ou mais modelos o quadro não
traz RMSE por ensaio; ele fica em `metricas_por_ensaio.csv` e `metricas_resumo.csv`.


## Uso rápido

```python
import sys; sys.path.insert(0, "Documento/padrao_graficos")
import padrao_graficos_lop as pg

fig, gs = pg.nova_figura(altura_cm=9, nlin=1, ncol=2)
a, b = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
pg.linha_modelo(a, t, x_hibrido, "hib")          # cor/linha do padrão
pg.pontos_exp(a, t_exp, x_exp)                   # círculo preto vazado
a.set_xlabel(pg.ROTULOS["t"]); a.set_ylabel(pg.ROTULOS["XZn"])
pg.diagonal_paridade(b, 0.3, 1.05)               # painel de paridade
pg.dispersao_modelo(b, x_exp, x_pred, "hib")
pg.rotular_paineis([a, b]); pg.legenda_topo(fig)
pg.salvar(fig, "Código/outputs/etapa_X/fig_14_exemplo")   # .png e .pdf
```

Funções: `nova_figura`, `linha_modelo`, `pontos_exp`, `dispersao_modelo`, `diagonal_paridade`, `linha_referencia`,
`barras_agrupadas`, `rotulos_ensaio`, `inserto_zoom`, `rotular_paineis`, `legenda_topo`, `num`, `serie_extra`,
`registrar_modelo`, `salvar`. Painel único não leva (a). Ensaios de teste cego levam asterisco (`rotulos_ensaio`) e a
legenda do Word explica com `pg.NOTA_TESTE_CEGO`.

## Pontos em aberto (decisão do grupo)

- A figura-modelo usa o ensaio 9 (C_A0 = 1,00 mol/L; η = 1). Para a seção, vale combinar quais ensaios entram como
  "figura-exemplo" e quais ficam no apêndice (4 × 4).
- Observação sobre o modelo, não sobre o padrão: a curva do híbrido serial sobe em linha reta de t = 0 até ≈ 0,25 min e só
  depois muda de inclinação (aparece no quadro ampliado). Vale entender a origem antes de a banca perguntar.
