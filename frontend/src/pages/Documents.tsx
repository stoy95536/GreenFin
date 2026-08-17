import { useCallback, useEffect, useState } from "react";
import { Upload, FileText, CheckCircle } from "lucide-react";
import {
  getFarmerDocuments,
  uploadDocument,
  processDocument,
  getDocumentFields,
} from "../api";
import type {
  DocumentEntity,
  DocumentFieldEntity,
  DocumentStatus,
} from "../types";
import { useFarmer } from "../context/FarmerContext";

const DOMAINS = [
  { value: "IDENTITY", label: "身分與資格" },
  { value: "LAND_CROP", label: "土地與作物" },
  { value: "TRANSACTION", label: "經營與交易" },
  { value: "INPUT_EQUIPMENT", label: "投入與設備" },
  { value: "GREEN_ACTION", label: "綠色行動" },
  { value: "CERTIFICATION", label: "認證與治理" },
  { value: "LOAN_PURPOSE", label: "申貸用途" },
] as const;

const STATUS_LABELS: Record<DocumentStatus, { text: string; color: string }> = {
  UPLOADED: { text: "已上傳", color: "bg-blue-100 text-blue-700" },
  OCR_COMPLETED: { text: "OCR 完成", color: "bg-yellow-100 text-yellow-700" },
  FIELDS_CONFIRMED: { text: "已確認", color: "bg-orange-100 text-orange-700" },
  NORMALIZED: { text: "已標準化", color: "bg-purple-100 text-purple-700" },
  VERIFIED: { text: "已核驗", color: "bg-green-100 text-green-700" },
};

export default function Documents() {
  const { currentFarmer } = useFarmer();
  const farmerId = currentFarmer.id;

  const [documents, setDocuments] = useState<DocumentEntity[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [selectedDomain, setSelectedDomain] = useState<string>("CERTIFICATION");
  const [message, setMessage] = useState<{ text: string; isError: boolean } | null>(null);
  const [selectedDoc, setSelectedDoc] = useState<DocumentEntity | null>(null);
  const [fields, setFields] = useState<DocumentFieldEntity[]>([]);

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getFarmerDocuments(farmerId);
      setDocuments(data.documents);
    } catch (e) {
      setMessage({
        text: e instanceof Error ? e.message : "載入失敗",
        isError: true,
      });
    } finally {
      setLoading(false);
    }
  }, [farmerId]);

  useEffect(() => {
    void loadDocuments();
    setSelectedDoc(null);
    setFields([]);
  }, [loadDocuments]);

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setBusy(true);
    setMessage(null);
    try {
      const result = await uploadDocument(file, farmerId, selectedDomain);
      setMessage({
        text: `上傳成功！OCR 擷取 ${result.fields.length} 個欄位`,
        isError: false,
      });
      await loadDocuments();
    } catch (e) {
      setMessage({
        text: e instanceof Error ? e.message : "上傳失敗",
        isError: true,
      });
    } finally {
      setBusy(false);
      event.target.value = "";
    }
  };

  const handleProcess = async (docId: string) => {
    setBusy(true);
    setMessage(null);
    try {
      const result = await processDocument(docId);
      setMessage({
        text: `處理完成：確認 → 標準化 → 核驗（發現 ${result.anomaly_count} 個異常）`,
        isError: false,
      });
      await loadDocuments();
    } catch (e) {
      setMessage({
        text: e instanceof Error ? e.message : "處理失敗",
        isError: true,
      });
    } finally {
      setBusy(false);
    }
  };

  const handleViewFields = async (doc: DocumentEntity) => {
    setSelectedDoc(doc);
    try {
      const data = await getDocumentFields(doc.id);
      setFields(data.fields);
    } catch {
      setFields([]);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">文件管理</h1>

      {/* Upload */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Upload className="w-5 h-5" /> 上傳文件
        </h2>
        <div className="flex items-center gap-4">
          <select
            value={selectedDomain}
            onChange={(e) => setSelectedDomain(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
          >
            {DOMAINS.map((domain) => (
              <option key={domain.value} value={domain.value}>
                {domain.label}
              </option>
            ))}
          </select>
          <label className="cursor-pointer bg-greenfin-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-greenfin-700 transition-colors">
            {busy ? "處理中..." : "選擇檔案"}
            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png,.xlsx"
              onChange={handleUpload}
              disabled={busy}
              className="hidden"
            />
          </label>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          支援: PDF, JPEG, PNG, WEBP, XLSX (最大 10MB)
        </p>
      </section>

      {message && (
        <div
          className={`rounded-lg p-3 text-sm ${
            message.isError ? "bg-red-50 text-red-700" : "bg-green-50 text-green-700"
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Document list */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5" /> 已上傳文件 ({documents.length})
        </h2>
        {loading ? (
          <p className="text-gray-400">載入中...</p>
        ) : documents.length === 0 ? (
          <p className="text-gray-400">尚無文件</p>
        ) : (
          <div className="space-y-3">
            {documents.map((doc) => {
              const status = STATUS_LABELS[doc.status] ?? {
                text: doc.status,
                color: "bg-gray-100",
              };
              return (
                <div
                  key={doc.id}
                  className="flex items-center justify-between border border-gray-100 rounded-lg p-3"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="w-4 h-4 text-gray-400" />
                    <div>
                      <p className="text-sm font-medium">{doc.filename}</p>
                      <p className="text-xs text-gray-400">
                        {doc.domain} ｜ {doc.source_level}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${status.color}`}>
                      {status.text}
                    </span>
                    <button
                      onClick={() => handleViewFields(doc)}
                      className="text-xs text-blue-600 hover:underline"
                    >
                      檢視欄位
                    </button>
                    {doc.status === "OCR_COMPLETED" && (
                      <button
                        onClick={() => handleProcess(doc.id)}
                        disabled={busy}
                        className="text-xs bg-greenfin-100 text-greenfin-700 px-2 py-1 rounded hover:bg-greenfin-200 disabled:opacity-50"
                      >
                        處理
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Field viewer */}
      {selectedDoc && (
        <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-4">
            欄位: {selectedDoc.filename}
          </h2>
          {fields.length === 0 ? (
            <p className="text-gray-400 text-sm">無欄位資料</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 text-gray-500">欄位名稱</th>
                  <th className="text-left py-2 text-gray-500">原始值</th>
                  <th className="text-left py-2 text-gray-500">標準化值</th>
                  <th className="text-left py-2 text-gray-500">信心度</th>
                  <th className="text-left py-2 text-gray-500">修正</th>
                </tr>
              </thead>
              <tbody>
                {fields.map((field) => (
                  <tr key={field.id} className="border-b border-gray-50">
                    <td className="py-2 font-medium">{field.field_name}</td>
                    <td className="py-2">{field.raw_value}</td>
                    <td className="py-2 text-greenfin-700">
                      {field.normalized_value || "—"}
                    </td>
                    <td className="py-2">
                      {field.confidence !== null ? (
                        <span
                          className={
                            field.confidence < 0.7 ? "text-orange-600" : "text-green-600"
                          }
                        >
                          {(field.confidence * 100).toFixed(0)}%
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="py-2">
                      {field.manually_corrected ? (
                        <CheckCircle className="w-4 h-4 text-blue-500" />
                      ) : (
                        <span className="text-gray-300">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}
    </div>
  );
}
