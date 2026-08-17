import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FileText, Leaf, Activity, Shield, AlertTriangle } from "lucide-react";
import {
  getExperienceSummary,
  getDataHealth,
  getIndicators,
  getReviewQueue,
  calculateIndicators,
  calculateDataHealth,
  recalculateExperience,
} from "../api";
import { useFarmer } from "../context/FarmerContext";

export default function Dashboard() {
  const { currentFarmer } = useFarmer();
  const FARMER_ID = currentFarmer.id;
  const [experience, setExperience] = useState<any>(null);
  const [indicators, setIndicators] = useState<any>(null);
  const [dataHealth, setDataHealth] = useState<any>(null);
  const [reviewQueue, setReviewQueue] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [exp, ind, dh, rq] = await Promise.all([
        getExperienceSummary(FARMER_ID),
        getIndicators(FARMER_ID),
        getDataHealth(FARMER_ID),
        getReviewQueue(FARMER_ID),
      ]);
      setExperience(exp);
      setIndicators(ind);
      setDataHealth(dh);
      setReviewQueue(rq);
      setError(null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRecalculate = async () => {
    setLoading(true);
    try {
      await recalculateExperience(FARMER_ID);
      await calculateIndicators(FARMER_ID);
      await calculateDataHealth(FARMER_ID);
      await loadData();
    } catch (e: any) {
      setError(e.message);
    }
    setLoading(false);
  };

  useEffect(() => { loadData(); }, [currentFarmer.id]);

  if (loading) return <p className="text-gray-400">載入中...</p>;
  if (error) return <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>;

  const levelColors: Record<string, string> = {
    L0: "text-gray-400", L1: "text-red-500", L2: "text-orange-500",
    L3: "text-yellow-600", L4: "text-green-500", L5: "text-greenfin-600",
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">小農 Dashboard</h1>
        <button
          onClick={handleRecalculate}
          className="px-4 py-2 bg-greenfin-600 text-white rounded-lg text-sm hover:bg-greenfin-700 transition-colors"
        >
          重新計算
        </button>
      </div>

      {/* Experience Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Leaf className="w-5 h-5 text-greenfin-600" />
          <h2 className="text-lg font-semibold">經驗值</h2>
        </div>
        {experience && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">總經驗值</p>
              <p className="text-2xl font-bold text-greenfin-700">{experience.total_experience}</p>
              <p className={`text-sm font-medium ${levelColors[experience.level] || ""}`}>
                {experience.level} {experience.level_label}
              </p>
            </div>
            {experience.dimensions && Object.entries(experience.dimensions).map(([dim, val]) => (
              <div key={dim}>
                <p className="text-sm text-gray-500">{dim}</p>
                <p className="text-lg font-semibold">{val as number}</p>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                  <div
                    className="bg-greenfin-500 h-2 rounded-full"
                    style={{ width: `${Math.min(100, ((val as number) / 250) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Indicators */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Activity className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold">四大分析指標</h2>
          <span className="text-xs text-gray-400">(獨立呈現，不合併)</span>
        </div>
        {indicators?.indicators && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { key: "completeness", label: "資料完整度" },
              { key: "credibility", label: "資料可信度" },
              { key: "business_maturity", label: "經營成熟度" },
              { key: "green_maturity", label: "綠色成熟度" },
            ].map(({ key, label }) => {
              const ind = indicators.indicators[key];
              if (!ind) return <div key={key} className="text-gray-400 text-sm">{label}: 未計算</div>;
              return (
                <div key={key} className="text-center">
                  <p className="text-sm text-gray-500 mb-1">{label}</p>
                  <p className="text-2xl font-bold">{ind.score}</p>
                  <p className={`text-sm font-medium ${levelColors[ind.level] || ""}`}>{ind.level}</p>
                </div>
              );
            })}
          </div>
        )}
        {!indicators?.indicators || indicators.indicator_count === 0 ? (
          <p className="text-sm text-gray-400">尚未計算，請點擊「重新計算」</p>
        ) : null}
      </div>

      {/* Data Health */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Shield className="w-5 h-5 text-purple-600" />
          <h2 className="text-lg font-semibold">Data Health</h2>
        </div>
        {dataHealth?.domains && Object.keys(dataHealth.domains).length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries(dataHealth.domains).map(([domain, info]: [string, any]) => {
              const statusColors: Record<string, string> = {
                GREEN: "bg-green-100 text-green-800 border-green-200",
                YELLOW: "bg-yellow-100 text-yellow-800 border-yellow-200",
                RED: "bg-red-100 text-red-800 border-red-200",
                GRAY: "bg-gray-100 text-gray-600 border-gray-200",
              };
              return (
                <div key={domain} className={`rounded-lg border p-3 ${statusColors[info.status] || statusColors.GRAY}`}>
                  <p className="text-xs font-medium">{domain}</p>
                  <p className="text-lg font-bold">{info.status}</p>
                  {info.reasons?.[0] && <p className="text-xs mt-1 opacity-80">{info.reasons[0]}</p>}
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-gray-400">尚未計算，請點擊「重新計算」</p>
        )}
      </div>

      {/* Review Queue */}
      {reviewQueue && reviewQueue.count > 0 && (
        <div className="bg-orange-50 rounded-xl border border-orange-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <AlertTriangle className="w-5 h-5 text-orange-600" />
            <h2 className="text-lg font-semibold text-orange-800">待覆核項目</h2>
            <span className="bg-orange-200 text-orange-800 text-xs px-2 py-0.5 rounded-full">
              {reviewQueue.count}
            </span>
          </div>
          <ul className="space-y-2">
            {reviewQueue.items?.slice(0, 5).map((item: any) => (
              <li key={item.id} className="text-sm text-orange-700">
                [{item.anomaly_type}] {item.description}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Quick Links */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Link to="/documents" className="bg-white rounded-lg border border-gray-200 p-4 text-center hover:border-greenfin-300 transition-colors">
          <FileText className="w-6 h-6 mx-auto text-gray-500 mb-2" />
          <span className="text-sm">上傳文件</span>
        </Link>
        <Link to="/experience" className="bg-white rounded-lg border border-gray-200 p-4 text-center hover:border-greenfin-300 transition-colors">
          <Leaf className="w-6 h-6 mx-auto text-gray-500 mb-2" />
          <span className="text-sm">經驗值詳情</span>
        </Link>
        <Link to="/indicators" className="bg-white rounded-lg border border-gray-200 p-4 text-center hover:border-greenfin-300 transition-colors">
          <Activity className="w-6 h-6 mx-auto text-gray-500 mb-2" />
          <span className="text-sm">指標分析</span>
        </Link>
        <Link to="/data-health" className="bg-white rounded-lg border border-gray-200 p-4 text-center hover:border-greenfin-300 transition-colors">
          <Shield className="w-6 h-6 mx-auto text-gray-500 mb-2" />
          <span className="text-sm">資料健康</span>
        </Link>
      </div>
    </div>
  );
}
