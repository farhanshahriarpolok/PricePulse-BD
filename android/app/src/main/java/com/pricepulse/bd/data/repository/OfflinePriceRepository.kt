package com.pricepulse.bd.data.repository

import android.content.Context
import com.pricepulse.bd.data.api.RetrofitClient
import com.pricepulse.bd.data.local.CommodityEntity
import com.pricepulse.bd.data.local.PriceObservationEntity
import com.pricepulse.bd.data.local.AnomalyEntity
import com.pricepulse.bd.data.local.PricePulseDatabase
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

class OfflinePriceRepository(context: Context) {
    private val db = PricePulseDatabase.getDatabase(context)
    private val commodityDao = db.commodityDao()
    private val observationDao = db.observationDao()
    private val anomalyDao = db.anomalyDao()
    private val api = RetrofitClient.apiService

    // Reactive Flow from Room
    val cachedCommodities: Flow<List<CommodityEntity>> = commodityDao.getAllCommodities()
    val activeAnomalies: Flow<List<AnomalyEntity>> = anomalyDao.getActiveAnomalies()

    suspend fun refreshCommodities(): Result<Int> {
        return try {
            val response = api.getCommodities()
            if (response.isSuccessful && response.body() != null) {
                val list = response.body()!!.items.map { dto ->
                    CommodityEntity(
                        id = dto.id,
                        canonicalName = dto.canonicalName,
                        banglaName = dto.banglaName,
                        category = dto.category,
                        defaultUnit = dto.defaultUnit
                    )
                }
                commodityDao.insertCommodities(list)
                Result.success(list.size)
            } else {
                Result.failure(Exception("Failed to fetch commodities: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun refreshAnomalies(): Result<Int> {
        return try {
            val response = api.getActiveAnomalies()
            if (response.isSuccessful && response.body() != null) {
                val anomalies = response.body()!!.anomalies.map { a ->
                    AnomalyEntity(
                        commodityId = a.commodityId,
                        canonicalName = a.canonicalName,
                        banglaName = a.banglaName,
                        isAnomaly = a.isAnomaly,
                        severity = a.anomalySeverity,
                        direction = a.anomalyDirection,
                        currentPrice = a.metrics.currentPrice,
                        baselineSma14d = a.metrics.baselineSma14d ?: 0.0,
                        zScore = a.metrics.zScore14d ?: 0.0,
                        explanation = a.explanation
                    )
                }
                anomalyDao.clearAnomalies()
                anomalyDao.insertAnomalies(anomalies)
                Result.success(anomalies.size)
            } else {
                Result.failure(Exception("Failed to fetch anomalies: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    fun getObservationsForCommodity(commodityId: Int): Flow<List<PriceObservationEntity>> {
        return observationDao.getObservationsForCommodity(commodityId)
    }
}
