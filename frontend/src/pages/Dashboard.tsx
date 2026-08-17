import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FileText, Leaf, Activity, Shield, AlertTriangle } from "lucide-react";
import {
  getExperienceSummary,
  getDataHealth,
  getIndicators,
  getReviewQueue,
  recalculateAll,
} from "../api";
import type {
  DataHealthResponse,
  DataHealthStatus,
  ExperienceSummary,
  IndicatorsResponse,
  IndicatorType,
  ReviewQueueResponse,
} from "../types";
import { useFarmer } from "../context/FarmerContext";

const LEVEL_COLORS: Record<string, string> = {
  L0: "text-gray-400",
  L1: "text-red-500",
  L2: "text-orange-500",
  L3: "text-yellow-600",
  L4: "text-green-500",
  L5: "text-greenfin-600",
};

const STATUS_COLORS: Record<DataHealthStatus, string> = {
  GREEN: "bg-green-100 text-green-800 border-green-200",
  YELLOW: "bg-yellow-100 text-yellow-800 border-yellow-200",
  RED: "bg-red-100 text-red-800 border-red-200",
  GRAY: "bg-gray-100 text-gray-600 border-gray-200",
};

const INDICATOR_LABELS: { key: IndicatorType; label: string }[] = [
  { key: "completeness", label: "資料完整度" },
  { key: "credibility", label: "資料可信度" },
  { key: "business_maturity", label: "經營成熟度" },
  { key: "green_maturity", label: "綠色成熟度" },
];

export default function Dashboard() {
  const { currentFarmer } = useFarmer();
  const farmerId = currentFarmer.id;

  const [experience, setExperience] = useState<ExperienceSummary | null>(null);
  const [indicators, setIndicators] = useState<IndicatorsResponse | null>(null);
  const [dataHealth, setDataHealth] = useState<DataHealthResponse | null>(null);
  const [reviewQueue, setReviewQueue] = useState<ReviewQueueResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [recalculating, setRecalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [exp, ind, dh, rq] = await Promise.all([
        getExperienceSummary(farmerId),
        getIndicators(farmerId),
        getDataHealth(farmerId),
        getReviewQueue(farmerId),
      ]);
      setExperience(exp);
      setIndicators(ind);
      setDataHealth(dh);
      setReviewQueue(rq);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "載入失敗");
    } finally {
      setLoading(false);
    }
  }, [farmerId]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  /** One backend call owns the ordering, so partial recalculation can't happen. */
  const handleRecalculate = async () => {
    setRecalculating(true);
    setError(null);
    try {
      await recalculateAll(farmerId);
      await loadData();
    } catch (e) {
      setError(e instanceof Error ? e.message : "重新計算失敗");
    } finally {
      setRecalculating(false);
    }
  };

  if (loading) return <p className="text-gray-400">載入中...</p>;

  const hasIndicators = (indicators?.indicator_count ?? 0) > 0;
  const healthDomains = Object.entries(dataHealth?.domains ?? {});

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">小農 Dashboard</h1>
        <button
          onClick={handleRecalculate}
          disabled={recalculating}
          className="px-4 py-2 bg-greenfin-600 text-white rounded-lg text-sm hover:bg-greenfin-700 disabled:opacity-50 transition-colors"
        >
          {recalculating ? "計算中..." : "重新計算"}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Experience */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Leaf className="w-5 h-5 text-greenfin-600" />
          <h2 className="text-lg font-semibold">經驗值</h2>
        </div>
        {experience && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div>
              <p className="text-sm text-gray-500">總經驗值</p>
              <p className="text-2xl font-bold text-greenfin-700">
                {experience.total_experience}
              </p>
              <p className={`text-sm font-medium ${LEVEL_COLORS[experience.level] ?? ""}`}>
                {experience.level} {experience.level_label}
              </p>
            </div>
            {Object.entries(experience.dimensions).map(([dim, value]) => (
              <div key={dim}>
                <p className="text-sm text-gray-500">{dim}</p>
                <p className="text-lg font-semibold">{value}</p>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                  <div
                    className="bg-greenfin-500 h-2 rounded-full"
                    style={{
                      width: `${Math.min(
                        100,
                        (value / experience.annual_limit_per_dimension) * 100
                      )}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Indicators */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Activity className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold">四大分析指標</h2>
          <span className="text-xs text-gray-400">(獨立呈現，不合併)</span>
        </div>
        {hasIndicators ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {INDICATOR_LABELS.map(({ key, label }) => {
              const indicator = indicators?.indicators[key];
              if (!indicator) {
                return (
                  <div key={key} className="text-sm text-gray-400">
                    {label}: 未計算
                  </div>
                );
              }
              return (
                <div key={key} className="text-center">
                  <p className="text-sm text-gray-500 mb-1">{label}</p>
                  <p className="text-2xl font-bold">{indicator.score}</p>
                  <p className={`text-sm font-medium ${LEVEL_COLORS[indicator.level] ?? ""}`}>
                    {indicator.level}
                  </p>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-gray-400">尚未計算，請點擊「重新計算」</p>
        )}
      </section>

      {/* Data Health */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Shield className="w-5 h-5 text-purple-600" />
          <h2 className="text-lg font-semibold">Data Health</h2>
        </div>
        {healthDomains.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {healthDomains.map(([domain, info]) => (
              <div
                key={domain}
                className={`rounded-lg border p-3 ${
                  STATUS_COLORS[info!.status] ?? STATUS_COLORS.GRAY
                }`}
              >
                <p className="text-xs font-medium">{domain}</p>
                <p className="text-lg font-bold">{info!.status}</p>
                {info!.reasons[0] && (
                  <p className="text-xs mt-1 opacity-80">{info!.reasons[0]}</p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">尚未計算，請點擊「重新計算」</p>
        )}
      </section>

      {/* Review queue */}
      {reviewQueue && reviewQueue.count > 0 && (
        <section className="bg-orange-50 rounded-xl border border-orange-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <AlertTriangle className="w-5 h-5 text-orange-600" />
            <h2 className="text-lg font-semibold text-orange-800">待覆核項目</h2>
            <span className="bg-orange-200 text-orange-800 text-xs px-2 py-0.5 rounded-full">
              {reviewQueue.count}
            </span>
          </div>
          <ul className="space-y-2">
            {reviewQueue.items.slice(0, 5).map((item) => (
              <li key={item.id} className="text-sm text-orange-700">
                [{item.anomaly_type}] {item.description}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Quick links */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { to: "/documents", icon: FileText, label: "上傳文件" },
          { to: "/experience", icon: Leaf, label: "經驗值詳情" },
          { to: "/indicators", icon: Activity, label: "指標分析" },
          { to: "/data-health", icon: Shield, label: "資料健康" },
        ].map(({ to, icon: Icon, label }) => (
          <Link
            key={to}
            to={to}
            className="bg-white rounded-lg border border-gray-200 p-4 text-center hover:border-greenfin-300 transition-colors"
          >
            <Icon className="w-6 h-6 mx-auto text-gray-500 mb-2" />
            <span className="text-sm">{label}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
