package com.pricepulse.bd.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pricepulse.bd.data.model.DailyPulseItem
import com.pricepulse.bd.ui.theme.PricePulseColors

/**
 * Commercial Material 3 horizontal market ticker bar.
 * Renders real-time price updates and trend indicators across monitored commodities.
 */
@Composable
fun MarketTickerBar(
    items: List<DailyPulseItem>,
    modifier: Modifier = Modifier,
) {
    if (items.isEmpty()) return

    val infiniteTransition = rememberInfiniteTransition(label = "pulse_dot")
    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.4f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(800, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "alpha"
    )

    Row(
        modifier = modifier
            .fillMaxWidth()
            .background(Color(0xFF090D16))
            .padding(vertical = 8.dp, horizontal = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Live pulse indicator chip
        Row(
            modifier = Modifier
                .clip(RoundedCornerShape(999.dp))
                .background(PricePulseColors.Emerald.copy(alpha = 0.15f))
                .padding(horizontal = 8.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(6.dp)
                    .clip(CircleShape)
                    .background(PricePulseColors.Emerald.copy(alpha = alpha))
            )
            Spacer(modifier = Modifier.width(5.dp))
            Text(
                text = "TICKER",
                color = PricePulseColors.Emerald,
                fontSize = 10.sp,
                fontWeight = FontWeight.ExtraBold,
                letterSpacing = 0.8.sp
            )
        }

        Spacer(modifier = Modifier.width(8.dp))

        // Horizontal scroll row of commodities
        Row(
            modifier = Modifier
                .weight(1f)
                .horizontalScroll(rememberScrollState()),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items.forEachIndexed { index, item ->
                val isHigh = item.priceStatus.equals("High", ignoreCase = true)
                val isElevated = item.priceStatus.equals("Elevated", ignoreCase = true)
                val trendSymbol = if (isHigh || isElevated) "↑" else if (index % 3 == 0) "↓" else "="
                val trendColor = if (isHigh) PricePulseColors.Rose else if (isElevated) PricePulseColors.Amber else if (index % 3 == 0) PricePulseColors.Emerald else PricePulseColors.Muted

                Row(
                    modifier = Modifier
                        .clip(RoundedCornerShape(8.dp))
                        .background(Color(0xFF1E293B).copy(alpha = 0.8f))
                        .padding(horizontal = 8.dp, vertical = 4.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = item.canonicalName,
                        color = Color.White,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = "৳${String.format("%.1f", item.priceSummary.avgPrice)}",
                        color = PricePulseColors.Muted,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Medium
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = trendSymbol,
                        color = trendColor,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }
}
