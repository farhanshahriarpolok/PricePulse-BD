package com.pricepulse.bd

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.pricepulse.bd.data.api.RetrofitClient
import com.pricepulse.bd.data.repository.PricePulseRepository
import com.pricepulse.bd.ui.screens.AnomalyScreen
import com.pricepulse.bd.ui.screens.FieldReportScreen
import com.pricepulse.bd.ui.screens.HomeScreen
import com.pricepulse.bd.ui.theme.PricePulseBDTheme
import com.pricepulse.bd.viewmodel.PricePulseViewModel

/**
 * Root Activity for PricePulse BD.
 *
 * Sets up the Compose content, Navigation graph, and manual dependency injection
 * (ViewModel factory wired to repository, repository wired to Retrofit singleton).
 *
 * Navigation routes:
 *   home    -> HomeScreen  (today's price pulse + anomaly badge)
 *   anomaly -> AnomalyScreen (statistical alert feed)
 *   report  -> FieldReportScreen (manual ingestion form)
 */
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        // Manual dependency wiring (no Hilt — keeps the project dependency-light)
        val repository = PricePulseRepository(RetrofitClient.apiService)
        val viewModelFactory = PricePulseViewModel.Factory(repository)

        setContent {
            PricePulseBDTheme {
                val navController = rememberNavController()
                val sharedViewModel: PricePulseViewModel = viewModel(factory = viewModelFactory)

                NavHost(
                    navController = navController,
                    startDestination = "home",
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
                    composable("report") {
                        FieldReportScreen(viewModel = sharedViewModel)
                    }
                }
            }
        }
    }
}
