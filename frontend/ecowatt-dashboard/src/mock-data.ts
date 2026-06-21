export type MeasurementPoint = {
  time: string;
  activePowerW: number;
  baselineW: number;
  costSoles: number;
};

export type ApplianceUsage = {
  name: string;
  powerW: number;
  share: number;
  state: "Activo" | "Standby" | "Apagado";
  confidence: number;
  color: string;
};

export const latestDetection = {
  appliance: "Hervidor",
  confidence: 0.86,
  activePowerW: 1842,
  voltage: 221.4,
  powerFactor: 0.97,
};

export const monthlyPrediction = {
  projectedKwh: 114.2,
  projectedCostSoles: 68.52,
  optimizedCostSoles: 57.61,
  tariffSolesKwh: 0.6,
  savingPercent: 15.9,
};

export const modelMetrics = {
  realF1: 0.347,
  simulatedF1: 0.818,
  simulatedAccuracy: 0.845,
  balancedAccuracy: 0.82,
  leakage: 0,
};

export const powerHistory: MeasurementPoint[] = [
  { time: "18:00", activePowerW: 96, baselineW: 145, costSoles: 0.08 },
  { time: "18:15", activePowerW: 134, baselineW: 152, costSoles: 0.11 },
  { time: "18:30", activePowerW: 162, baselineW: 158, costSoles: 0.15 },
  { time: "18:45", activePowerW: 118, baselineW: 165, costSoles: 0.18 },
  { time: "19:00", activePowerW: 235, baselineW: 178, costSoles: 0.24 },
  { time: "19:15", activePowerW: 418, baselineW: 186, costSoles: 0.31 },
  { time: "19:30", activePowerW: 676, baselineW: 194, costSoles: 0.42 },
  { time: "19:45", activePowerW: 282, baselineW: 202, costSoles: 0.47 },
  { time: "20:00", activePowerW: 194, baselineW: 210, costSoles: 0.51 },
  { time: "20:15", activePowerW: 1842, baselineW: 218, costSoles: 0.72 },
  { time: "20:30", activePowerW: 148, baselineW: 224, costSoles: 0.76 },
  { time: "20:45", activePowerW: 126, baselineW: 220, costSoles: 0.79 },
  { time: "21:00", activePowerW: 312, baselineW: 212, costSoles: 0.85 },
  { time: "21:15", activePowerW: 228, baselineW: 205, costSoles: 0.89 },
  { time: "21:30", activePowerW: 176, baselineW: 194, costSoles: 0.93 },
  { time: "21:45", activePowerW: 112, baselineW: 184, costSoles: 0.96 },
];

export const applianceUsage: ApplianceUsage[] = [
  {
    name: "Refrigeradora",
    powerW: 138,
    share: 34,
    state: "Activo",
    confidence: 0.82,
    color: "#20d6a2",
  },
  {
    name: "Lavadora",
    powerW: 0,
    share: 22,
    state: "Apagado",
    confidence: 0.74,
    color: "#62a8ff",
  },
  {
    name: "Hervidor",
    powerW: 1842,
    share: 18,
    state: "Activo",
    confidence: 0.86,
    color: "#f9c74f",
  },
  {
    name: "Microondas",
    powerW: 3,
    share: 15,
    state: "Standby",
    confidence: 0.69,
    color: "#b388ff",
  },
  {
    name: "Iluminación",
    powerW: 61,
    share: 11,
    state: "Activo",
    confidence: 0.91,
    color: "#ff7f6e",
  },
];

export const recommendations = [
  {
    title: "Reduce consumo fantasma",
    detail: "Desconecta microondas y entretenimiento durante la madrugada.",
    saving: "S/ 3.40 / mes",
    level: "Alta",
  },
  {
    title: "Optimiza el hervidor",
    detail: "Calienta solo el volumen necesario; detectamos picos repetidos.",
    saving: "S/ 4.10 / mes",
    level: "Alta",
  },
  {
    title: "Mueve la lavadora",
    detail: "Programa ciclos fuera del bloque de mayor demanda del hogar.",
    saving: "S/ 3.41 / mes",
    level: "Media",
  },
];
