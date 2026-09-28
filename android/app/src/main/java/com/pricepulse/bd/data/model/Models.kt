package com.pricepulse.bd.data.model

import com.google.gson.annotations.SerializedName

// ---------------------------------------------------------------------------
// Today's Pulse
// ---------------------------------------------------------------------------

data class PulseItem(
    @SerializedName("commodity_id")   val commodityId: Int,
    @SerializedName("canonical_name") val canonicalName: String,
    @SerializedName("bangla_name")    val banglaName: String?,
    @SerializedName("category")       val category: String?,
    @SerializedName("market_name")    val marketName: String?,
    @SerializedName("district")       val district: String?,
    @SerializedName("normalized_price") val normalizedPrice: Double?,
    @SerializedName("normalized_unit")  val normalizedUnit: String?,
    @SerializedName("price_type")     val priceType: String?,
    @SerializedName("confidence_score") val confidenceScore: Double?,
    @SerializedName("observation_date") val observationDate: String?,
    @SerializedName("source_name")    val sourceName: String?,
)

data class PulseResponse(
    @SerializedName("observation_date") val observationDate: String?,
    @SerializedName("total")           val total: Int,
    @SerializedName("items")           val items: List<PulseItem>,
    @SerializedName("freshness")       val freshness: String?,
)

data class PriceSummary(
    @SerializedName("avg_price") val avgPrice: Double = 0.0,
    @SerializedName("min_price") val minPrice: Double = 0.0,
    @SerializedName("max_price") val maxPrice: Double = 0.0,
    @SerializedName("sample_count") val sampleCount: Int = 1,
)

data class ChannelComparison(
    @SerializedName("wholesale_avg") val wholesaleAvg: Double? = null,
    @SerializedName("retail_avg") val retailAvg: Double? = null,
    @SerializedName("online_avg") val onlineAvg: Double? = null,
)

data class DailyPulseItem(
    @SerializedName("commodity_id") val commodityId: Int,
    @SerializedName("canonical_name") val canonicalName: String,
    @SerializedName("bangla_name") val banglaName: String = "",
    @SerializedName("category") val category: String = "Staples",
    @SerializedName("unit") val unit: String = "kg",
    @SerializedName("price_status") val priceStatus: String = "Normal",
    @SerializedName("price_summary") val priceSummary: PriceSummary = PriceSummary(),
    @SerializedName("channels") val channels: ChannelComparison? = null,
)

// ---------------------------------------------------------------------------
// Commodity catalog
// ---------------------------------------------------------------------------

data class CommodityOut(
    @SerializedName("id")             val id: Int,
    @SerializedName("canonical_name") val canonicalName: String,
    @SerializedName("bangla_name")    val banglaName: String?,
    @SerializedName("category")       val category: String?,
    @SerializedName("default_unit")   val defaultUnit: String?,
)

data class CommodityListResponse(
    @SerializedName("total") val total: Int,
    @SerializedName("items") val items: List<CommodityOut>,
)

// ---------------------------------------------------------------------------
// Historical price series
// ---------------------------------------------------------------------------

data class HistoricalPoint(
    @SerializedName("date")              val date: String,
    @SerializedName("normalized_price")  val normalizedPrice: Double,
    @SerializedName("normalized_unit")   val normalizedUnit: String?,
    @SerializedName("price_type")        val priceType: String?,
    @SerializedName("market_name")       val marketName: String?,
    @SerializedName("confidence_score")  val confidenceScore: Double?,
)

data class CommodityHistoryResponse(
    @SerializedName("commodity_id")   val commodityId: Int,
    @SerializedName("canonical_name") val canonicalName: String,
    @SerializedName("days")           val days: Int,
    @SerializedName("observations")   val observations: List<HistoricalPoint>,
)

// ---------------------------------------------------------------------------
// Anomaly detection
// ---------------------------------------------------------------------------

data class MetricBreakdown(
    @SerializedName("current_price")  val currentPrice: Double?,
    @SerializedName("sma_7d")         val sma7d: Double?,
    @SerializedName("sma_14d")        val sma14d: Double?,
    @SerializedName("std_dev")        val stdDev: Double?,
    @SerializedName("z_score")        val zScore: Double?,
    @SerializedName("delta_pct")      val deltaPct: Double?,
    @SerializedName("cv_pct")         val cvPct: Double?,
)

data class AnomalyDetail(
    @SerializedName("commodity_id")   val commodityId: Int,
    @SerializedName("commodity_name") val commodityName: String,
    @SerializedName("bangla_name")    val banglaName: String?,
    @SerializedName("is_anomaly")     val isAnomaly: Boolean,
    @SerializedName("severity")       val severity: String,
    @SerializedName("direction")      val direction: String?,
    @SerializedName("explanation")    val explanation: String?,
    @SerializedName("metrics")        val metrics: MetricBreakdown?,
)

data class AnomalyMonitorResponse(
    @SerializedName("evaluation_date")    val evaluationDate: String?,
    @SerializedName("total_commodities")  val totalCommodities: Int,
    @SerializedName("flagged_count")      val flaggedCount: Int,
    @SerializedName("anomalies")          val anomalies: List<AnomalyDetail>,
)

// ---------------------------------------------------------------------------
// Field report (manual ingestion)
// ---------------------------------------------------------------------------

data class FieldReportRequest(
    @SerializedName("commodity_id")   val commodityId: Int,
    @SerializedName("market_name")    val marketName: String,
    @SerializedName("district")       val district: String?,
    @SerializedName("price")          val price: Double,
    @SerializedName("unit")           val unit: String,
    @SerializedName("price_type")     val priceType: String = "retail_avg",
    @SerializedName("note")           val note: String?,
)

data class FieldReportResponse(
    @SerializedName("status")         val status: String,
    @SerializedName("observation_id") val observationId: Int?,
    @SerializedName("confidence_score") val confidenceScore: Double?,
    @SerializedName("message")        val message: String?,
)

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------

data class SearchResult(
    @SerializedName("commodity_id")   val commodityId: Int,
    @SerializedName("canonical_name") val canonicalName: String,
    @SerializedName("bangla_name")    val banglaName: String?,
    @SerializedName("category")       val category: String?,
    @SerializedName("latest_price")   val latestPrice: Double?,
    @SerializedName("unit")           val unit: String?,
)

data class SearchResponse(
    @SerializedName("query")   val query: String,
    @SerializedName("total")   val total: Int,
    @SerializedName("results") val results: List<SearchResult>,
)
