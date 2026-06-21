import {
  Activity,
  BarChart3,
  Bell,
  Bolt,
  Bot,
  BrainCircuit,
  ChevronRight,
  CircleDollarSign,
  Cpu,
  Gauge,
  Home,
  Leaf,
  Menu,
  PlugZap,
  Radar,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingDown,
  WalletCards,
  Wifi,
  X,
  Zap,
} from "lucide-react";
import { useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  applianceUsage,
  latestDetection,
  modelMetrics,
  monthlyPrediction,
  powerHistory,
  recommendations,
} from "./mock-data";

const navItems = [
  { label: "Resumen", icon: Home },
  { label: "Consumo", icon: BarChart3 },
  { label: "NILM inteligente", icon: BrainCircuit },
  { label: "Predicción", icon: Target },
];

function MetricCard({
  label,
  value,
  detail,
  icon: Icon,
  tone,
}: {
  label: string;
  value: string;
  detail: string;
  icon: typeof Bolt;
  tone: "green" | "blue" | "amber" | "violet";
}) {
  return (
    <article className={`metric-card metric-card-${tone}`}>
      <div className="metric-icon">
        <Icon size={20} aria-hidden="true" />
      </div>
      <div className="min-w-0">
        <p className="eyebrow">{label}</p>
        <p className="mt-2 truncate text-2xl font-semibold tracking-tight text-white">
          {value}
        </p>
        <p className="mt-1 text-xs text-slate-400">{detail}</p>
      </div>
    </article>
  );
}

function Pill({
  children,
  tone = "green",
}: {
  children: React.ReactNode;
  tone?: "green" | "amber" | "slate";
}) {
  return <span className={`status-pill status-pill-${tone}`}>{children}</span>;
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-white/10 bg-slate-950/95 px-3 py-2 shadow-2xl backdrop-blur">
      <p className="mb-1 text-xs font-semibold text-slate-300">{label}</p>
      {payload.map((item) => (
        <p key={item.name} className="text-xs" style={{ color: item.color }}>
          {item.name}: {Number(item.value).toFixed(1)}
        </p>
      ))}
    </div>
  );
}

export default function App() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [period, setPeriod] = useState<"Hoy" | "Semana" | "Mes">("Hoy");
  const [assistantOpen, setAssistantOpen] = useState(true);

  const totalAppliancePower = useMemo(
    () => applianceUsage.reduce((total, item) => total + item.powerW, 0),
    [],
  );
  const saving = (
    monthlyPrediction.projectedCostSoles - monthlyPrediction.optimizedCostSoles
  ).toFixed(2);

  return (
    <main className="app-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
        <div className="flex items-center justify-between px-5 py-6">
          <div className="flex items-center gap-3">
            <div className="logo-mark">
              <Zap size={20} fill="currentColor" />
            </div>
            <div>
              <p className="text-lg font-bold tracking-tight text-white">EcoWatt</p>
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-300">
                Energy intelligence
              </p>
            </div>
          </div>
          <button
            className="icon-button lg:hidden"
            onClick={() => setMenuOpen(false)}
            aria-label="Cerrar menú"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="mt-4 space-y-1 px-3">
          {navItems.map(({ label, icon: Icon }, index) => (
            <button
              key={label}
              className={`nav-item ${index === 0 ? "nav-item-active" : ""}`}
            >
              <Icon size={18} />
              <span>{label}</span>
              {index === 0 && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-300" />}
            </button>
          ))}
        </nav>

        <div className="mx-4 mt-auto mb-5 rounded-2xl border border-emerald-300/15 bg-emerald-300/[0.06] p-4">
          <div className="flex items-center gap-2 text-emerald-200">
            <ShieldCheck size={17} />
            <p className="text-xs font-semibold">Modo demo verificable</p>
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-slate-400">
            Simulación separada de REFIT. Cero sesiones compartidas entre
            entrenamiento y prueba.
          </p>
          <div className="mt-3 flex items-center gap-2 text-[10px] text-slate-500">
            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
            Pipeline disponible
          </div>
        </div>
      </aside>

      {menuOpen && (
        <button
          aria-label="Cerrar navegación"
          className="fixed inset-0 z-30 bg-slate-950/70 backdrop-blur-sm lg:hidden"
          onClick={() => setMenuOpen(false)}
        />
      )}

      <section className="content-shell">
        <header className="topbar">
          <div className="flex items-center gap-3">
            <button
              className="icon-button lg:hidden"
              onClick={() => setMenuOpen(true)}
              aria-label="Abrir menú"
            >
              <Menu size={20} />
            </button>
            <div>
              <p className="eyebrow">Centro de control residencial</p>
              <h1 className="text-xl font-semibold text-white sm:text-2xl">
                Buenos días, Jesús
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Pill>
              <Wifi size={12} />
              Simulación activa
            </Pill>
            <button className="icon-button" aria-label="Notificaciones">
              <Bell size={18} />
              <span className="notification-dot" />
            </button>
            <div className="avatar">JM</div>
          </div>
        </header>

        <div className="dashboard-scroll">
          <section className="hero-panel">
            <div className="relative z-10 max-w-2xl">
              <Pill tone="slate">
                <Sparkles size={12} />
                EcoWatt AI · análisis en tiempo real
              </Pill>
              <h2 className="mt-5 max-w-xl text-3xl font-semibold leading-tight text-white sm:text-4xl">
                Tu hogar puede gastar{" "}
                <span className="text-gradient">S/ {saving} menos</span> este mes.
              </h2>
              <p className="mt-3 max-w-xl text-sm leading-relaxed text-slate-300">
                Detectamos tres oportunidades de ahorro basadas en patrones de
                consumo, horarios y cargas en standby.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <button
                  className="primary-button"
                  onClick={() => setAssistantOpen((value) => !value)}
                >
                  <Bot size={17} />
                  {assistantOpen ? "Ocultar análisis" : "Ver análisis inteligente"}
                </button>
                <button className="secondary-button">
                  Explorar recomendaciones
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
            <div className="hero-orbit" aria-hidden="true">
              <div className="hero-core">
                <Leaf size={34} />
              </div>
              <span className="orbit-dot orbit-dot-one" />
              <span className="orbit-dot orbit-dot-two" />
              <span className="orbit-dot orbit-dot-three" />
            </div>
          </section>

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Potencia instantánea"
              value={`${latestDetection.activePowerW.toLocaleString("es-PE")} W`}
              detail="Pico detectado hace 12 s"
              icon={Gauge}
              tone="green"
            />
            <MetricCard
              label="Proyección mensual"
              value={`S/ ${monthlyPrediction.projectedCostSoles.toFixed(2)}`}
              detail={`${monthlyPrediction.projectedKwh} kWh estimados`}
              icon={WalletCards}
              tone="blue"
            />
            <MetricCard
              label="Ahorro potencial"
              value={`S/ ${saving}`}
              detail={`${monthlyPrediction.savingPercent}% optimizable`}
              icon={TrendingDown}
              tone="amber"
            />
            <MetricCard
              label="Calidad de energía"
              value={`${latestDetection.powerFactor.toFixed(2)} FP`}
              detail={`${latestDetection.voltage.toFixed(1)} V estables`}
              icon={Activity}
              tone="violet"
            />
          </section>

          <section className="grid gap-4 xl:grid-cols-[1.55fr_0.85fr]">
            <article className="glass-panel min-w-0">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Demanda energética</p>
                  <h3 className="panel-title">Consumo vs. línea base</h3>
                </div>
                <div className="segmented-control">
                  {(["Hoy", "Semana", "Mes"] as const).map((item) => (
                    <button
                      key={item}
                      onClick={() => setPeriod(item)}
                      className={period === item ? "segment-active" : ""}
                    >
                      {item}
                    </button>
                  ))}
                </div>
              </div>
              <div className="h-80 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={powerHistory} margin={{ top: 12, right: 4, left: -18, bottom: 0 }}>
                    <defs>
                      <linearGradient id="powerArea" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#20d6a2" stopOpacity={0.42} />
                        <stop offset="100%" stopColor="#20d6a2" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="#21354a" strokeDasharray="4 5" vertical={false} />
                    <XAxis dataKey="time" stroke="#73869a" tickLine={false} axisLine={false} fontSize={11} />
                    <YAxis stroke="#73869a" tickLine={false} axisLine={false} fontSize={11} />
                    <Tooltip content={<CustomTooltip />} />
                    <Area
                      type="monotone"
                      dataKey="activePowerW"
                      name="Consumo W"
                      stroke="#20d6a2"
                      strokeWidth={2.5}
                      fill="url(#powerArea)"
                    />
                    <Line
                      type="monotone"
                      dataKey="baselineW"
                      name="Base W"
                      stroke="#62a8ff"
                      strokeDasharray="5 5"
                      strokeWidth={1.5}
                      dot={false}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="glass-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">NILM · SGN</p>
                  <h3 className="panel-title">Detección actual</h3>
                </div>
                <div className="radar-icon">
                  <Radar size={21} />
                </div>
              </div>
              <div className="detection-orb">
                <div>
                  <PlugZap size={30} />
                  <span>{Math.round(latestDetection.confidence * 100)}%</span>
                </div>
              </div>
              <div className="mt-5 text-center">
                <p className="text-2xl font-semibold text-white">
                  {latestDetection.appliance}
                </p>
                <p className="mt-1 text-xs text-slate-400">
                  {latestDetection.activePowerW.toLocaleString("es-PE")} W · alta
                  confianza
                </p>
              </div>
              <div className="mt-5 grid grid-cols-2 gap-2">
                <div className="mini-stat">
                  <span>Voltaje</span>
                  <strong>{latestDetection.voltage} V</strong>
                </div>
                <div className="mini-stat">
                  <span>Factor P.</span>
                  <strong>{latestDetection.powerFactor}</strong>
                </div>
              </div>
            </article>
          </section>

          <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
            <article className="glass-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Mapa de cargas</p>
                  <h3 className="panel-title">Artefactos del hogar</h3>
                </div>
                <Pill tone="slate">{totalAppliancePower.toFixed(0)} W ahora</Pill>
              </div>
              <div className="space-y-3">
                {applianceUsage.map((item) => (
                  <div key={item.name} className="appliance-row">
                    <span
                      className="appliance-dot"
                      style={{ backgroundColor: item.color, boxShadow: `0 0 18px ${item.color}` }}
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-4">
                        <p className="truncate text-sm font-medium text-slate-200">{item.name}</p>
                        <p className="text-sm font-semibold text-white">{item.powerW} W</p>
                      </div>
                      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className="h-full rounded-full"
                          style={{ width: `${item.share}%`, backgroundColor: item.color }}
                        />
                      </div>
                    </div>
                    <span className={`device-state device-${item.state.toLowerCase()}`}>{item.state}</span>
                  </div>
                ))}
              </div>
            </article>

            <article className="glass-panel min-w-0">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Proyección financiera</p>
                  <h3 className="panel-title">Costo acumulado</h3>
                </div>
                <CircleDollarSign className="text-amber-300" size={21} />
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={powerHistory} margin={{ left: -28, right: 0 }}>
                    <CartesianGrid stroke="#21354a" strokeDasharray="4 5" vertical={false} />
                    <XAxis dataKey="time" stroke="#73869a" tickLine={false} axisLine={false} fontSize={10} />
                    <YAxis stroke="#73869a" tickLine={false} axisLine={false} fontSize={10} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="costSoles" name="Costo S/" fill="#f9c74f" radius={[5, 5, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="cost-summary">
                <div>
                  <span>Proyección actual</span>
                  <strong>S/ {monthlyPrediction.projectedCostSoles}</strong>
                </div>
                <ChevronRight size={18} className="text-slate-600" />
                <div>
                  <span>Con optimización</span>
                  <strong className="text-emerald-300">S/ {monthlyPrediction.optimizedCostSoles}</strong>
                </div>
              </div>
            </article>
          </section>

          {assistantOpen && (
            <section className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
              <article className="glass-panel">
                <div className="panel-heading">
                  <div className="flex items-center gap-3">
                    <div className="ai-avatar"><Bot size={20} /></div>
                    <div>
                      <p className="eyebrow">EcoWatt AI</p>
                      <h3 className="panel-title">Acciones recomendadas</h3>
                    </div>
                  </div>
                  <Pill><Cpu size={12} /> 3 hallazgos</Pill>
                </div>
                <div className="space-y-3">
                  {recommendations.map((item, index) => (
                    <button key={item.title} className="recommendation-row">
                      <span className="recommendation-number">0{index + 1}</span>
                      <span className="min-w-0 flex-1 text-left">
                        <strong>{item.title}</strong>
                        <small>{item.detail}</small>
                      </span>
                      <span className="saving-tag">{item.saving}</span>
                      <ChevronRight size={16} className="text-slate-600" />
                    </button>
                  ))}
                </div>
              </article>

              <article className="glass-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Transparencia del modelo</p>
                    <h3 className="panel-title">Métricas separadas</h3>
                  </div>
                  <ShieldCheck size={21} className="text-cyan-300" />
                </div>
                <div className="space-y-3">
                  <div className="model-metric">
                    <span>Benchmark sintético F1</span>
                    <strong>{modelMetrics.simulatedF1.toFixed(3)}</strong>
                    <div style={{ width: `${modelMetrics.simulatedF1 * 100}%` }} />
                  </div>
                  <div className="model-metric">
                    <span>Accuracy sintético</span>
                    <strong>{modelMetrics.simulatedAccuracy.toFixed(3)}</strong>
                    <div style={{ width: `${modelMetrics.simulatedAccuracy * 100}%` }} />
                  </div>
                  <div className="model-metric model-metric-muted">
                    <span>F1 REFIT real</span>
                    <strong>{modelMetrics.realF1.toFixed(3)}</strong>
                    <div style={{ width: `${modelMetrics.realF1 * 100}%` }} />
                  </div>
                </div>
                <div className="mt-4 rounded-xl border border-cyan-300/10 bg-cyan-300/[0.05] p-3 text-[11px] leading-relaxed text-slate-400">
                  El benchmark de demo no reemplaza la validación REFIT. Las
                  sesiones de prueba tienen <strong className="text-cyan-200">0 solapamiento</strong>.
                </div>
              </article>
            </section>
          )}

          <footer className="flex flex-col gap-2 border-t border-white/5 py-5 text-xs text-slate-600 sm:flex-row sm:items-center sm:justify-between">
            <span>EcoWatt 2026 · Inteligencia energética residencial</span>
            <span>Tarifa: S/ {monthlyPrediction.tariffSolesKwh.toFixed(2)} / kWh · Datos demo identificados</span>
          </footer>
        </div>
      </section>
    </main>
  );
}
