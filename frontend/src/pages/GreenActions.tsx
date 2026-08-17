import { useCallback, useEffect, useState } from "react";
import { Leaf, Plus } from "lucide-react";
import { useFarmer } from "../context/FarmerContext";

const DIMENSIONS = [
  { value: "減量", label: "減量" },
  { value: "增匯", label: "增匯" },
  { value: "循環", label: "循環" },
  { value: "綠色治理", label: "綠色治理" },
];

const LEVELS = [
  { value: "BASIC", label: "單次基礎行為（20 點）" },
  { value: "SUSTAINED", label: "持續性措施（50 點）" },
  { value: "CERTIFIED", label: "正式驗證／重大投入（100 點）" },
];

interface GreenActionItem {
  id: string;
  dimension: string;
  action_level: string;
  description: string;
  action_date: string;
  is_active: boolean;
}

export default function GreenActions() {
  const { currentFarmer } = useFarmer();
  const farmerId = currentFarmer.id;

  const [actions, setActions] = useState<GreenActionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ text: string; isError: boolean } | null>(null);

  const [form, setForm] = useState({
    dimension: "減量",
    action_level: "BASIC",
    description: "",
    action_date: new Date().toISOString().split("T")[0],
  });

  const loadActions = useCallback(async () => {
    try {
      const r = await fetch(`/api/farmers/${farmerId}/green-actions`);
      const d = await r.json();
      setActions(d.actions || []);
    } catch { /* ignore */ }
    setLoading(false);
  }, [farmerId]);

  useEffect(() => {
    setLoading(true);
    void loadActions();
  }, [loadActions]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setMessage(null);

    try {
      const res = await fetch("/api/green-actions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, farmer_id: farmerId }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || "新增失敗");

      setMessage({ text: "綠色行動已新增！可按「重新計算」更新經驗值。", isError: false });
      setForm({ dimension: "減量", action_level: "BASIC", description: "", action_date: new Date().toISOString().split("T")[0] });
      setShowForm(false);
      await loadActions();
    } catch (err) {
      setMessage({ text: err instanceof Error ? err.message : "新增失敗", isError: true });
    } finally {
      setBusy(false);
    }
  };

  const levelLabel = (level: string) => {
    if (level === "BASIC") return "基礎";
    if (level === "SUSTAINED") return "持續";
    return "驗證";
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <Leaf className="w-6 h-6 text-greenfin-600" /> 綠色行動
        </h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1 px-4 py-2 bg-greenfin-600 text-white rounded-lg text-sm hover:bg-greenfin-700"
        >
          <Plus className="w-4 h-4" /> 新增行動
        </button>
      </div>

      {message && (
        <div className={`rounded-lg p-3 text-sm ${message.isError ? "bg-red-50 text-red-700" : "bg-green-50 text-green-700"}`}>
          {message.text}
        </div>
      )}

      {/* Add form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white rounded-xl border p-6 space-y-4">
          <h2 className="font-semibold">新增綠色行動</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-500">構面 *</label>
              <select
                value={form.dimension}
                onChange={(e) => setForm({ ...form, dimension: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm mt-1"
              >
                {DIMENSIONS.map((d) => (
                  <option key={d.value} value={d.value}>{d.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500">等級 *</label>
              <select
                value={form.action_level}
                onChange={(e) => setForm({ ...form, action_level: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm mt-1"
              >
                {LEVELS.map((l) => (
                  <option key={l.value} value={l.value}>{l.label}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs text-gray-500">描述 *</label>
            <input
              required
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm mt-1"
              placeholder="例如：取得有機認證"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500">日期 *</label>
            <input
              required
              type="date"
              value={form.action_date}
              onChange={(e) => setForm({ ...form, action_date: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm mt-1"
            />
          </div>
          <button
            type="submit"
            disabled={busy}
            className="bg-greenfin-600 text-white px-6 py-2 rounded-lg text-sm hover:bg-greenfin-700 disabled:opacity-50"
          >
            {busy ? "新增中..." : "新增"}
          </button>
        </form>
      )}

      {/* Action list */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h2 className="text-lg font-semibold mb-4">已記錄的綠色行動 ({actions.length})</h2>
        {loading ? (
          <p className="text-gray-400">載入中...</p>
        ) : actions.length === 0 ? (
          <p className="text-gray-400 text-sm">尚無綠色行動，請點「新增行動」開始建立綠色履歷。</p>
        ) : (
          <div className="space-y-3">
            {actions.map((action) => (
              <div key={action.id} className="flex items-center justify-between border border-gray-100 rounded-lg p-3">
                <div>
                  <p className="text-sm font-medium">{action.description}</p>
                  <p className="text-xs text-gray-400">
                    {action.dimension} ｜ {levelLabel(action.action_level)} ｜ {action.action_date}
                  </p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${action.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                  {action.is_active ? "有效" : "停用"}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
