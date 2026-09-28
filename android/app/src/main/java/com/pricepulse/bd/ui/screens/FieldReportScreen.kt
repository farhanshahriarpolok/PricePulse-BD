package com.pricepulse.bd.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pricepulse.bd.data.model.FieldReportRequest
import com.pricepulse.bd.ui.theme.PricePulseColors
import com.pricepulse.bd.viewmodel.PricePulseViewModel
import com.pricepulse.bd.viewmodel.UiState

/**
 * Field Report Form — Human-in-the-Loop manual price ingestion.
 * Features real-time metric unit normalization preview (হালি, ডজন, ২৫০ গ্রাম, মণ).
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FieldReportScreen(viewModel: PricePulseViewModel) {
    val reportState by viewModel.fieldReportResult.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    // Form state
    var commodityId by remember { mutableStateOf("") }
    var marketName  by remember { mutableStateOf("") }
    var district    by remember { mutableStateOf("") }
    var price       by remember { mutableStateOf("") }
    var unit        by remember { mutableStateOf("kg") }
    var note        by remember { mutableStateOf("") }

    // Form validation
    var formError by remember { mutableStateOf("") }

    // Real-time metric conversion preview calculation
    val parsedPrice = price.trim().toDoubleOrNull()
    val unitPreview = remember(parsedPrice, unit) {
        if (parsedPrice == null || parsedPrice <= 0.0) return@remember null
        val u = unit.trim().lowercase()
        when {
            u in listOf("হালি", "hali", "৪টি", "4টি", "4 pc") -> {
                val perPc = parsedPrice / 4.0
                Pair("pc", perPc)
            }
            u in listOf("ডজন", "dozen", "১২টি", "12টি", "12 pc") -> {
                val perPc = parsedPrice / 12.0
                Pair("pc", perPc)
            }
            u in listOf("হাফ ডজন", "half dozen", "৬টি", "6টি", "6 pc") -> {
                val perPc = parsedPrice / 6.0
                Pair("pc", perPc)
            }
            u in listOf("২৫০ গ্রাম", "250g", "250 gm", "১ পোয়া", "১ পোয়া", "powa", "পোয়া", "পোয়া") -> {
                val perKg = parsedPrice * 4.0
                Pair("kg", perKg)
            }
            u in listOf("আধা কেজি", "500g", "500 gm", "half kg", "0.5 kg") -> {
                val perKg = parsedPrice * 2.0
                Pair("kg", perKg)
            }
            u in listOf("মণ", "mon", "maund", "৪০ কেজি", "40 kg") -> {
                val perKg = parsedPrice / 40.0
                Pair("kg", perKg)
            }
            u in listOf("সের", "seer", "sher") -> {
                val perKg = parsedPrice / 0.9331
                Pair("kg", perKg)
            }
            u in listOf("kg", "কেজি", "kilogram", "কেজিতে") -> {
                Pair("kg", parsedPrice)
            }
            u in listOf("liter", "লিটার", "ltr") -> {
                Pair("liter", parsedPrice)
            }
            else -> Pair(unit, parsedPrice)
        }
    }

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
                        Text("Crowdsourced Price Reporter", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                        Text("Decentralized spot-price intelligence", color = PricePulseColors.Muted, fontSize = 12.sp)
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
                text = "Manual spot reports are ingested with Tier 4 confidence dampening (0.60) " +
                       "to prevent statistical baseline contamination before automated cross-validation.",
                color = PricePulseColors.Muted,
                fontSize = 13.sp,
                lineHeight = 18.sp,
            )

            Spacer(Modifier.height(16.dp))

            OutlinedTextField(
                value = commodityId,
                onValueChange = { commodityId = it; formError = "" },
                label = { Text("Commodity ID") },
                placeholder = { Text("e.g. 1 (Onion), 2 (Potato), 5 (Beef)") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Spacer(Modifier.height(12.dp))

            OutlinedTextField(
                value = marketName,
                onValueChange = { marketName = it; formError = "" },
                label = { Text("Market / Bazaar Name") },
                placeholder = { Text("e.g. Karwan Bazar, Khatunganj, New Market") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Spacer(Modifier.height(12.dp))

            OutlinedTextField(
                value = district,
                onValueChange = { district = it },
                label = { Text("District (optional)") },
                placeholder = { Text("e.g. Dhaka, Chittagong, Sylhet") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Spacer(Modifier.height(12.dp))

            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedTextField(
                    value = price,
                    onValueChange = { price = it; formError = "" },
                    label = { Text("Raw Price (BDT)") },
                    placeholder = { Text("e.g. 52.0") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    modifier = Modifier.weight(1.5f),
                    singleLine = true,
                )

                OutlinedTextField(
                    value = unit,
                    onValueChange = { unit = it },
                    label = { Text("Unit") },
                    placeholder = { Text("kg / হালি / ডজন") },
                    modifier = Modifier.weight(1f),
                    singleLine = true,
                )
            }

            // Real-time metric conversion preview card
            if (unitPreview != null) {
                Spacer(Modifier.height(12.dp))
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(12.dp))
                        .background(PricePulseColors.Emerald.copy(alpha = 0.12f))
                        .padding(horizontal = 14.dp, vertical = 10.dp)
                ) {
                    Column {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                text = "⚡ Metric Normalization Preview",
                                color = PricePulseColors.Emerald,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold,
                            )
                        }
                        Spacer(Modifier.height(4.dp))
                        Text(
                            text = "Normalized Canonical Price: BDT ${String.format("%.2f", unitPreview.second)} / ${unitPreview.first}",
                            color = Color.White,
                            fontSize = 14.sp,
                            fontWeight = FontWeight.SemiBold,
                        )
                        Text(
                            text = "Input: ৳$price / $unit",
                            color = PricePulseColors.Muted,
                            fontSize = 11.sp,
                        )
                    }
                }
            }

            Spacer(Modifier.height(12.dp))

            OutlinedTextField(
                value = note,
                onValueChange = { note = it },
                label = { Text("Field Notes / Vendor Context (optional)") },
                placeholder = { Text("Observed at stall #14, wholesale batch price verified.") },
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
                colors = ButtonDefaults.buttonColors(containerColor = PricePulseColors.EmeraldDark),
                enabled = reportState !is UiState.Loading,
            ) {
                if (reportState is UiState.Loading) {
                    CircularProgressIndicator(color = MaterialTheme.colorScheme.onPrimary, strokeWidth = 2.dp)
                } else {
                    Text("Submit Verified Price Report", fontWeight = FontWeight.Bold, color = Color.White)
                }
            }

            Spacer(Modifier.height(40.dp))
        }
    }
}
