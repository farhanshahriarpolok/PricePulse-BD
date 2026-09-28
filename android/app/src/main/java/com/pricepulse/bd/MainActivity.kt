package com.pricepulse.bd

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.ShoppingCart
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.pricepulse.bd.data.api.RetrofitClient
import com.pricepulse.bd.data.repository.PricePulseRepository
import com.pricepulse.bd.ui.screens.AnomalyScreen
import com.pricepulse.bd.ui.screens.BasketScreen
import com.pricepulse.bd.ui.screens.FieldReportScreen
import com.pricepulse.bd.ui.screens.HomeScreen
import com.pricepulse.bd.ui.theme.DarkSlateBackground
import com.pricepulse.bd.ui.theme.EmeraldLight
import com.pricepulse.bd.ui.theme.PricePulseBDTheme
import com.pricepulse.bd.ui.theme.SlateSurface
import com.pricepulse.bd.ui.theme.TextMuted
import com.pricepulse.bd.viewmodel.PricePulseViewModel

private data class NavItem(
    val route: String,
    val label: String,
    val icon: ImageVector
)

/**
 * Root Activity for PricePulse BD.
 *
 * Sets up Compose edge-to-edge content, bottom navigation bar, and NavHost routing:
 *   home    -> HomeScreen (today's price pulse + ticker marquee)
 *   anomaly -> AnomalyScreen (statistical alert radar)
 *   basket  -> BasketScreen (3-channel consumer basket & Room DB saved baskets)
 *   report  -> FieldReportScreen (manual field report submission)
 */
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val repository = PricePulseRepository(RetrofitClient.apiService)
        val viewModelFactory = PricePulseViewModel.Factory(repository)

        val navItems = listOf(
            NavItem("home", "Pulse", Icons.Default.Home),
            NavItem("anomaly", "Anomalies", Icons.Default.Warning),
            NavItem("basket", "Basket", Icons.Default.ShoppingCart),
            NavItem("report", "Report", Icons.Default.Edit),
        )

        setContent {
            PricePulseBDTheme {
                val navController = rememberNavController()
                val sharedViewModel: PricePulseViewModel = viewModel(factory = viewModelFactory)

                Scaffold(
                    bottomBar = {
                        val navBackStackEntry by navController.currentBackStackEntryAsState()
                        val currentDestination = navBackStackEntry?.destination?.route

                        NavigationBar(
                            containerColor = SlateSurface
                        ) {
                            navItems.forEach { item ->
                                val selected = currentDestination == item.route
                                NavigationBarItem(
                                    selected = selected,
                                    onClick = {
                                        if (currentDestination != item.route) {
                                            navController.navigate(item.route) {
                                                popUpTo("home") { saveState = true }
                                                launchSingleTop = true
                                                restoreState = true
                                            }
                                        }
                                    },
                                    icon = { Icon(item.icon, contentDescription = item.label) },
                                    label = {
                                        Text(
                                            text = item.label,
                                            fontSize = 11.sp,
                                            fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal
                                        )
                                    },
                                    colors = NavigationBarItemDefaults.colors(
                                        selectedIconColor = EmeraldLight,
                                        selectedTextColor = EmeraldLight,
                                        unselectedIconColor = TextMuted,
                                        unselectedTextColor = TextMuted,
                                        indicatorColor = SlateSurface
                                    )
                                )
                            }
                        }
                    },
                    containerColor = DarkSlateBackground
                ) { innerPadding ->
                    NavHost(
                        navController = navController,
                        startDestination = "home",
                        modifier = Modifier.padding(innerPadding)
                    ) {
                        composable("home") {
                            HomeScreen(
                                viewModel = sharedViewModel,
                                onNavigateToAnomalies = { navController.navigate("anomaly") },
                            )
                        }
                        composable("anomaly") {
                            AnomalyScreen(viewModel = sharedViewModel)
                        }
                        composable("basket") {
                            BasketScreen(
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }
                        composable("report") {
                            FieldReportScreen(viewModel = sharedViewModel)
                        }
                    }
                }
            }
        }
    }
}
