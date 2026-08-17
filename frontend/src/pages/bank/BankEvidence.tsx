import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, FileText, CheckCircle, XCircle } from "lucide-react";
import { ApiError, getBankCaseEvidence } from "../../api";
import type { BankEvidenceResponse } from "../../types";

export default function BankEvidence() {
  const { farmerId } = useParams<{ farmerId: string }>();
  const [data, setData] = useState<BankEvidenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!farmerId) return;
    setLoading(true);
    getBankCaseEvidence(farmerId)
      .then(setData)
      .catch((e) => {
        if (e instanceof ApiError && e.isForbidden) {
          setError("存取被拒絕：無有效授權");
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
        <Link
          to={`/bank/case/${farmerId}`}
          className="text-blue-600 text-sm flex items-center gap-1"
        >
          <ArrowLeft className="w-4 h-4" /> 返回案件詳情
        </Link>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      <Link
        to={`/bank/case/${farmerId}`}
        className="text-blue-600 text-sm flex items-center gap-1"
      >
        <ArrowLeft className="w-4 h-4" /> 返回案件詳情
      </Link>

      <h1 className="text-xl font-bold flex items-center gap-2">
        <FileText className="w-6 h-6 text-gray-600" />
        證據追溯 — {farmerId}
      </h1>

      <p className="text-sm text-gray-500">
        文件數: {data.document_count} ｜ 紀錄數: {data.record_count}
      </p>

      <div className="bg-greenfin-50 border border-greenfin-200 rounded-lg p-3 text-sm text-greenfin-800">
        追溯路徑: Result → StandardizedRecord → DocumentFields → Original Document
      </div>

      {data.evidence.map((item) => (
        <div key={item.document.id} className="bg-white rounded-xl border p-5 space-y-4">
          {/* Document */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-500" />
              <span className="font-medium">{item.document.filename}</span>
              <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">
                {item.document.domain}
              </span>
              <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">
                {item.document.source_level}
              </span>
            </div>
            <span className="text-xs text-gray-400">{item.document.status}</span>
          </div>

          {/* Fields */}
          {item.fields.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-1">
                擷取欄位 ({item.fields.length})
              </p>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {item.fields.map((field) => (
                  <div key={field.id} className="text-xs border border-gray-100 rounded p-2">
                    <span className="text-gray-500">{field.field_name}:</span>{" "}
                    <span className="font-medium">
                      {field.normalized_value || field.raw_value}
                    </span>
                    {field.confidence !== null && (
                      <span
                        className={`ml-1 ${
                          field.confidence < 0.7 ? "text-orange-500" : "text-green-500"
                        }`}
                      >
                        ({(field.confidence * 100).toFixed(0)}%)
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Verifications */}
          {item.verifications.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-1">核驗結果</p>
              {item.verifications.map((verification) => (
                <div key={verification.id} className="flex items-center gap-2 text-xs">
                  {verification.source_level === "V0" ? (
                    <XCircle className="w-3 h-3 text-red-500" />
                  ) : (
                    <CheckCircle className="w-3 h-3 text-green-500" />
                  )}
                  <span className="font-medium">{verification.source_level}</span>
                  <span className="text-gray-500">{verification.reason}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
