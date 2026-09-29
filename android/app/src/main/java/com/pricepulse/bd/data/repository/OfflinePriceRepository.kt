package com.pricepulse.bd.data.repository

import android.content.Context
import com.pricepulse.bd.data.api.RetrofitClient
import com.pricepulse.bd.data.local.CommodityEntity
import com.pricepulse.bd.data.local.PriceObservationEntity
import com.pricepulse.bd.data.local.AnomalyEntity
import com.pricepulse.bd.data.local.SavedBasketEntity
import com.pricepulse.bd.data.local.SavedBasketItemEntity
import com.pricepulse.bd.data.local.PricePulseDatabase
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

class OfflinePriceRepository(context: Context) {
    private val db = PricePulseDatabase.getDatabase(context)
    private val commodityDao = db.commodityDao()
    private val observationDao = db.observationDao()
    private val anomalyDao = db.anomalyDao()
    private val basketDao = db.basketDao()
    private val api = RetrofitClient.apiService

    // Reactive Flows from Room
    val cachedCommodities: Flow<List<CommodityEntity>> = commodityDao.getAllCommodities()
    val activeAnomalies: Flow<List<AnomalyEntity>> = anomalyDao.getActiveAnomalies()
    val savedBaskets: Flow<List<SavedBasketEntity>> = basketDao.getSavedBaskets()

    suspend fun refreshCommodities(): Result<Int> {
        return try {
            val response = api.getCommodities()
            if (response.isSuccessful && response.body() != null) {
                val list = response.body()!!.items.map { dto ->
                    CommodityEntity(
                        id = dto.id,
                        canonicalName = dto.canonicalName,
                        banglaName = dto.banglaName ?: "",
                        category = dto.category ?: "Staples",
                        defaultUnit = dto.defaultUnit ?: "kg"
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
            val response = api.getAnomalyMonitor()
            if (response.isSuccessful && response.body() != null) {
                val anomalies = response.body()!!.anomalies.map { a ->
                    AnomalyEntity(
                        commodityId = a.commodityId,
                        canonicalName = a.commodityName,
                        banglaName = a.banglaName ?: "",
                        isAnomaly = a.isAnomaly,
                        severity = a.severity,
                        direction = a.direction,
                        currentPrice = a.metrics?.currentPrice ?: 0.0,
                        baselineSma14d = a.metrics?.sma14d ?: 0.0,
                        zScore = a.metrics?.zScore ?: 0.0,
                        explanation = a.explanation ?: ""
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

    fun getItemsForBasket(basketId: Int): Flow<List<SavedBasketItemEntity>> {
        return basketDao.getItemsForBasket(basketId)
    }

    suspend fun saveBasketLocally(
        name: String,
        banglaName: String = "",
        description: String = "",
        items: List<SavedBasketItemEntity>
    ): Long {
        val basket = SavedBasketEntity(
            name = name,
            banglaName = banglaName,
            description = description,
            updatedAt = System.currentTimeMillis().toString()
        )
        val basketId = basketDao.insertBasket(basket)
        val itemsWithId = items.map { it.copy(basketId = basketId.toInt()) }
        basketDao.insertBasketItems(itemsWithId)
        return basketId
    }

    suspend fun deleteBasketLocally(basketId: Int) {
        basketDao.deleteBasketItems(basketId)
        basketDao.deleteBasket(basketId)
    }
}

