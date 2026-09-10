import * as XLSX from "xlsx";

/**
 * Exports an array of plain objects to a downloaded .xlsx file.
 * @param {Array<Object>} rows - one object per row; object keys become column headers
 * @param {string} filename - without extension, e.g. "vendors"
 * @param {string} sheetName - defaults to "Sheet1"
 */
export function exportToExcel(rows, filename, sheetName = "Sheet1") {
  if (!rows || rows.length === 0) {
    alert("Nothing to export yet.");
    return;
  }
  const worksheet = XLSX.utils.json_to_sheet(rows);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);
  const stamp = new Date().toISOString().slice(0, 10);
  XLSX.writeFile(workbook, `${filename}_${stamp}.xlsx`);
}
