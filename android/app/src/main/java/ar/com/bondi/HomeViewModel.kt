package ar.com.bondi

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

data class HomeState(val query: String = "", val onlyFavorites: Boolean = false,
                     val favorites: Set<String> = emptySet(), val selected: BusLine? = null)

class HomeViewModel(application: Application) : AndroidViewModel(application) {
    private val preferences = application.getSharedPreferences("bondi-favorites", 0)
    private val mutable = MutableStateFlow(HomeState(favorites = preferences.getStringSet("lines", emptySet())!!.toSet()))
    val state = mutable.asStateFlow()
    fun query(value: String) { mutable.value = mutable.value.copy(query = value) }
    fun filter(value: Boolean) { mutable.value = mutable.value.copy(onlyFavorites = value) }
    fun select(value: BusLine?) { mutable.value = mutable.value.copy(selected = value) }
    fun favorite(id: String) {
        val current = mutable.value.favorites
        val updated = if (id in current) current - id else current + id
        preferences.edit().putStringSet("lines", updated).apply()
        mutable.value = mutable.value.copy(favorites = updated)
    }
}
