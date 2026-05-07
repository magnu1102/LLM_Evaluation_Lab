import { Navigate, Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { ComparePage } from "./pages/Compare";
import { DashboardPage } from "./pages/Dashboard";
import { HealthPage } from "./pages/Health";
import { NewRunPage } from "./pages/NewRun";
import { RunDetailPage } from "./pages/RunDetail";
import { TrendsPage } from "./pages/Trends";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="runs/new" element={<NewRunPage />} />
        <Route path="runs/:id" element={<RunDetailPage />} />
        <Route path="compare" element={<ComparePage />} />
        <Route path="trends" element={<TrendsPage />} />
        <Route path="health" element={<HealthPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
