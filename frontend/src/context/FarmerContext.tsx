import { createContext, useContext, useState, ReactNode } from "react";

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

  return (
    <FarmerContext.Provider value={{ currentFarmer, setFarmer: setCurrentFarmer, farmers: DEMO_FARMERS }}>
      {children}
    </FarmerContext.Provider>
  );
}

export function useFarmer() {
  const ctx = useContext(FarmerContext);
  if (!ctx) throw new Error("useFarmer must be used inside FarmerProvider");
  return ctx;
}
