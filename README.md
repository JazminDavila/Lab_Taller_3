<div align="center">

# Canal de medición de oxígeno de una máquina de anestesia
### Celda galvánica de O₂ simulada (ESP32) y amplificador no inversor (TL084N)

**Informe de Laboratorio N.º 3 — Taller de Equipos Biomédicos II**
*Escuela Profesional de Ingeniería Biomédica · Universidad Nacional Mayor de San Marcos (UNMSM)*

![ESP32](https://img.shields.io/badge/MCU-ESP32-red?logo=espressif&logoColor=white)
![Arduino](https://img.shields.io/badge/Firmware-Arduino_IDE-00979D?logo=arduino&logoColor=white)
![Proteus](https://img.shields.io/badge/Simulación-Proteus-blue)
![Python](https://img.shields.io/badge/Análisis-Python-3776AB?logo=python&logoColor=white)
![UNMSM](https://img.shields.io/badge/UNMSM-Ing._Biomédica-8B0000)

</div>

---

## Tabla de contenidos

1. [Resumen](#1-resumen)
2. [Objetivos](#2-objetivos)
3. [Estructura del repositorio](#3-estructura-del-repositorio)
4. [Fundamento teórico](#4-fundamento-teórico)
5. [Diagrama de bloques](#5-diagrama-de-bloques)
6. [Etapa A — Celda de O₂ simulada](#6-etapa-a--celda-de-o₂-simulada)
7. [Etapa B — Amplificador no inversor](#7-etapa-b--amplificador-no-inversor)
8. [Resultados y análisis](#8-resultados-y-análisis)
9. [Conclusiones](#9-conclusiones)
10. [Materiales y equipos](#10-materiales-y-equipos)
11. [Cómo reproducir el trabajo](#11-cómo-reproducir-el-trabajo)
12. [Referencias](#12-referencias)
13. [Integrantes](#13-integrantes)

---

## 1. Resumen

Se implementaron y caracterizaron las **dos primeras etapas del canal de medición de oxígeno** de una máquina de anestesia:

- **Etapa A:** una celda galvánica simulada mediante el **DAC de 8 bits del ESP32** (GPIO25) con un divisor resistivo R₁–R₂.
- **Etapa B:** una **etapa de amplificación no inversora** basada en el amplificador operacional **TL084N**, alimentada con ±12 V.

### Resultados principales

| Indicador | Valor |
|---|---|
| TP1 en 50 % O₂ | **23.8 mV** (dentro del margen aceptable) |
| TP1 en 100 % O₂ | **45.5 mV** (dentro del margen aceptable) |
| Desviación máxima del DAC en V₁ | **−20.79 %** (f100) |
| Voltaje residual en 0 % O₂ (V₁ / TP1) | **88 mV / 1.9 mV** |
| Offset del amplificador referido a la salida | **−39.9 mV** |
| Offset referido a la entrada (Vₒₛ) | **−1.91 mV** (dentro de la hoja de datos) |
| Ganancia real / ganancia de diseño | **20.84 / 21.02** (error −0.86 %) |
| FiO₂ indicada sin calibrar en aire (real 21 %) | **19.1 %** |
| FiO₂ indicada sin calibrar en O₂ puro (real 100 %) | **90.8 %** (error −9.2 %O₂) |

> **Conclusión clave:** el circuito opera de forma lineal y estable, pero la combinación del offset y la desviación de ganancia produciría un error de hasta **−9.2 % O₂** en oxígeno puro sin calibrar. Esto confirma la **necesidad de la calibración clínica en dos puntos (21 % y 100 % O₂)**.

📄 Informe completo en PDF: [`docs/Informe_Laboratorio_3_TEB_II.pdf`](docs/Informe_Laboratorio_3_TEB_II.pdf)

---

## 2. Objetivos

**Objetivo general:** armar la celda de O₂ simulada y su amplificador, que forman las dos primeras etapas del canal de medición de oxígeno de una máquina de anestesia, y comprobar que cada etapa funciona.

**Objetivos específicos:**
- Comprobar que **TP1** entrega los milivoltios esperados para 0, 21, 50 y 100 % de O₂ y, si algún valor no coincide, determinar si el error proviene del **ESP32** o de las **resistencias del divisor**.
- Medir el **offset** del amplificador y su **ganancia real**, y compararlos con los valores de diseño.

---

## 3. Estructura del repositorio

```text
.
├── README.md                      ← este documento
├── LICENSE
├── analisis/
│   ├── analisis.py                ← recalcula Tablas 5 y 6 y genera gráficas
│   └── requirements.txt
├── datos/                         ← datos medidos en laboratorio (CSV)
│   ├── etapa_A_celda_simulada.csv
│   ├── etapa_B_amplificador.csv
│   └── resistencias_y_parametros.csv
├── docs/
│   └── Informe_Laboratorio_3_TEB_II.pdf
├── firmware/
│   └── simulador_o2/
│       └── simulador_o2.ino       ← código del ESP32 (comandos f0, f21, f50, f100)
├── imagenes/
│   ├── diagramas/                 ← diagrama de bloques y esquemáticos
│   ├── etapa_a/                   ← montaje y mediciones de la Etapa A
│   ├── etapa_b/                   ← montaje y mediciones de la Etapa B
│   ├── osciloscopio/              ← captura de TP2
│   └── resultados/                ← gráficas de resultados
└── proteus/
    ├── etapa_A/                   ← proyecto Proteus (ISIS) de la Etapa A
    └── etapa_B/                   ← proyecto Proteus (ISIS) de la Etapa B
```

---

## 4. Fundamento teórico

### Celda galvánica de O₂

La celda galvánica es un sensor electroquímico amperométrico que **genera su propia corriente**, proporcional a la presión parcial de O₂ del gas. Una resistencia de carga la convierte en una tensión de pocos milivoltios:

$$V_{celda} = I_{celda} \cdot R_{carga} \propto P_{O_2}$$

En el laboratorio se simula una celda de **10 mV en aire (21 % O₂)** y **47.6 mV en O₂ puro**, es decir, **0.476 mV por punto porcentual de O₂**. Como el ánodo de plomo se consume con el uso, la sensibilidad baja con el tiempo y el monitor debe calibrarse periódicamente.

### Etapa A: DAC del ESP32 y divisor resistivo

$$V_1 = \frac{N}{255}\cdot V_0 \qquad\qquad TP1 = V_1\cdot\frac{R_2}{R_1+R_2} = k\cdot V_1$$

La guía asigna los códigos **N = 44, 104 y 208** para f21, f50 y f100. Cada paso del DAC equivale a ≈ 12.9 mV en V₁, es decir, ≈ 0.23 mV en TP1 (≈ 0.5 % de O₂).

### Etapa B: amplificador no inversor y offset

$$TP2 = G\cdot TP1 + V_{off}, \qquad G = 1+\frac{R_{f1}+R_{f2}}{R_g}, \qquad V_{off} = G\cdot V_{OS}$$

Con R_f1 = R_f2 = 10 kΩ y R_g = 1 kΩ, la ganancia de diseño es **G = 21**, de modo que TP2 entrega **10 mV por cada punto porcentual de O₂** (0.21 V en aire, 1.00 V en oxígeno puro).

---

## 5. Diagrama de bloques

La laptop envía por el Monitor Serie los comandos `fN` al ESP32, cuyo DAC (GPIO25) genera V₁. El divisor R₁–R₂ entrega TP1 (0 a 47.6 mV) y el amplificador no inversor (G = 21), alimentado con ±12 V, entrega TP2 (0 a 1.00 V).

<p align="center">
  <img src="imagenes/diagramas/fig01_diagrama_bloques.png" alt="Diagrama de bloques del canal de medición" width="800"><br>
  <em>Figura 1. Diagrama de bloques del canal de medición: celda de O₂ simulada y amplificador.</em>
</p>

---

## 6. Etapa A — Celda de O₂ simulada

### Esquemáticos

El pin GPIO25 del ESP32 (canal 1 del DAC) se conecta a R₁ (10 kΩ), cuyo otro extremo es TP1. Entre TP1 y GND se conecta R₂, formando el divisor. Los puntos de medición son V₀ (pin 3V3), V₁ (GPIO25) y TP1.

<table>
  <tr>
    <td align="center"><img src="imagenes/diagramas/fig02_esquematico_referencia_etapa_A.png" width="380"><br><em>Figura 2. Esquemático de referencia (Guía N.º 3)</em></td>
    <td align="center"><img src="imagenes/diagramas/fig03_esquematico_proteus_etapa_A.png" width="380"><br><em>Figura 3. Esquemático en Proteus</em></td>
  </tr>
</table>

> Los proyectos de Proteus están en [`proteus/etapa_A/`](proteus/etapa_A/) (abrir `ROOT.DSN` con Proteus ISIS).

### Montaje

<p align="center">
  <img src="imagenes/etapa_a/fig04_montaje_etapa_A.jpg" alt="Montaje Etapa A" width="450"><br>
  <em>Figura 4. Implementación del circuito de la Etapa A.</em>
</p>

### Medición de resistencias (Tabla 1)

| Resistencia | Ubicación | Valor nominal | Valor medido |
|:-:|---|:-:|:-:|
| R1 | Divisor de la celda simulada | 10 kΩ | 9.73 kΩ |
| R2 | Divisor de la celda simulada | 220 Ω | 216.2 Ω |
| Rg | Amplificador | 1 kΩ | 0.981 kΩ |
| Rf1 | Amplificador | 10 kΩ | 9.88 kΩ |
| Rf2 | Amplificador | 10 kΩ | 9.75 kΩ |

<table>
  <tr>
    <td align="center"><img src="imagenes/etapa_a/fig05_medicion_R1.jpg" width="190"><br><sub>R1 = 9.73 kΩ</sub></td>
    <td align="center"><img src="imagenes/etapa_a/fig06_medicion_R2.jpg" width="190"><br><sub>R2 = 216.2 Ω</sub></td>
    <td align="center"><img src="imagenes/etapa_a/fig07_medicion_Rg.jpg" width="190"><br><sub>Rg = 0.981 kΩ</sub></td>
    <td align="center"><img src="imagenes/etapa_a/fig08_medicion_Rf1.jpg" width="190"><br><sub>Rf1 = 9.88 kΩ</sub></td>
    <td align="center"><img src="imagenes/etapa_a/fig09_medicion_Rf2.jpg" width="190"><br><sub>Rf2 = 9.75 kΩ</sub></td>
  </tr>
</table>

### Tensiones de la celda simulada (Tabla 2)

**V₀ medido (3V3 – GND): 3.29 V**

| Comando | Código DAC | V₁ medido (V) | TP1 medido (mV) |
|:-:|:-:|:-:|:-:|
| `f0` | 0 | 0.088 | 1.9 |
| `f21` | 44 | 0.518 | 11.1 |
| `f50` | 104 | 1.110 | 23.8 |
| `f100` | 208 | 2.126 | 45.5 |

<details>
<summary><b>📷 Ver fotografías de todas las mediciones de la Etapa A (V₀, V₁ y TP1)</b></summary>

<table>
  <tr>
    <td align="center"><img src="imagenes/etapa_a/fig10_medicion_V0.jpg" width="230"><br><sub>V₀ = 3.290 V</sub></td>
    <td align="center"><img src="imagenes/etapa_a/fig11_V1_f0.jpg" width="230"><br><sub>V₁ en f0 = 0.088 V</sub></td>
    <td align="center"><img src="imagenes/etapa_a/fig12_TP1_f0.jpg" width="230"><br><sub>TP1 en f0 = 1.9 mV</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="imagenes/etapa_a/fig13_V1_f21.jpg" width="230"><br><sub>V₁ en f21 = 0.518 V</sub></td>
    <td align="center"><img src="imagenes/etapa_a/fig14_TP1_f21.jpg" width="230"><br><sub>TP1 en f21 = 11.1 mV</sub></td>
    <td align="center"><img src="imagenes/etapa_a/fig15_V1_f50.jpg" width="230"><br><sub>V₁ en f50 = 1.110 V</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="imagenes/etapa_a/fig16_TP1_f50.jpg" width="230"><br><sub>TP1 en f50 = 23.8 mV</sub></td>
    <td align="center"><img src="imagenes/etapa_a/fig17a_V1_f100.jpg" width="230"><br><sub>V₁ en f100 = 2.126 V</sub></td>
    <td align="center"><img src="imagenes/etapa_a/fig17b_TP1_f100.jpg" width="230"><br><sub>TP1 en f100 = 45.5 mV</sub></td>
  </tr>
</table>

</details>

---

## 7. Etapa B — Amplificador no inversor

### Esquemáticos

TP1 se conecta a la entrada no inversora (pin 3) del primer amplificador del TL084N. La entrada inversora (pin 2) va a GND mediante R_g (1 kΩ) y a la salida (pin 1, TP2) mediante R_f1 y R_f2 (10 kΩ cada una) en serie. Se alimenta con **+12 V (pin 4)** y **−12 V (pin 11)**, con capacitores de **100 nF** entre cada pin de alimentación y GND. Los op-amps 2, 3 y 4, que no se usan, se conectan como **seguidores** con la entrada no inversora a GND.

<table>
  <tr>
    <td align="center"><img src="imagenes/diagramas/fig18_esquematico_referencia_etapa_B.png" width="380"><br><em>Figura 18. Esquemático de referencia (Guía N.º 3)</em></td>
    <td align="center"><img src="imagenes/diagramas/fig19_esquematico_proteus_etapa_B.png" width="380"><br><em>Figura 19. Esquemático en Proteus</em></td>
  </tr>
</table>

> Proyecto de Proteus en [`proteus/etapa_B/`](proteus/etapa_B/).

### Montaje

<p align="center">
  <img src="imagenes/etapa_b/fig20_montaje_etapa_B.jpg" alt="Montaje Etapa B" width="450"><br>
  <em>Figura 20. Implementación de la Etapa B: TL084N con alimentación, op-amps no usados como seguidores, G = 21, puente y puntos de prueba TP1 y TP2.</em>
</p>

### Alimentación y offset (Tabla 3)

| Medición | Punto | Valor medido |
|---|:-:|:-:|
| Alimentación positiva | Pin 4 | 12.01 V |
| Alimentación negativa | Pin 11 | −12.00 V |
| **Offset (entrada a GND)** | TP2 | **−39.9 mV** |

<table>
  <tr>
    <td align="center"><img src="imagenes/etapa_b/fig21_alimentacion_pin4_12V.jpg" width="260"><br><sub>Alimentación positiva (pin 4)</sub></td>
    <td align="center"><img src="imagenes/etapa_b/fig22_offset_entrada_a_GND.jpg" width="260"><br><sub>Offset en TP2 con la entrada a GND</sub></td>
  </tr>
</table>

### Entrada y salida del amplificador (Tabla 4)

| Comando | TP1 medido (mV) | TP2 medido (V) |
|:-:|:-:|:-:|
| `f0` | 1.7 | −0.001 |
| `f21` | 10.9 | 0.191 |
| `f50` | 23.6 | 0.455 |
| `f100` | 45.3 | 0.909 |

<details>
<summary><b>📷 Ver fotografías de las mediciones de TP1 y TP2 (Etapa B)</b></summary>

<table>
  <tr>
    <th>Nivel</th><th>TP1</th><th>TP2</th>
  </tr>
  <tr>
    <td align="center"><b>f0</b></td>
    <td align="center"><img src="imagenes/etapa_b/fig24_TP1_f0.jpg" width="230"><br><sub>TP1 = 1.7 mV</sub></td>
    <td align="center"><img src="imagenes/etapa_b/fig25_TP2_f0.jpg" width="230"><br><sub>TP2 = −0.001 V</sub></td>
  </tr>
  <tr>
    <td align="center"><b>f21</b></td>
    <td align="center"><img src="imagenes/etapa_b/fig26_TP1_f21.jpg" width="230"><br><sub>TP1 = 10.9 mV</sub></td>
    <td align="center"><img src="imagenes/etapa_b/fig27_TP2_f21.jpg" width="230"><br><sub>TP2 = 0.191 V</sub></td>
  </tr>
  <tr>
    <td align="center"><b>f50</b></td>
    <td align="center"><img src="imagenes/etapa_b/fig28_TP1_f50.jpg" width="230"><br><sub>TP1 = 23.6 mV</sub></td>
    <td align="center"><img src="imagenes/etapa_b/fig29_TP2_f50.jpg" width="230"><br><sub>TP2 = 0.455 V</sub></td>
  </tr>
  <tr>
    <td align="center"><b>f100</b></td>
    <td align="center"><img src="imagenes/etapa_b/fig30_TP1_f100.jpg" width="230"><br><sub>TP1 = 45.3 mV</sub></td>
    <td align="center"><img src="imagenes/etapa_b/fig31_TP2_f100.jpg" width="230"><br><sub>TP2 = 0.909 V</sub></td>
  </tr>
</table>

</details>

### Captura del osciloscopio

Con `f50`, la punta del canal 1 en TP2, acoplamiento DC, 500 mV/div y 5 ms/div, se observa una **línea horizontal estable** a ≈ 0.455 V, sin oscilaciones, zumbido de red ni sobreimpulsos.

<table>
  <tr>
    <td align="center"><img src="imagenes/osciloscopio/fig32_montaje_osciloscopio_TP2.jpg" width="300"><br><em>Figura 32. Punta del canal 1 en TP2</em></td>
    <td align="center"><img src="imagenes/osciloscopio/fig33_captura_f50_linea_estable.jpg" width="420"><br><em>Figura 33. Visualización de f50: línea horizontal estable</em></td>
  </tr>
</table>

---

## 8. Resultados y análisis

### 8.1 Celda simulada (Tabla 5)

$$V_{1,esp} = \frac{N}{255}\cdot V_0 \quad (V_0 = 3.29\ \text{V}) \qquad\qquad \text{Desv.}(\%) = \frac{\text{medido}-\text{esperado}}{\text{esperado}}\times 100$$

| Comando | V₁ esperado (V) | Desviación V₁ (%) | TP1 esperado (mV) | Desviación TP1 (%) | TP1 / V₁ |
|:-:|:-:|:-:|:-:|:-:|:-:|
| `f0` | 0.000 | — | 0.0 | — | — |
| `f21` | 0.568 | −8.80 | 10.0 | +11.00 | 0.0214 |
| `f50` | 1.342 | −17.29 | 23.8 | 0.00 | 0.0214 |
| `f100` | 2.684 | −20.79 | 47.6 | −4.41 | 0.0214 |

<p align="center">
  <img src="imagenes/resultados/grafica_V1_esperado_vs_medido.png" width="440">
  <img src="imagenes/resultados/grafica_TP1_esperado_vs_medido.png" width="440">
</p>

**¿De dónde viene el error, del ESP32 o del divisor?**
Las desviaciones de V₁ son grandes y negativas (hasta −20.79 %), mientras que las de TP1 son mucho menores. El cociente TP1/V₁ se mantiene **constante (≈ 0.0214)** en los tres niveles. Esto indica que el **DAC del ESP32 es la principal fuente de error**, mientras que el divisor R₁–R₂ funciona de forma consistente y compensa parcialmente la desviación. Los tres niveles quedaron dentro del rango aceptable, aunque `f21` se ubicó en el límite superior.

**Relación del divisor.** Con los valores medidos:

$$k = \frac{R_2}{R_1+R_2} = \frac{216.2}{9730+216.2} = 0.02173 \quad\text{vs}\quad \frac{TP1}{V_1}\approx 0.0214$$

La diferencia (≈ 1.5 %) se explica por la tolerancia de las resistencias y la precisión del multímetro.

**Valor de TP1 en `f0`.** El DAC entregó V₁ = 0.088 V (TP1 = 1.9 mV) en lugar de 0 V, porque su etapa de salida no llega a 0 V (no es *rail-to-rail* hacia tierra). Con una sensibilidad de 0.476 mV/%O₂, 1.9 mV equivaldrían a una **lectura falsa de ≈ 4 % de O₂** con ausencia total de oxígeno: un riesgo clínico, pues podría retrasar la alarma de hipoxia.

### 8.2 Amplificador (Tabla 6)

| Parámetro | Valor |
|---|:-:|
| Ganancia de diseño, 1 + (Rf1 + Rf2)/Rg, con resistencias medidas | **21.02** |
| Ganancia real, (TP2<sub>f100</sub> − TP2<sub>f21</sub>)/(TP1<sub>f100</sub> − TP1<sub>f21</sub>) | **20.84** |
| Error de la ganancia real respecto a la de diseño | **−0.86 %** |
| Offset referido a la salida | **−39.9 mV** |
| Offset referido a la entrada (V_off / G_real) | **−1.91 mV** |

$$G_{real}=\frac{0.908-0.191}{0.0453-0.0109}=\frac{0.717\ \text{V}}{0.0344\ \text{V}}=20.84 \qquad V_{OS}=\frac{-39.9\ \text{mV}}{20.84}=-1.91\ \text{mV}$$

<p align="center">
  <img src="imagenes/resultados/fig_regresion_TP2_vs_TP1.png" alt="Regresión TP2 vs TP1" width="640"><br>
  <em>Característica de transferencia TP2 vs. TP1 con ajuste lineal (R² ≈ 1.000) — gráfica del informe.</em>
</p>

- **Linealidad:** la regresión lineal da una pendiente (≈ 20.8) prácticamente idéntica a la ganancia real, con R² ≈ 1.000.
- **Ordenada en el origen:** ≈ −35 mV, cercana al offset medido con el puente a GND (−39.9 mV).
- **Hoja de datos TL084:** V_OS típico 3 mV y máximo 10 mV a 25 °C. El valor medido (|−1.91 mV|) está **dentro de especificación**.
- **Estabilidad:** el osciloscopio muestra una traza plana y estable, lo que confirma la efectividad de los capacitores de desacoplo de 100 nF y la correcta terminación de los op-amps no usados.

### 8.3 Efecto sin calibrar

Con la escala de diseño de 10 mV por punto porcentual de O₂:

| Condición | FiO₂ real | TP2 medido | FiO₂ indicada | Error |
|---|:-:|:-:|:-:|:-:|
| Aire (`f21`) | 21 % | 0.191 V | **19.1 %** | −1.9 %O₂ |
| Oxígeno puro (`f100`) | 100 % | 0.908 V* | **90.8 %** | **−9.2 %O₂** |

*El informe usa 0.908 V en este cálculo (la Tabla 4 registra 0.909 V); la diferencia es de 0.1 %O₂.

<p align="center">
  <img src="imagenes/resultados/grafica_FiO2_sin_calibrar.png" alt="FiO2 indicada sin calibrar" width="560">
</p>

Este error **excede** el límite que establece la norma **IEC/ISO 80601-2-55** para monitores de gases respiratorios. Por eso los equipos comerciales realizan una **calibración de dos puntos** (aire y oxígeno puro), que corrige:

- **Punto bajo (aire, 21 %):** el offset o desplazamiento de cero del sistema.
- **Punto alto (O₂ puro, 100 %):** la pendiente real (ganancia), incluyendo la tolerancia de las resistencias y el desgaste del ánodo de plomo de la celda.

### 8.4 Pregunta de ampliación: Lima vs. Cusco

La celda responde a la **presión parcial** de O₂ (pO₂ = FiO₂ × P_atm), no al porcentaje. En Lima (≈ 760 mmHg) el aire da pO₂ ≈ 160 mmHg; en Cusco (≈ 510 mmHg), ≈ 105 mmHg (≈ 67 % de la de Lima). Un monitor calibrado en Lima y usado en Cusco sin recalibrar indicaría **≈ 14 % de O₂ en aire** (en lugar de 21 %) y ≈ 67 % en oxígeno puro, con riesgo de falsas alarmas de oxígeno bajo. La solución es **recalibrar en el lugar de uso**.

---

## 9. Conclusiones

- Se implementaron y verificaron las dos primeras etapas del canal de medición de O₂ (celda simulada y amplificador no inversor), que operan dentro de los parámetros funcionales esperados.
- **Etapa A:** TP1 cumplió los rangos en `f50` (23.8 mV) y `f100` (45.5 mV); `f21` (11.1 mV) quedó en el límite superior. El DAC del ESP32 introduce una atenuación de hasta **−20.79 %** en V₁ y un voltaje residual de **88 mV** en `f0` (1.9 mV en TP1), parcialmente compensados por el divisor.
- **Etapa B:** offset de salida de **−39.9 mV** (V_OS = **−1.91 mV**, dentro de la hoja de datos) y ganancia real de **20.84**, con un error de **−0.86 %** respecto al diseño (21.02).
- Sin calibración, el monitor indicaría **19.1 % O₂ en aire** y **90.8 % O₂ en oxígeno puro**, lo que confirma la **necesidad crítica de la calibración de dos puntos** antes de cualquier procedimiento anestésico.

---

## 10. Materiales y equipos

| Componente / equipo | Cantidad |
|---|:-:|
| ESP32 DevKit V1 (ESP32-WROOM-32, con DAC; no sirven las variantes S3 ni C3) | 1 |
| Cable USB de datos para el ESP32 | 1 |
| Laptop con Arduino IDE y soporte para ESP32 | 1 |
| TL084N | 1 |
| Resistencia 10 kΩ | 3 |
| Resistencia 1 kΩ | 1 |
| Resistencia 220 Ω | 1 |
| Capacitor cerámico 100 nF | 2 |
| Protoboard | 1 |
| Cables jumper macho-macho | ≈ 20 |
| Multímetro (Fluke 179), osciloscopio (ATTEN ADS1062CML) y fuente de banco dual ±12 V | 1 c/u |

---

## 11. Cómo reproducir el trabajo

### Firmware del ESP32

1. Instalar el soporte de ESP32 en el **Arduino IDE** y seleccionar la placa **ESP32 Dev Module**.
2. Abrir [`firmware/simulador_o2/simulador_o2.ino`](firmware/simulador_o2/simulador_o2.ino) y cargarlo.
3. Abrir el **Monitor Serie** a **115200 baudios** (nueva línea). Debe aparecer el mensaje de inicio con la FiO₂ fija en 21 %.
4. Enviar `f0`, `f21`, `f50` o `f100` y medir V₁ (GPIO25) y TP1 con el multímetro.

| Comando | Código DAC | V₁ teórico (V₀ = 3.3 V) | TP1 teórico (guía) |
|:-:|:-:|:-:|:-:|
| `f0` | 0 | 0.000 V | 0.0 mV |
| `f21` | 44 | 0.569 V | 10.0 mV |
| `f50` | 104 | 1.346 V | 23.8 mV |
| `f100` | 208 | 2.692 V | 47.6 mV |

### Análisis de datos

```bash
pip install -r analisis/requirements.txt
python analisis/analisis.py
```

El script lee los CSV de [`datos/`](datos/), recalcula las Tablas 5 y 6 y regenera las gráficas en `imagenes/resultados/`.

> **Nota:** pequeñas diferencias (≤ 0.2 %) respecto a las tablas del informe provienen del redondeo de los datos (por ejemplo, TP2 en f100 = 0.909 V en la tabla y 0.908 V en el cálculo del informe).

### Simulación en Proteus

Abrir `proteus/etapa_A/ROOT.DSN` o `proteus/etapa_B/ROOT.DSN` con **Proteus ISIS**.

---

## 12. Referencias

- Dorsch, J. A., y Dorsch, S. E. (2008). *Understanding anesthesia equipment* (5.ª ed.). Lippincott Williams & Wilkins.
- Texas Instruments. (s. f.). *TLx08x JFET-input operational amplifiers* [Hoja de datos, SLOS081].
- Espressif Systems. (2020). DAC. En *Arduino-ESP32 documentation*. https://docs.espressif.com/projects/arduino-esp32/en/latest/api/dac.html
- Horowitz, P., y Hill, W. (2015). *The art of electronics* (3.ª ed.). Cambridge University Press.
- Sedra, A. S., y Smith, K. C. (2015). *Microelectronic circuits* (7.ª ed.). Oxford University Press.
- Willett, M. (2014). Oxygen sensing for industrial safety — Evolution and new approaches. *Sensors, 14*(4), 6084–6103. https://doi.org/10.3390/s141406084
- Maxtec. (s. f.). *MAXO2 OM-25ME oxygen monitor* [Manual de usuario].
- Nuova GmbH. (s. f.). *Medical oxygen sensor M-15M* y *M-16* [Especificación de producto].
- Fluke Biomedical. (s. f.). *MAXO2+AE oxygen analyzer* [Hoja técnica].
- Hummingbird Sensing Technology. (s. f.). *Paracube Sprint paramagnetic oxygen sensor* [Nota de prensa]. Thomasnet News.
- Theard, A. M. (s. f.). *Monitoring* [Material de clase]. Stanford University, Neuroanesthesia.

---

## 13. Integrantes

| N.° | Apellidos y nombres | Código |
|:-:|---|:-:|
| 1 | Dávila Pucuhuayla, Jazmín Sarai | 23190369 |
| 2 | More Quispe, Gregory Martin | 23190125 |
| 3 | León Vasquez, Jimmy Fabricio | 23190378 |

**Docente:** Dra. María Elisa Armas Alvarado
**Curso:** Taller de Equipos Biomédicos II — Escuela Profesional de Ingeniería Biomédica, UNMSM
**Grupo / horario:** Sábado 12:00–2:00 pm · **Fecha de la práctica:** 07/11/2026

---

<div align="center">
<sub>Universidad Nacional Mayor de San Marcos · Escuela Profesional de Ingeniería Biomédica · 2026</sub>
</div>
