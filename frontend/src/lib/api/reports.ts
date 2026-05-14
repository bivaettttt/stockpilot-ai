import type { AnalyzeResponse } from "@/src/types/api";

export function getReportLinks(result: AnalyzeResponse | null) {
  return {
    reportUrl: result?.report_url ?? "",
    dashboardUrl: result?.dashboard_url ?? "",
    recommendationsCsvUrl: result?.recommendations_csv_url ?? "",
    abcXyzCsvUrl: result?.abc_xyz_matrix_csv_url ?? "",
  };
}
