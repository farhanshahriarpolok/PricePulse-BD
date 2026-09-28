package com.pricepulse.bd.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface CommodityDao {
    @Query("SELECT * FROM commodities ORDER BY canonicalName ASC")
    fun getAllCommodities(): Flow<List<CommodityEntity>>

    @Query("SELECT * FROM commodities WHERE category = :category ORDER BY canonicalName ASC")
    fun getCommoditiesByCategory(category: String): Flow<List<CommodityEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCommodities(commodities: List<CommodityEntity>)

    @Query("DELETE FROM commodities")
    suspend fun clearAll()
}

@Dao
interface ObservationDao {
    @Query("SELECT * FROM price_observations WHERE commodityId = :commodityId ORDER BY observationDate ASC")
    fun getObservationsForCommodity(commodityId: Int): Flow<List<PriceObservationEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertObservations(observations: List<PriceObservationEntity>)

    @Query("DELETE FROM price_observations WHERE observationDate < :beforeDate")
    suspend fun deleteOldObservations(beforeDate: String)
}

@Dao
interface AnomalyDao {
    @Query("SELECT * FROM anomalies WHERE isAnomaly = 1 ORDER BY zScore DESC")
    fun getActiveAnomalies(): Flow<List<AnomalyEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAnomalies(anomalies: List<AnomalyEntity>)

    @Query("DELETE FROM anomalies")
    suspend fun clearAnomalies()
}

@Dao
interface BasketDao {
    @Query("SELECT * FROM saved_baskets ORDER BY id DESC")
    fun getSavedBaskets(): Flow<List<SavedBasketEntity>>

    @Query("SELECT * FROM saved_baskets WHERE id = :basketId")
    suspend fun getBasketById(basketId: Int): SavedBasketEntity?

    @Query("SELECT * FROM saved_basket_items WHERE basketId = :basketId")
    fun getItemsForBasket(basketId: Int): Flow<List<SavedBasketItemEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertBasket(basket: SavedBasketEntity): Long

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertBasketItems(items: List<SavedBasketItemEntity>)

    @Query("DELETE FROM saved_baskets WHERE id = :basketId")
    suspend fun deleteBasket(basketId: Int)

    @Query("DELETE FROM saved_basket_items WHERE basketId = :basketId")
    suspend fun deleteBasketItems(basketId: Int)

    @Query("DELETE FROM saved_baskets")
    suspend fun clearAllBaskets()
}

