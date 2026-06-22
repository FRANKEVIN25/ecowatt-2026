import { useEffect, useRef, useState } from "react";

const BACKEND_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";
const API_BASE = `${BACKEND_BASE}/api`;
const WS_URL = `${BACKEND_BASE.replace(/^http/, "ws")}/ws/mediciones/`;

export type MeasurementPoint = {
  time: string;
  activePowerW: number;
  baselineW: number;
  energyKwh: number;
  costSoles: number;
};

export type ApplianceDetection = {
  appliance: string;
  applianceKey: string;
  confidence: number;
  activePowerW: number;
  predictedPowerW: number;
  voltage: number;
  powerFactor: number;
  appliances: AppliancePrediction[];
};

export type AppliancePrediction = {
  appliance: string;
  displayName: string;
  confidence: number;
  predictedPowerW: number;
  isOn: boolean;
};

export type MonthlyPrediction = {
  projectedKwh: number;
  projectedCostSoles: number;
  tariffSolesKwh: number;
};

type RawMedicionHistorial = {
  timestamp: string;
  potencia_activa: number;
  voltaje_rms: number;
  factor_potencia: number;
  kwh_acumulado: number;
};

type RawMedicionWs = {
  timestamp: string;
  P: number;
  V: number;
  fp: number;
  kWh: number;
};

function formatTime(isoTimestamp: string): string {
  const date = new Date(isoTimestamp);
  return date.toLocaleTimeString("es-PE", { hour: "2-digit", minute: "2-digit" });
}

export function useLiveData() {
  const [connected, setConnected] = useState(false);
  const [latestDetection, setLatestDetection] = useState<ApplianceDetection>({
    appliance: "Esperando datos...",
    applianceKey: "standby",
    confidence: 0,
    activePowerW: 0,
    predictedPowerW: 0,
    voltage: 0,
    powerFactor: 0,
    appliances: [],
  });
  const [monthlyPrediction, setMonthlyPrediction] = useState<MonthlyPrediction>({
    projectedKwh: 0,
    projectedCostSoles: 0,
    tariffSolesKwh: 0.6,
  });
  const [powerHistory, setPowerHistory] = useState<MeasurementPoint[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const tariffRef = useRef(0.6);
  const baselineSumRef = useRef(0);
  const baselineCountRef = useRef(0);

  function nextBaselineW(activePowerW: number): number {
    baselineSumRef.current += activePowerW;
    baselineCountRef.current += 1;
    return baselineSumRef.current / baselineCountRef.current;
  }

  // Carga inicial: historial, NILM y prediccion de costo desde la API REST
  useEffect(() => {
    async function loadInitial() {
      try {
        const histRes = await fetch(`${API_BASE}/mediciones/historial/?limite=60`);
        if (histRes.ok) {
          const data: RawMedicionHistorial[] = await histRes.json();
          const points = data
            .slice()
            .reverse()
            .map((m) => ({
              time: formatTime(m.timestamp),
              activePowerW: m.potencia_activa,
              baselineW: nextBaselineW(m.potencia_activa),
              energyKwh: m.kwh_acumulado,
              costSoles: Number((m.kwh_acumulado * tariffRef.current).toFixed(2)),
            }));
          setPowerHistory(points);

          const last = data[0];
          if (last) {
            setLatestDetection((prev) => ({
              ...prev,
              voltage: last.voltaje_rms,
              powerFactor: last.factor_potencia,
              activePowerW: last.potencia_activa,
            }));
          }
        }
      } catch (err) {
        console.warn("No se pudo cargar historial", err);
      }

      try {
        const nilmRes = await fetch(`${API_BASE}/nilm/latest/`);
        if (nilmRes.ok) {
          const data = await nilmRes.json();
          setLatestDetection((prev) => ({
            ...prev,
            appliance: data.detected_appliance,
            applianceKey: data.detected_appliance_key,
            confidence: data.confidence,
            predictedPowerW: data.predicted_power_w ?? prev.predictedPowerW,
            appliances: (data.appliance_predictions ?? []).map(
              (item: {
                appliance: string;
                display_name: string;
                confidence: number;
                predicted_power_w: number;
                is_on: boolean;
              }) => ({
                appliance: item.appliance,
                displayName: item.display_name,
                confidence: item.confidence,
                predictedPowerW: item.predicted_power_w,
                isOn: item.is_on,
              }),
            ),
          }));
        }
      } catch (err) {
        console.warn("No se pudo cargar NILM", err);
      }

      try {
        const costRes = await fetch(`${API_BASE}/cost/prediction/`);
        if (costRes.ok) {
          const data = await costRes.json();
          tariffRef.current = data.tariff_soles_kwh ?? 0.6;
          setMonthlyPrediction({
            projectedKwh: data.projected_cost_soles / (data.tariff_soles_kwh || 0.6),
            projectedCostSoles: data.projected_cost_soles,
            tariffSolesKwh: data.tariff_soles_kwh ?? 0.6,
          });
        }
      } catch (err) {
        console.warn("No se pudo cargar prediccion de costo", err);
      }
    }

    loadInitial();
  }, []);

  // WebSocket: actualizaciones en tiempo real
  useEffect(() => {
    function connect() {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        setTimeout(connect, 3000);
      };
      ws.onerror = () => ws.close();

      ws.onmessage = (event) => {
        try {
          const data: RawMedicionWs = JSON.parse(event.data);
          const point: MeasurementPoint = {
            time: formatTime(data.timestamp),
            activePowerW: data.P,
            baselineW: nextBaselineW(data.P),
            energyKwh: data.kWh,
            costSoles: Number((data.kWh * tariffRef.current).toFixed(2)),
          };

          setPowerHistory((prev) => {
            const next = [...prev, point];
            return next.length > 60 ? next.slice(next.length - 60) : next;
          });

          setLatestDetection((prev) => ({
            ...prev,
            activePowerW: data.P,
            voltage: data.V,
            powerFactor: data.fp,
          }));
        } catch (err) {
          console.warn("Mensaje WS invalido", err);
        }
      };
    }

    connect();
    return () => wsRef.current?.close();
  }, []);

  // Refrescar deteccion NILM periodicamente (cada 10s)
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/nilm/latest/`);
        if (res.ok) {
          const data = await res.json();
          setLatestDetection((prev) => ({
            ...prev,
            appliance: data.detected_appliance,
            applianceKey: data.detected_appliance_key,
            confidence: data.confidence,
            predictedPowerW: data.predicted_power_w ?? prev.predictedPowerW,
            appliances: (data.appliance_predictions ?? []).map(
              (item: {
                appliance: string;
                display_name: string;
                confidence: number;
                predicted_power_w: number;
                is_on: boolean;
              }) => ({
                appliance: item.appliance,
                displayName: item.display_name,
                confidence: item.confidence,
                predictedPowerW: item.predicted_power_w,
                isOn: item.is_on,
              }),
            ),
          }));
        }
      } catch {
        // silencioso, mantiene el ultimo valor conocido
      }
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  return { connected, latestDetection, monthlyPrediction, powerHistory };
}
