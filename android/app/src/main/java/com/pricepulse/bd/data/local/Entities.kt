package com.pricepulse.bd.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "commodities")
data class CommodityEntity(
    @PrimaryKey
    val id: Int,
    val canonicalName: String,
    val banglaName: String,
    val category: String,
    val defaultUnit: String,
    val lastUpdated: Long = System.currentTimeMillis()
)

@Entity(tableName = "price_observations")
data class PriceObservationEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val commodityId: Int,
    val marketName: String,
    val districtName: String,
    val normalizedPrice: Double,
    val normalizedUnit: String,
    val observationDate: String,
    val confidenceScore: Double = 0.95
)

@Entity(tableName = "anomalies")
data class AnomalyEntity(
    @PrimaryKey
    val commodityId: Int,
    val canonicalName: String,
    val banglaName: String,
    val isAnomaly: Boolean,
    val severity: String,
    val direction: String?,
    val currentPrice: Double,
    val baselineSma14d: Double,
    val zScore: Double,
    val explanation: String,
    val detectedAt: Long = System.currentTimeMillis()
)

@Entity(tableName = "saved_baskets")
data class SavedBasketEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Int = 0,
    val name: String,
    val banglaName: String = "",
    val description: String = "",
    val updatedAt: String = ""
)

@Entity(tableName = "saved_basket_items")
data class SavedBasketItemEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Int = 0,
    val basketId: Int,
    val commodityId: Int,
    val quantity: Double,
    val unit: String
)

