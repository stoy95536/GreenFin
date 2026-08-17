import { useEffect, useState } from "react";
import { Leaf } from "lucide-react";
import { getExperienceSummary, getExperienceHistory } from "../api";
import { useFarmer } from "../context/FarmerContext";

export default function Experience() {
  const { currentFarmer } = useFarmer();
  const FARMER_ID = currentFarmer.id;
  const [summary, setSummary] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getExperienceSummary(FARMER_ID),
      getExperienceHistory(FARMER_ID),
    ]).then(([s, h]) => {
      setSummary(s);
      setHistory(h.transactions || []);
    }).finally(() => setLoading(false));
  }, [currentFarmer.id]);

  if (loading) return <p className="text-gray-400">載入中...</p>;

  const levelLabels: Record<string, string> = {
    L0: "尚未建立", L1: "萌芽", L2: "成長", L3: "穩健", L4: "領航", L5: "示範",
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
        <Leaf className="w-6 h-6 text-greenfin-600" /> 經驗值
      </h1>

      {summary && (
        <>
          {/* Summary */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="col-span-2 md:col-span-1">
                <p className="text-sm text-gray-500">總經驗值</p>
                <p className="text-3xl font-bold text-greenfin-700">{summary.total_experience}</p>
                <p className="text-sm text-greenfin-600 font-medium">
                  {summary.level} — {levelLabels[summary.level] || ""}
                </p>
                <p className="text-xs text-gray-400 mt-1">上限: {summary.total_limit}</p>
              </div>
              {summary.dimensions && Object.entries(summary.dimensions).map(([dim, val]) => (
                <div key={dim}>
                  <p className="text-sm text-gray-500">{dim}</p>
                  <p className="text-xl font-bold">{val as number}</p>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                    <div
                      className="bg-greenfin-500 h-2 rounded-full transition-all"
                      style={{ width: `${Math.min(100, ((val as number) / summary.annual_limit_per_dimension) * 100)}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-400 mt-1">/ {summary.annual_limit_per_dimension}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Formula explanation */}
          <div className="bg-greenfin-50 rounded-xl border border-greenfin-200 p-4">
            <p className="text-sm text-greenfin-800 font-medium">計算公式</p>
            <p className="text-sm text-greenfin-700 mt-1">
              有效經驗值 = 行為基礎值 × 來源認列比例
            </p>
            <p className="text-xs text-greenfin-600 mt-1">
              規則版本: {summary.rule_version}
            </p>
          </div>

          {/* History */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h2 className="text-lg font-semibold mb-4">計算紀錄 ({history.length})</h2>
            {history.length === 0 ? (
              <p className="text-gray-400 text-sm">尚無計算紀錄</p>
            ) : (
              <div className="space-y-3">
                {history.map((txn: any) => (
                  <div key={txn.id} className="border border-gray-100 rounded-lg p-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-sm font-medium">{txn.dimension}</p>
                        <p className="text-xs text-gray-500 mt-1">{txn.calculation_trace}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-greenfin-700">+{txn.effective_value}</p>
                        <p className="text-xs text-gray-400">base: {txn.base_value} × {txn.source_recognition_ratio}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
