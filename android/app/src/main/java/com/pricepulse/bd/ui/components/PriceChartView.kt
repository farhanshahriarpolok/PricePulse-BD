package com.pricepulse.bd.ui.components

import android.graphics.Paint
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlin.math.max
import kotlin.math.min

data class PriceChartPoint(
    val date: String,
    val price: Float,
    val sma14d: Float? = null,
    val isAnomaly: Boolean = false,
    val anomalySeverity: String? = null
)

@Composable
fun PriceChartView(
    points: List<PriceChartPoint>,
    modifier: Modifier = Modifier,
    unit: String = "kg",
    lineColor: Color = Color(0xFF10B981), // Emerald
    smaColor: Color = Color(0xFF38BDF8),  // Sky Blue
    anomalyColor: Color = Color(0xFFF43F5E) // Rose
) {
    if (points.isEmpty()) {
        Box(
            modifier = modifier
                .fillMaxWidth()
                .height(220.dp)
                .background(Color(0xFF0F172A), RoundedCornerShape(16.dp)),
            contentAlignment = androidx.compose.ui.Alignment.Center
        ) {
            Text(
                text = "No historical price series available",
                color = Color(0xFF64748B),
                fontSize = 12.sp
            )
        }
        return
    }

    var selectedIndex by remember { mutableStateOf<Int?>(null) }

    val minPrice = remember(points) { points.minOf { it.price } * 0.95f }
    val maxPrice = remember(points) { points.maxOf { it.price } * 1.05f }
    val priceRange = remember(minPrice, maxPrice) { max(maxPrice - minPrice, 1.0f) }

    Column(
        modifier = modifier
            .fillMaxWidth()
            .background(Color(0xFF0F172A), RoundedCornerShape(16.dp))
            .padding(16.dp)
    ) {
        // Active Crosshair readout bar
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 8.dp),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            val activePoint = selectedIndex?.let { points.getOrNull(it) } ?: points.last()
            Column {
                Text(
                    text = activePoint.date,
                    color = Color(0xFF94A3B8),
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace
                )
                Text(
                    text = "${String.format("%.2f", activePoint.price)} BDT/$unit",
                    color = Color.White,
                    fontSize = 18.sp,
                    fontWeight = androidx.compose.ui.text.font.FontWeight.Bold,
                    fontFamily = FontFamily.Monospace
                )
            }

            if (activePoint.sma14d != null) {
                Column(horizontalAlignment = androidx.compose.ui.Alignment.End) {
                    Text(
                        text = "14d Rolling SMA",
                        color = Color(0xFF38BDF8),
                        fontSize = 11.sp
                    )
                    Text(
                        text = "${String.format("%.2f", activePoint.sma14d)} BDT",
                        color = Color(0xFF38BDF8),
                        fontSize = 14.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }

        // Custom Canvas Chart
        Canvas(
            modifier = Modifier
                .fillMaxWidth()
                .height(180.dp)
                .pointerInput(points) {
                    detectTapGestures { offset ->
                        val stepX = size.width / (points.size - 1).coerceAtLeast(1)
                        val idx = (offset.x / stepX).toInt().coerceIn(0, points.size - 1)
                        selectedIndex = idx
                    }
                }
                .pointerInput(points) {
                    detectDragGestures { change, _ ->
                        val stepX = size.width / (points.size - 1).coerceAtLeast(1)
                        val idx = (change.position.x / stepX).toInt().coerceIn(0, points.size - 1)
                        selectedIndex = idx
                    }
                }
        ) {
            val width = size.width
            val height = size.height
            val n = points.size
            if (n < 2) return@Canvas

            val stepX = width / (n - 1)

            fun getY(price: Float): Float {
                val norm = (price - minPrice) / priceRange
                return height - (norm * height * 0.85f) - (height * 0.08f)
            }

            // Draw horizontal grid lines
            val gridLines = 4
            for (i in 0..gridLines) {
                val y = height * (i.toFloat() / gridLines)
                drawLine(
                    color = Color(0xFF1E293B),
                    start = Offset(0f, y),
                    end = Offset(width, y),
                    strokeWidth = 1f
                )
            }

            // Draw 14-day Rolling SMA (Dashed Cyan Curve)
            val smaPath = Path()
            var smaStarted = false
            for (i in 0 until n) {
                val smaVal = points[i].sma14d ?: continue
                val x = i * stepX
                val y = getY(smaVal)
                if (!smaStarted) {
                    smaPath.moveTo(x, y)
                    smaStarted = true
                } else {
                    smaPath.lineTo(x, y)
                }
            }
            if (smaStarted) {
                drawPath(
                    path = smaPath,
                    color = smaColor,
                    style = Stroke(
                        width = 2.dp.toPx(),
                        pathEffect = PathEffect.dashPathEffect(floatArrayOf(12f, 10f), 0f)
                    )
                )
            }

            // Draw Smooth Cubic Bezier Price Curve
            val pricePath = Path()
            val fillPath = Path()

            pricePath.moveTo(0f, getY(points[0].price))
            fillPath.moveTo(0f, height)
            fillPath.lineTo(0f, getY(points[0].price))

            for (i in 0 until n - 1) {
                val x0 = i * stepX
                val y0 = getY(points[i].price)
                val x1 = (i + 1) * stepX
                val y1 = getY(points[i + 1].price)

                val cx = (x0 + x1) / 2f
                pricePath.cubicTo(cx, y0, cx, y1, x1, y1)
                fillPath.cubicTo(cx, y0, cx, y1, x1, y1)
            }

            fillPath.lineTo(width, height)
            fillPath.close()

            // Gradient Fill Under Curve
            drawPath(
                path = fillPath,
                brush = Brush.verticalGradient(
                    colors = listOf(lineColor.copy(alpha = 0.25f), Color.Transparent),
                    startY = 0f,
                    endY = height
                )
            )

            // Main Price Stroke
            drawPath(
                path = pricePath,
                color = lineColor,
                style = Stroke(width = 2.5.dp.toPx(), cap = StrokeCap.Round, join = StrokeJoin.Round)
            )

            // Draw Anomaly glowing markers
            for (i in 0 until n) {
                val pt = points[i]
                if (pt.isAnomaly) {
                    val x = i * stepX
                    val y = getY(pt.price)
                    // Outer glow
                    drawCircle(
                        color = anomalyColor.copy(alpha = 0.35f),
                        radius = 8.dp.toPx(),
                        center = Offset(x, y)
                    )
                    // Inner dot
                    drawCircle(
                        color = anomalyColor,
                        radius = 4.dp.toPx(),
                        center = Offset(x, y)
                    )
                }
            }

            // Draw Crosshair on Touch / Drag
            selectedIndex?.let { idx ->
                val activePt = points[idx]
                val x = idx * stepX
                val y = getY(activePt.price)

                // Vertical line
                drawLine(
                    color = Color.White.copy(alpha = 0.6f),
                    start = Offset(x, 0f),
                    end = Offset(x, height),
                    strokeWidth = 1.dp.toPx(),
                    pathEffect = PathEffect.dashPathEffect(floatArrayOf(6f, 6f), 0f)
                )

                // Selected point halo
                drawCircle(
                    color = Color.White,
                    radius = 5.dp.toPx(),
                    center = Offset(x, y)
                )
                drawCircle(
                    color = lineColor,
                    radius = 3.dp.toPx(),
                    center = Offset(x, y)
                )
            }
        }
    }
}
