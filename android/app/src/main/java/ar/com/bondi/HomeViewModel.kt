package ar.com.bondi

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

data class HomeState(
    val activeTab: String = "lines", // "lines", "stops", "sube", "alerts"
    val query: String = "",
    val onlyFavorites: Boolean = false,
    val typeFilter: String = "all", // "all", "comunal", "provincial", "especial"
    val favorites: Set<String> = emptySet(),
    val selected: BusLine? = null,
    val selectedStop: BusStop? = null,
    val subeBalanceInput: String = "1500.0",
    val subeEstimation: SubeEstimation = SubeEstimation.calculate(1500.0)
)

class HomeViewModel(application: Application) : AndroidViewModel(application) {
    private val dbHelper = BondiDbHelper(application)
    private val preferences = application.getSharedPreferences("bondi-favorites", 0)

    private val mutable = MutableStateFlow(
        HomeState(
            favorites = loadInitialFavorites()
        )
    )
    val state = mutable.asStateFlow()

    private fun loadInitialFavorites(): Set<String> {
        val dbFavs = try { dbHelper.getFavorites() } catch (e: Exception) { emptySet() }
        val prefFavs = preferences.getStringSet("lines", emptySet()) ?: emptySet()
        return dbFavs.ifEmpty { prefFavs }
    }

    fun setTab(tab: String) {
        mutable.value = mutable.value.copy(activeTab = tab)
    }

    fun query(value: String) {
        mutable.value = mutable.value.copy(query = value)
    }

    fun filter(value: Boolean) {
        mutable.value = mutable.value.copy(onlyFavorites = value)
    }

    fun setTypeFilter(type: String) {
        mutable.value = mutable.value.copy(typeFilter = type)
    }

    fun select(value: BusLine?) {
        mutable.value = mutable.value.copy(selected = value)
    }

    fun selectStop(value: BusStop?) {
        mutable.value = mutable.value.copy(selectedStop = value)
    }

    fun updateSubeBalance(text: String) {
        val parsed = text.toDoubleOrNull() ?: 0.0
        mutable.value = mutable.value.copy(
            subeBalanceInput = text,
            subeEstimation = SubeEstimation.calculate(parsed)
        )
    }

    fun favorite(id: String) {
        val current = mutable.value.favorites
        val isFav = id in current
        val updated = if (isFav) current - id else current + id
        try {
            dbHelper.setFavorite(id, !isFav)
        } catch (e: Exception) {
            // fallback
        }
        preferences.edit().putStringSet("lines", updated).apply()
        mutable.value = mutable.value.copy(favorites = updated)
    }
}
