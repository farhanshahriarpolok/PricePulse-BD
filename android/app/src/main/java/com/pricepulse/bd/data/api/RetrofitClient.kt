package com.pricepulse.bd.data.api

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

/**
 * Singleton Retrofit client factory for the PricePulse BD API.
 *
 * Base URL points to the Android emulator loopback alias (10.0.2.2:8000)
 * which routes to the developer machine's localhost where FastAPI is running.
 *
 * OkHttp logging is enabled at BODY level so that all request/response
 * pairs appear in Logcat during development and viva demo sessions.
 */
object RetrofitClient {

    // Emulator loopback: 10.0.2.2 resolves to host machine's 127.0.0.1
    private const val BASE_URL = "http://10.0.2.2:8000/api/v1/"

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(15, TimeUnit.SECONDS)
        .build()

    private val retrofit: Retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()

    val apiService: PricePulseApiService by lazy {
        retrofit.create(PricePulseApiService::class.java)
    }
}
