#!/usr/bin/env python3
"""
Laboratorio N.º 3 - Canal de medición de O2 (celda simulada + amplificador)
Recalcula las Tablas 5 y 6 del informe a partir de los CSV de /datos
y genera las gráficas de /imagenes/resultados.

Uso:  python analisis/analisis.py
"""
import csv, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = pathlib.Path(__file__).resolve().parent.parent
OUT = RAIZ / "imagenes" / "resultados"
OUT.mkdir(parents=True, exist_ok=True)

def leer(nombre):
    with open(RAIZ / "datos" / nombre, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

A = leer("etapa_A_celda_simulada.csv")
B = leer("etapa_B_amplificador.csv")

# --- parámetros medidos (Tabla 1 y 2) ---
V0 = 3.29
R1, R2, Rg, Rf1, Rf2 = 9730.0, 216.2, 981.0, 9880.0, 9750.0
OFFSET_SALIDA_mV = -39.9

cmd   = [r["comando"] for r in A]
cod   = np.array([float(r["codigo_dac"]) for r in A])
V1    = np.array([float(r["V1_medido_V"]) for r in A])
TP1_A = np.array([float(r["TP1_medido_mV"]) for r in A])
TP1_e = np.array([float(r["TP1_esperado_guia_mV"]) for r in A])

# =============== ETAPA A (Tabla 5) ===============
V1_esp = cod / 255 * V0
with np.errstate(divide="ignore", invalid="ignore"):
    dV1  = (V1 - V1_esp) / V1_esp * 100
    dTP1 = (TP1_A - TP1_e) / TP1_e * 100
    cociente = (TP1_A / 1000) / V1
k = R2 / (R1 + R2)

print("=== ETAPA A: celda simulada ===")
print(f"k = R2/(R1+R2) = {k:.5f}")
for i, c in enumerate(cmd):
    d1 = "N/A" if np.isinf(dV1[i]) else f"{dV1[i]:+.2f} %"
    d2 = "N/A" if np.isinf(dTP1[i]) else f"{dTP1[i]:+.2f} %"
    print(f"{c:5s} V1_esp={V1_esp[i]:.3f} V  dV1={d1}  dTP1={d2}  TP1/V1={cociente[i]:.4f}")

# =============== ETAPA B (Tablas 4 y 6) ===============
TP1_B = np.array([float(r["TP1_medido_mV"]) for r in B])
TP2   = np.array([float(r["TP2_medido_V"]) for r in B]) * 1000   # mV
G_dis = 1 + (Rf1 + Rf2) / Rg
G_real = (TP2[3] - TP2[1]) / (TP1_B[3] - TP1_B[1])
err_G = (G_real - G_dis) / G_dis * 100
Vos = OFFSET_SALIDA_mV / G_real
pend, interc = np.polyfit(TP1_B, TP2, 1)
r2 = np.corrcoef(TP1_B, TP2)[0, 1] ** 2

print("\n=== ETAPA B: amplificador ===")
print(f"G diseño = {G_dis:.2f} | G real = {G_real:.2f} | error = {err_G:+.2f} %")
print(f"Offset salida = {OFFSET_SALIDA_mV} mV | Vos referido a entrada = {Vos:.2f} mV")
print(f"Regresión TP2 = {pend:.2f}*TP1 {interc:+.1f} mV  (R2 = {r2:.5f})")

# FiO2 indicada sin calibrar (10 mV por %O2)
fio2_ind = TP2 / 10.0
fio2_real = np.array([0, 21, 50, 100])
print("\nFiO2 indicada sin calibrar (10 mV/%O2):")
for r, i in zip(fio2_real, fio2_ind):
    print(f"  real {r:5.1f} %  ->  indicada {i:6.1f} %  (error {i-r:+.1f} %O2)")

# =============== GRÁFICAS ===============
plt.rcParams.update({"font.size": 11, "axes.grid": True, "grid.alpha": .3})
AZUL, NAR, ROJO, GRIS = "#1f6feb", "#f0883e", "#d1242f", "#6e7781"

# 1) V1 esperado vs medido
fig, ax = plt.subplots(figsize=(7, 4.5))
x = np.arange(len(cmd)); w = .36
ax.bar(x - w/2, V1_esp, w, label="V1 esperado (código/255 · V0)", color=GRIS)
ax.bar(x + w/2, V1, w, label="V1 medido", color=AZUL)
for i in range(len(cmd)):
    if np.isfinite(dV1[i]):
        ax.text(x[i] + w/2, V1[i] + .04, f"{dV1[i]:+.1f} %", ha="center", fontsize=9, color=ROJO)
ax.set_xticks(x); ax.set_xticklabels(cmd); ax.set_ylabel("V1 (V)")
ax.set_title("Etapa A — Salida del DAC del ESP32 (GPIO25)")
ax.legend(); fig.tight_layout(); fig.savefig(OUT / "grafica_V1_esperado_vs_medido.png", dpi=200); plt.close(fig)

# 2) TP1 esperado vs medido
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.bar(x - w/2, TP1_e, w, label="TP1 esperado (guía)", color=GRIS)
ax.bar(x + w/2, TP1_A, w, label="TP1 medido", color=NAR)
ax.set_xticks(x); ax.set_xticklabels(cmd); ax.set_ylabel("TP1 (mV)")
ax.set_title("Etapa A — Tensión de la celda simulada en TP1")
ax.legend(); fig.tight_layout(); fig.savefig(OUT / "grafica_TP1_esperado_vs_medido.png", dpi=200); plt.close(fig)

# 3) TP2 vs TP1 + ajuste lineal
fig, ax = plt.subplots(figsize=(7, 4.5))
xx = np.linspace(0, 50, 100)
ax.plot(xx, pend * xx + interc, "--", color=AZUL, label=f"Ajuste: y = {pend:.2f}x {interc:+.1f}  (R² = {r2:.5f})")
ax.plot(xx, G_dis * xx, ":", color=GRIS, label=f"Ideal sin offset (G = {G_dis:.2f})")
ax.scatter(TP1_B, TP2, s=70, color=NAR, zorder=3, label="Datos medidos (Tabla 4)")
ax.set_xlabel("TP1 (mV)"); ax.set_ylabel("TP2 (mV)")
ax.set_title("Etapa B — Característica de transferencia del amplificador")
ax.legend(fontsize=9); fig.tight_layout(); fig.savefig(OUT / "grafica_TP2_vs_TP1_ajuste.png", dpi=200); plt.close(fig)

# 4) FiO2 indicada sin calibrar vs real
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.plot([0, 100], [0, 100], "--", color=GRIS, label="Lectura ideal")
ax.plot(fio2_real, fio2_ind, "o-", color=ROJO, label="Lectura sin calibrar (10 mV/%O₂)")
for r, i in zip(fio2_real, fio2_ind):
    if r in (21, 100):
        ax.annotate(f"{i:.1f} %", (r, i), textcoords="offset points", xytext=(8, -14), color=ROJO)
ax.set_xlabel("FiO₂ real (%)"); ax.set_ylabel("FiO₂ indicada (%)")
ax.set_title("Efecto del offset y la ganancia sin calibración de 2 puntos")
ax.legend(); fig.tight_layout(); fig.savefig(OUT / "grafica_FiO2_sin_calibrar.png", dpi=200); plt.close(fig)

print("\nGráficas guardadas en", OUT)
