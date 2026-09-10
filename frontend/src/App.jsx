import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import AgreementList from "./pages/agreements/AgreementList";
import AgreementForm from "./pages/agreements/AgreementForm";
import AgreementDetail from "./pages/agreements/AgreementDetail";
import LeaseScheduleView from "./pages/lease/LeaseScheduleView";
import AmendmentsView from "./pages/amendments/AmendmentsView";
import MastersView from "./pages/masters/MastersView";
import ReportsView from "./pages/reports/ReportsView";
import RentPostingView from "./pages/rent-posting/RentPostingView";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/agreements" element={<AgreementList />} />
        <Route path="/agreements/new" element={<AgreementForm />} />
        <Route path="/agreements/:id" element={<AgreementDetail />} />
        <Route path="/lease" element={<LeaseScheduleView />} />
        <Route path="/amendments" element={<AmendmentsView />} />
        <Route path="/masters" element={<MastersView />} />
        <Route path="/reports" element={<ReportsView />} />
        <Route path="/rent-posting" element={<RentPostingView />} />
      </Routes>
    </Layout>
  );
}
