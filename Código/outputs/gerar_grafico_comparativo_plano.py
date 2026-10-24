"""Script de Geração da Figura Comparativa Síntese do Plano de Implementação.

Gera a figura de 4 painéis em 300 DPI (PNG e PDF):
  (a) Evolução Histórica do Erro RMSE de Conversão de Zinco (Antigo vs. Novo White-Box vs. Híbrido MLP);
  (b) Comparativo dos 4 Modelos Híbridos Acoplados ao PBM em t > 0 (R² e RMSE);
  (c) Matriz de Decisão Multicritério MCDA (Opção 5) coroando o MLP;
  (d) Status Geral de Execução: O Que Foi Feito (100% das Etapas 0.3 a 5) vs. Próximos Passos (Texto TCC e CSTRs).
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8.5,
    "figure.titlesize": 13,
    "axes.grid": True,
    "grid.alpha": 0.35,
    "grid.linestyle": "--",
})

fig = plt.figure(figsize=(16, 11), constrained_layout=True)
gs = fig.add_gridspec(2, 2)

# -------------------------------------------------------------
# Painel (a): Evolução Histórica do Erro RMSE (X_Zn, Global e Teste Cego)
# -------------------------------------------------------------
ax1 = fig.add_subplot(gs[0, 0])
etapas_nomes = [
    "Abordagem Antiga\n(com α=5500, sem ÷D³)",
    "Novo White-Box Puro\n(RRB ÷ D³, sem α, t>0)",
    "Novo Híbrido Serial\n(MLP Campeão + PBM, t>0)",
]
rmse_glob = [10.79, 7.02, 2.57]
rmse_teste = [11.50, 7.80, 3.53]

x = np.arange(len(etapas_nomes))
w = 0.32

b1 = ax1.bar(x - w/2, rmse_glob, w, label="In-Domain Global (16 ensaios)", color="#3b82f6", edgecolor="black", alpha=0.9)
b2 = ax1.bar(x + w/2, rmse_teste, w, label="Teste Cego (Ensaios 7, 8, 14)", color="#ef4444", edgecolor="black", alpha=0.9)

for bar in b1:
    h = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2, h + 0.25, f"{h:.2f}%", ha="center", va="bottom", fontweight="bold", fontsize=9)
for bar in b2:
    h = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2, h + 0.25, f"{h:.2f}%", ha="center", va="bottom", fontweight="bold", fontsize=9)

ax1.set_xticks(x)
ax1.set_xticklabels(etapas_nomes, fontweight="bold")
ax1.set_ylabel("Erro Médio de Conversão RMSE (%)")
ax1.set_ylim(0, 14.5)
ax1.set_title("(a) Evolução do Erro de Predição com as Novas Modificações", fontweight="bold")
ax1.legend(loc="upper right", framealpha=0.9)
ax1.annotate("Redução de -76,2% no erro global!", xy=(2 - w/2, 2.57), xytext=(1.2, 5.0),
            arrowprops=dict(arrowstyle="->", color="#1e3a8a", lw=1.5),
            fontweight="bold", color="#1e3a8a", fontsize=9.5, bbox=dict(boxstyle="round,pad=0.3", facecolor="#dbeafe", edgecolor="#3b82f6"))

# -------------------------------------------------------------
# Painel (b): Comparativo dos 4 Modelos Híbridos In-Domain (t > 0, N = 112 pts)
# -------------------------------------------------------------
ax2 = fig.add_subplot(gs[0, 1])
modelos_labels = ["White-Box Puro\n(Sem α)", "Híbrido SVR", "Híbrido RF", "Híbrido XGBoost", "Híbrido MLP\n(Campeão C∞)"]
r2_vals = [0.8709, 0.6813, 0.9877, 0.9930, 0.9827]
rmse_vals = [7.02, 11.03, 2.17, 1.63, 2.57]

x2 = np.arange(len(modelos_labels))
ax2_twin = ax2.twinx()

bars_r2 = ax2.bar(x2 - 0.18, [v * 100 for v in r2_vals], 0.35, label="Acurácia R² (%)", color="#10b981", edgecolor="black", alpha=0.85)
bars_rmse = ax2_twin.bar(x2 + 0.18, rmse_vals, 0.35, label="Erro RMSE (%)", color="#f59e0b", edgecolor="black", alpha=0.85)

ax2.set_xticks(x2)
ax2.set_xticklabels(modelos_labels, fontweight="bold", fontsize=8.5)
ax2.set_ylabel("Coeficiente de Determinação R² (%)", color="#047857", fontweight="bold")
ax2_twin.set_ylabel("Erro RMSE de Conversão (%)", color="#b45309", fontweight="bold")
ax2.set_ylim(50, 108)
ax2_twin.set_ylim(0, 13)
ax2.grid(True, linestyle="--", alpha=0.3)
ax2_twin.grid(False)
ax2.set_title("(b) Comparativo dos 4 Modelos Híbridos Acoplados ao PBM (t > 0)", fontweight="bold")

lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2_twin.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc="lower right", framealpha=0.9)

# -------------------------------------------------------------
# Painel (c): Matriz MCDA Opção 5 — Por que o MLP foi Campeão
# -------------------------------------------------------------
ax3 = fig.add_subplot(gs[1, 0])
mcda_modelos = ["MLP (Campeão)", "SVR (RBF)", "Random Forest", "XGBoost"]
mcda_scores = [92.84, 79.91, 34.50, 24.14]
cores_mcda = ["#2563eb", "#8b5cf6", "#10b981", "#f97316"]

y_pos = np.arange(len(mcda_modelos))
bars_mcda = ax3.barh(y_pos, mcda_scores, color=cores_mcda, edgecolor="black", height=0.55, alpha=0.9)
ax3.set_yticks(y_pos)
ax3.set_yticklabels(mcda_modelos, fontweight="bold")
ax3.invert_yaxis()
ax3.set_xlabel("Score Total MCDA (0 a 100 pontos — Opção 5)")
ax3.set_xlim(0, 105)
ax3.set_title("(c) Seleção Multicritério (MCDA Opção 5: C∞, Autograd, Log, Latência)", fontweight="bold")

for bar in bars_mcda:
    w_val = bar.get_width()
    ax3.text(w_val + 1.2, bar.get_y() + bar.get_height()/2, f"{w_val:.2f} pts", va="center", fontweight="bold", fontsize=9)

ax3.text(0.04, 0.12, "Critérios Físicos: Suavidade C∞ (25%), R²_log (25%), R²_δ (20%), R²_teste (20%), Latência (10%)\nMLP: Diferenciável C∞ + Autograd + Latência recorde de 0,19 ms (5,2M pts/s)",
         transform=ax3.transAxes, fontsize=8.2, bbox=dict(boxstyle="round,pad=0.4", facecolor="#f8fafc", edgecolor="#cbd5e1"))

# -------------------------------------------------------------
# Painel (d): Status de Execução do Plano: O Que Foi Feito vs. O Que Falta
# -------------------------------------------------------------
ax4 = fig.add_subplot(gs[1, 1])
etapas_cronograma = [
    "Etapa 0.3: Transformação RRB ÷ D³",
    "Etapa 1.3: White-Box Puro (Sem α, t>0)",
    "Etapa 2.1: Otimização Inversa |v(t)| (t>0)",
    "Etapa 3.1: Splits & Scaler 3D [CA0, η, t]",
    "Etapa 3.2: Treinamento 4 Modelos (3 Inputs)",
    "Etapa 3.2.1: MLP C∞, Autograd & Superfície 3D",
    "Etapa 3.2.5: Matriz MCDA Opção 5 (MLP Campeão)",
    "Etapa 4.1: Orquestrador Serial (t=0 Hardcoded)",
    "Etapa 4.2: Benchmark In-Domain 16 Ensaios",
    "Etapa 5: Validação Externa (Júlio Balarini)",
    "Etapa 6 (Futuro/TCC): Texto Final da Dissertação",
    "Etapa 7 (Futuro/Expansão): Cascata CSTRs Contínuos",
]

status_pct = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 30, 0]
cores_status = ["#16a34a" if p == 100 else ("#f59e0b" if p > 0 else "#94a3b8") for p in status_pct]

y_cron = np.arange(len(etapas_cronograma))
bars_cron = ax4.barh(y_cron, status_pct, color=cores_status, edgecolor="black", height=0.6, alpha=0.9)
ax4.set_yticks(y_cron)
ax4.set_yticklabels(etapas_cronograma, fontsize=8.5)
ax4.invert_yaxis()
ax4.set_xlabel("Progresso de Conclusão (%)")
ax4.set_xlim(0, 120)
ax4.set_title("(d) Status de Execução do Plano: Concluído vs. Próximos Passos", fontweight="bold")

for bar, p in zip(bars_cron, status_pct):
    if p == 100:
        txt = "100% [CONCLUÍDO]"
    elif p > 0:
        txt = f"{p}% [Em Andamento]"
    else:
        txt = "Pendente (Expansão)"
    ax4.text(p + 1.5, bar.get_y() + bar.get_height()/2, txt, va="center", fontsize=7.5, fontweight="bold")

fig.suptitle("Síntese Executiva do Plano de Modelagem Híbrida: O Que Foi Feito vs. O Que Falta", fontsize=13, fontweight="bold")
fig.savefig(OUT_DIR / "fig_comparativo_plano_modificacoes.png", dpi=300)
fig.savefig(OUT_DIR / "fig_comparativo_plano_modificacoes.pdf", dpi=300)
plt.close(fig)
print(f"[OK] Figura comparativa geral salva com sucesso em {OUT_DIR / 'fig_comparativo_plano_modificacoes.png'}!")
