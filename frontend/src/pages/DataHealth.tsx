import { useEffect, useState } from "react";
import { Shield } from "lucide-react";
import { getDataHealth, calculateDataHealth } from "../api";
import { useFarmer } from "../context/FarmerContext";

const DOMAIN_LABELS: Record<string, string> = {
  IDENTITY: "身分與資格",
  LAND_CROP: "土地與作物",
  TRANSACTION: "經營與交易",
  INPUT_EQUIPMENT: "投入與設備",
  GREEN_ACTION: "綠色行動",
  CERTIFICATION: "認證與治理",
  LOAN_PURPOSE: "申貸用途",
};

export default function DataHealth() {
  const { currentFarmer } = useFarmer();
  const FARMER_ID = currentFarmer.id;
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);

  const load = async () => {
    try {
      const d = await getDataHealth(FARMER_ID);
      setData(d);
    } catch { /* ignore */ }
    setLoading(false);
  };

  const handleCalculate = async () => {
    setCalculating(true);
    try {
      await calculateDataHealth(FARMER_ID);
      await load();
    } catch { /* ignore */ }
    setCalculating(false);
  };

  useEffect(() => { setLoading(true); load(); }, [currentFarmer.id]);

  if (loading) return <p className="text-gray-400">載入中...</p>;

  const domains = data?.domains || {};
  const summary = data?.summary || {};
  const hasDomains = Object.keys(domains).length > 0;

  const statusConfig: Record<string, { bg: string; border: string; text: string; label: string; description: string }> = {
    GREEN: { bg: "bg-green-50", border: "border-green-200", text: "text-green-800", label: "GREEN", description: "目前可供參考" },
    YELLOW: { bg: "bg-yellow-50", border: "border-yellow-200", text: "text-yellow-800", label: "YELLOW", description: "可參考但需補強" },
    RED: { bg: "bg-red-50", border: "border-red-200", text: "text-red-800", label: "RED", description: "目前不宜使用" },
    GRAY: { bg: "bg-gray-50", border: "border-gray-200", text: "text-gray-600", label: "GRAY", description: "未提供或不適用" },
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <Shield className="w-6 h-6 text-purple-600" /> Data Health
        </h1>
        <button
          onClick={handleCalculate}
          disabled={calculating}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 disabled:opacity-50"
        >
          {calculating ? "計算中..." : "重新計算"}
        </button>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
        RED 不代表拒貸；GRAY 不代表表現差。Data Health 是資料品質的即時診斷。
      </div>

      {/* Summary */}
      {hasDomains && (
        <div className="grid grid-cols-4 gap-3">
          {Object.entries(summary).map(([status, count]) => {
            const config = statusConfig[status] || statusConfig.GRAY;
            return (
              <div key={status} className={`${config.bg} ${config.border} border rounded-lg p-3 text-center`}>
                <p className={`text-2xl font-bold ${config.text}`}>{count as number}</p>
                <p className={`text-xs ${config.text}`}>{config.label}</p>
              </div>
            );
          })}
        </div>
      )}

      {!hasDomains ? (
        <p className="text-gray-400">尚未計算，請點擊「重新計算」</p>
      ) : (
        <div className="space-y-4">
          {Object.entries(domains).map(([domain, info]: [string, any]) => {
            const config = statusConfig[info.status] || statusConfig.GRAY;
            return (
              <div key={domain} className={`${config.bg} ${config.border} border rounded-xl p-5`}>
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h3 className={`font-semibold ${config.text}`}>
                      {DOMAIN_LABELS[domain] || domain}
                    </h3>
                    <p className="text-xs text-gray-500">{domain}</p>
                  </div>
                  <span className={`text-lg font-bold ${config.text}`}>
                    {info.status}
                  </span>
                </div>

                {/* Reasons */}
                {info.reasons?.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs font-medium text-gray-500 mb-1">原因:</p>
                    <ul className="space-y-0.5">
                      {info.reasons.map((r: string, i: number) => (
                        <li key={i} className={`text-sm ${config.text}`}>• {r}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Actions */}
                {info.actions?.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs font-medium text-gray-500 mb-1">建議動作:</p>
                    <ul className="space-y-0.5">
                      {info.actions.map((a: string, i: number) => (
                        <li key={i} className="text-sm text-gray-700">→ {a}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
