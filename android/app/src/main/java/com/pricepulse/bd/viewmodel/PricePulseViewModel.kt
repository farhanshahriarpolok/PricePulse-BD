package com.pricepulse.bd.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.pricepulse.bd.data.model.AnomalyDetail
import com.pricepulse.bd.data.model.CommodityOut
import com.pricepulse.bd.data.model.FieldReportRequest
import com.pricepulse.bd.data.model.PulseItem
import com.pricepulse.bd.data.repository.PricePulseRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

/**
 * Sealed state wrapper for UI state management.
 * Each screen observes a StateFlow<UiState<T>> to drive Loading/Success/Error rendering.
 */
sealed class UiState<out T> {
    object Idle    : UiState<Nothing>()
    object Loading : UiState<Nothing>()
    data class Success<T>(val data: T) : UiState<T>()
    data class Error(val message: String) : UiState<Nothing>()
}

/**
 * Shared ViewModel for the PricePulse BD Android app.
 *
 * Exposes StateFlows consumed by all Compose screens. Each data fetch is
 * launched in viewModelScope so it is automatically cancelled if the ViewModel
 * is cleared (e.g. on back navigation).
 */
class PricePulseViewModel(private val repository: PricePulseRepository) : ViewModel() {

    // -------- Today's price pulse --------
    private val _pulse = MutableStateFlow<UiState<List<PulseItem>>>(UiState.Idle)
    val pulse: StateFlow<UiState<List<PulseItem>>> = _pulse

    // -------- Commodity catalog --------
    private val _commodities = MutableStateFlow<UiState<List<CommodityOut>>>(UiState.Idle)
    val commodities: StateFlow<UiState<List<CommodityOut>>> = _commodities

    // -------- Anomaly monitor --------
    private val _anomalies = MutableStateFlow<UiState<List<AnomalyDetail>>>(UiState.Idle)
    val anomalies: StateFlow<UiState<List<AnomalyDetail>>> = _anomalies

    // -------- Field report submission --------
    private val _fieldReportResult = MutableStateFlow<UiState<String>>(UiState.Idle)
    val fieldReportResult: StateFlow<UiState<String>> = _fieldReportResult

    // -------- Statistics --------
    private val _flaggedCount = MutableStateFlow(0)
    val flaggedCount: StateFlow<Int> = _flaggedCount

    fun loadTodayPulse() {
        _pulse.value = UiState.Loading
        viewModelScope.launch {
            repository.getTodayPulse().fold(
                onSuccess = { response ->
                    _pulse.value = UiState.Success(response.items)
                },
                onFailure = { exception ->
                    _pulse.value = UiState.Error(exception.message ?: "Failed to load pulse.")
                }
            )
        }
    }

    fun loadCommodities(category: String? = null) {
        _commodities.value = UiState.Loading
        viewModelScope.launch {
            repository.getCommodities(category).fold(
                onSuccess = { response ->
                    _commodities.value = UiState.Success(response.items)
                },
                onFailure = { exception ->
                    _commodities.value = UiState.Error(exception.message ?: "Failed to load commodities.")
                }
            )
        }
    }

    fun loadAnomalyMonitor() {
        _anomalies.value = UiState.Loading
        viewModelScope.launch {
            repository.getAnomalyMonitor().fold(
                onSuccess = { response ->
                    _flaggedCount.value = response.flaggedCount
                    _anomalies.value = UiState.Success(response.anomalies)
                },
                onFailure = { exception ->
                    _anomalies.value = UiState.Error(exception.message ?: "Failed to load anomaly data.")
                }
            )
        }
    }

    fun submitFieldReport(request: FieldReportRequest) {
        _fieldReportResult.value = UiState.Loading
        viewModelScope.launch {
            repository.submitFieldReport(request).fold(
                onSuccess = { response ->
                    val msg = response.message ?: "Report submitted successfully. Confidence: ${response.confidenceScore}"
                    _fieldReportResult.value = UiState.Success(msg)
                },
                onFailure = { exception ->
                    _fieldReportResult.value = UiState.Error(exception.message ?: "Submission failed.")
                }
            )
        }
    }

    fun resetFieldReportState() {
        _fieldReportResult.value = UiState.Idle
    }

    // ---------------------------------------------------------------------------
    // ViewModelProvider.Factory
    // ---------------------------------------------------------------------------

    class Factory(private val repository: PricePulseRepository) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            if (modelClass.isAssignableFrom(PricePulseViewModel::class.java)) {
                return PricePulseViewModel(repository) as T
            }
            throw IllegalArgumentException("Unknown ViewModel class: ${modelClass.name}")
        }
    }
}
