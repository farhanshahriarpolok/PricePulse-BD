package com.pricepulse.bd.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pricepulse.bd.ui.components.PriceTileCard
import com.pricepulse.bd.ui.theme.PricePulseColors
import com.pricepulse.bd.viewmodel.PricePulseViewModel
import com.pricepulse.bd.viewmodel.UiState

/**
 * Home Dashboard screen displaying today's market price pulse.
 *
 * Renders a scrollable list of PriceTileCards with real-time prices,
 * anomaly severity badges, and confidence scores sourced from the
 * FastAPI backend via the shared ViewModel.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    viewModel: PricePulseViewModel,
    onNavigateToAnomalies: () -> Unit = {},
) {
    val pulseState by viewModel.pulse.collectAsState()
    val flaggedCount by viewModel.flaggedCount.collectAsState()

    LaunchedEffect(Unit) {
        viewModel.loadTodayPulse()
        viewModel.loadAnomalyMonitor()
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            "PricePulse BD",
                            fontWeight = FontWeight.Bold,
                            fontSize = 18.sp,
                        )
                        Text(
                            "Today's Market Pulse",
                            color = PricePulseColors.Muted,
                            fontSize = 12.sp,
                        )
                    }
                },
                actions = {
                    if (flaggedCount > 0) {
                        Button(
                            onClick = onNavigateToAnomalies,
                            modifier = Modifier.padding(end = 8.dp),
                        ) {
                            Text(
                                "⚠ $flaggedCount Alert${if (flaggedCount > 1) "s" else ""}",
                                fontSize = 12.sp,
                                color = PricePulseColors.Rose,
                            )
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                ),
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { viewModel.loadTodayPulse() },
                containerColor = PricePulseColors.Indigo,
            ) {
                Icon(Icons.Default.Refresh, contentDescription = "Refresh prices")
            }
        },
        containerColor = MaterialTheme.colorScheme.background,
    ) { innerPadding ->
        when (val state = pulseState) {
            is UiState.Idle, is UiState.Loading -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(innerPadding),
                    contentAlignment = Alignment.Center,
                ) {
                    CircularProgressIndicator(color = PricePulseColors.Indigo)
                }
            }

            is UiState.Error -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(innerPadding),
                    contentAlignment = Alignment.Center,
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            text = "Connection error",
                            color = PricePulseColors.Rose,
                            fontWeight = FontWeight.Bold,
                        )
                        Spacer(Modifier.height(8.dp))
                        Text(
                            text = state.message,
                            color = PricePulseColors.Muted,
                            fontSize = 13.sp,
                        )
                        Spacer(Modifier.height(16.dp))
                        Button(onClick = { viewModel.loadTodayPulse() }) {
                            Text("Retry")
                        }
                    }
                }
            }

            is UiState.Success -> {
                if (state.data.isEmpty()) {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(innerPadding),
                        contentAlignment = Alignment.Center,
                    ) {
                        Text(
                            "No observations for today.\nTap refresh to fetch latest data.",
                            color = PricePulseColors.Muted,
                            fontSize = 14.sp,
                        )
                    }
                } else {
                    LazyColumn(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(innerPadding),
                        contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp),
                        verticalArrangement = Arrangement.spacedBy(10.dp),
                    ) {
                        items(state.data) { item ->
                            PriceTileCard(
                                name = item.canonicalName,
                                banglaName = item.banglaName,
                                price = item.normalizedPrice?.let { "%.2f".format(it) } ?: "—",
                                unit = item.normalizedUnit ?: "kg",
                                marketName = item.marketName,
                                confidenceScore = item.confidenceScore,
                                modifier = Modifier.fillMaxWidth(),
                            )
                        }
                        item { Spacer(Modifier.height(80.dp)) }
                    }
                }
            }
        }
    }
}
