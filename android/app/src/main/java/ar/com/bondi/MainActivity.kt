package ar.com.bondi

import android.content.Intent
import android.net.Uri
import android.nfc.NfcAdapter
import android.os.Bundle
import android.provider.Settings
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
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
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(
                colorScheme = lightColorScheme(
                    primary = Color(0xFF18382B),
                    primaryContainer = Color(0xFFE7ECCF),
                    secondary = Color(0xFF2E7D32),
                    surface = Color(0xFFF7F8F3),
                    background = Color(0xFFF4F5EF)
                )
            ) {
                val model: HomeViewModel = viewModel()
                val state by model.state.collectAsStateWithLifecycle()

                BackHandler(state.selected != null || state.selectedStop != null) {
                    if (state.selected != null) model.select(null)
                    else if (state.selectedStop != null) model.selectStop(null)
                }

                Scaffold(
                    bottomBar = {
                        NavigationBar(containerColor = Color.White) {
                            NavigationBarItem(
                                selected = state.activeTab == "lines",
                                onClick = { model.setTab("lines") },
                                label = { Text("Líneas") },
                                icon = { Text("🚌", fontSize = 18.sp) }
                            )
                            NavigationBarItem(
                                selected = state.activeTab == "stops",
                                onClick = { model.setTab("stops") },
                                label = { Text("Paradas") },
                                icon = { Text("🚏", fontSize = 18.sp) }
                            )
                            NavigationBarItem(
                                selected = state.activeTab == "sube",
                                onClick = { model.setTab("sube") },
                                label = { Text("SUBE / NFC") },
                                icon = { Text("💳", fontSize = 18.sp) }
                            )
                            NavigationBarItem(
                                selected = state.activeTab == "alerts",
                                onClick = { model.setTab("alerts") },
                                label = { Text("Alertas") },
                                icon = { Text("⚠️", fontSize = 18.sp) }
                            )
                        }
                    }
                ) { innerPadding ->
                    Surface(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(innerPadding)
                    ) {
                        when {
                            state.selected != null -> {
                                LineDetailScreen(
                                    line = state.selected!!,
                                    favorite = state.selected!!.id in state.favorites,
                                    onFavorite = { model.favorite(state.selected!!.id) },
                                    onBack = { model.select(null) }
                                )
                            }
                            state.selectedStop != null -> {
                                StopDetailScreen(
                                    stop = state.selectedStop!!,
                                    onBack = { model.selectStop(null) },
                                    onSelectLine = { lineId ->
                                        val l = Catalog.lines.find { it.id == lineId }
                                        if (l != null) {
                                            model.selectStop(null)
                                            model.select(l)
                                        }
                                    }
                                )
                            }
                            else -> {
                                when (state.activeTab) {
                                    "lines" -> LinesTabScreen(state, model)
                                    "stops" -> StopsTabScreen(state, model)
                                    "sube" -> SubeTabScreen(
                                        state = state,
                                        onBalanceChange = model::updateSubeBalance,
                                        onLaunchNfc = { launchNfcAction() }
                                    )
                                    "alerts" -> AlertsTabScreen()
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    private fun launchNfcAction() {
        val nfcAdapter = NfcAdapter.getDefaultAdapter(this)
        if (nfcAdapter == null) {
            Toast.makeText(this, "Este dispositivo no cuenta con hardware NFC", Toast.LENGTH_LONG).show()
            return
        }
        if (!nfcAdapter.isEnabled) {
            Toast.makeText(this, "Por favor, activá el NFC en ajustes", Toast.LENGTH_LONG).show()
            startActivity(Intent(Settings.ACTION_NFC_SETTINGS))
            return
        }

        // Try opening SUBE official app if installed, or dispatch general NFC prompt
        val pm = packageManager
        val subeIntent = pm.getLaunchIntentForPackage("com.sube.app")
        if (subeIntent != null) {
            startActivity(subeIntent)
        } else {
            Toast.makeText(this, "Acercá tu tarjeta SUBE a la parte trasera del teléfono", Toast.LENGTH_SHORT).show()
            val playStoreIntent = Intent(Intent.ACTION_VIEW, Uri.parse("market://details?id=com.sube.app"))
            try {
                startActivity(playStoreIntent)
            } catch (e: Exception) {
                // Ignore if Play Store is unavailable
            }
        }
    }
}

@Composable
fun LinesTabScreen(state: HomeState, model: HomeViewModel) {
    val searchResults = Catalog.searchPlatense(state.query)
    val visible = searchResults.filter { line ->
        val matchesFav = !state.onlyFavorites || line.id in state.favorites
        val matchesType = when (state.typeFilter) {
            "comunal" -> line.kind.equals("comunal", ignoreCase = true)
            "provincial" -> line.kind.equals("provincial", ignoreCase = true)
            else -> true
        }
        matchesFav && matchesType
    }

    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Text("bondi ↗", fontSize = 38.sp, fontWeight = FontWeight.Black, color = MaterialTheme.colorScheme.primary)
            Text("GRAN LA PLATA · TRANSPORTE PÚBLICO", style = MaterialTheme.typography.labelMedium)
            Spacer(Modifier.height(12.dp))
        }

        item {
            OutlinedTextField(
                value = state.query,
                onValueChange = model::query,
                modifier = Modifier.fillMaxWidth(),
                placeholder = { Text("Línea, calle o diagonal (ej: 7 y 50, Diag 74)") },
                label = { Text("Buscar en La Plata") },
                singleLine = true,
                shape = RoundedCornerShape(12.dp)
            )
            Spacer(Modifier.height(8.dp))

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilterChip(
                    selected = state.typeFilter == "all" && !state.onlyFavorites,
                    onClick = {
                        model.filter(false)
                        model.setTypeFilter("all")
                    },
                    label = { Text("Todas") }
                )
                FilterChip(
                    selected = state.onlyFavorites,
                    onClick = { model.filter(!state.onlyFavorites) },
                    label = { Text("★ Favoritos") }
                )
                FilterChip(
                    selected = state.typeFilter == "comunal",
                    onClick = {
                        model.filter(false)
                        model.setTypeFilter(if (state.typeFilter == "comunal") "all" else "comunal")
                    },
                    label = { Text("Comunales") }
                )
                FilterChip(
                    selected = state.typeFilter == "provincial",
                    onClick = {
                        model.filter(false)
                        model.setTypeFilter(if (state.typeFilter == "provincial") "all" else "provincial")
                    },
                    label = { Text("Provinciales") }
                )
            }
            Text("${visible.size} líneas disponibles (100% offline)", style = MaterialTheme.typography.labelSmall)
        }

        if (visible.isEmpty()) {
            item {
                Card(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
                    Text(
                        "No se encontraron líneas para '${state.query}'. Probá con el número de línea (ej: 506, Este, 273) o una esquina platense (ej: 7 y 50).",
                        modifier = Modifier.padding(16.dp),
                        style = MaterialTheme.typography.bodyMedium
                    )
                }
            }
        }

        items(visible, key = { it.id }) { line ->
            Card(
                onClick = { model.select(line) },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White)
            ) {
                Row(
                    Modifier
                        .padding(16.dp)
                        .fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(Modifier.weight(1f)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(line.name, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                            Spacer(Modifier.width(8.dp))
                            Surface(
                                shape = RoundedCornerShape(6.dp),
                                color = MaterialTheme.colorScheme.primaryContainer
                            ) {
                                Text(
                                    line.kind,
                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                                    style = MaterialTheme.typography.labelSmall,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }
                        if (line.headsign.isNotEmpty()) {
                            Text(line.headsign, style = MaterialTheme.typography.bodyMedium, color = Color.Gray)
                        }
                        Text("Frecuencia: cada ${line.frequencyMin} min", style = MaterialTheme.typography.labelSmall)
                    }
                    IconButton(onClick = { model.favorite(line.id) }) {
                        Text(if (line.id in state.favorites) "★" else "☆", fontSize = 22.sp, color = MaterialTheme.colorScheme.primary)
                    }
                }
            }
        }
    }
}

@Composable
fun StopsTabScreen(state: HomeState, model: HomeViewModel) {
    val stopsList = remember { Catalog.stops.values.toList() }
    val filtered = remember(state.query) {
        if (state.query.isBlank()) stopsList
        else {
            val q = state.query.lowercase()
            stopsList.filter { it.name.lowercase().contains(q) || it.address.lowercase().contains(q) }
        }
    }

    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Text("Paradas de La Plata", fontSize = 28.sp, fontWeight = FontWeight.Bold)
            Text("Consultá arribos y tiempos de espera en vivo", style = MaterialTheme.typography.bodySmall)
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(
                value = state.query,
                onValueChange = model::query,
                modifier = Modifier.fillMaxWidth(),
                placeholder = { Text("Buscar parada o calle (ej: Plaza Moreno, 1 y 44)") },
                singleLine = true,
                shape = RoundedCornerShape(12.dp)
            )
        }

        items(filtered, key = { it.id }) { stop ->
            val arrivals = remember(stop.id) { Catalog.calculateArrivals(stop.id) }
            val next = arrivals.firstOrNull()

            Card(
                onClick = { model.selectStop(stop) },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White)
            ) {
                Column(Modifier.padding(16.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(stop.name, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        if (next != null) {
                            Surface(
                                shape = RoundedCornerShape(8.dp),
                                color = MaterialTheme.colorScheme.primaryContainer
                            ) {
                                Text(
                                    text = if (next.etaSeconds <= 45) "🟢 AHORA" else "⏱️ ${next.etaMinutes} min",
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                    style = MaterialTheme.typography.labelSmall,
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.primary
                                )
                            }
                        }
                    }
                    Text(stop.address, style = MaterialTheme.typography.bodySmall, color = Color.Gray)
                    Spacer(Modifier.height(4.dp))
                    Text("Líneas con parada acá: ${arrivals.map { it.lineName }.distinct().joinToString(", ")}", style = MaterialTheme.typography.labelSmall)
                }
            }
        }
    }
}

@Composable
fun StopDetailScreen(stop: BusStop, onBack: () -> Unit, onSelectLine: (String) -> Unit) {
    val arrivals = remember(stop.id) { Catalog.calculateArrivals(stop.id) }

    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        item {
            TextButton(onClick = onBack) { Text("← Volver a paradas") }
            Text(stop.name, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
            Text("📍 ${stop.address}", style = MaterialTheme.typography.bodyMedium)
            Spacer(Modifier.height(8.dp))
            Text("Próximos micros a arribar (${arrivals.size})", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
        }

        if (arrivals.isEmpty()) {
            item {
                Text("No hay servicios programados en los próximos minutos.")
            }
        }

        items(arrivals) { arr ->
            Card(
                onClick = { onSelectLine(arr.lineId) },
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = Color.White),
                shape = RoundedCornerShape(12.dp)
            ) {
                Row(
                    modifier = Modifier.padding(16.dp).fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(Modifier.weight(1f)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("Línea ${arr.lineName}", fontWeight = FontWeight.Bold, style = MaterialTheme.typography.titleMedium)
                            Spacer(Modifier.width(8.dp))
                            Text("(${arr.scheduledTime} hs)", style = MaterialTheme.typography.bodySmall)
                        }
                        Text(arr.headsign, style = MaterialTheme.typography.bodySmall, color = Color.Gray)
                    }

                    Surface(
                        shape = RoundedCornerShape(8.dp),
                        color = MaterialTheme.colorScheme.primaryContainer
                    ) {
                        Text(
                            text = if (arr.etaSeconds <= 45) "🟢 Llegando" else "en ${arr.etaMinutes} min",
                            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                            style = MaterialTheme.typography.labelMedium,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun SubeTabScreen(
    state: HomeState,
    onBalanceChange: (String) -> Unit,
    onLaunchNfc: () -> Unit
) {
    val est = state.subeEstimation

    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            Text("Saldo SUBE y Carga NFC", fontSize = 28.sp, fontWeight = FontWeight.Bold)
            Text("Calculadora orientativa de pasajes y atajo a carga contactless", style = MaterialTheme.typography.bodyMedium)
        }

        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = Color.White),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(Modifier.padding(20.dp)) {
                    Text("Ingresá tu saldo actual", style = MaterialTheme.typography.labelLarge)
                    Spacer(Modifier.height(8.dp))
                    OutlinedTextField(
                        value = state.subeBalanceInput,
                        onValueChange = onBalanceChange,
                        modifier = Modifier.fillMaxWidth(),
                        prefix = { Text("$ ") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        singleLine = true,
                        shape = RoundedCornerShape(12.dp)
                    )

                    Spacer(Modifier.height(16.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Column {
                            Text("Viajes restantes (Comunal)", style = MaterialTheme.typography.labelMedium)
                            Text(
                                "${est.tripsComunal} viajes",
                                fontSize = 26.sp,
                                fontWeight = FontWeight.Black,
                                color = MaterialTheme.colorScheme.primary
                            )
                        }
                        Column(horizontalAlignment = Alignment.End) {
                            Text("Tarifa base", style = MaterialTheme.typography.labelMedium)
                            Text("$371,13", fontSize = 18.sp, fontWeight = FontWeight.Bold)
                        }
                    }

                    Spacer(Modifier.height(12.dp))
                    HorizontalDivider()
                    Spacer(Modifier.height(12.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("Saldo negativo límite:", style = MaterialTheme.typography.bodySmall)
                        Text("-$480,00", style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.Bold)
                    }
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("Disponible total (con saldo de emergencia):", style = MaterialTheme.typography.bodySmall)
                        Text("$ ${"%.2f".format(est.remainingWithEmergency)}", style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }

        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(Modifier.padding(20.dp)) {
                    Text("📲 Atajo de Carga NFC", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    Spacer(Modifier.height(6.dp))
                    Text(
                        "Apoyá tu tarjeta SUBE en la parte trasera del teléfono para acreditar saldo pendiente o consultar el saldo físico mediante NFC.",
                        style = MaterialTheme.typography.bodyMedium
                    )
                    Spacer(Modifier.height(16.dp))
                    Button(
                        onClick = onLaunchNfc,
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Text("Activar NFC / Abrir App SUBE ↗", fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
    }
}

@Composable
fun AlertsTabScreen() {
    val alerts = Catalog.alerts

    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        item {
            Text("Alertas y Desvíos", fontSize = 28.sp, fontWeight = FontWeight.Bold)
            Text("Estado del tránsito y recorridos en Gran La Plata", style = MaterialTheme.typography.bodySmall)
        }

        items(alerts, key = { it.id }) { alert ->
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = Color.White),
                shape = RoundedCornerShape(14.dp)
            ) {
                Column(Modifier.padding(18.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Surface(
                            shape = RoundedCornerShape(6.dp),
                            color = if (alert.isDetour) Color(0xFFFFEBEE) else Color(0xFFE8F5E9)
                        ) {
                            Text(
                                text = if (alert.isDetour) "⚠️ DESVÍO" else "ℹ️ NOVEDAD",
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                style = MaterialTheme.typography.labelSmall,
                                fontWeight = FontWeight.Bold,
                                color = if (alert.isDetour) Color(0xFFC62828) else Color(0xFF2E7D32)
                            )
                        }
                        if (alert.lineName != null) {
                            Text(alert.lineName, style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.Bold)
                        }
                    }

                    Spacer(Modifier.height(8.dp))
                    Text(alert.title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    Spacer(Modifier.height(4.dp))
                    Text(alert.description, style = MaterialTheme.typography.bodyMedium, color = Color.DarkGray)
                }
            }
        }
    }
}

@Composable
fun LineDetailScreen(line: BusLine, favorite: Boolean, onFavorite: () -> Unit, onBack: () -> Unit) {
    val stops = remember(line.id) { Catalog.getStopsForLine(line.id) }

    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        item {
            TextButton(onClick = onBack) { Text("← Volver a líneas") }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(line.name, style = MaterialTheme.typography.headlineLarge, fontWeight = FontWeight.Black)
                    Text("${line.kind} · Cada ${line.frequencyMin} min", style = MaterialTheme.typography.bodyMedium)
                }
                IconButton(onClick = onFavorite) {
                    Text(if (favorite) "★" else "☆", fontSize = 28.sp, color = MaterialTheme.colorScheme.primary)
                }
            }
            if (line.headsign.isNotEmpty()) {
                Text(
                    line.headsign,
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.SemiBold,
                    color = MaterialTheme.colorScheme.primary
                )
            }
            Spacer(Modifier.height(8.dp))
            Text("Trazado y Paradas Secuenciales (${stops.size})", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
        }

        items(stops) { stop ->
            val arrivals = remember(stop.id) { Catalog.calculateArrivals(stop.id) }
            val nextBus = arrivals.firstOrNull { it.lineId == line.id } ?: arrivals.firstOrNull()

            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = Color.White),
                shape = RoundedCornerShape(12.dp)
            ) {
                Row(
                    modifier = Modifier.padding(16.dp).fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        modifier = Modifier
                            .size(24.dp)
                            .clip(CircleShape)
                            .background(MaterialTheme.colorScheme.primary),
                        contentAlignment = Alignment.Center
                    ) {
                        Text("•", color = Color.White, fontWeight = FontWeight.Bold)
                    }

                    Spacer(Modifier.width(12.dp))

                    Column(Modifier.weight(1f)) {
                        Text(stop.name, style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
                        Text(stop.address, style = MaterialTheme.typography.bodySmall, color = Color.Gray)
                    }

                    if (nextBus != null) {
                        Surface(
                            shape = RoundedCornerShape(8.dp),
                            color = MaterialTheme.colorScheme.primaryContainer
                        ) {
                            Text(
                                text = if (nextBus.etaSeconds <= 45) "🟢 Llegando" else "en ${nextBus.etaMinutes} min",
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                style = MaterialTheme.typography.labelSmall,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.primary
                            )
                        }
                    }
                }
            }
        }
    }
}
