import type { Recommendation } from "@/src/types/api";

export function getPlanningStats(recommendations: Recommendation[]) {
  const purchaseRecommendations = recommendations.filter((item) => item.recommended_order_qty > 0);
  return {
    purchaseRecommendations,
    urgentRecommendations: recommendations.filter((item) => ["critical", "high"].includes(item.priority)),
    totalExpectedRevenue: purchaseRecommendations.reduce((sum, item) => sum + (item.expected_revenue ?? 0), 0),
    totalRecommendedUnits: purchaseRecommendations.reduce((sum, item) => sum + (item.recommended_order_qty ?? 0), 0),
  };
}
