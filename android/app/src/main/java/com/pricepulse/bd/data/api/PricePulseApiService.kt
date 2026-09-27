package com.pricepulse.bd.data.api

import com.pricepulse.bd.data.model.AnomalyMonitorResponse
import com.pricepulse.bd.data.model.CommodityListResponse
import com.pricepulse.bd.data.model.FieldReportRequest
import com.pricepulse.bd.data.model.FieldReportResponse
import com.pricepulse.bd.data.model.PulseResponse
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

/**
 * Retrofit service interface mapping PricePulse BD REST endpoints.
 *
 * Base URL: http://10.0.2.2:8000/api/v1/
 * (10.0.2.2 is the Android emulator's alias for the host machine's localhost.)
 *
 * All calls are suspend functions for use with Kotlin Coroutines and
 * Jetpack Compose's collectAsState / LaunchedEffect patterns.
 */
interface PricePulseApiService {

    /**
     * Retrieve today's market pulse — latest normalized prices across all commodities.
     */
    @GET("pulse/today")
    suspend fun getTodayPulse(): Response<PulseResponse>

    /**
     * List all canonical commodities in the taxonomy.
     *
     * @param category Optional filter (e.g. "Vegetables", "Grains")
     */
    @GET("commodities")
    suspend fun getCommodities(
        @Query("category") category: String? = null
    ): Response<CommodityListResponse>

    /**
     * Retrieve 14-day historical price series for a single commodity.
     *
     * @param commodityId Database primary key of the commodity.
     * @param days        Number of historical days to fetch (default 14).
     */
    @GET("commodities/{id}/history")
    suspend fun getCommodityHistory(
        @Path("id") commodityId: Int,
        @Query("days") days: Int = 14
    ): Response<com.pricepulse.bd.data.model.CommodityHistoryResponse>

    /**
     * Retrieve anomaly detection results for all monitored commodities.
     * Returns flagged commodities with Z-scores, severity levels, and
     * human-readable explanation text.
     */
    @GET("anomalies/monitor")
    suspend fun getAnomalyMonitor(): Response<AnomalyMonitorResponse>

    /**
     * Submit a manual field spot price report (Human-in-the-Loop ingestion).
     * Reports are tagged source_id='field_report' with Tier 4 confidence (0.60)
     * to prevent outlier poisoning of the historical baseline.
     */
    @POST("observations/field-report")
    suspend fun submitFieldReport(
        @Body request: FieldReportRequest
    ): Response<FieldReportResponse>

    /**
     * Full-text search across commodity names and bangla aliases.
     *
     * @param query Raw search term (Bengali or English).
     */
    @GET("search")
    suspend fun search(
        @Query("q") query: String
    ): Response<com.pricepulse.bd.data.model.SearchResponse>
}
