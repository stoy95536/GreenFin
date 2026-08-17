import { useCallback, useEffect, useState } from "react";
import { Shield } from "lucide-react";
import { getDataHealth, calculateDataHealth } from "../api";
import type { DataDomainKey, DataHealthResponse, DataHealthStatus } from "../types";
import { useFarmer } from "../context/FarmerContext";

const DOMAIN_LABELS: Record<DataDomainKey, string> = {
  IDENTITY: "身分與資格",
  LAND_CROP: "土地與作物",
  TRANSACTION: "經營與交易",
  INPUT_EQUIPMENT: "投入與設備",
  GREEN_ACTION: "綠色行動",
  CERTIFICATION: "認證與治理",
  LOAN_PURPOSE: "申貸用途",
};

const STATUS_CONFIG: Record<
  DataHealthStatus,
  { bg: string; border: string; text: string; description: string }
> = {
  GREEN: {
    bg: "bg-green-50",
    border: "border-green-200",
    text: "text-green-800",
    description: "目前可供參考",
  },
  YELLOW: {
    bg: "bg-yellow-50",
    border: "border-yellow-200",
    text: "text-yellow-800",
    description: "可參考但需補強",
  },
  RED: {
    bg: "bg-red-50",
    border: "border-red-200",
    text: "text-red-800",
    description: "目前不宜使用",
  },
  GRAY: {
    bg: "bg-gray-50",
    border: "border-gray-200",
    text: "text-gray-600",
    description: "未提供或不適用",
  },
};

export default function DataHealth() {
  const { currentFarmer } = useFarmer();
  const farmerId = currentFarmer.id;

  const [data, setData] = useState<DataHealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setData(await getDataHealth(farmerId));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "載入失敗");
    } finally {
      setLoading(false);
    }
  }, [farmerId]);

  useEffect(() => {
    setLoading(true);
    void load();
  }, [load]);

  const handleCalculate = async () => {
    setCalculating(true);
    try {
      await calculateDataHealth(farmerId);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "計算失敗");
    } finally {
      setCalculating(false);
    }
  };

  if (loading) return <p className="text-gray-400">載入中...</p>;

  const domains = Object.entries(data?.domains ?? {});
  const summary = Object.entries(data?.summary ?? {});

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
        {data?.note ?? "RED 不代表拒貸；GRAY 不代表表現差。"}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Summary counts */}
      {domains.length > 0 && (
        <div className="grid grid-cols-4 gap-3">
          {summary.map(([status, count]) => {
            const config = STATUS_CONFIG[status as DataHealthStatus] ?? STATUS_CONFIG.GRAY;
            return (
              <div
                key={status}
                className={`${config.bg} ${config.border} border rounded-lg p-3 text-center`}
              >
                <p className={`text-2xl font-bold ${config.text}`}>{count}</p>
                <p className={`text-xs ${config.text}`}>{status}</p>
              </div>
            );
          })}
        </div>
      )}

      {domains.length === 0 ? (
        <p className="text-gray-400">尚未計算，請點擊「重新計算」</p>
      ) : (
        <div className="space-y-4">
          {domains.map(([domain, info]) => {
            const config = STATUS_CONFIG[info!.status] ?? STATUS_CONFIG.GRAY;
            return (
              <div
                key={domain}
                className={`${config.bg} ${config.border} border rounded-xl p-5`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h3 className={`font-semibold ${config.text}`}>
                      {DOMAIN_LABELS[domain as DataDomainKey] ?? domain}
                    </h3>
                    <p className="text-xs text-gray-500">{domain}</p>
                  </div>
                  <div className="text-right">
                    <span className={`text-lg font-bold ${config.text}`}>
                      {info!.status}
                    </span>
                    <p className="text-xs text-gray-500">{config.description}</p>
                  </div>
                </div>

                {info!.reasons.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs font-medium text-gray-500 mb-1">原因:</p>
                    <ul className="space-y-0.5">
                      {info!.reasons.map((reason, i) => (
                        <li key={i} className={`text-sm ${config.text}`}>
                          • {reason}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {info!.actions.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs font-medium text-gray-500 mb-1">建議動作:</p>
                    <ul className="space-y-0.5">
                      {info!.actions.map((action, i) => (
                        <li key={i} className="text-sm text-gray-700">
                          → {action}
                        </li>
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
