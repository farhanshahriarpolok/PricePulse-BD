package com.pricepulse.bd.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val PricePulseDarkScheme = darkColorScheme(
    primary = EmeraldLight,
    onPrimary = DarkSlateBackground,
    primaryContainer = EmeraldContainer,
    onPrimaryContainer = EmeraldOnContainer,
    secondary = AmberAccent,
    onSecondary = DarkSlateBackground,
    secondaryContainer = AmberContainer,
    tertiary = WholesaleBlue,
    error = RoseCritical,
    errorContainer = RoseContainer,
    background = DarkSlateBackground,
    onBackground = TextPrimary,
    surface = SlateSurface,
    onSurface = TextPrimary,
    surfaceVariant = SlateSurfaceVariant,
    onSurfaceVariant = TextSecondary,
    outline = SlateBorder,
)

// Semantic color helpers available across the app
object PricePulseColors {
    val Emerald = EmeraldLight
    val EmeraldDark = EmeraldPrimary
    val Amber = AmberAccent
    val Rose = RoseCritical
    val Indigo = Color(0xFF818CF8)
    val Cyan = Color(0xFF22D3EE)
    val Slate = SlateSurface
    val Background = DarkSlateBackground
    val Text = TextPrimary
    val Muted = TextSecondary
    val Wholesale = WholesaleBlue
    val Retail = RetailGreen
    val Online = OnlinePurple
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
