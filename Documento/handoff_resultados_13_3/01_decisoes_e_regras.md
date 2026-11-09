# Decisões e regras permanentes

## Modo de trabalho pedido pelo usuário (importante)

- Escrever **de forma pausada**: um bloco por vez (uma subseção, uma tabela, uma figura), parando para o usuário.
- A cada bloco, **oferecer duas opções**: (a) o usuário lê o texto aqui no chat e edita ele mesmo; (b) o texto já entra no Word (na última versão) e o usuário dá feedback depois. Perguntar qual prefere logo no início e respeitar a escolha.
- Ser direto e honesto sobre o que não foi verificado. Não afirmar causa que os dados não mostram.
- Não passar para a etapa seguinte sem o usuário aprovar a anterior.

## Regras do relatório (Word)

- Versão de trabalho: cada versão nasce da anterior por **script incremental** em `Documento/ferramentas/` (padrão `adicionar_resultados_vNN.py`; usa `docx_utils.SectionWriter`, `pintar`, `add_references`). A próxima é a **v11**, nascida da **v10**. Não alterar a v10. Nunca regerar a partir do "-fab" sem perguntar.
- **Tudo que for novo ou alterado fora da seção de Materiais e Métodos fica em fonte VERMELHA** (Resultados, Apêndices, referências novas). Dentro de Métodos, cor normal.
- **Não tocar** nos marcadores "AA" do grupo (4 títulos vazios no início de RESULTADOS E DISCUSSÃO), no Resumo, nas Conclusões e no Apêndice A: são dos outros membros.
- O Google Docs oficial do grupo (arquivo `1qBF5H-0xXd5G3Sm4L3So825MNsQi5WLM`) é **só leitura**. Não escrever nada lá. O usuário compara a versão dele com o grupo.
- Numeração provisória: "5.XX" nos Resultados (Tabela 5.XX.1, Figura 5.XX.1...), "4.XX" em Métodos. A numeração definitiva é com o grupo.
- Não é possível renderizar o Word aqui: a conferência visual é do usuário. Dizer isso ao entregar.
- Figuras em **300 DPI, PNG e PDF**. Números sempre **lidos dos CSVs** por script, com asserções, nunca digitados à mão.

## Estilo de escrita (pedido do orientador)

Texto curto, sem repetição, sem "cara de texto de IA". Voz impessoal e humana, **uma mensagem por parágrafo**, cada termo definido **uma vez**, nada de citar nomes sem explicar. Português. Citações no formato (Autor; Autor, ano). Evitar travessão em excesso, listas dentro de parágrafos, adjetivos de promoção ("robusto", "excelente") e frases que só repetem a tabela. O que já está em Métodos ou nos Apêndices B a E não se repete: só se referencia ("Seção E.7").

## Regras de dados e de ciência

- **Teste cego (Ensaios 7, 8 e 14):** já foi visto uma vez (Fase E). Escolher configurações **só pela validação cruzada**. O teste novo é relatado ao lado do antigo, sem afinar nada nele.
- Regra de ganho claro nos testes de variantes: diferença média pareada maior que 1 erro-padrão em 10 sementes.
- **Positividade da taxa** (ν > 0) é a única restrição física imposta à rede; a monotonia (D2) foi descartada (08/11) porque a lei física exige só ν > 0 e os dados têm erro experimental. Já está em Métodos.
- **Modelo congelado: MLP v2.** Não retreinar, não reajustar, não mudar nenhum número. Melhorias de modelagem estão pausadas por decisão do usuário.
- Nunca excluir arquivos: mover para `old\` da etapa, com README de justificativa.

## DEVLOG, commits, PR

- `Codigo_v4/DEVLOG.md` é cumulativo. Entrada nova no **TOPO**, uma por atividade, com as 6 seções: objetivo; hipótese/decisão; ações; o que funcionou com métricas; o que falhou; próximos passos. Nunca apagar entradas. O arquivo tem bytes NUL: inserir em **modo binário**, logo depois da linha `---` que segue a "Regra de Governança" (padrão nos scripts `devlog*.py` do chat anterior: localizar `Regra de Governança`, depois `b"---\r\n\r\n"`, inserir o texto com `\r\n` e terminar com `b"\r\n---\r\n\r\n"`).
- Commits e push no branch `feat/mlp-otimizacao` são permitidos, **sem incluir .docx**. Mensagem termina com `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. O PR #1 (`feat/mlp-otimizacao` para `main`) já existe. **Merge no main: perguntar antes.**

## Armadilhas já encontradas

- Heredocs longos no Bash quebram ("unexpected EOF"): escrever scripts com a ferramenta Write e rodar.
- Em f-strings com LaTeX use `rf"..."`.
- Alvos ν exatamente nulos (126 de 960 registros) estão nos Ensaios **3, 5 e 9**.
- Para medir positividade use `predict_rate` (a conversão simulada zera ν depois de esgotar o ácido).
- O RMSE de referência "teto" (0,0142) é o da conversão calculada com as taxas do problema inverso nos 13 ensaios de treino. Não chamá-lo de "menor erro possível".
