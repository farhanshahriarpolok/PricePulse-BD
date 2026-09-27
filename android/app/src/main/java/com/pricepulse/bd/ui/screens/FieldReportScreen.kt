package com.pricepulse.bd.ui.screens

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pricepulse.bd.data.model.FieldReportRequest
import com.pricepulse.bd.ui.theme.PricePulseColors
import com.pricepulse.bd.viewmodel.PricePulseViewModel
import com.pricepulse.bd.viewmodel.UiState
import kotlinx.coroutines.launch

/**
 * Field Report Form — Human-in-the-Loop manual price ingestion.
 *
 * Validates required fields before submission. Reports are tagged as
 * source_id='field_report' with Tier 4 confidence (0.60) on the backend.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FieldReportScreen(viewModel: PricePulseViewModel) {
    val reportState by viewModel.fieldReportResult.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()

    // Form state
    var commodityId by remember { mutableStateOf("") }
    var marketName  by remember { mutableStateOf("") }
    var district    by remember { mutableStateOf("") }
    var price       by remember { mutableStateOf("") }
    var unit        by remember { mutableStateOf("kg") }
    var note        by remember { mutableStateOf("") }

    // Form validation
    var formError by remember { mutableStateOf("") }

    // React to submission result
    LaunchedEffect(reportState) {
        when (val state = reportState) {
            is UiState.Success -> {
                snackbarHostState.showSnackbar(state.data)
                viewModel.resetFieldReportState()
                // Reset form
                commodityId = ""; marketName = ""; district = ""; price = ""; note = ""
            }
            is UiState.Error -> {
                snackbarHostState.showSnackbar("Error: ${state.message}")
                viewModel.resetFieldReportState()
            }
            else -> Unit
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("Report a Price", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                        Text("Field spot price submission", color = PricePulseColors.Muted, fontSize = 12.sp)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                ),
            )
        },
        snackbarHost = { SnackbarHost(snackbarHostState) },
        containerColor = MaterialTheme.colorScheme.background,
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(horizontal = 20.dp, vertical = 12.dp)
                .verticalScroll(rememberScrollState())
        ) {
            Text(
                text = "Manual price reports are assigned a Tier 4 confidence score (0.60) " +
                       "to prevent outlier poisoning of the statistical baseline.",
                color = PricePulseColors.Muted,
                fontSize = 13.sp,
                lineHeight = 18.sp,
            )

            Spacer(Modifier.height(20.dp))

            OutlinedTextField(
                value = commodityId,
                onValueChange = { commodityId = it; formError = "" },
                label = { Text("Commodity ID") },
                placeholder = { Text("e.g. 1 (use /commodities API to look up)") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Spacer(Modifier.height(12.dp))

            OutlinedTextField(
                value = marketName,
                onValueChange = { marketName = it; formError = "" },
                label = { Text("Market Name") },
                placeholder = { Text("e.g. Karwan Bazar") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Spacer(Modifier.height(12.dp))

            OutlinedTextField(
                value = district,
                onValueChange = { district = it },
                label = { Text("District (optional)") },
                placeholder = { Text("e.g. Dhaka") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Spacer(Modifier.height(12.dp))

            OutlinedTextField(
                value = price,
                onValueChange = { price = it; formError = "" },
                label = { Text("Price (BDT)") },
                placeholder = { Text("e.g. 95.0") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Spacer(Modifier.height(12.dp))

            OutlinedTextField(
                value = unit,
                onValueChange = { unit = it },
                label = { Text("Unit") },
                placeholder = { Text("kg / liter / pc") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Spacer(Modifier.height(12.dp))

            OutlinedTextField(
                value = note,
                onValueChange = { note = it },
                label = { Text("Note (optional)") },
                placeholder = { Text("Observed at central market stall, checked 3 vendors.") },
                modifier = Modifier.fillMaxWidth(),
                maxLines = 3,
            )

            if (formError.isNotBlank()) {
                Spacer(Modifier.height(8.dp))
                Text(text = formError, color = PricePulseColors.Rose, fontSize = 13.sp)
            }

            Spacer(Modifier.height(24.dp))

            Button(
                onClick = {
                    val idInt = commodityId.trim().toIntOrNull()
                    val priceDouble = price.trim().toDoubleOrNull()
                    when {
                        idInt == null   -> formError = "Commodity ID must be a valid integer."
                        marketName.isBlank() -> formError = "Market name is required."
                        priceDouble == null || priceDouble <= 0 -> formError = "Enter a valid positive price."
                        unit.isBlank()  -> formError = "Unit is required (e.g. kg)."
                        else -> {
                            viewModel.submitFieldReport(
                                FieldReportRequest(
                                    commodityId = idInt,
                                    marketName  = marketName.trim(),
                                    district    = district.trim().ifBlank { null },
                                    price       = priceDouble,
                                    unit        = unit.trim(),
                                    note        = note.trim().ifBlank { null },
                                )
                            )
                        }
                    }
                },
                modifier = Modifier.fillMaxWidth().height(52.dp),
                colors = ButtonDefaults.buttonColors(containerColor = PricePulseColors.Indigo),
                enabled = reportState !is UiState.Loading,
            ) {
                if (reportState is UiState.Loading) {
                    CircularProgressIndicator(color = MaterialTheme.colorScheme.onPrimary, strokeWidth = 2.dp)
                } else {
                    Text("Submit Price Report", fontWeight = FontWeight.Bold)
                }
            }

            Spacer(Modifier.height(40.dp))
        }
    }
}
