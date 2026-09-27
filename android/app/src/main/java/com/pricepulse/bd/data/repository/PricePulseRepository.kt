package com.pricepulse.bd.data.repository

import com.pricepulse.bd.data.api.PricePulseApiService
import com.pricepulse.bd.data.model.AnomalyMonitorResponse
import com.pricepulse.bd.data.model.CommodityHistoryResponse
import com.pricepulse.bd.data.model.CommodityListResponse
import com.pricepulse.bd.data.model.FieldReportRequest
import com.pricepulse.bd.data.model.FieldReportResponse
import com.pricepulse.bd.data.model.PulseResponse
import com.pricepulse.bd.data.model.SearchResponse

/**
 * PricePulseRepository abstracts all network I/O from the ViewModel layer.
 *
 * Each method returns a Result<T> wrapping either the deserialized API response
 * or an exception — callers do not need to handle Retrofit exceptions directly.
 */
class PricePulseRepository(private val api: PricePulseApiService) {

    suspend fun getTodayPulse(): Result<PulseResponse> = safeCall { api.getTodayPulse() }

    suspend fun getCommodities(category: String? = null): Result<CommodityListResponse> =
        safeCall { api.getCommodities(category) }

    suspend fun getCommodityHistory(id: Int, days: Int = 14): Result<CommodityHistoryResponse> =
        safeCall { api.getCommodityHistory(id, days) }

    suspend fun getAnomalyMonitor(): Result<AnomalyMonitorResponse> =
        safeCall { api.getAnomalyMonitor() }

    suspend fun submitFieldReport(request: FieldReportRequest): Result<FieldReportResponse> =
        safeCall { api.submitFieldReport(request) }

    suspend fun search(query: String): Result<SearchResponse> =
        safeCall { api.search(query) }

    /**
     * Generic safe network call wrapper.
     * Converts non-2xx HTTP responses to exceptions with status information.
     */
    private suspend fun <T> safeCall(block: suspend () -> retrofit2.Response<T>): Result<T> {
        return try {
            val response = block()
            if (response.isSuccessful) {
                val body = response.body()
                if (body != null) {
                    Result.success(body)
                } else {
                    Result.failure(IllegalStateException("Empty response body from server."))
                }
            } else {
                Result.failure(
                    RuntimeException(
                        "API error ${response.code()}: ${response.errorBody()?.string() ?: "No details"}"
                    )
                )
            }
        } catch (exception: Exception) {
            Result.failure(exception)
        }
    }
}
