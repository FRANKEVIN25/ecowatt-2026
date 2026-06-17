export type MeasurementPoint = {
  time: string;
  activePowerW: number;
  energyKwh: number;
  costSoles: number;
};

export type ApplianceDetection = {
  appliance: string;
  confidence: number;
  activePowerW: number;
};

export const latestDetection: ApplianceDetection = {
  appliance: "Foco 100W",
  confidence: 0.91,
  activePowerW: 101.2,
};

export const monthlyPrediction = {
  projectedKwh: 114.2,
  projectedCostSoles: 68.52,
  tariffSolesKwh: 0.6,
};

export const powerHistory: MeasurementPoint[] = [
  { time: "20:00", activePowerW: 8, energyKwh: 0.01, costSoles: 0.01 },
  { time: "20:05", activePowerW: 25, energyKwh: 0.03, costSoles: 0.02 },
  { time: "20:10", activePowerW: 101, energyKwh: 0.12, costSoles: 0.07 },
  { time: "20:15", activePowerW: 153, energyKwh: 0.26, costSoles: 0.16 },
  { time: "20:20", activePowerW: 1195, energyKwh: 0.78, costSoles: 0.47 },
  { time: "20:25", activePowerW: 98, energyKwh: 0.86, costSoles: 0.52 },
  { time: "20:30", activePowerW: 148, energyKwh: 0.99, costSoles: 0.59 },
  { time: "20:35", activePowerW: 24, energyKwh: 1.02, costSoles: 0.61 },
];
