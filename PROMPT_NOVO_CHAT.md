# Prompt para continuar o trabalho em outro chat

Cole o texto abaixo (dentro do bloco) no início do novo chat. O estado detalhado está em `PLANO_RETOMADA_PROXIMO_CHAT.md`, nesta mesma pasta.

```text
Você vai continuar o trabalho do meu TCC (LOP, UFMG, Engenharia Química): modelagem híbrida serial (rede neural + balanço populacional) da lixiviação de concentrado ustulado de zinco. Meu grupo tem 4 pessoas e o orientador é o Prof. Fabrício Bortot Coelho. A ENTREGA FINAL É EM 13/11/2026 (hoje é 07/11/2026 ou depois). O código e a metodologia são só meus; a revisão bibliográfica e as outras seções são do grupo.

PRIMEIRO, leia estes arquivos, nesta ordem:
1. C:\us trem\Doc\UFMG\9\Lop\Codigo_v4\PLANO_RETOMADA_PROXIMO_CHAT.md  (estado, decisões, plano em etapas, perguntas em aberto)
2. A memória do projeto: pasta C:\Users\Usuário\.claude\projects\C--us-trem-Doc-UFMG-9-Lop\memory\ (comece por MEMORY.md)
3. As regras do projeto: C:\us trem\Doc\UFMG\9\Lop\Codigo_v4\.agents\rules\lop_project_rules.md
4. As primeiras entradas do DEVLOG.md (as de 25/10 e 07/11) e C:\us trem\Doc\UFMG\9\Lop\Codigo_v4\Código\etapas\etapa_3_2\subetapa_3_2_6_mlp_otimizacao\PLANO_PENDENTE_FASES_C_D_E.md

O QUE FAZER (na ordem; pare ao fim de cada etapa e me mostre o resultado antes de seguir):
- Etapa 1: integrar o comitê de 10 redes da MLP v2 (pasta Código\outputs\models_saved\mlp_v2) ao SerialHybridModel e à Etapa 4.2, sem mudar nenhum número. Aceitação: a linha da v1 continua com RMSE global de 0,0257 e a da v2 reproduz a Fase E (treino 0,0145; teste cego 0,0202; global 0,0157).
- Etapa 2: Fases C e D do plano pendente (perda ponderada, monotonia e treino ponta a ponta pelo PBM). Etapa 2b: escolher os pesos λ do problema inverso de forma criteriosa (eles foram "chutes" por tentativa e erro; quero testar valores melhores, com validação cruzada deixando um instante de fora e checando o efeito a jusante no erro de X_Zn). Parada de segurança: terça 10/11 ao meio-dia congelo o modelo final; sem ganho claro (maior que 1 erro-padrão em 10 sementes), a v2 fica como final.
- Etapa 3: gráficos e tabela dos 4 ensaios novos de laboratório, com o modelo final congelado: (η; C_A0 em mol/L; V em mL; m em g) = E1 (0,75; 0,25; 200; 6,7), E2 (1,25; 0,75; 200; 12,1), E3 (2,25; 0,75; 200; 6,7), E4 (0,40; 0,25; 200; 12,6). Temperatura (40 °C) e agitação (1000 rpm) iguais às originais; só o volume mudou (200 mL em vez de 400 mL). Instantes: 0,5; 1; 2; 3; 4; 5 e 15 min. E4 tem η abaixo do mínimo do treino (0,5): sinalize a extrapolação. Quero saber se a modelagem prevê esses ensaios. Gere e guarde as previsões ANTES de eu mostrar as medições, registrando no DEVLOG a data e o hash dos arquivos do modelo.
- Etapas 4 a 6: escrever o restante da minha parte (Resultados do híbrido serial, curtos), checklist dos 115 comentários de 09/09, numeração com o grupo, fechamento.

REGRAS QUE VALEM SEMPRE:
- DEVLOG.md cumulativo: uma entrada nova no TOPO por atividade, com as 6 seções (objetivo; hipótese/decisão; ações; o que funcionou com métricas; o que falhou; próximos passos). Nunca apague entradas. O arquivo tem bytes NUL: insira a entrada em modo binário, logo depois da linha "---" que segue a "Regra de Governança".
- Nunca exclua arquivos: mova para uma pasta old\ da etapa, com um README de justificativa.
- Figuras em 300 DPI, PNG e PDF.
- No relatório Word, TUDO que for novo ou alterado FORA da seção de Materiais e Métodos fica em fonte VERMELHA (apêndices, resultados, referências novas). Dentro de Métodos, cor normal.
- O Google Docs oficial do grupo (arquivo 1qBF5H-0xXd5G3Sm4L3So825MNsQi5WLM) é SÓ PARA LEITURA: não escreva nem retire nada de lá. Não altere as partes dos outros membros; eu aviso o grupo.
- O orientador pediu texto curto, sem repetição e sem "cara de texto de IA": voz impessoal e humana, uma mensagem por parágrafo, cada termo definido uma vez, nada de citar nomes sem explicar. Textos em português, citações no formato (Autor; Autor, ano).
- O teste cego (ensaios 7, 8 e 14) já foi visto uma vez (Fase E mínima). Escolha configurações só pela validação cruzada e relate o teste novo ao lado do antigo.
- O NOSSO documento de trabalho é o Documento\RELATÓRIO FINAL LOP_v8.docx (veio da v7, que veio do RELATÓRIO PARCIAL-fab.docx; nenhuma versão anterior é alterada). Cada versão nova nasce da anterior por um script incremental em Documento\ferramentas (a v8 vem de adicionar_resultados_apendices_v8.py), para preservar as minhas edições manuais: nunca regere a partir do -fab sem perguntar. O documento final do grupo continua sendo o do Google Docs. Não tenho como renderizar o Word aqui; a conferência visual é minha.
- Os apêndices B a E têm explicação e RESULTADOS das análises concluídas (para justificar as escolhas). Quando uma análise nova terminar (Fases C e D, pesos do problema inverso, ensaios novos), acrescente os resultados ao apêndice correspondente, em vermelho, com números lidos dos CSVs.
- Commits e push do branch feat/mlp-otimizacao são permitidos (sem incluir arquivos .docx). O pull request #1 (feat/mlp-otimizacao → main) já foi aberto por mim; novos commits entram nele com push. Merge no main: pergunte antes.
- Eu quero acompanhar passo a passo: proponha, execute uma etapa, mostre números e figuras, e pergunte antes de passar para a próxima. Seja direto e honesto sobre o que não foi verificado.
```
