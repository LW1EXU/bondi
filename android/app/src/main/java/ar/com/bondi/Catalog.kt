package ar.com.bondi

import java.text.Normalizer

data class BusLine(val id: String, val name: String, val kind: String)

object Catalog {
    val lines = listOf("506", "518", "520", "561", "Este", "Oeste", "Norte", "Sur")
        .map { BusLine(it.lowercase(), it, "Comunal") } +
        listOf("273", "275", "214", "307", "202", "215", "418", "414", "129", "195")
        .map { BusLine(it, it, "Provincial") } +
        BusLine("unlp", "Rondín Universitario UNLP", "Especial")

    private fun normalize(value: String): String = Normalizer.normalize(value, Normalizer.Form.NFD)
        .replace(Regex("\\p{M}+"), "").lowercase().trim()

    fun search(query: String): List<BusLine> {
        val needle = normalize(query)
        return lines.filter { normalize(it.name + " " + it.kind).contains(needle) }
    }
}
