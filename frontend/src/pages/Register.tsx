import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Leaf } from "lucide-react";
import { useAuth, SessionUser } from "../context/AuthContext";

export default function Register() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    username: "",
    display_name: "",
    real_name: "",
    phone: "",
    address: "",
    farm_name: "",
    farm_location: "",
    farm_area_hectares: "",
    crop_name: "",
    crop_variety: "",
  });

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);

    try {
      const payload = {
        ...form,
        farm_area_hectares: form.farm_area_hectares ? parseFloat(form.farm_area_hectares) : null,
      };

      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "註冊失敗");
      }

      const data = await res.json();

      // Auto-login after registration
      const session: SessionUser = {
        id: data.user.id,
        username: data.user.username,
        display_name: data.user.display_name,
        role: "farmer",
        farmer_id: data.farmer.id,
      };
      login(session);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "註冊失敗");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-greenfin-50 to-white flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <button
          onClick={() => navigate("/login")}
          className="text-sm text-greenfin-600 mb-4 flex items-center gap-1 hover:underline"
        >
          <ArrowLeft className="w-4 h-4" /> 返回登入
        </button>

        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-6">
            <Leaf className="w-6 h-6 text-greenfin-600" />
            <h1 className="text-xl font-bold text-gray-800">小農註冊</h1>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm mb-4">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-500">帳號 *</label>
                <input
                  required
                  value={form.username}
                  onChange={set("username")}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1"
                  placeholder="例: chen_farmer"
                />
              </div>
              <div>
                <label className="text-xs text-gray-500">顯示名稱 *</label>
                <input
                  required
                  value={form.display_name}
                  onChange={set("display_name")}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1"
                  placeholder="例: 陳小農"
                />
              </div>
            </div>

            <div>
              <label className="text-xs text-gray-500">真實姓名 *</label>
              <input
                required
                value={form.real_name}
                onChange={set("real_name")}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-500">電話</label>
                <input
                  value={form.phone}
                  onChange={set("phone")}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1"
                />
              </div>
              <div>
                <label className="text-xs text-gray-500">地址</label>
                <input
                  value={form.address}
                  onChange={set("address")}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1"
                />
              </div>
            </div>

            <hr className="my-2" />
            <p className="text-xs text-gray-500 font-medium">農場資訊</p>

            <div>
              <label className="text-xs text-gray-500">農場名稱 *</label>
              <input
                required
                value={form.farm_name}
                onChange={set("farm_name")}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1"
                placeholder="例: 綠田友善農場"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-500">地點</label>
                <input
                  value={form.farm_location}
                  onChange={set("farm_location")}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1"
                />
              </div>
              <div>
                <label className="text-xs text-gray-500">面積（公頃）</label>
                <input
                  type="number"
                  step="0.1"
                  value={form.farm_area_hectares}
                  onChange={set("farm_area_hectares")}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-500">主要作物</label>
                <input
                  value={form.crop_name}
                  onChange={set("crop_name")}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1"
                  placeholder="例: 稻米"
                />
              </div>
              <div>
                <label className="text-xs text-gray-500">品種</label>
                <input
                  value={form.crop_variety}
                  onChange={set("crop_variety")}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1"
                  placeholder="例: 台南11號"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={busy}
              className="w-full bg-greenfin-600 text-white py-3 rounded-xl font-medium hover:bg-greenfin-700 disabled:opacity-50 transition-colors"
            >
              {busy ? "建立中..." : "建立帳號"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
