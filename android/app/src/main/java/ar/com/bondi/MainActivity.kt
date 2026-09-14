package ar.com.bondi

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(colorScheme = lightColorScheme(primary = Color(0xFF18382B),
                background = Color(0xFFF4F5EF), surface = Color(0xFFF4F5EF),
                primaryContainer = Color(0xFFE7ECCF))) {
                val model: HomeViewModel = viewModel()
                val state by model.state.collectAsStateWithLifecycle()
                BackHandler(state.selected != null) { model.select(null) }
                Surface(Modifier.fillMaxSize()) {
                    val selected = state.selected
                    if (selected == null) HomeScreen(state, model)
                    else LineDetailScreen(selected, selected.id in state.favorites,
                        { model.favorite(selected.id) }, { model.select(null) })
                }
            }
        }
    }
}

@Composable
fun HomeScreen(state: HomeState, model: HomeViewModel) {
    val visible = Catalog.search(state.query).filter { !state.onlyFavorites || it.id in state.favorites }
    LazyColumn(Modifier.fillMaxSize().safeDrawingPadding(), contentPadding = PaddingValues(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Text("bondi ↗", fontSize = 42.sp, fontWeight = FontWeight.Black)
            Text("LA PLATA Y ALREDEDORES", style = MaterialTheme.typography.labelMedium)
            Spacer(Modifier.height(24.dp))
            Text("Tu próximo viaje\nempieza acá.", style = MaterialTheme.typography.headlineLarge, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(16.dp))
            PreviewNotice()
        }
        item {
            OutlinedTextField(state.query, model::query, Modifier.fillMaxWidth(),
                label = { Text("Buscar línea o tipo") }, singleLine = true)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilterChip(!state.onlyFavorites, { model.filter(false) }, { Text("Todas") })
                FilterChip(state.onlyFavorites, { model.filter(true) }, { Text("Favoritos") })
            }
            Text("${visible.size} líneas", style = MaterialTheme.typography.labelLarge)
        }
        if (visible.isEmpty()) item {
            Text(if (state.onlyFavorites) "No hay favoritos que coincidan. Guardá una línea con la estrella."
                 else "No encontramos líneas con ese nombre.")
        }
        items(visible, key = { it.id }) { line ->
            Card(onClick = { model.select(line) }, modifier = Modifier.fillMaxWidth()) {
                Row(Modifier.padding(18.dp).fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Column(Modifier.weight(1f)) {
                        Text(line.name, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                        Text(line.kind, style = MaterialTheme.typography.bodyMedium)
                    }
                    TextButton(onClick = { model.favorite(line.id) }) {
                        Text(if (line.id in state.favorites) "★ Quitar" else "☆ Guardar")
                    }
                }
            }
        }
        item { Text("Catálogo disponible sin conexión · v0.1.0-alpha.1", style = MaterialTheme.typography.bodySmall) }
    }
}

@Composable
fun PreviewNotice() {
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)) {
        Text("Versión preliminar. Catálogo por verificar: todavía no hay recorridos, horarios ni arribos en tiempo real.",
            modifier = Modifier.padding(16.dp), style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
fun LineDetailScreen(line: BusLine, favorite: Boolean, onFavorite: () -> Unit, onBack: () -> Unit) {
    LazyColumn(Modifier.fillMaxSize().safeDrawingPadding(), contentPadding = PaddingValues(24.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp)) {
        item { TextButton(onClick = onBack) { Text("← Todas las líneas") } }
        item {
            Text(line.name, style = MaterialTheme.typography.headlineLarge, fontWeight = FontWeight.Bold)
            Text(line.kind)
        }
        item { Button(onClick = onFavorite) { Text(if (favorite) "Quitar de favoritos" else "Guardar en favoritos") } }
        item { PreviewNotice() }
        item {
            Text("Ramales y paradas", style = MaterialTheme.typography.titleLarge)
            Text("Estamos preparando la información oficial de esta línea. La empresa, sus variantes y la vigencia del servicio aún requieren validación.")
        }
        item {
            Text("Tus favoritos quedan en este dispositivo", style = MaterialTheme.typography.titleMedium)
            Text("Esta versión no requiere cuenta, ubicación ni conexión a Internet.")
        }
    }
}
