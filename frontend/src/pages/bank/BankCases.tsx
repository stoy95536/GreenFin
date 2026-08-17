import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Building2, User, Clock } from "lucide-react";
import { getBankCases } from "../../api";
import type { BankCaseSummary } from "../../types";

export default function BankCases() {
  const [cases, setCases] = useState<BankCaseSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getBankCases()
      .then((data) => setCases(data.cases))
      .catch((e) => setError(e instanceof Error ? e.message : "載入失敗"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Building2 className="w-6 h-6 text-blue-600" />
        <h1 className="text-2xl font-bold text-gray-800">銀行端 — 授權案件</h1>
        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
          DEMO
        </span>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
        僅顯示小農已授權的案件。此為授信補充資訊，不代表核貸建議。
      </div>

      {loading && <p className="text-gray-400">載入中...</p>}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {!loading && !error && cases.length === 0 && (
        <p className="text-gray-400">目前無授權案件</p>
      )}

      <div className="space-y-3">
        {cases.map((item) => (
          <Link
            key={item.authorization_id}
            to={`/bank/case/${item.farmer_id}`}
            className="block bg-white rounded-xl border border-gray-200 p-5 hover:border-blue-300 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <User className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="font-semibold">{item.farmer_name}</p>
                  <p className="text-sm text-gray-500">{item.purpose}</p>
                </div>
              </div>
              <div className="text-right text-sm">
                <div className="flex items-center gap-1 text-gray-400 justify-end">
                  <Clock className="w-3 h-3" />
                  <span>到期: {item.expire_at.split("T")[0]}</span>
                </div>
                <div className="mt-1 flex gap-1 flex-wrap justify-end">
                  {item.data_scope.map((scope) => (
                    <span key={scope} className="text-xs bg-gray-100 px-1.5 py-0.5 rounded">
                      {scope}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
