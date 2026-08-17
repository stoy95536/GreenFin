import { useCallback, useEffect, useState } from "react";
import { Activity } from "lucide-react";
import { getIndicators, calculateIndicators } from "../api";
import type { IndicatorsResponse, IndicatorType } from "../types";
import { useFarmer } from "../context/FarmerContext";

const INDICATOR_META: { key: IndicatorType; label: string; description: string }[] = [
  { key: "completeness", label: "資料完整度", description: "衡量資料領域的覆蓋程度" },
  { key: "credibility", label: "資料可信度", description: "衡量資料的來源可靠性" },
  { key: "business_maturity", label: "經營成熟度", description: "衡量經營紀錄的豐富程度" },
  { key: "green_maturity", label: "綠色成熟度", description: "衡量綠色行動的深度與廣度" },
];

const LEVEL_GRADIENTS: Record<string, string> = {
  L1: "from-red-400 to-red-500",
  L2: "from-orange-400 to-orange-500",
  L3: "from-yellow-400 to-yellow-500",
  L4: "from-green-400 to-green-500",
  L5: "from-greenfin-400 to-greenfin-600",
};

export default function Indicators() {
  const { currentFarmer } = useFarmer();
  const farmerId = currentFarmer.id;

  const [data, setData] = useState<IndicatorsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setData(await getIndicators(farmerId));
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
      await calculateIndicators(farmerId);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "計算失敗");
    } finally {
      setCalculating(false);
    }
  };

  if (loading) return <p className="text-gray-400">載入中...</p>;

  const hasData = (data?.indicator_count ?? 0) > 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <Activity className="w-6 h-6 text-blue-600" /> 四大分析指標
        </h1>
        <button
          onClick={handleCalculate}
          disabled={calculating}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          {calculating ? "計算中..." : "重新計算"}
        </button>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-sm text-yellow-800">
        {data?.note ?? "四項指標須獨立呈現，不得直接平均成信用總分。"}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {!hasData ? (
        <p className="text-gray-400">尚未計算，請點擊「重新計算」</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {INDICATOR_META.map(({ key, label, description }) => {
            const indicator = data?.indicators[key];
            if (!indicator) return null;
            const gradient = LEVEL_GRADIENTS[indicator.level] ?? "from-gray-300 to-gray-400";
            return (
              <div key={key} className="bg-white rounded-xl shadow-sm border p-6">
                <h3 className="text-lg font-semibold mb-1">{label}</h3>
                <p className="text-xs text-gray-400 mb-4">{description}</p>

                <div className="mb-3">
                  <div className="w-full bg-gray-200 rounded-full h-4">
                    <div
                      className={`bg-gradient-to-r ${gradient} h-4 rounded-full transition-all`}
                      style={{ width: `${indicator.score}%` }}
                    />
                  </div>
                  <div className="flex justify-between mt-1">
                    <span className="text-xs text-gray-400">0</span>
                    <span className="text-sm font-bold">{indicator.score}</span>
                    <span className="text-xs text-gray-400">100</span>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-600">
                    等級: {indicator.level}
                  </span>
                  <span className="text-xs text-gray-400">
                    {indicator.calculated_at?.split("T")[0]}
                  </span>
                </div>

                {indicator.calculation_trace && (
                  <p className="text-xs text-gray-400 mt-3 border-t pt-2">
                    {indicator.calculation_trace}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
