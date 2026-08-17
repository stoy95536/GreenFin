import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Shield, Leaf, Activity, FileText, AlertTriangle } from "lucide-react";
import { ApiError, getBankCaseDetail } from "../../api";
import type {
  BankCaseDetailResponse,
  DataHealthStatus,
  IndicatorType,
} from "../../types";

const STATUS_COLORS: Record<DataHealthStatus, string> = {
  GREEN: "bg-green-100 text-green-800",
  YELLOW: "bg-yellow-100 text-yellow-800",
  RED: "bg-red-100 text-red-800",
  GRAY: "bg-gray-100 text-gray-600",
};

const LEVEL_COLORS: Record<string, string> = {
  L1: "text-red-500",
  L2: "text-orange-500",
  L3: "text-yellow-600",
  L4: "text-green-500",
  L5: "text-greenfin-600",
};

const INDICATOR_LABELS: Record<IndicatorType, string> = {
  completeness: "資料完整度",
  credibility: "資料可信度",
  business_maturity: "經營成熟度",
  green_maturity: "綠色成熟度",
};

export default function BankCaseDetail() {
  const { farmerId } = useParams<{ farmerId: string }>();
  const [data, setData] = useState<BankCaseDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!farmerId) return;
    setLoading(true);
    getBankCaseDetail(farmerId)
      .then(setData)
      .catch((e) => {
        if (e instanceof ApiError && e.isForbidden) {
          setError("存取被拒絕：無有效授權或授權已過期／撤回");
        } else {
          setError(e instanceof Error ? e.message : "載入失敗");
        }
      })
      .finally(() => setLoading(false));
  }, [farmerId]);

  if (loading) return <p className="text-gray-400">載入中...</p>;

  if (error) {
    return (
      <div className="space-y-4">
        <Link to="/bank" className="text-blue-600 text-sm flex items-center gap-1">
          <ArrowLeft className="w-4 h-4" /> 返回案件列表
        </Link>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      </div>
    );
  }

  if (!data) return null;

  const farm = data.farms[0];

  return (
    <div className="space-y-6">
      <Link to="/bank" className="text-blue-600 text-sm flex items-center gap-1">
        <ArrowLeft className="w-4 h-4" /> 返回案件列表
      </Link>

      {/* Profile */}
      <section className="bg-white rounded-xl border p-6">
        <h1 className="text-xl font-bold mb-2">
          {data.profile?.real_name ?? farmerId}
        </h1>
        {farm && (
          <p className="text-sm text-gray-500">
            {farm.name} ｜ {farm.location}
          </p>
        )}
        <p className="text-xs text-gray-400 mt-1">farmer_id: {farmerId}</p>
      </section>

      {/* Experience */}
      <section className="bg-white rounded-xl border p-6">
        <h2 className="text-lg font-semibold flex items-center gap-2 mb-3">
          <Leaf className="w-5 h-5 text-greenfin-600" /> 經驗值
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div>
            <p className="text-sm text-gray-500">總經驗值</p>
            <p className="text-2xl font-bold text-greenfin-700">
              {data.experience.total_experience}
            </p>
            <p className={`text-sm font-medium ${LEVEL_COLORS[data.experience.level] ?? ""}`}>
              {data.experience.level} {data.experience.level_label}
            </p>
          </div>
          {Object.entries(data.experience.dimensions).map(([dim, value]) => (
            <div key={dim}>
              <p className="text-sm text-gray-500">{dim}</p>
              <p className="text-lg font-semibold">{value}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Indicators */}
      <section className="bg-white rounded-xl border p-6">
        <h2 className="text-lg font-semibold flex items-center gap-2 mb-3">
          <Activity className="w-5 h-5 text-blue-600" /> 四大分析指標
        </h2>
        {data.indicators.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {data.indicators.map((indicator) => (
              <div key={indicator.indicator_type} className="text-center border rounded-lg p-3">
                <p className="text-xs text-gray-500">
                  {INDICATOR_LABELS[indicator.indicator_type] ?? indicator.indicator_type}
                </p>
                <p className="text-xl font-bold">{indicator.score}</p>
                <p className={`text-sm ${LEVEL_COLORS[indicator.level] ?? ""}`}>
                  {indicator.level}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-400 text-sm">尚未計算</p>
        )}
      </section>

      {/* Data Health */}
      <section className="bg-white rounded-xl border p-6">
        <h2 className="text-lg font-semibold flex items-center gap-2 mb-3">
          <Shield className="w-5 h-5 text-purple-600" /> Data Health
        </h2>
        {data.data_health.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {data.data_health.map((item) => (
              <div
                key={item.domain}
                className={`rounded-lg p-3 ${STATUS_COLORS[item.status] ?? STATUS_COLORS.GRAY}`}
              >
                <p className="text-xs font-medium">{item.domain}</p>
                <p className="text-lg font-bold">{item.status}</p>
                {item.reasons[0] && (
                  <p className="text-xs mt-1 opacity-80">{item.reasons[0]}</p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-400 text-sm">尚未計算</p>
        )}
      </section>

      {/* Anomalies */}
      {data.anomalies.total > 0 && (
        <section className="bg-orange-50 rounded-xl border border-orange-200 p-6">
          <h2 className="text-lg font-semibold flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-orange-600" /> 異常
            <span className="text-xs bg-orange-200 text-orange-800 px-2 py-0.5 rounded-full">
              {data.anomalies.unresolved} 未解決
            </span>
          </h2>
          <div className="space-y-2">
            {data.anomalies.items.slice(0, 10).map((anomaly) => (
              <div key={anomaly.id} className="text-sm flex items-center gap-2">
                <span
                  className={`text-xs px-1.5 py-0.5 rounded ${
                    anomaly.severity === "CRITICAL"
                      ? "bg-red-200 text-red-800"
                      : "bg-yellow-200 text-yellow-800"
                  }`}
                >
                  {anomaly.severity}
                </span>
                <span className="text-gray-600">[{anomaly.anomaly_type}]</span>
                <span>{anomaly.description}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Evidence link */}
      <section className="bg-white rounded-xl border p-6">
        <h2 className="text-lg font-semibold flex items-center gap-2 mb-3">
          <FileText className="w-5 h-5 text-gray-600" /> 證據追溯
        </h2>
        <Link
          to={`/bank/case/${farmerId}/evidence`}
          className="text-blue-600 hover:underline text-sm"
        >
          查看完整證據鏈 →
        </Link>
      </section>

      <div className="bg-gray-100 rounded-lg p-4 text-xs text-gray-500">
        {data.disclaimer}
      </div>
    </div>
  );
}
