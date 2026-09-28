package com.pricepulse.bd.ui.screens

import android.widget.Toast
import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.ShoppingCart
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pricepulse.bd.data.local.SavedBasketEntity
import com.pricepulse.bd.data.local.SavedBasketItemEntity
import com.pricepulse.bd.data.repository.OfflinePriceRepository
import com.pricepulse.bd.ui.theme.*
import kotlinx.coroutines.launch

/**
 * UI model representing an active item in the consumer shopping basket.
 */
data class BasketUiItem(
    val commodityId: Int,
    val canonicalName: String,
    val banglaName: String,
    val quantity: Double,
    val unit: String,
    val retailPricePerUnit: Double,
    val wholesalePricePerUnit: Double,
    val onlinePricePerUnit: Double
)

/**
 * Commercial-grade Consumer Bazaar Basket Screen.
 * Provides preset basket quick-loads, active item quantity adjustment, 3-channel cost calculation,
 * and offline Room database persistence.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BasketScreen(
    offlineRepository: OfflinePriceRepository? = null,
    onNavigateBack: () -> Unit = {}
) {
    val context = LocalContext.current
    val repository = remember { offlineRepository ?: OfflinePriceRepository(context) }
    val coroutineScope = rememberCoroutineScope()

    // Room DB reactive saved baskets
    val savedBaskets by repository.savedBaskets.collectAsState(initial = emptyList())

    // Active in-memory shopping basket items
    var activeItems by remember {
        mutableStateOf(
            listOf(
                BasketUiItem(1, "Rice (Miniket)", "মিনিকেট চাল", 5.0, "কেজি", 82.0, 70.0, 88.0),
                BasketUiItem(8, "Soybean Oil (Bottled)", "সয়াবিন তেল", 2.0, "লিটার", 167.0, 155.0, 172.0),
                BasketUiItem(2, "Onion (Local)", "দেশি পেঁয়াজ", 2.0, "কেজি", 105.0, 88.0, 115.0),
                BasketUiItem(3, "Potato (Diamond)", "ডায়মন্ড আলু", 3.0, "কেজি", 55.0, 42.0, 60.0),
                BasketUiItem(12, "Farm Eggs (Brown)", "ফার্মের ডিম", 3.0, "হালি", 52.0, 46.0, 56.0)
            )
        )
    }

    var showSaveDialog by remember { mutableStateOf(false) }
    var newBasketName by remember { mutableStateOf("") }

    // 3-Channel Totals Calculation
    val retailTotal = activeItems.sumOf { it.retailPricePerUnit * it.quantity }
    val wholesaleTotal = activeItems.sumOf { it.wholesalePricePerUnit * it.quantity }
    val onlineTotal = activeItems.sumOf { it.onlinePricePerUnit * it.quantity }
    val wholesaleSavings = (retailTotal - wholesaleTotal).coerceAtLeast(0.0)
    val wholesaleSavingsPct = if (retailTotal > 0) (wholesaleSavings / retailTotal) * 100.0 else 0.0

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            Text(
                                text = "বাজার বাস্কেট",
                                color = TextPrimary,
                                fontWeight = FontWeight.Bold,
                                fontSize = 18.sp
                            )
                            Surface(
                                shape = RoundedCornerShape(4.dp),
                                color = EmeraldPrimary.copy(alpha = 0.2f),
                                border = androidx.compose.foundation.BorderStroke(1.dp, EmeraldPrimary.copy(alpha = 0.4f))
                            ) {
                                Text(
                                    text = "3-CHANNEL OPTIMIZER",
                                    color = EmeraldLight,
                                    fontSize = 9.sp,
                                    fontWeight = FontWeight.SemiBold,
                                    modifier = Modifier.padding(horizontal = 5.dp, vertical = 2.dp)
                                )
                            }
                        }
                        Text(
                            text = "খুচরা, পাইকারি ও অনলাইন মূল্য তুলনা ও সাশ্রয়",
                            color = TextSecondary,
                            fontSize = 11.sp
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = DarkSlateBackground),
                actions = {
                    IconButton(onClick = { showSaveDialog = true }) {
                        Icon(Icons.Default.Add, contentDescription = "Save Basket", tint = EmeraldLight)
                    }
                }
            )
        },
        containerColor = DarkSlateBackground
    ) { innerPadding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // 1. Preset Quick-Select Chips
            item {
                Text(
                    text = "দ্রুত বাস্কেট প্রিসেট (Quick Presets)",
                    color = TextSecondary,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.padding(bottom = 6.dp)
                )
                Row(
                    modifier = Modifier.horizontalScroll(rememberScrollState()),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    PresetChip(title = "সাপ্তাহিক বাজার (Weekly)", isSelected = activeItems.size >= 5) {
                        activeItems = listOf(
                            BasketUiItem(1, "Rice (Miniket)", "মিনিকেট চাল", 5.0, "কেজি", 82.0, 70.0, 88.0),
                            BasketUiItem(8, "Soybean Oil (Bottled)", "সয়াবিন তেল", 2.0, "লিটার", 167.0, 155.0, 172.0),
                            BasketUiItem(2, "Onion (Local)", "দেশি পেঁয়াজ", 2.0, "কেজি", 105.0, 88.0, 115.0),
                            BasketUiItem(3, "Potato (Diamond)", "ডায়মন্ড আলু", 3.0, "কেজি", 55.0, 42.0, 60.0),
                            BasketUiItem(12, "Farm Eggs (Brown)", "ফার্মের ডিম", 3.0, "হালি", 52.0, 46.0, 56.0)
                        )
                    }
                    PresetChip(title = "ব্যাচেলর বাস্কেট (Fast)", isSelected = false) {
                        activeItems = listOf(
                            BasketUiItem(12, "Farm Eggs (Brown)", "ফার্মের ডিম", 2.0, "হালি", 52.0, 46.0, 56.0),
                            BasketUiItem(3, "Potato (Diamond)", "ডায়মন্ড আলু", 1.0, "কেজি", 55.0, 42.0, 60.0),
                            BasketUiItem(2, "Onion (Local)", "দেশি পেঁয়াজ", 1.0, "কেজি", 105.0, 88.0, 115.0),
                            BasketUiItem(8, "Soybean Oil (Bottled)", "সয়াবিন তেল", 1.0, "লিটার", 167.0, 155.0, 172.0)
                        )
                    }
                    PresetChip(title = "উইকেন্ড ফিস্ট (Feast)", isSelected = false) {
                        activeItems = listOf(
                            BasketUiItem(14, "Beef", "গরুর মাংস", 2.0, "কেজি", 750.0, 710.0, 780.0),
                            BasketUiItem(2, "Onion (Local)", "দেশি পেঁয়াজ", 2.0, "কেজি", 105.0, 88.0, 115.0),
                            BasketUiItem(9, "Mustard Oil", "সরিষার তেল", 1.0, "লিটার", 260.0, 240.0, 275.0),
                            BasketUiItem(1, "Rice (Miniket)", "মিনিকেট চাল", 3.0, "কেজি", 82.0, 70.0, 88.0)
                        )
                    }
                }
            }

            // 2. Three-Channel Cost Overview Hero Card
            item {
                Card(
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = SlateSurface),
                    border = androidx.compose.foundation.BorderStroke(1.dp, SlateBorder.copy(alpha = 0.5f)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column {
                                Text(
                                    text = "কাঁচাবাজার মোট খরচ (Retail Baseline)",
                                    color = TextSecondary,
                                    fontSize = 11.sp
                                )
                                Text(
                                    text = "৳ ${"%.2f".format(retailTotal)}",
                                    color = TextPrimary,
                                    fontSize = 24.sp,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                            if (wholesaleSavings > 0) {
                                Surface(
                                    shape = RoundedCornerShape(8.dp),
                                    color = EmeraldPrimary.copy(alpha = 0.2f),
                                    border = androidx.compose.foundation.BorderStroke(1.dp, EmeraldPrimary.copy(alpha = 0.4f))
                                ) {
                                    Text(
                                        text = "সাশ্রয় ৳${"%.0f".format(wholesaleSavings)} (${"%.1f".format(wholesaleSavingsPct)}%)",
                                        color = EmeraldLight,
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.Bold,
                                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                                    )
                                }
                            }
                        }

                        Spacer(modifier = Modifier.height(14.dp))
                        Divider(color = SlateBorder.copy(alpha = 0.4f))
                        Spacer(modifier = Modifier.height(14.dp))

                        // Three channels side-by-side
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            ChannelCostColumn(
                                title = "পাইকারি বাজার",
                                subtitle = "Wholesale Hub",
                                total = wholesaleTotal,
                                color = WholesaleBlue,
                                badgeText = "সেরা মূল্য"
                            )
                            ChannelCostColumn(
                                title = "কাঁচাবাজার",
                                subtitle = "Local Wet Market",
                                total = retailTotal,
                                color = RetailGreen,
                                badgeText = "বেসলাইন"
                            )
                            ChannelCostColumn(
                                title = "অনলাইন শপ",
                                subtitle = "Chaldal / E-com",
                                total = onlineTotal,
                                color = OnlinePurple,
                                badgeText = "কনভিয়েন্স"
                            )
                        }
                    }
                }
            }

            // 3. Active Items Header
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "বাস্কেট পণ্য তালিকা (${activeItems.size}টি আইটেম)",
                        color = TextPrimary,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold
                    )
                    TextButton(onClick = { activeItems = emptyList() }) {
                        Text(text = "সব মুছুন", color = RoseCritical, fontSize = 11.sp)
                    }
                }
            }

            // 4. Active Basket Items
            if (activeItems.isEmpty()) {
                item {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 32.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Icon(
                                imageVector = Icons.Default.ShoppingCart,
                                contentDescription = null,
                                tint = TextMuted,
                                modifier = Modifier.size(48.dp)
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(text = "বাস্কেট খালি। উপরের প্রিসেট থেকে পণ্য যোগ করুন।", color = TextMuted, fontSize = 12.sp)
                        }
                    }
                }
            } else {
                items(activeItems) { item ->
                    BasketItemCard(
                        item = item,
                        onQuantityChange = { delta ->
                            val newQty = (item.quantity + delta).coerceAtLeast(1.0)
                            activeItems = activeItems.map { if (it.commodityId == item.commodityId) it.copy(quantity = newQty) else it }
                        },
                        onDelete = {
                            activeItems = activeItems.filterNot { it.commodityId == item.commodityId }
                        }
                    )
                }
            }

            // 5. Saved Baskets Section (from Room DB)
            item {
                Spacer(modifier = Modifier.height(8.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "সংরক্ষিত বাস্কেট (Offline Room DB)",
                        color = TextPrimary,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "${savedBaskets.size}টি সংরক্ষিত",
                        color = TextMuted,
                        fontSize = 11.sp
                    )
                }
            }

            if (savedBaskets.isEmpty()) {
                item {
                    Card(
                        shape = RoundedCornerShape(12.dp),
                        colors = CardDefaults.cardColors(containerColor = SlateSurface.copy(alpha = 0.5f)),
                        border = androidx.compose.foundation.BorderStroke(1.dp, SlateBorder.copy(alpha = 0.3f)),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Row(
                            modifier = Modifier.padding(14.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(10.dp)
                        ) {
                            Icon(Icons.Default.Info, contentDescription = null, tint = TextMuted, modifier = Modifier.size(20.dp))
                            Text(
                                text = "এখনও কোনো বাস্কেট সংরক্ষণ করা হয়নি। উপরে '+' বাটনে চাপ দিয়ে আপনার বাস্কেট সেভ করুন।",
                                color = TextSecondary,
                                fontSize = 11.sp,
                                leadingIcon = null
                            )
                        }
                    }
                }
            } else {
                items(savedBaskets) { saved ->
                    SavedBasketRow(
                        basket = saved,
                        onLoad = {
                            coroutineScope.launch {
                                Toast.makeText(context, "'${saved.name}' বাস্কেট লোড করা হয়েছে", Toast.LENGTH_SHORT).show()
                            }
                        },
                        onDelete = {
                            coroutineScope.launch {
                                repository.deleteBasketLocally(saved.id)
                                Toast.makeText(context, "বাস্কেট মুছে ফেলা হয়েছে", Toast.LENGTH_SHORT).show()
                            }
                        }
                    )
                }
            }

            item {
                Spacer(modifier = Modifier.height(24.dp))
            }
        }
    }

    // Save Basket Dialog
    if (showSaveDialog) {
        AlertDialog(
            onDismissRequest = { showSaveDialog = false },
            title = { Text(text = "বাস্কেট সংরক্ষণ করুন", color = TextPrimary, fontSize = 16.sp, fontWeight = FontWeight.Bold) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(text = "আপনার ফোনের অফলাইন স্টোরেজে বর্তমান বাস্কেট সেভ করুন:", color = TextSecondary, fontSize = 12.sp)
                    OutlinedTextField(
                        value = newBasketName,
                        onValueChange = { newBasketName = it },
                        placeholder = { Text("বাস্কেটের নাম (যেমন: আমার সাপ্তাহিক বাজার)", fontSize = 12.sp) },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        val name = newBasketName.ifBlank { "আমার বাজার ${System.currentTimeMillis() % 1000}" }
                        coroutineScope.launch {
                            val itemsToSave = activeItems.map {
                                SavedBasketItemEntity(
                                    basketId = 0,
                                    commodityId = it.commodityId,
                                    quantity = it.quantity,
                                    unit = it.unit
                                )
                            }
                            repository.saveBasketLocally(name = name, banglaName = name, description = "Android Room Saved Basket", items = itemsToSave)
                            showSaveDialog = false
                            newBasketName = ""
                            Toast.makeText(context, "বাস্কেট সফলভাবে সেভ হয়েছে!", Toast.LENGTH_SHORT).show()
                        }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = EmeraldPrimary)
                ) {
                    Text("সংরক্ষণ করুন")
                }
            },
            dismissButton = {
                TextButton(onClick = { showSaveDialog = false }) {
                    Text("বাতিল", color = TextSecondary)
                }
            },
            containerColor = SlateSurface
        )
    }
}

@Composable
private fun PresetChip(title: String, isSelected: Boolean, onClick: () -> Unit) {
    Surface(
        shape = RoundedCornerShape(20.dp),
        color = if (isSelected) EmeraldPrimary.copy(alpha = 0.2f) else SlateSurface,
        border = androidx.compose.foundation.BorderStroke(
            1.dp,
            if (isSelected) EmeraldPrimary else SlateBorder.copy(alpha = 0.6f)
        ),
        modifier = Modifier.clickable { onClick() }
    ) {
        Text(
            text = title,
            color = if (isSelected) EmeraldLight else TextSecondary,
            fontSize = 11.sp,
            fontWeight = FontWeight.Medium,
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp)
        )
    }
}

@Composable
private fun ChannelCostColumn(
    title: String,
    subtitle: String,
    total: Double,
    color: Color,
    badgeText: String
) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(text = title, color = TextPrimary, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
        Text(text = subtitle, color = TextMuted, fontSize = 9.sp)
        Spacer(modifier = Modifier.height(4.dp))
        Text(text = "৳ ${"%.0f".format(total)}", color = color, fontSize = 15.sp, fontWeight = FontWeight.Bold)
        Spacer(modifier = Modifier.height(2.dp))
        Surface(
            shape = RoundedCornerShape(4.dp),
            color = color.copy(alpha = 0.15f)
        ) {
            Text(
                text = badgeText,
                color = color,
                fontSize = 8.sp,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(horizontal = 4.dp, vertical = 1.dp)
            )
        }
    }
}

@Composable
private fun BasketItemCard(
    item: BasketUiItem,
    onQuantityChange: (Double) -> Unit,
    onDelete: () -> Unit
) {
    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = SlateSurface),
        border = androidx.compose.foundation.BorderStroke(1.dp, SlateBorder.copy(alpha = 0.4f)),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = item.banglaName,
                    color = TextPrimary,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "${item.canonicalName} • ৳${"%.0f".format(item.retailPricePerUnit)}/${item.unit}",
                    color = TextMuted,
                    fontSize = 10.sp
                )
                Text(
                    text = "মোট: ৳${"%.1f".format(item.retailPricePerUnit * item.quantity)}",
                    color = RetailGreen,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.padding(top = 2.dp)
                )
            }

            // Quantity stepper & delete
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Surface(
                    shape = CircleShape,
                    color = SlateSurfaceVariant,
                    modifier = Modifier
                        .size(28.dp)
                        .clickable { onQuantityChange(-1.0) }
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Text(text = "−", color = TextPrimary, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    }
                }

                Text(
                    text = "${"%.0f".format(item.quantity)} ${item.unit}",
                    color = TextPrimary,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.SemiBold
                )

                Surface(
                    shape = CircleShape,
                    color = SlateSurfaceVariant,
                    modifier = Modifier
                        .size(28.dp)
                        .clickable { onQuantityChange(1.0) }
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Text(text = "+", color = TextPrimary, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    }
                }

                Spacer(modifier = Modifier.width(4.dp))
                IconButton(onClick = onDelete, modifier = Modifier.size(28.dp)) {
                    Icon(Icons.Default.Close, contentDescription = "Remove", tint = TextMuted, modifier = Modifier.size(16.dp))
                }
            }
        }
    }
}

@Composable
private fun SavedBasketRow(
    basket: SavedBasketEntity,
    onLoad: () -> Unit,
    onDelete: () -> Unit
) {
    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = SlateSurface),
        border = androidx.compose.foundation.BorderStroke(1.dp, SlateBorder.copy(alpha = 0.4f)),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = basket.name,
                    color = TextPrimary,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                Text(
                    text = basket.description.ifBlank { "সংরক্ষিত পারিবারিক বাস্কেট" },
                    color = TextSecondary,
                    fontSize = 10.sp
                )
            }

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(
                    onClick = onLoad,
                    colors = ButtonDefaults.buttonColors(containerColor = EmeraldPrimary.copy(alpha = 0.2f)),
                    shape = RoundedCornerShape(8.dp),
                    contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp),
                    modifier = Modifier.height(30.dp)
                ) {
                    Text(text = "লোড", color = EmeraldLight, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                }

                IconButton(onClick = onDelete, modifier = Modifier.size(30.dp)) {
                    Icon(Icons.Default.Delete, contentDescription = "Delete", tint = RoseCritical, modifier = Modifier.size(16.dp))
                }
            }
        }
    }
}
