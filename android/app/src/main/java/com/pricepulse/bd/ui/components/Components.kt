package com.pricepulse.bd.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pricepulse.bd.ui.theme.PricePulseColors

/**
 * Severity badge chip — colored label matching the anomaly severity level.
 */
@Composable
fun SeverityBadge(severity: String, modifier: Modifier = Modifier) {
    val (bgColor, textColor) = when (severity.lowercase()) {
        "critical" -> Pair(PricePulseColors.Rose.copy(alpha = 0.2f),  PricePulseColors.Rose)
        "severe"   -> Pair(PricePulseColors.Amber.copy(alpha = 0.2f), PricePulseColors.Amber)
        "moderate" -> Pair(PricePulseColors.Indigo.copy(alpha = 0.2f),PricePulseColors.Indigo)
        else       -> Pair(PricePulseColors.Emerald.copy(alpha = 0.2f),PricePulseColors.Emerald)
    }

    Box(
        modifier = modifier
            .background(bgColor, RoundedCornerShape(999.dp))
            .padding(horizontal = 10.dp, vertical = 3.dp)
    ) {
        Text(
            text = severity.uppercase(),
            color = textColor,
            fontSize = 11.sp,
            fontWeight = FontWeight.Bold,
            letterSpacing = 0.8.sp,
        )
    }
}

/**
 * Metric display card — shows a large numeric value with a label underneath.
 * Used on the anomaly and pulse screens.
 */
@Composable
fun MetricCard(
    value: String,
    label: String,
    color: Color = PricePulseColors.Indigo,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .background(
                MaterialTheme.colorScheme.surface,
                RoundedCornerShape(12.dp)
            )
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            text = value,
            color = color,
            fontSize = 26.sp,
            fontWeight = FontWeight.ExtraBold,
        )
        Spacer(Modifier.height(4.dp))
        Text(
            text = label,
            color = PricePulseColors.Muted,
            fontSize = 11.sp,
        )
    }
}

/**
 * Horizontal key-value row for displaying labelled metric pairs.
 */
@Composable
fun MetricRow(
    label: String,
    value: String,
    valueColor: Color = MaterialTheme.colorScheme.onSurface,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 3.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = label,
            color = PricePulseColors.Muted,
            fontSize = 13.sp,
            modifier = Modifier.width(140.dp),
        )
        Text(
            text = value,
            color = valueColor,
            fontSize = 13.sp,
            fontWeight = FontWeight.SemiBold,
        )
    }
}

/**
 * Price tile card — compact commodity price snapshot for the pulse list.
 */
@Composable
fun PriceTileCard(
    name: String,
    banglaName: String?,
    price: String,
    unit: String,
    marketName: String?,
    confidenceScore: Double?,
    anomalySeverity: String = "Normal",
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surface, RoundedCornerShape(12.dp))
            .padding(16.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = name,
                    color = MaterialTheme.colorScheme.onSurface,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.SemiBold,
                )
                if (!banglaName.isNullOrBlank()) {
                    Text(
                        text = banglaName,
                        color = PricePulseColors.Muted,
                        fontSize = 12.sp,
                    )
                }
            }
            if (anomalySeverity != "Normal") {
                SeverityBadge(severity = anomalySeverity)
            }
        }

        Spacer(Modifier.height(10.dp))

        Row(verticalAlignment = Alignment.Bottom) {
            Text(
                text = price,
                color = PricePulseColors.Amber,
                fontSize = 22.sp,
                fontWeight = FontWeight.ExtraBold,
            )
            Spacer(Modifier.width(4.dp))
            Text(
                text = "BDT/$unit",
                color = PricePulseColors.Muted,
                fontSize = 12.sp,
                modifier = Modifier.padding(bottom = 2.dp),
            )
        }

        Spacer(Modifier.height(4.dp))

        Row {
            if (!marketName.isNullOrBlank()) {
                Text(
                    text = marketName,
                    color = PricePulseColors.Muted,
                    fontSize = 11.sp,
                )
            }
            if (confidenceScore != null) {
                Spacer(Modifier.width(8.dp))
                Text(
                    text = "Conf: ${"%.0f".format(confidenceScore * 100)}%",
                    color = PricePulseColors.Emerald,
                    fontSize = 11.sp,
                )
            }
        }
    }
}
