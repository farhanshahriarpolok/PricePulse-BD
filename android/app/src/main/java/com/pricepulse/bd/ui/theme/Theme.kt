package com.pricepulse.bd.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// ---------------------------------------------------------------------------
// PricePulse BD design tokens — Material 3 dark scheme
// ---------------------------------------------------------------------------

private val Indigo400  = Color(0xFF818CF8)
private val Indigo600  = Color(0xFF4F46E5)
private val Cyan400    = Color(0xFF22D3EE)
private val Emerald400 = Color(0xFF34D399)
private val Amber400   = Color(0xFFFBBF24)
private val Rose400    = Color(0xFFFB7185)
private val Surface    = Color(0xFF1E293B)
private val Background = Color(0xFF0F172A)
private val OnSurface  = Color(0xFFE2E8F0)

private val PricePulseDarkScheme = darkColorScheme(
    primary          = Indigo400,
    onPrimary        = Color.White,
    primaryContainer = Indigo600,
    secondary        = Cyan400,
    onSecondary      = Background,
    tertiary         = Emerald400,
    error            = Rose400,
    background       = Background,
    onBackground     = OnSurface,
    surface          = Surface,
    onSurface        = OnSurface,
)

// Semantic color helpers available across the app
object PricePulseColors {
    val Indigo  = Indigo400
    val Cyan    = Cyan400
    val Emerald = Emerald400
    val Amber   = Amber400
    val Rose    = Rose400
    val Muted   = Color(0xFF94A3B8)
}

/**
 * PricePulse BD Material 3 dark theme wrapper.
 * Apply this at the root of the Compose UI tree.
 */
@Composable
fun PricePulseBDTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = PricePulseDarkScheme,
        content = content,
    )
}
