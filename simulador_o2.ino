/*
 * simulador_o2.ino
 * Laboratorio N.º 3 — Taller de Equipos Biomédicos II (UNMSM)
 * Celda galvánica de O2 simulada con el DAC de 8 bits del ESP32 (GPIO25).
 *
 * Placa: ESP32 Dev Module (ESP32-WROOM-32 con DAC; no sirven S3 ni C3)
 * Monitor Serie: 115200 baudios, "Nueva línea" (\n)
 *
 * Comandos por Monitor Serie:  f0, f21, f50, f100   (también fN, 0 <= N <= 100)
 *
 *   V1  = (N_DAC / 255) · V0            (V0 ≈ 3.3 V)
 *   TP1 = V1 · R2 / (R1 + R2)           (divisor resistivo)
 *
 * Códigos del DAC asignados por la guía (V0 = 3.30 V, sensibilidad 0.476 mV/%O2):
 *   f0 -> 0 | f21 -> 44 | f50 -> 104 | f100 -> 208
 *
 * NOTA: reconstruido a partir de la Guía de Laboratorio N.º 3. Si tu grupo usó
 * el archivo original de la guía, reemplaza este archivo por el tuyo.
 */

const uint8_t PIN_DAC = 25;           // DAC canal 1 (GPIO25)
const float   V0_NOMINAL = 3.30f;     // tensión de alimentación nominal (V)
const float   SENS_mV_POR_PCT = 0.476f; // sensibilidad de la celda simulada
const float   K_DIVISOR = 180.0f / (10000.0f + 180.0f); // k de la guía (R2 = 180 Ω)

int fio2 = 21;                        // FiO2 inicial: aire ambiente

// Convierte un % de O2 en el código de 8 bits del DAC
uint8_t codigoDAC(int pct) {
  switch (pct) {                      // valores fijados por la guía
    case 0:   return 0;
    case 21:  return 44;
    case 50:  return 104;
    case 100: return 208;
  }
  float tp1_V = pct * SENS_mV_POR_PCT / 1000.0f;   // TP1 deseado
  float v1    = tp1_V / K_DIVISOR;                 // V1 necesario
  int   n     = (int)roundf(v1 / V0_NOMINAL * 255.0f);
  return (uint8_t)constrain(n, 0, 255);
}

void aplicarFiO2(int pct) {
  pct = constrain(pct, 0, 100);
  fio2 = pct;
  uint8_t n = codigoDAC(pct);
  dacWrite(PIN_DAC, n);
  float v1_teo  = (n / 255.0f) * V0_NOMINAL;
  float tp1_teo = v1_teo * K_DIVISOR * 1000.0f;
  Serial.printf("FiO2 = %3d %% | codigo DAC = %3u | V1 teorico = %.3f V | TP1 teorico = %.1f mV\n",
                pct, n, v1_teo, tp1_teo);
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println();
  Serial.println("=== Simulador de celda de O2 (ESP32 + DAC GPIO25) ===");
  Serial.println("Comandos: f0, f21, f50, f100  (o fN con N entre 0 y 100)");
  Serial.println("Inicio con FiO2 fija en 21 % (aire ambiente).");
  aplicarFiO2(fio2);
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toLowerCase();
    if (cmd.length() >= 2 && cmd.charAt(0) == 'f') {
      int n = cmd.substring(1).toInt();
      bool numeroValido = (n > 0) || cmd.substring(1) == "0";
      if (numeroValido && n >= 0 && n <= 100) {
        aplicarFiO2(n);
        return;
      }
    }
    if (cmd.length() > 0) Serial.println("Comando no valido. Use f0, f21, f50 o f100.");
  }
}
