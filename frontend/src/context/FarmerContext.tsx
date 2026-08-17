import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useAuth } from "./AuthContext";

export interface FarmerOption {
  id: string;
  name: string;
  farm: string;
  case_type: string;
}

const DEMO_FARMERS: FarmerOption[] = [
  { id: "farmer-a-chen", name: "陳小農", farm: "綠田友善農場", case_type: "Healthy (GREEN)" },
  { id: "farmer-b-lin", name: "林阿花", farm: "日出有機園", case_type: "Needs Improvement (YELLOW)" },
  { id: "farmer-c-wang", name: "王大明", farm: "舊園地", case_type: "Abnormal (RED)" },
];

interface FarmerContextType {
  currentFarmer: FarmerOption;
  setFarmer: (farmer: FarmerOption) => void;
  farmers: FarmerOption[];
}

const FarmerContext = createContext<FarmerContextType | null>(null);

export function FarmerProvider({ children }: { children: ReactNode }) {
  const [currentFarmer, setCurrentFarmer] = useState<FarmerOption>(DEMO_FARMERS[0]);
  const { user } = useAuth();

  // When a farmer logs in, set the current farmer to their own profile
  useEffect(() => {
    if (user?.role === "farmer" && user.farmer_id) {
      const existing = DEMO_FARMERS.find((f) => f.id === user.farmer_id);
      if (existing) {
        setCurrentFarmer(existing);
      } else {
        // Newly registered farmer not in the static list
        setCurrentFarmer({
          id: user.farmer_id,
          name: user.display_name,
          farm: "",
          case_type: "新註冊",
        });
      }
    }
  }, [user]);

  return (
    <FarmerContext.Provider
      value={{ currentFarmer, setFarmer: setCurrentFarmer, farmers: DEMO_FARMERS }}
    >
      {children}
    </FarmerContext.Provider>
  );
}

export function useFarmer() {
  const ctx = useContext(FarmerContext);
  if (!ctx) throw new Error("useFarmer must be used inside FarmerProvider");
  return ctx;
}
