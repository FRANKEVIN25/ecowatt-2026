import {
  Activity,
  BadgeCheck,
  Bolt,
  Gauge,
  History,
  PlugZap,
  WalletCards,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { latestDetection, monthlyPrediction, powerHistory } from "./mock-data";

const confidencePercent = Math.round(latestDetection.confidence * 100);

function StatCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string;
  icon: typeof Bolt;
}) {
  return (
    <section className="rounded-lg border border-grid bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-slate-600">{label}</p>
        <Icon className="h-5 w-5 text-energy" aria-hidden="true" />
      </div>
      <p className="mt-3 text-2xl font-semibold text-ink">{value}</p>
    </section>
  );
}

export default function App() {
  return (
    <main className="min-h-screen bg-panel text-ink">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 border-b border-grid pb-5 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-energy">
              EcoWatt 2026
            </p>
            <h1 className="mt-1 text-3xl font-bold">Dashboard residencial</h1>
          </div>
          <div className="flex items-center gap-2 rounded-lg border border-grid bg-white px-3 py-2 text-sm font-medium shadow-sm">
            <Activity className="h-4 w-4 text-energy" aria-hidden="true" />
            Mock API activo
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-3">
          <StatCard
            label="Potencia actual"
            value={`${latestDetection.activePowerW.toFixed(1)} W`}
            icon={Gauge}
          />
          <StatCard
            label="Gasto proyectado"
            value={`S/ ${monthlyPrediction.projectedCostSoles.toFixed(2)}`}
            icon={WalletCards}
          />
          <StatCard
            label="Energia proyectada"
            value={`${monthlyPrediction.projectedKwh.toFixed(1)} kWh`}
            icon={Bolt}
          />
        </section>

        <section className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
          <article className="rounded-lg border border-grid bg-white p-5 shadow-sm">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-slate-600">
                  Artefacto detectado
                </p>
                <h2 className="mt-2 text-3xl font-bold">
                  {latestDetection.appliance}
                </h2>
              </div>
              <PlugZap className="h-8 w-8 text-energy" aria-hidden="true" />
            </div>

            <div className="mt-8">
              <div className="mb-2 flex items-center justify-between text-sm">
                <span className="font-medium text-slate-600">Confianza SGN</span>
                <span className="font-semibold">{confidencePercent}%</span>
              </div>
              <div className="h-3 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-energy"
                  style={{ width: `${confidencePercent}%` }}
                />
              </div>
            </div>

            <div className="mt-6 flex items-center gap-2 rounded-lg bg-emerald-50 px-3 py-3 text-sm font-medium text-emerald-800">
              <BadgeCheck className="h-4 w-4" aria-hidden="true" />
              Listo para reemplazar mock por `/api/nilm/latest/`
            </div>
          </article>

          <article className="rounded-lg border border-grid bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-slate-600">
                  Historial de potencia
                </p>
                <h2 className="text-xl font-semibold">Ultimos minutos</h2>
              </div>
              <History className="h-5 w-5 text-energy" aria-hidden="true" />
            </div>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={powerHistory} margin={{ left: 0, right: 10 }}>
                  <defs>
                    <linearGradient id="power" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="5%" stopColor="#0f9f6e" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#0f9f6e" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#d9e2dc" strokeDasharray="3 3" />
                  <XAxis dataKey="time" tickLine={false} />
                  <YAxis tickLine={false} width={48} />
                  <Tooltip />
                  <Area
                    dataKey="activePowerW"
                    name="W"
                    stroke="#0f9f6e"
                    fill="url(#power)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </article>
        </section>

        <section className="rounded-lg border border-grid bg-white p-5 shadow-sm">
          <div className="mb-4">
            <p className="text-sm font-medium text-slate-600">
              Prediccion de gasto
            </p>
            <h2 className="text-xl font-semibold">Costo acumulado simulado</h2>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={powerHistory} margin={{ left: 0, right: 10 }}>
                <CartesianGrid stroke="#d9e2dc" strokeDasharray="3 3" />
                <XAxis dataKey="time" tickLine={false} />
                <YAxis tickLine={false} width={48} />
                <Tooltip />
                <Line
                  dataKey="costSoles"
                  name="S/"
                  stroke="#e6a700"
                  strokeWidth={3}
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>
    </main>
  );
}
