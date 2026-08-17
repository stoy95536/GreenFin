import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Leaf, Building2, Shield, UserPlus } from "lucide-react";
import { useAuth, SessionUser } from "../context/AuthContext";

interface UserOption {
  id: string;
  username: string;
  display_name: string;
  role: string;
}

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [users, setUsers] = useState<UserOption[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/auth/users")
      .then((r) => r.json())
      .then((d) => setUsers(d.users || []))
      .finally(() => setLoading(false));
  }, []);

  const handleLogin = async (user: UserOption) => {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: user.id }),
    });
    const data = await res.json();

    const session: SessionUser = {
      id: user.id,
      username: user.username,
      display_name: user.display_name,
      role: user.role as SessionUser["role"],
      farmer_id: data.farmer_profile?.id,
    };
    login(session);

    // Route based on role
    if (user.role === "bank") navigate("/bank");
    else navigate("/");
  };

  const roleIcon = (role: string) => {
    if (role === "farmer") return <Leaf className="w-5 h-5 text-greenfin-600" />;
    if (role === "bank") return <Building2 className="w-5 h-5 text-blue-600" />;
    return <Shield className="w-5 h-5 text-purple-600" />;
  };

  const roleLabel = (role: string) => {
    if (role === "farmer") return "小農";
    if (role === "bank") return "銀行";
    return "管理員";
  };

  const roleBg = (role: string) => {
    if (role === "farmer") return "hover:border-greenfin-300 hover:bg-greenfin-50";
    if (role === "bank") return "hover:border-blue-300 hover:bg-blue-50";
    return "hover:border-purple-300 hover:bg-purple-50";
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-greenfin-50 to-white flex items-center justify-center p-4">
      <div className="max-w-lg w-full">
        <div className="text-center mb-8">
          <Leaf className="w-12 h-12 text-greenfin-600 mx-auto mb-3" />
          <h1 className="text-3xl font-bold text-greenfin-800">GreenFin</h1>
          <p className="text-gray-500 mt-2">小農綠色數位融資履歷平台</p>
          <span className="inline-block mt-2 text-xs bg-yellow-100 text-yellow-700 px-3 py-1 rounded-full">
            DEMO 模式
          </span>
        </div>

        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">選擇帳號登入</h2>

          {loading ? (
            <p className="text-gray-400 text-center py-4">載入中...</p>
          ) : (
            <div className="space-y-3">
              {users.map((user) => (
                <button
                  key={user.id}
                  onClick={() => handleLogin(user)}
                  className={`w-full flex items-center gap-4 p-4 border border-gray-200 rounded-xl transition-all ${roleBg(user.role)}`}
                >
                  {roleIcon(user.role)}
                  <div className="text-left flex-1">
                    <p className="font-medium text-gray-800">{user.display_name}</p>
                    <p className="text-xs text-gray-400">@{user.username}</p>
                  </div>
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                    {roleLabel(user.role)}
                  </span>
                </button>
              ))}
            </div>
          )}

          <div className="mt-6 pt-4 border-t border-gray-100">
            <button
              onClick={() => navigate("/register")}
              className="w-full flex items-center justify-center gap-2 py-3 text-greenfin-700 bg-greenfin-50 rounded-xl hover:bg-greenfin-100 transition-colors"
            >
              <UserPlus className="w-4 h-4" />
              <span className="text-sm font-medium">註冊新帳號（小農）</span>
            </button>
          </div>
        </div>

        <p className="text-xs text-gray-400 text-center mt-6">
          Demo 模式：點擊帳號即可登入，無需密碼。
        </p>
      </div>
    </div>
  );
}
