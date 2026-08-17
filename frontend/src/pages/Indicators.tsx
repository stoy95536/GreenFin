import { useEffect, useState } from "react";
import { Activity } from "lucide-react";
import { getIndicators, calculateIndicators } from "../api";
import { useFarmer } from "../context/FarmerContext";

const INDICATOR_META: Record<string, { label: string; description: string }> = {
  completeness: { label: "資料完整度", description: "衡量資料領域的覆蓋程度" },
  credibility: { label: "資料可信度", description: "衡量資料的來源可靠性" },
  business_maturity: { label: "經營成熟度", description: "衡量經營紀錄的豐富程度" },
  green_maturity: { label: "綠色成熟度", description: "衡量綠色行動的深度與廣度" },
};

export default function Indicators() {
  const { currentFarmer } = useFarmer();
  const FARMER_ID = currentFarmer.id;
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);

  const load = async () => {
    try {
      const d = await getIndicators(FARMER_ID);
      setData(d);
    } catch { /* ignore */ }
    setLoading(false);
  };

  const handleCalculate = async () => {
    setCalculating(true);
    try {
      await calculateIndicators(FARMER_ID);
      await load();
    } catch { /* ignore */ }
    setCalculating(false);
  };

  useEffect(() => { setLoading(true); load(); }, [currentFarmer.id]);

  if (loading) return <p className="text-gray-400">載入中...</p>;

  const indicators = data?.indicators || {};
  const hasData = Object.keys(indicators).length > 0;

  const levelColors: Record<string, string> = {
    L1: "from-red-400 to-red-500",
    L2: "from-orange-400 to-orange-500",
    L3: "from-yellow-400 to-yellow-500",
    L4: "from-green-400 to-green-500",
    L5: "from-greenfin-400 to-greenfin-600",
  };

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
        四項指標須獨立呈現，不得直接平均成信用總分。
      </div>

      {!hasData ? (
        <p className="text-gray-400">尚未計算，請點擊「重新計算」</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Object.entries(INDICATOR_META).map(([key, meta]) => {
            const ind = indicators[key];
            if (!ind) return null;
            const gradientClass = levelColors[ind.level] || "from-gray-300 to-gray-400";
            return (
              <div key={key} className="bg-white rounded-xl shadow-sm border p-6">
                <h3 className="text-lg font-semibold mb-1">{meta.label}</h3>
                <p className="text-xs text-gray-400 mb-4">{meta.description}</p>

                {/* Score bar */}
                <div className="relative mb-3">
                  <div className="w-full bg-gray-200 rounded-full h-4">
                    <div
                      className={`bg-gradient-to-r ${gradientClass} h-4 rounded-full transition-all`}
                      style={{ width: `${ind.score}%` }}
                    />
                  </div>
                  <div className="flex justify-between mt-1">
                    <span className="text-xs text-gray-400">0</span>
                    <span className="text-sm font-bold">{ind.score}</span>
                    <span className="text-xs text-gray-400">100</span>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-600">等級: {ind.level}</span>
                  <span className="text-xs text-gray-400">
                    {ind.calculated_at?.split("T")[0]}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
