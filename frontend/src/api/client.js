import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({ baseURL });

// ---- Masters ----
export const getProperties = () => api.get("/api/masters/properties").then((r) => r.data);
export const getVendors = () => api.get("/api/masters/vendors").then((r) => r.data);
export const getCostCenters = () => api.get("/api/masters/cost-centers").then((r) => r.data);
export const getProfitCenters = () => api.get("/api/masters/profit-centers").then((r) => r.data);

// ---- Agreements ----
export const listAgreements = () => api.get("/api/agreements").then((r) => r.data);
// Alias used by the Agreements list's Export-to-Excel button - same data,
// just a distinct name so the export action reads clearly at the call site.
export const exportAgreements = () => api.get("/api/agreements").then((r) => r.data);
export const getAgreement = (id) => api.get(`/api/agreements/${id}`).then((r) => r.data);
export const createAgreement = (payload) =>
  api.post("/api/agreements", payload).then((r) => r.data);
export const updateAgreement = (id, payload) =>
  api.put(`/api/agreements/${id}`, payload).then((r) => r.data);

// ---- Lease Schedule ----
export const generateLeaseSchedule = (agreementId) =>
  api.post(`/api/lease-schedules/generate/${agreementId}`).then((r) => r.data);
export const getLeaseSchedule = (agreementId) =>
  api.get(`/api/lease-schedules/${agreementId}`).then((r) => r.data);

// ---- Masters (mutations) ----
export const createProperty = (payload) => api.post("/api/masters/properties", payload).then((r) => r.data);
export const removeProperty = (id) => api.delete(`/api/masters/properties/${id}`).then((r) => r.data);
export const createVendor = (payload) => api.post("/api/masters/vendors", payload).then((r) => r.data);
export const removeVendor = (id) => api.delete(`/api/masters/vendors/${id}`).then((r) => r.data);
export const createCostCenter = (payload) => api.post("/api/masters/cost-centers", payload).then((r) => r.data);
export const removeCostCenter = (id) => api.delete(`/api/masters/cost-centers/${id}`).then((r) => r.data);
export const createProfitCenter = (payload) => api.post("/api/masters/profit-centers", payload).then((r) => r.data);
export const removeProfitCenter = (id) => api.delete(`/api/masters/profit-centers/${id}`).then((r) => r.data);

export const postLeaseSchedulePeriod = (periodId) =>
  api.post(`/api/lease-schedules/period/${periodId}/post`).then((r) => r.data);
export const postRecognition = (agreementId) =>
  api.post(`/api/lease-schedules/${agreementId}/post-recognition`).then((r) => r.data);
export const getPostingFilter = (agreementId, periodNumber, vendorId) =>
  api
    .get("/api/postings/filter", { params: { agreement_id: agreementId, period_number: periodNumber, vendor_id: vendorId } })
    .then((r) => r.data);
export const postPostingEntry = (payload) => api.post("/api/postings/post", payload).then((r) => r.data);
export const postInterestAndDepreciation = (payload) =>
  api.post("/api/postings/post-interest-depreciation", payload).then((r) => r.data);

// ---- Rent Posting (Operational SPOC -> Finance SPOC invoice workflow) ----
export const getRentCap = (agreementId, vendorId, periodNumber) =>
  api
    .get("/api/rent-postings/rent-cap", {
      params: { agreement_id: agreementId, vendor_id: vendorId, period_number: periodNumber },
    })
    .then((r) => r.data);

export const submitRentInvoice = (formData) =>
  api
    .post("/api/rent-postings", formData, { headers: { "Content-Type": "multipart/form-data" } })
    .then((r) => r.data);

export const getPendingRentPostings = () => api.get("/api/rent-postings/pending").then((r) => r.data);
export const getRentPostingHistory = (agreementId, month) =>
  api
    .get("/api/rent-postings/history", {
      params: {
        ...(agreementId ? { agreement_id: agreementId } : {}),
        ...(month ? { month } : {}),
      },
    })
    .then((r) => r.data);

export const bulkDecideRentPostings = (payload) =>
  api.post("/api/rent-postings/bulk-decision", payload).then((r) => r.data);

export const getRentPostingDownloadUrl = (requestId) =>
  `${api.defaults.baseURL}/api/rent-postings/${requestId}/download`;
export const getRentPostingsForAgreement = (agreementId) =>
  api.get(`/api/rent-postings/agreement/${agreementId}`).then((r) => r.data);

// ---- Amendments ----
export const getAmendmentTypes = () => api.get("/api/amendments/types").then((r) => r.data);
export const listAmendments = (agreementId) =>
  api.get(`/api/amendments/agreement/${agreementId}`).then((r) => r.data);
export const createAmendmentRequest = (payload) =>
  api.post("/api/amendments", payload).then((r) => r.data);
export const decideAmendment = (amendmentId, payload) =>
  api.post(`/api/amendments/${amendmentId}/decision`, payload).then((r) => r.data);
export const postAmendment = (amendmentId) =>
  api.post(`/api/amendments/${amendmentId}/post`).then((r) => r.data);

// ---- AI Chatbot (local model, reads the DB as its knowledge base) ----
export const askChatbot = (question) =>
  api.post("/api/chatbot/ask", { question }).then((r) => r.data);

// ---- Dashboard ----
export const getDashboardSummary = () =>
  api.get("/api/dashboard/summary").then((r) => r.data);
export const getKpis = () => api.get("/api/dashboard/kpis").then((r) => r.data);
