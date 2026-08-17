import { useEffect, useState } from "react";
import { Leaf } from "lucide-react";
import { getExperienceSummary, getExperienceHistory } from "../api";
import type { ExperienceSummary, ExperienceTransaction } from "../types";
import { useFarmer } from "../context/FarmerContext";

export default function Experience() {
  const { currentFarmer } = useFarmer();
  const farmerId = currentFarmer.id;

  const [summary, setSummary] = useState<ExperienceSummary | null>(null);
  const [history, setHistory] = useState<ExperienceTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([getExperienceSummary(farmerId), getExperienceHistory(farmerId)])
      .then(([summaryData, historyData]) => {
        setSummary(summaryData);
        setHistory(historyData.transactions);
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "載入失敗"))
      .finally(() => setLoading(false));
  }, [farmerId]);

  if (loading) return <p className="text-gray-400">載入中...</p>;

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
        {error}
      </div>
    );
  }

  if (!summary) return null;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
        <Leaf className="w-6 h-6 text-greenfin-600" /> 經驗值
      </h1>

      {/* Summary */}
      <section className="bg-white rounded-xl shadow-sm border p-6">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="col-span-2 md:col-span-1">
            <p className="text-sm text-gray-500">總經驗值</p>
            <p className="text-3xl font-bold text-greenfin-700">
              {summary.total_experience}
            </p>
            <p className="text-sm text-greenfin-600 font-medium">
              {summary.level} — {summary.level_label}
            </p>
            <p className="text-xs text-gray-400 mt-1">上限: {summary.total_limit}</p>
          </div>
          {Object.entries(summary.dimensions).map(([dim, value]) => (
            <div key={dim}>
              <p className="text-sm text-gray-500">{dim}</p>
              <p className="text-xl font-bold">{value}</p>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div
                  className="bg-greenfin-500 h-2 rounded-full transition-all"
                  style={{
                    width: `${Math.min(
                      100,
                      (value / summary.annual_limit_per_dimension) * 100
                    )}%`,
                  }}
                />
              </div>
              <p className="text-xs text-gray-400 mt-1">
                / {summary.annual_limit_per_dimension}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Formula */}
      <section className="bg-greenfin-50 rounded-xl border border-greenfin-200 p-4">
        <p className="text-sm text-greenfin-800 font-medium">計算公式</p>
        <p className="text-sm text-greenfin-700 mt-1">
          有效經驗值 = 行為基礎值 × 來源認列比例
        </p>
        <p className="text-xs text-greenfin-600 mt-1">
          規則版本: {summary.rule_version}
        </p>
      </section>

      {/* History */}
      <section className="bg-white rounded-xl shadow-sm border p-6">
        <h2 className="text-lg font-semibold mb-4">計算紀錄 ({history.length})</h2>
        {history.length === 0 ? (
          <p className="text-gray-400 text-sm">尚無計算紀錄</p>
        ) : (
          <div className="space-y-3">
            {history.map((txn) => (
              <div key={txn.id} className="border border-gray-100 rounded-lg p-3">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-sm font-medium">{txn.dimension}</p>
                    <p className="text-xs text-gray-500 mt-1">{txn.calculation_trace}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-greenfin-700">
                      +{txn.effective_value}
                    </p>
                    <p className="text-xs text-gray-400">
                      base: {txn.base_value} × {txn.source_recognition_ratio}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
