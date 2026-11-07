# Plano de retomada para o próximo chat (escrito em 07/11/2026; prazo atualizado no mesmo dia)

Este arquivo reúne o estado do projeto, as decisões do usuário e o que fazer em seguida, para que um novo chat continue sem depender da conversa anterior. **A entrega final é em 13/11/2026** (sexta-feira; antes era 10/11). O usuário disse que sobra tempo até para receber os resultados do laboratório e incluí-los.

## 0. Prompt para abrir o novo chat

O prompt completo, pronto para colar, está em `Codigo_v4/PROMPT_NOVO_CHAT.md`.

## 1. Situação em uma página

- **Modelo.** O pipeline oficial (`main`, commit `f62f39b`) usa a MLP v1. No branch `feat/mlp-otimizacao` há a **MLP v2**: comitê de 10 redes ([90, 45, 22] residual, GELU, entrada em ln t, 928 épocas fixas), com RMSE de X_Zn fora da dobra de 0,0326 ± 0,0050 (10 sementes) e **0,0202 no teste cego** (v1: 0,0353; fenomenológico puro: 0,0780). A v2 **ainda não está integrada** ao `SerialHybridModel` nem à Etapa 4.2.
- **Teste cego (ensaios 7, 8 e 14) já foi visto uma vez**, na Fase E mínima. Qualquer mudança futura deve ser escolhida só pela validação cruzada.
- **Relatório.** A v7 (`Documento/RELATÓRIO FINAL LOP_v7.docx`) tem a Metodologia do híbrido serial com 3.317 palavras (eram 6.296) e os Apêndices B a E, em vermelho, com a explicação completa. Os Resultados, as Conclusões, o Resumo e o Apêndice A continuam vazios no documento do grupo.
- **Orientador (Fabrício).** Em 29/10 deixou 38 comentários no `RELATÓRIO PARCIAL-fab.docx` (3 na minha seção, já tratados na v7) e, em 07/11, pediu por WhatsApp texto bem mais curto, sem repetição e sem "cara de texto de IA", além de corrigir a ideia de que v(D,t) → v(t) transforma a EDP em EDO (o que faz isso é o método das características). Essas duas últimas correções estão em seções de outros membros.
- **4 ensaios novos de laboratório** (07/11): o usuário quer saber se a modelagem os prevê e precisa de gráficos e tabela (Seção 5), gerados por último, com o modelo final.

## 2. Regras de trabalho e decisões do usuário

**Regras do projeto** (`.agents/rules/lop_project_rules.md`):
- `DEVLOG.md` cumulativo, com 6 seções por entrada (objetivo, hipótese/decisão, ações, o que funcionou com métricas, o que falhou, próximos passos). Nunca apagar entradas antigas. O arquivo tem trechos corrompidos (bytes NUL), então a entrada nova é inserida **em bytes**: abrir o arquivo em modo binário, localizar `---\r\n\r\n` depois do texto "Regra de Governança", inserir a entrada (com `\r\n`) nesse ponto e gravar de volta, sem reescrever o restante.
- Nunca excluir arquivos: mover para `old/` da etapa com um README de justificativa.
- Figuras em 300 DPI, PNG e PDF. Checkpoints versionados em `Código/outputs/models_saved/`.

**Decisões do usuário** (com a data):
1. (24/10) Código congelado até então; foco na Metodologia. (07/11) Retomar a implementação do que falta, na ordem: apêndices → modelagem → escrever o restante → gráficos dos 4 ensaios.
2. (24/10) Escrever direto no Word, formato ABNT igual ao do documento, equações nativas (LaTeX → OMML), voz impessoal e humana, citações "(Autor; Autor, ano)".
3. (24/10) Nada de regime contínuo nem de Balarini na Metodologia; usar só a MLP; sem RF, SVR, XGBoost nem MCDA por enquanto; a discussão sobre a escolha do campeão fica para depois.
4. (25/10) **Tudo o que for novo ou alterado fora de Métodos vai em fonte vermelha** (apêndices, resultados, referências novas).
5. (25/10) Pausa nas Fases C e D até alinhar o caixa-preta com o grupo; (07/11) retomar: integrar a v2 e depois as Fases C e D.
6. (07/11) O **Google Docs oficial** (arquivo `1qBF5H-0xXd5G3Sm4L3So825MNsQi5WLM`, de Rodrigo, atualizado em 07/11) é **só para leitura**: não escrever, não retirar nada. As partes dos outros membros ficam como estão; o usuário vai avisá-los e o grupo adequa depois.
7. (07/11) Metodologia enxuta e explicação completa em **apêndices separados** (B a E). Aprovado.
8. (07/11) Ensaios novos: temperatura (40 °C) e agitação (1000 rpm) iguais; só o volume mudou, de 400 para 200 mL. **Instantes de amostragem iguais aos originais: 0,5; 1; 2; 3; 4; 5 e 15 min.** As medições ainda serão recebidas e entrarão no relatório.
9. (07/11) **Prazo da entrega final: 13/11/2026.**
10. (07/11) Pesos λ do problema inverso (λ1 = λ2 = 1e-4, λ3 = 1e-7, λ4 = 1e-6): foram escolhidos por **tentativa e erro** ("chutes"), sem critério sistemático. O usuário quer **testar valores melhores** (Etapa 2b). O texto da v7 já diz isso (no script `reorganizar_apendices_hibrido_serial.py`; a v7 em si ainda não foi regerada).
11. (07/11, depois) O documento final do grupo continua sendo o do Google Docs, mas **o nosso documento de trabalho é a v7, que passa a v8** (e v9 etc. nas próximas rodadas): ele é a base para editar. Cada versão nova nasce da anterior por um script incremental (que preserva edições manuais), e não por regeração a partir do `-fab`.
12. (07/11, depois) Push do branch autorizado e **feito** (`origin/feat/mlp-otimizacao`). O **pull request #1** (`feat/mlp-otimizacao` → `main`) foi aberto pelo usuário em 07/11, sem descrição; novos commits entram nele com push. Não há `gh` no computador e o conector do GitHub não está autorizado, então a descrição e o merge são feitos por ele (merge só com autorização).
13. (07/11, depois) Cortar da Metodologia o parágrafo de abertura do híbrido serial que repete a revisão: **feito na v8**.
14. (07/11, depois) Os **apêndices passam a conter também os resultados das análises** (para justificar as escolhas), e não só a explicação do método. Feito na v8 para as análises concluídas (B.5, D.3, E.5 a E.7). As análises ainda em andamento (Fases C e D, escolha dos pesos do problema inverso, ensaios novos) entram quando terminarem.
15. Commits estão autorizados; arquivos Word (`.docx`) ficam fora dos commits. Push e pull request **não foram discutidos**: perguntar antes.

## 3. O que já está pronto

| Item | Onde | Observação |
| :--- | :--- | :--- |
| Protocolo comum e trainer v2 | `Código/etapas/etapa_3_2/subetapa_3_2_6_mlp_otimizacao/` (`protocolo_cv.py`, `modelo_mlp_v2.py`) | 4 dobras por ensaio, 3 sementes na busca, nota em X_Zn fora da dobra (91 pontos) |
| Fases A, B, B2 | mesma pasta, saídas em `Código/outputs/etapa_3_2/subetapa_3_2_6_mlp_otimizacao/fase_a, fase_b, fase_b2` | v1: 0,183; Fase B: 0,0363; B2: 0,0326; teto: 0,014 |
| Fase E mínima | `fase_e_ensemble_final.py`; modelos em `Código/outputs/models_saved/mlp_v2/` (10 membros + `mlp_v2_config.json`) | O script recusa retreinar se já houver membros |
| Plano das Fases C, D, E completas | `PLANO_PENDENTE_FASES_C_D_E.md` (na pasta da subetapa) | Detalha D1, D2 e D4 |
| Contribuição dos termos de penalização do problema inverso | `Código/outputs/etapa_2_1/tabela_contribuicao_penalidades.csv` | Usada no Apêndice B |
| Relatório v7 | `Documento/RELATÓRIO FINAL LOP_v7.docx` | Gerado por `Documento/ferramentas/reorganizar_apendices_hibrido_serial.py` a partir do `RELATÓRIO PARCIAL-fab.docx` (na pasta `Lop`), que não é alterado |
| **Relatório v8 (documento de trabalho)** | `Documento/RELATÓRIO FINAL LOP_v8.docx` | Gerado a partir da v7 por `Documento/ferramentas/adicionar_resultados_apendices_v8.py` (a v7 não é alterada): remove o parágrafo repetido da abertura e acrescenta, em vermelho, B.5 (reconstrução do problema inverso), D.3 (treino do comitê) e E.5 a E.7 (linha de base, busca de hiperparâmetros, teste cego). Todos os números vêm dos CSVs de `Código/outputs/` |
| Texto longo original (25/10) | `Documento/ferramentas/escrever_hibrido_serial.py` e `escrever_resultados_hibrido.py` | A primeira alimenta o Apêndice E (E.2 a E.4); a segunda tem os Resultados da 25/10 (em vermelho), ainda longos |
| Figuras da Metodologia e dos Resultados | `Documento/figuras_metodologia/`, `Documento/figuras_resultados/` | Geradas por scripts `gerar_figuras_*.py` |

**Commits no branch `feat/mlp-otimizacao`:** `9ed5e31` (Fase A), `51cdccc` (B), `cdf37d7` (B2), `ebf08e7` (Fase E mínima), mais o commit das notas de 07/11 (esta etapa). O GitHub (`origin/main`) ainda está em `f62f39b`.

## 4. Plano do que fazer agora

### Etapa 1. Integrar a v2 ao pipeline (sem mudar nenhum número)
1. Em `Código/etapas/etapa_3_2/subetapa_3_2_6_mlp_otimizacao/modelo_mlp_v2.py`, acrescentar uma função `carregar_ensemble_v2(models_dir, scaler_X)` que lê `mlp_v2_config.json`, monta cada membro com `MLPTrainerV2(...).build_model()` e carrega os `.pt` (veja `carregar_membros` em `fase_e_ensemble_final.py`).
2. Em `Código/src/hybrid/serial_hybrid.py`: incluir a pasta da subetapa 3.2.6 no `sys.path` e aceitar `model_type="mlp_v2"` em `_load_model_by_type`. O nome `KineticsMLPEnsemble` contém "MLP", então a detecção de tipo e o carregamento do `scaler_X` já funcionam. Acrescentar um método que devolva o X_Zn de **cada membro** (para a faixa mínimo–máximo), sem mudar o `simulate` existente.
3. Em `Código/etapas/etapa_4_2_avaliacao_indomain/avaliar_hibrido_indomain.py`: acrescentar a linha "Híbrido Serial (MLP v2, comitê)". Antes, mover as saídas atuais para `outputs/etapa_4_2_avaliacao_indomain/old_mlp_v1_<data>/` com README.
4. Testes novos (em `test_mlp_otimizacao.py` ou arquivo próprio): `model_type="mlp_v2"` instancia, simula, respeita X ≤ min(1, η) e reproduz o X_Zn da Fase E.
5. `modelo_campeao_info.json` e a MCDA **não** são alterados (discussão pendente).

**Aceitação:** a linha da v1 continua com RMSE global de 0,0257; a da v2 reproduz a Fase E (treino 0,0145; teste cego 0,0202; global 0,0157); os testes antigos (`test_mlp.py`, `test_serial_hybrid.py`, `test_avaliacao_indomain.py`) passam. Registrar no DEVLOG e fazer commit.

### Etapa 2. Fases C e D (com parada de segurança)
O detalhe está em `PLANO_PENDENTE_FASES_C_D_E.md`. Resumo:
- **Fase C:** perda ponderada pela sensibilidade de X_Zn a ν (D1) e penalidade de monotonia ∂ν/∂t ≤ 0 (D2, já implementada no `MLPTrainerV2`), sobre a configuração da B2; estudo Optuna pequeno (cerca de 80 tentativas) para γ e λ; ablação com 10 sementes e comparação pareada contra a B2.
- **Fase D:** treino ponta a ponta através do PBM (novo `Código/src/hybrid/pbm_torch.py`, que deve reproduzir o `SerialHybridModel` com diferença menor que 1e-6), partindo da rede da Fase C.
- **Parada de segurança:** se até a **terça-feira 10/11 ao meio-dia** C, D e a Etapa 2b não tiverem ganho claro, **congelar a v2 (B2 + comitê) como modelo final**. Critério de ganho: RMSE fora da dobra menor, em mais de 1 erro-padrão, que o da B2 (0,0326), em 10 sementes.
- **Cuidado:** o teste cego já foi visto. Escolher só pela validação cruzada e, se adotar uma configuração nova, **relatar o teste cego novo ao lado do antigo**. Se for retreinar o comitê, mover `models_saved/mlp_v2/` para `old_mlp_v2_B2/` com README (o script recusa sobrescrever). Chamar o novo modelo de "v3" para não confundir.
- **Se adotar algo novo,** atualizar a v7: números do Apêndice D (arquitetura/treino), do Apêndice E (busca, comitê), da Tabela 4.XX.8 e dos parágrafos T_TR2 e T_CR3 de `reorganizar_apendices_hibrido_serial.py`. Se não adotar, registrar C e D como resultado neutro, em poucas linhas no Apêndice E.

### Etapa 2b. Escolha criteriosa dos pesos do problema inverso (opcional, mexe nos alvos)
**Por quê.** Os pesos λ foram "chutes" (decisão 10). Além disso, em 12 dos 16 ensaios algum parâmetro do ajuste parou no limite (a2 = 80, b2 = 4 ou c = 0,03), e a verificação a posteriori (Apêndice B) mostra que a penalidade de a1 pesa em média 16% do termo de ajuste. Melhores alvos ν podem baixar o teto de 0,014 e o erro da rede.

**Como (pasta nova `Código/etapas/etapa_2_2_sensibilidade_penalizacoes/`; não alterar a Etapa 2.1):**
1. **Critério.** Não escolher λ pelo ajuste dentro da amostra aos 7 pontos de cada ensaio (as penalidades existem justamente para regularizar). Usar **validação cruzada deixando um instante de fora** em cada ensaio (16 ensaios × 7 instantes): resolver o problema inverso sem aquele ponto e medir o erro de X_Zn nele. Comparar uma grade (por exemplo, multiplicar todos os λ por 0, 0,1, 1, 10 e 100, e variar cada λ isoladamente) pela regra de um erro-padrão. Custo estimado: cerca de 20 min com 24 processos (a função objetivo está em `Código/etapas/etapa_2_1_otimizacao_alvos_v/otimizar_alvos_v.py`, linhas 59 a 110).
2. **Limites.** Testar também limites mais largos para a2, b2 e c (e a forma da parametrização), já que muitos ensaios ficam presos neles.
3. **Efeito a jusante.** Para os melhores candidatos, gerar os novos alvos ν, retreinar a configuração da B2 **no mesmo protocolo** (4 dobras, 10 sementes) e comparar o RMSE de X_Zn fora da dobra contra a **conversão medida** (nunca contra a reconstruída) com 0,0326.
4. **Adoção.** Só se o ganho for maior que 1 erro-padrão. Adotar significa regerar as bases em `Base de dados/processed/` (mover as atuais para `old/` com README; as partições por ensaio e os escalonadores das entradas não mudam, só a coluna do alvo), refazer a Etapa 3.1 e a Fase E, e **atualizar os números dos Apêndices B, C, D e E, as Figuras de reconstrução e os Resultados**. Se não adotar, registrar o resultado (também é informação útil para o Apêndice B).
5. Mesmo sem adotar, o resultado serve para responder ao orientador sobre a escolha "empírica" dos pesos.

**Atenção:** o teste cego já foi visto; relatar o novo ao lado do antigo.

### Etapa 3. Os 4 ensaios novos (modelo final congelado)
Ver Seção 5.

### Calendário (hoje é sábado 07/11; entrega na sexta 13/11)
| Dia | O que |
| :--- | :--- |
| Sáb 07 e dom 08 | Etapa 1 (integração da v2) e início das Etapas 2 e 2b |
| Seg 09 | Fases C e D; Etapa 2b |
| **Ter 10, meio-dia** | **Decisão e congelamento do modelo final** (parada de segurança) |
| Ter 10 e qua 11 | Gráficos e tabela dos 4 ensaios; atualizar a v7 com os números finais; Resultados |
| Qui 12 | Medições do laboratório (se chegarem), comparação, checklist dos comentários, numeração com o grupo |
| Sex 13 | Revisão final e entrega |

### Etapa 4. Escrever o restante da minha parte
- **Resultados do híbrido serial**, curtos (o orientador pediu texto enxuto): reconstrução pelo problema inverso, escolha da configuração, teste cego (v1 × v2 × fenomenológico), e a subseção com os 4 ensaios novos. Partir de `escrever_resultados_hibrido.py` (texto de 25/10, longo, em vermelho) e **cortar**; usar as figuras da Fase E (`fase_e/fig_fe_*`) e `Documento/figuras_resultados/`.
- Atualizar a v7 com os números finais; manter a regra do vermelho fora de Métodos.
- Conclusões, Resumo e Apêndice A são do grupo.

### Etapa 5. Comentários do orientador
- **115 comentários de 09/09** (`Summary of Comments on RELATÓRIO FINAL LOP.pdf`, na pasta `Lop`): montar o checklist comentário a comentário contra a v7. **Ainda não foi feito** (o usuário pediu em 24/10).
- **38 comentários de 29/10** (no `RELATÓRIO PARCIAL-fab.docx`): os 3 da minha seção foram atendidos na v7; os demais são das seções dos colegas. O usuário vai avisá-los.
- **Mensagens de 07/11:** correção de EDP × EDO (seção do white box, de outra pessoa); corte de repetições entre revisão e metodologia (definições de rede neural, treinamento, erro quadrático, SVM etc.).

### Etapa 6. Fechamento
- Numeração definitiva (cerca de 140 marcadores "4.XX"/"3.XX", figuras, tabelas, equações) **junto com o grupo**, no documento oficial.
- Conferir referências (todas as citações da minha parte já têm entrada).
- Merge do branch no `main` e push só com autorização do usuário.
- Discussão pendente da MCDA e do campeão: a MCDA usa métricas do teste cego (vazamento), o R² do SVR está fixo em 0,72 no `comparar_modelos.py:267`, e o "DDM puro" da Etapa 4.2 passa a taxa da MLP pelo PBM (não é caixa-preta pura).

## 5. Os 4 ensaios novos: especificação

| Ensaio | η | C_A0 (mol/L) | V (mL) | m (g) |
| :-: | :-: | :-: | :-: | :-: |
| E1 | 0,75 | 0,25 | 200 | 6,7 |
| E2 | 1,25 | 0,75 | 200 | 12,1 |
| E3 | 2,25 | 0,75 | 200 | 6,7 |
| E4 | 0,40 | 0,25 | 200 | 12,6 |

- η é a razão molar H2SO4/ZnO. A calcina equivale a cerca de 81% de ZnO (65% de Zn total), e com isso m, V, C_A0 e η fecham nos quatro ensaios, como nos 16 originais. Os 16 originais usaram 400 mL; os novos usam 200 mL. O modelo só usa C_A0, η e t.
- **Domínio:** E1, E2 e E3 estão dentro do planejamento (C_A0 de 0,1 a 1,5; η de 0,5 a 3,1). **E4 (η = 0,40) está abaixo do mínimo do treino (0,5): pequena extrapolação**, a sinalizar nos gráficos e na tabela.
- **Limite físico:** o modelo impõe X_Zn ≤ min(1, η). Em E1 o patamar não pode passar de 0,75 e em E4, de 0,40 (ácido limitante). Mostrar essa linha.
- **O que gerar** (pasta nova em `Código/etapas/`, por exemplo `etapa_6_novos_ensaios_laboratorio/`; confirmar a numeração em `PLANO_MESTRE_FASES_4_5_6.md`):
  - 4 figuras, uma por ensaio, e 1 painel com os 4: X_Zn(t) de 0 a 15 min, com a média do comitê, a faixa mínimo–máximo dos 10 membros, o modelo fenomenológico puro (`BatchPBMSolver.simulate(..., alpha=0.0)`, como na Etapa 4.2), a linha min(1, η) e marcadores nos instantes de amostragem.
  - Tabela (CSV e XLSX): ensaio, η, C_A0, t, X_Zn prevista (média, mínimo, máximo, desvio entre membros), X_Zn do fenomenológico, limite min(1, η) e C_A residual prevista.
  - Um modelo de arquivo `medicoes_template.csv` (ensaio, t_min, XZn_medido) e uma opção do script para **sobrepor as medições** e calcular o RMSE, para o usuário comparar quando tiver os dados.
  - Relatório curto `.md`, DEVLOG e commit.
- **Leitura dos resultados:** a faixa entre membros **não é intervalo de confiança** (só variabilidade de treino). Como referência de erro típico, usar o RMSE fora da dobra (0,033) e o do teste cego (0,020). Uma diferença sistemática pode vir da mudança de volume, que o modelo não conhece; dizer isso nas conclusões.
- **Instantes (confirmado em 07/11):** 0,5; 1; 2; 3; 4; 5 e 15 min, iguais aos originais. As medições serão recebidas depois e entram no relatório.
- **Integridade da previsão:** para que seja uma previsão de verdade, **gerar e guardar as previsões antes de ver as medições**, com o modelo congelado (registrar no DEVLOG a data e o hash SHA-256 dos arquivos `.pt` usados). Se o usuário receber as medições antes de o modelo final estar congelado, gerar antes uma previsão com a v2 atual e guardá-la como "previsão a priori". Não ajustar o modelo com os 4 ensaios para avaliar a previsão; usá-los depois, se o usuário quiser, como validação adicional (decisão à parte).
- **Resultados no relatório:** se as medições chegarem, acrescentar nos Resultados (em vermelho) uma subseção curta com as 4 curvas previstas e medidas e o RMSE por ensaio.

## 6. Perguntas em aberto
Respondidas em 07/11: a entrega final é 13/11; os instantes dos ensaios novos são os originais; os pesos λ foram por tentativa e erro; o documento de trabalho é a v7/v8 (o do Google Docs segue como o oficial do grupo); as medições dos ensaios novos têm data desconhecida; o push foi autorizado e feito; o parágrafo repetido da abertura foi cortado. Seguem abertas:
1. Escrever a descrição do pull request #1 (hoje vazia) e decidir o merge, depois da integração e do congelamento do modelo.
2. Se a Etapa 2b mudar os alvos ν, o grupo precisa ser avisado (a base e os Apêndices B, C, D e E mudam).
3. Quando as medições dos 4 ensaios chegarem, comparar com as previsões e acrescentar o resultado aos Apêndices e aos Resultados.

## 7. Armadilhas técnicas
- **Word:** a exportação por COM já travou (processo `WINWORD.EXE` oculto); não há outro renderizador no computador. A conferência visual é do usuário.
- **Strings com LaTeX** nos scripts devem ser raw (`r"..."`); integrandos e somatórios em `{}` para não gerar caixas vazias no Word.
- **`fase_b_optuna_hpo.n_parametros`** subconta parâmetros de redes residuais (a contagem real da B2 é 21.569, não 5.490); a escolha da B2 não muda.
- `pytest` da subetapa 3.2.6 leva cerca de 40 s.
- A v7 é gerada por script a partir do `-fab`; editar à mão no Word e depois rodar o script de novo **apaga** as edições. Alterar o script e regerar, ou editar o resultado e parar de regerar.
- Máquina: 32 núcleos; as buscas Optuna usaram 24 processos em paralelo.

## 8. Mapa de arquivos e comandos úteis

```bash
# testes da subetapa
python -m pytest -q Código/etapas/etapa_3_2/subetapa_3_2_6_mlp_otimizacao/test_mlp_otimizacao.py
# Fase E (já feita; o treino recusa sobrescrever)
python fase_e_ensemble_final.py avaliar
# regerar a v7 (não sobrescreve o -fab)
python Documento/ferramentas/reorganizar_apendices_hibrido_serial.py --saida "Documento/teste_v7.docx"
```

- Ferramentas do relatório: `Documento/ferramentas/docx_utils.py` (`SectionWriter`, `pintar`, `latex_to_omml`), `reorganizar_apendices_hibrido_serial.py`, `escrever_hibrido_serial.py`, `escrever_resultados_hibrido.py`, `analisar_contribuicao_penalidades.py`.
- Memória do projeto: pasta `memory` do projeto LOP (índice em `MEMORY.md`): escopo e prazo, estilo de escrita, regra do vermelho, otimização da MLP, ensaios novos e lembrete dos 115 comentários.
