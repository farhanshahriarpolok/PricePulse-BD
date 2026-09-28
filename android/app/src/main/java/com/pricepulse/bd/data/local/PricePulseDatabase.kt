package com.pricepulse.bd.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(
    entities = [
        CommodityEntity::class,
        PriceObservationEntity::class,
        AnomalyEntity::class,
        SavedBasketEntity::class,
        SavedBasketItemEntity::class
    ],
    version = 2,
    exportSchema = false
)
abstract class PricePulseDatabase : RoomDatabase() {

    abstract fun commodityDao(): CommodityDao
    abstract fun observationDao(): ObservationDao
    abstract fun anomalyDao(): AnomalyDao
    abstract fun basketDao(): BasketDao

    companion object {
        @Volatile
        private var INSTANCE: PricePulseDatabase? = null

        fun getDatabase(context: Context): PricePulseDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    PricePulseDatabase::class.java,
                    "pricepulse_bd_offline.db"
                )
                    .fallbackToDestructiveMigration()
                    .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
