package com.pricepulse.bd.ui.screens

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pricepulse.bd.data.model.AnomalyDetail
import com.pricepulse.bd.ui.components.MetricRow
import com.pricepulse.bd.ui.components.SeverityBadge
import com.pricepulse.bd.ui.theme.PricePulseColors
import com.pricepulse.bd.viewmodel.PricePulseViewModel
import com.pricepulse.bd.viewmodel.UiState

/**
 * Commercial-grade Anomaly Radar screen displaying flagged commodities with statistical breakdown.
 * Features visual badge hierarchy, expandable 'Why flagged?' drawer, and Z-score meter.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AnomalyScreen(viewModel: PricePulseViewModel) {
    val anomalyState by viewModel.anomalies.collectAsState()

    LaunchedEffect(Unit) {
        viewModel.loadAnomalyMonitor()
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("Anomaly Radar & Spikes", fontWeight = FontWeight.ExtraBold, fontSize = 18.sp)
                        Text("Explainable rolling Z-score outlier alerts", color = PricePulseColors.Muted, fontSize = 12.sp)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                ),
            )
        },
        containerColor = MaterialTheme.colorScheme.background,
    ) { innerPadding ->
        when (val state = anomalyState) {
            is UiState.Idle, is UiState.Loading -> {
                Box(Modifier.fillMaxSize().padding(innerPadding), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(color = PricePulseColors.Emerald)
                }
            }
            is UiState.Error -> {
                Box(Modifier.fillMaxSize().padding(innerPadding), contentAlignment = Alignment.Center) {
                    Text(state.message, color = PricePulseColors.Rose, fontSize = 14.sp)
                }
            }
            is UiState.Success -> {
                val flagged = state.data.filter { it.isAnomaly }
                if (flagged.isEmpty()) {
                    Box(Modifier.fillMaxSize().padding(innerPadding), contentAlignment = Alignment.Center) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("✓", fontSize = 44.sp, color = PricePulseColors.Emerald)
                            Spacer(Modifier.height(8.dp))
                            Text(
                                "All commodities operating in statistical equilibrium.",
                                color = Color.White,
                                fontWeight = FontWeight.Bold,
                                fontSize = 15.sp,
                            )
                            Text(
                                "No rolling |Z| ≥ 1.5 deviations detected across markets today.",
                                color = PricePulseColors.Muted,
                                fontSize = 12.sp,
                            )
                        }
                    }
                } else {
                    LazyColumn(
                        modifier = Modifier.fillMaxSize().padding(innerPadding),
                        contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        item {
                            Text(
                                "Detected ${flagged.size} statistical outliers exceeding standard baseline envelopes:",
                                color = PricePulseColors.Muted,
                                fontSize = 12.sp,
                            )
                        }
                        items(flagged) { anomaly ->
                            CommercialAnomalyCard(anomaly = anomaly)
                        }
                        item { Spacer(Modifier.height(80.dp)) }
                    }
                }
            }
        }
    }
}

@Composable
private fun CommercialAnomalyCard(anomaly: AnomalyDetail) {
    var isExpanded by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(Color(0xFF1E293B))
            .padding(16.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = anomaly.commodityName,
                    fontWeight = FontWeight.Bold,
                    fontSize = 16.sp,
                    color = Color.White,
                )
                if (!anomaly.banglaName.isNullOrBlank()) {
                    Text(
                        text = anomaly.banglaName,
                        color = PricePulseColors.Emerald,
                        fontSize = 12.sp,
                    )
                }
            }
            SeverityBadge(severity = anomaly.severity)
        }

        Spacer(Modifier.height(12.dp))

        anomaly.metrics?.let { m ->
            MetricRow("Observed Price", "BDT ${m.currentPrice ?: "—"}")
            MetricRow("14-Day SMA Baseline", "BDT ${m.sma14d ?: "—"}")
            MetricRow(
                "Standard Score (Z-Score)",
                "Z = ${String.format("%.2f", m.zScore ?: 0.0)}",
                valueColor = if ((m.zScore ?: 0.0) > 2.5) PricePulseColors.Rose else PricePulseColors.Amber
            )

            // Visual Z-Score meter bar
            Spacer(Modifier.height(8.dp))
            val zScoreVal = m.zScore ?: 0.0
            val normalizedMeter = ((zScoreVal.coerceIn(-3.0, 3.0) + 3.0) / 6.0).toFloat()
            Column {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("-3σ (Depressed)", color = PricePulseColors.Muted, fontSize = 9.sp)
                    Text("0 (Baseline)", color = PricePulseColors.Muted, fontSize = 9.sp)
                    Text("+3σ (Critical Spike)", color = PricePulseColors.Rose, fontSize = 9.sp)
                }
                Spacer(Modifier.height(4.dp))
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(8.dp)
                        .clip(RoundedCornerShape(4.dp))
                        .background(Color(0xFF0F172A))
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth(normalizedMeter)
                            .fillMaxHeight()
                            .clip(RoundedCornerShape(4.dp))
                            .background(
                                if (zScoreVal > 2.0) PricePulseColors.Rose
                                else if (zScoreVal > 1.5) PricePulseColors.Amber
                                else PricePulseColors.Emerald
                            )
                    )
                }
            }

            Spacer(Modifier.height(8.dp))
            MetricRow(
                "Net Percentage Deviation",
                "${if ((m.deltaPct ?: 0.0) > 0) "+" else ""}${m.deltaPct ?: "—"}%",
                valueColor = if ((m.deltaPct ?: 0.0) > 20) PricePulseColors.Rose else PricePulseColors.Amber
            )
            MetricRow("Volatility Index (CV%)", "${m.cvPct ?: "—"}%")
        }

        Spacer(Modifier.height(10.dp))

        // Expandable 'Why was this flagged?' section
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(8.dp))
                .background(Color(0xFF0F172A))
                .clickable { isExpanded = !isExpanded }
                .padding(horizontal = 12.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Info, contentDescription = null, tint = PricePulseColors.Emerald, modifier = Modifier.size(16.dp))
                Spacer(Modifier.width(8.dp))
                Text(
                    "Why was this flagged?",
                    color = PricePulseColors.Emerald,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold
                )
            }
            Icon(
                if (isExpanded) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                contentDescription = null,
                tint = PricePulseColors.Muted,
                modifier = Modifier.size(18.dp)
            )
        }

        AnimatedVisibility(visible = isExpanded) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 8.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(Color(0xFF0F172A).copy(alpha = 0.6f))
                    .padding(12.dp)
            ) {
                Text(
                    text = anomaly.explanation ?: "Observed market price deviates statistically from the 14-day rolling moving average by more than 1.5 standard deviations.",
                    color = Color(0xFFCBD5E1),
                    fontSize = 12.sp,
                    lineHeight = 17.sp,
                )
            }
        }
    }
}
