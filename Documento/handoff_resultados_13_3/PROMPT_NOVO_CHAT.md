# Prompt para abrir o novo chat (escrever os Resultados do híbrido serial, modelo 13 + 3)

Cole o texto do bloco abaixo como primeira mensagem do novo chat. Pasta de trabalho do chat: `C:\us trem\Doc\UFMG\9\Lop\Codigo_v4`.

```text
Você vai me ajudar a escrever a parte de RESULTADOS do modelo híbrido serial do meu TCC (LOP, UFMG, Engenharia Química): rede neural + balanço populacional da lixiviação de concentrado ustulado de zinco. Meu grupo tem 4 pessoas; o orientador é o Prof. Fabrício Bortot Coelho. A entrega final é em 13/11/2026. O código e a metodologia são só meus; as outras seções são do grupo. Escreva em português.

PRIMEIRO, leia nesta ordem (sem alterar nada):
1. C:\us trem\Doc\UFMG\9\Lop\Codigo_v4\Documento\handoff_resultados_13_3\00_LEIA_PRIMEIRO.md
2. ...\01_decisoes_e_regras.md  (regras permanentes e modo de trabalho)
3. ...\02_estado_do_documento_e_estrutura.md  (o que a v10 já tem e a estrutura proposta)
4. ...\03_numeros_e_fontes.md  (números e de onde vêm; o que NÃO está verificado)
5. ...\04_ensaios_novos_depois.md  (o que fica de fora por enquanto)
6. A memória do projeto: C:\Users\Usuário\.claude\projects\C--us-trem-Doc-UFMG-9-Lop\memory\MEMORY.md
7. As duas entradas mais recentes do topo de Codigo_v4\DEVLOG.md (09/11 e 08/11).
Não use Codigo_v4\PROMPT_NOVO_CHAT.md nem PLANO_RETOMADA_PROXIMO_CHAT.md: estão desatualizados.

DECISÃO JÁ TOMADA (não reabra): os Resultados mostram a individualidade de cada modelagem do grupo, e aqui entra SÓ a serial. A parte do modelo é breve (só o que não está em Métodos nem nos Apêndices B a E). O foco é TREINAMENTO e VALIDAÇÃO: 13 ensaios de treino/validação cruzada e 3 de teste cego (7, 8 e 14), com o modelo v2 (comitê de 10 redes) CONGELADO. Não retreine nem mude nenhum número. Os 4 ensaios novos de laboratório ficam de fora por enquanto; entram depois como um extra, se os dados forem esclarecidos.

COMO QUERO TRABALHAR: devagar, um bloco por vez (uma subseção, tabela ou figura), parando para eu aprovar antes do próximo. Em cada bloco, me ofereça duas opções: (a) eu leio o texto no chat e edito eu mesmo; (b) você já coloca no Word (versão nova v11, nascida da v10 por script incremental em Documento\ferramentas, sem alterar a v10) e eu dou feedback depois. Pergunte logo no início qual eu prefiro. Antes de escrever qualquer coisa, me proponha a ordem das subseções (há uma sugestão no arquivo 02) e me pergunte o que eu quero mudar.

REGRAS QUE VALEM SEMPRE:
- Tudo que for novo ou alterado FORA de Materiais e Métodos fica em fonte VERMELHA no Word (pintar). Dentro de Métodos, cor normal.
- Não toque nos marcadores "AA", no Resumo, nas Conclusões nem no Apêndice A (são do grupo). O Google Docs oficial do grupo é SÓ LEITURA.
- Texto curto, sem repetição, sem "cara de texto de IA": voz impessoal e humana, uma mensagem por parágrafo, cada termo definido uma vez, nada de citar nome sem explicar. Citações no formato (Autor; Autor, ano). Não repita o que já está nos Apêndices: referencie (por exemplo, "Seção E.7").
- Todo número vem de CSV lido por script, com asserções. Seja direto e honesto sobre o que não foi verificado. Não afirme causa que os dados não mostram. Não consigo renderizar o Word aqui: a conferência visual é minha, e você deve dizer isso ao entregar.
- Teste cego já foi visto uma vez: nada de escolher configuração nele.
- Figuras em 300 DPI, PNG e PDF. Nunca exclua arquivos (mova para old\ com README).
- DEVLOG.md cumulativo: uma entrada nova no TOPO por atividade, com as 6 seções, inserida em modo binário (o arquivo tem bytes NUL); detalhes no arquivo 01.
- Commits e push no branch feat/mlp-otimizacao são permitidos (sem .docx), com "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>". Merge no main: pergunte antes.

COMECE por me dizer em poucas linhas o que entendeu, confirmar que leu os arquivos, e me perguntar (1) a ordem/subseções e (2) o modo (a) ou (b). Não escreva texto do relatório antes das minhas respostas.
```
