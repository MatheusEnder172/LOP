# Plano: próximos passos da otimização da MLP (subetapa 3.2.6), a partir de 25/10/2026

> **Situação:** pausado em 25/10/2026 a pedido do usuário. O grupo vai alinhar como seguirão os treinos do modelo caixa-preta antes de retomar. O pipeline principal (`main`) continua com a MLP v1; tudo o que está aqui vive no branch `feat/mlp-otimizacao`.

## Contexto: onde estamos

O objetivo da subetapa 3.2.6 é diminuir o erro de X_Zn do híbrido serial nos ensaios que a rede não viu. O protocolo é sempre o mesmo:
- 4 dobras por ensaio e várias sementes;
- nota pelo RMSE de X_Zn fora da dobra, nos 91 pontos experimentais;
- teste cego (ensaios 7, 8 e 14) intocado até o fim.

| Fase | Situação | RMSE de X_Zn fora da dobra (10 sementes) |
| :--- | :--- | :--- |
| A. Linha de base honesta (v1) | concluída, commit `9ed5e31` | 0,183 ± 0,039 |
| B. Optuna (1 a 4 camadas) | concluída, commit `51cdccc` | 0,0363 ± 0,0053 (4 × 21, Tanh, 1.714 épocas fixas) |
| B2. Busca ampliada (até 8 camadas, ln t, residual, Glorot) | concluída, commit no mesmo branch | **0,0326 ± 0,0050** ([90, 45, 22] residual, GELU, ln t, 928 épocas) |
| Teto: X_Zn calculado com os próprios alvos ν | – | 0,014 |

O que aprendemos e muda as fases seguintes:
1. **Treinar com épocas fixas e todos os ensaios** é muito melhor que reservar ensaios para a parada antecipada. A partir de agora, todo treino usa épocas fixas, com o número de épocas escolhido pela validação cruzada. Isso vale também para o ajuste fino da Fase D e para o *ensemble* da Fase E, o que muda o plano original.
2. **A entrada em ln t** foi a melhor ideia nova.
3. **Sementes fazem diferença.** Toda comparação final usa 10 sementes e comparação pareada.
4. **Ainda há espaço até o teto** (0,033 contra 0,014). É esse espaço que D1, D2 e D4 tentam fechar, atacando o desalinhamento entre a perda em ν e o erro em X_Zn.

Base de partida das próximas fases: a **configuração da B2 (tentativa 511)**. A da Fase B fica como alternativa mais simples para a comparação final.

## Passo 0: fechar a B2 (feito em 25/10/2026)
- Fazer o commit da B2 no branch `feat/mlp-otimizacao`: scripts, saídas, README e DEVLOG.

## Fase C: perdas com informação física (D1 e D2)

**Ideia.** Manter a rede da B2 e mudar só a função de perda.
- **D1, perda ponderada pela sensibilidade.** Hoje cada ponto de ν(t) pesa igual na perda, mas ν nos primeiros instantes pesa muito mais em X_Zn, porque δ é a integral de ν. Pela regra da cadeia, o peso de ν(tᵢ) é a soma, nos tempos experimentais tₖ ≥ tᵢ, de X′(δₖ)·∂δₖ/∂νᵢ·(1 + νᵢ). O fator (1 + νᵢ) aparece porque a perda está em ln(1 + ν).
  - O peso é calculado uma vez, na trajetória-alvo de cada ensaio. X′ vem da derivada da PCHIP do `BatchPBMSolver` e vale zero quando X atinge min(1, η).
  - O peso é normalizado para média 1 e elevado a um expoente γ (γ = 0 equivale ao treino atual).
- **D2, monotonia.** Acrescenta-se λ·média(ReLU(∂ν/∂t)²), calculado por autograd em pontos sorteados em todo o domínio de C_A0, η e t, inclusive combinações sem ensaio. Isso obriga ν a não crescer com o tempo, como na física e nos alvos biexponenciais. A penalidade já está implementada e testada no `MLPTrainerV2`. Base: Raissi et al. (2019); von Stosch et al. (2014); Schweidtmann et al. (2024).

**Como.**
1. `fase_c_perdas_fisicas.py`: função `pesos_sensibilidade(dados, gamma)`; o `rodar_cv` já aceita `pesos`.
2. Estudo Optuna pequeno (cerca de 80 tentativas, 24 processos) sobre γ ∈ [0, 2], λ ∈ [1e-4, 10] (escala log, mais a opção λ = 0), com a taxa de aprendizado e o número de épocas reajustados em torno da B2 (os pesos mudam a escala da perda). Estimativa: cerca de 30 a 40 min.
3. Ablação com 10 sementes: base B2, +D1, +D2 e +D1+D2, cada uma com o melhor γ e λ, e comparação pareada contra a B2.

**Figuras.**
- Perfil dos pesos D1 ao longo do tempo para alguns ensaios, mostrando onde a perda passa a "olhar".
- Barras de RMSE com desvio-padrão para as 4 variantes.
- Percentual de pontos do domínio com ∂ν/∂t > 0, antes e depois do D2.
- ν(t) e X_Zn(t) em condições sem ensaio (por exemplo C_A0 = 0,75 M e η = 2), para mostrar que a forma fica física.
- RMSE por ensaio.

**Saída:** `melhor_config_fase_c.json`, relatório, README e DEVLOG. Paro para revisão e faço o commit depois do OK.

## Fase D: treino ponta a ponta através do PBM (D4)

**Ideia.** Em vez de só imitar os alvos ν do problema inverso, ajustar a rede diretamente no X_Zn experimental, passando ν pela integração e pela curva X(δ) dentro do PyTorch. É a forma clássica de treinar um híbrido serial (Psichogios; Ungar, 1992; Thompson; Kramer, 1994; Oliveira, 2004, todos já na revisão). Ela evita herdar o erro dos ajustes inversos, que em 12 ensaios bateram em limites de parâmetro.

**Como.**
1. `Código/src/hybrid/pbm_torch.py`: replica em torch o `simulate_with_v_profile` com o acoplamento do `SerialHybridModel`:
   - malha de 0,25 a 15 min;
   - δ(t₁) = ν(t₁)·t₁, depois trapézio acumulado;
   - X = Hermite cúbica com os nós e as inclinações da PCHIP;
   - X ≤ min(1, η);
   - leitura nos tempos 0,5, 1, 2, 3, 4, 5 e 15 min.
   - Teste: reproduzir o `SerialHybridModel` com diferença menor que 1e-6.
2. `fase_d_ponta_a_ponta.py`: em cada dobra, partir da rede treinada na Fase C (pré-treino) e fazer o ajuste fino com a perda
   MSE(X_Zn experimental) + λ_ν·MSE_log(ν, ν_alvo) + λ·D2.
   - O termo de âncora λ_ν impede que ν perca a forma física, já que são só cerca de 70 pontos de X por dobra.
   - Ajuste em lote completo, com épocas fixas.
3. Estudo Optuna pequeno (cerca de 50 tentativas) sobre λ_ν, a taxa de aprendizado do ajuste fino e o número de épocas. Depois, 10 sementes com comparação pareada contra a Fase C.

**Figuras.**
- X_Zn por ensaio (C contra D).
- ν(t) antes e depois do ajuste fino.
- Barras de RMSE.
- RMSE por ensaio.

**Risco.** Com poucos pontos, o ajuste fino pode sobreajustar. Se a Fase D não superar a C dentro de um erro-padrão, ela entra no texto como resultado negativo documentado e a Fase C segue.

Paro para revisão e faço o commit depois do OK.

## Fase E: modelo final em *ensemble* e comparação v1 × v2

> **Atualização (25/10/2026, noite):** a pedido do usuário, rodou-se uma **Fase E mínima** sobre a B2, sem C e D, para a metodologia do relatório descrever o pipeline completo. Feitos: itens 2 (ensemble de 10 membros, `outputs/models_saved/mlp_v2/`) e 4 (teste cego avaliado uma vez: RMSE de X_Zn 0,0202 contra 0,0353 da v1), mais figuras e relatório em `fase_e/`. Pendentes: itens 3 e 5 (integração no `SerialHybridModel` e na Etapa 4.2). **Atenção:** como o teste cego já foi visto, se as Fases C e D forem retomadas, a escolha entre B2, C e D deve ser feita só pela validação cruzada, e o resultado no teste da nova configuração deve ser relatado junto com este, sem substituí-lo em silêncio.

1. **Escolha** entre B, B2, C e D pelo RMSE com 10 sementes e regra de um erro-padrão (Hastie et al., 2009).
2. **Ensemble:** 10 membros da configuração escolhida, cada um com uma semente, treinados nos **13 ensaios de treino com épocas fixas**, sem reserva de ensaios. A predição é a média de ν, que depois passa pelo PBM. A faixa de incerteza de X_Zn vem de integrar cada membro separadamente (Lakshminarayanan et al., 2017).
   - Arquivos em `outputs/models_saved/mlp_v2/` (membros `.pt` e `mlp_v2_config.json`); `mlp_kinetics_v1.pt` fica intacto.
3. **Integração mínima** em `src/hybrid/serial_hybrid.py`: nova opção `model_type="mlp_v2"` que monta o `KineticsMLPEnsemble`.
4. **Teste cego avaliado uma única vez** (ensaios 7, 8 e 14, 21 pontos).
5. **Etapa 4.2:** `avaliar_hibrido_indomain.py` ganha a linha "Híbrido Serial (MLP v2)". As saídas antigas vão para `old_mlp_v1_<data>/`, com README. A linha da v1 deve continuar com RMSE global de 0,0257.
6. **Figuras finais:**
   - evolução do RMSE fora da dobra de A até D;
   - teste cego, v1 contra v2, por ensaio;
   - curvas de X_Zn dos ensaios de teste com a faixa do *ensemble*;
   - paridade de X_Zn.
7. `modelo_campeao_info.json` e a MCDA ficam como estão até a discussão pendente sobre o campeão.

Paro para revisão e faço o commit depois do OK.

## Depois da subetapa 3.2.6
- Voltar ao relatório no Word e escrever a subseção da arquitetura e do treino da MLP com o pipeline novo, usando os relatórios `.md` de cada fase.
- Referências novas a incluir, em vermelho: Akiba et al. (2019), Bergstra et al. (2011), Cawley e Talbot (2010), Glorot e Bengio (2010), He et al. (2016) e Lakshminarayanan et al. (2017).

## Regras mantidas em todas as fases
- Nada é apagado: o que for substituído vai para `old/`, com README.
- DEVLOG cumulativo, com 6 seções por entrada, inserido em bytes logo após o cabeçalho.
- Figuras em 300 DPI, PNG e PDF.
- Paro ao fim de cada fase para revisão; um commit por fase aprovada.

## Verificação
- `python -m pytest -q test_mlp_otimizacao.py`, com testes novos: pesos D1 com γ = 0 dão 1; `pbm_torch` reproduz o `SerialHybridModel`; o *ensemble* devolve ν ≥ 0.
- A configuração base da B2 reproduz 0,0326 na ablação da Fase C.
- Os testes antigos (`test_mlp.py`, `test_serial_hybrid.py` e `test_avaliacao_indomain.py`) continuam passando.
- Na etapa 4.2, a linha da v1 continua com 0,0257.
