/**
 * Turns a period_start date (e.g. "2026-07-01") into a clean "Month Year"
 * label (e.g. "July 2026") for dropdown options - used wherever someone
 * picks a lease schedule period, so they see a plain month/year instead of
 * the raw date range.
 */
export function formatMonthYear(dateString) {
  if (!dateString) return "";
  const [year, month] = dateString.split("-");
  const date = new Date(parseInt(year, 10), parseInt(month, 10) - 1, 1);
  return date.toLocaleDateString("en-IN", { month: "long", year: "numeric" });
}
