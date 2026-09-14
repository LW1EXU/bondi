package ar.com.bondi

import java.text.Normalizer
import java.util.Calendar

data class BusStop(
    val id: String,
    val name: String,
    val address: String,
    val lat: Double,
    val lon: Double
)

data class NextArrival(
    val lineId: String,
    val lineName: String,
    val headsign: String,
    val scheduledTime: String,
    val etaMinutes: Int,
    val etaSeconds: Int
)

data class BusLine(
    val id: String,
    val name: String,
    val kind: String,
    val headsign: String = "",
    val stopIds: List<String> = emptyList(),
    val frequencyMin: Int = 10
)

object Catalog {
    val stops = listOf(
        BusStop("stop_plaza_moreno", "Plaza Moreno", "Calle 12 y 51", -34.9214, -57.9545),
        BusStop("stop_plaza_san_martin", "Plaza San Martín", "Calle 7 y 50", -34.9142, -57.9498),
        BusStop("stop_plaza_italia", "Plaza Italia", "Calle 7 y 44", -34.9082, -57.9576),
        BusStop("stop_estacion_tren", "Estación La Plata", "Calle 1 y 44", -34.9048, -57.9463),
        BusStop("stop_terminal_bus", "Terminal de Ómnibus", "Calle 4 y 42", -34.9031, -57.9507),
        BusStop("stop_plaza_rocha", "Plaza Rocha", "Calle 7 y 60", -34.9248, -57.9419),
        BusStop("stop_plaza_paso", "Plaza Paso", "Calle 13 y 44", -34.9155, -57.9652),
        BusStop("stop_hosp_ninos", "Hospital de Niños", "Calle 14 y 66", -34.9351, -57.9462),
        BusStop("stop_hosp_san_martin", "Hospital Policlínico San Martín", "Calle 1 y 70", -34.9221, -57.9254),
        BusStop("stop_hosp_san_juan", "Hospital San Juan de Dios", "Calle 27 y 70", -34.9427, -57.9490),
        BusStop("stop_hosp_espanol", "Hospital Español", "Calle 9 y 36", -34.9002, -57.9620),
        BusStop("stop_estadio_unico", "Estadio Diego Armando Maradona", "Av. 25 y 32", -34.9001, -57.9892),
        BusStop("stop_cementerio", "Cementerio La Plata", "Calle 31 y 72", -34.9526, -57.9622),
        BusStop("stop_los_hornos_60", "Los Hornos (Centro)", "Av. 60 y 137", -34.9548, -57.9942),
        BusStop("stop_los_hornos_66", "Los Hornos (Sur)", "Av. 66 y 143", -34.9691, -58.0062),
        BusStop("stop_san_carlos", "San Carlos", "Av. 32 y 137", -34.9282, -58.0142),
        BusStop("stop_melchor_romero", "Melchor Romero", "Av. 520 y 173", -34.9452, -58.0640),
        BusStop("stop_tolosa", "Tolosa", "Calle 7 y 528", -34.8872, -57.9732),
        BusStop("stop_rep_ninos", "República de los Niños", "Cno. Belgrano y 500", -34.8835, -57.9982),
        BusStop("stop_gonnet", "Estación Gonnet", "Cno. Centenario y 502", -34.8802, -57.9904),
        BusStop("stop_city_bell", "Estación City Bell", "Cno. Centenario y Cantilo", -34.8621, -58.0163),
        BusStop("stop_villa_elisa", "Villa Elisa", "Cno. Centenario y Arana", -34.8482, -58.0381),
        BusStop("stop_berisso_puente_roma", "Berisso - Puente Roma", "Av. Génova y 158", -34.8722, -57.8862),
        BusStop("stop_berisso_centro", "Berisso Centro", "Av. Montevideo y 11", -34.8785, -57.8761),
        BusStop("stop_berisso_los_talas", "Berisso - Los Talas", "Av. Montevideo y 30", -34.8992, -57.8480),
        BusStop("stop_ensenada_centro", "Ensenada - Plaza Belgrano", "Don Bosco y La Merced", -34.8601, -57.9102),
        BusStop("stop_ensenada_astillero", "Ensenada - Astillero", "Cestino y Río Santiago", -34.8512, -57.9021),
        BusStop("stop_villa_elvira", "Villa Elvira", "Calle 7 y 80", -34.9392, -57.9281),
        BusStop("stop_sicardi", "Parque Sicardi", "Calle 659 y 22", -34.9921, -57.8862),
        BusStop("stop_unlp_bosque", "UNLP - Exactas / Museo", "Av. 1 y 50", -34.9082, -57.9412),
        BusStop("stop_unlp_informatica", "UNLP - Informática", "Calle 120 y 52", -34.9061, -57.9302),
        BusStop("stop_unlp_medicina", "UNLP - Medicina", "Calle 60 y 120", -34.9123, -57.9242),
        BusStop("stop_rotonda_autopista", "Rotonda Autopista", "Av. 120 y 32", -34.8912, -57.9442),
        BusStop("stop_calle_1_42", "Calle 1 y Calle 42", "Calle 1 y 42", -34.9040, -57.9482)
    ).associateBy { it.id }

    val lines = listOf(
        BusLine("506", "506", "Comunal", "Los Hornos ↔ Ensenada",
            listOf("stop_los_hornos_60", "stop_cementerio", "stop_plaza_moreno", "stop_plaza_san_martin", "stop_calle_1_42", "stop_estacion_tren", "stop_ensenada_centro"), 10),
        BusLine("518", "518", "Comunal", "Aeropuerto ↔ Rep. de los Niños",
            listOf("stop_plaza_rocha", "stop_plaza_italia", "stop_tolosa", "stop_rep_ninos"), 12),
        BusLine("520", "520", "Comunal", "Parque Sicardi ↔ Estación",
            listOf("stop_sicardi", "stop_villa_elvira", "stop_los_hornos_60", "stop_plaza_rocha", "stop_plaza_san_martin", "stop_estacion_tren"), 15),
        BusLine("561", "561", "Comunal", "San Carlos ↔ Estación por Estadio Único",
            listOf("stop_san_carlos", "stop_estadio_unico", "stop_plaza_paso", "stop_plaza_moreno", "stop_estacion_tren"), 12),
        BusLine("508", "508", "Comunal", "Los Hornos ↔ Villa Elisa",
            listOf("stop_los_hornos_60", "stop_plaza_paso", "stop_estacion_tren", "stop_villa_elisa"), 15),
        BusLine("este", "Este", "Comunal", "Villa Elvira ↔ Plaza Italia",
            listOf("stop_villa_elvira", "stop_hosp_san_martin", "stop_unlp_bosque", "stop_calle_1_42", "stop_plaza_san_martin", "stop_plaza_italia"), 8),
        BusLine("oeste", "Oeste", "Comunal", "Melchor Romero ↔ Estación",
            listOf("stop_melchor_romero", "stop_san_carlos", "stop_hosp_espanol", "stop_plaza_italia", "stop_estacion_tren"), 10),
        BusLine("norte", "Norte", "Comunal", "City Bell ↔ Plaza Moreno",
            listOf("stop_city_bell", "stop_gonnet", "stop_rep_ninos", "stop_tolosa", "stop_plaza_italia", "stop_plaza_moreno"), 10),
        BusLine("sur", "Sur", "Comunal", "Los Hornos ↔ Plaza Italia por Hospitales",
            listOf("stop_los_hornos_66", "stop_hosp_san_juan", "stop_hosp_ninos", "stop_plaza_moreno", "stop_plaza_italia"), 10),
        BusLine("273", "273", "Provincial", "Villa Elisa ↔ Cementerio",
            listOf("stop_villa_elisa", "stop_city_bell", "stop_gonnet", "stop_plaza_italia", "stop_plaza_moreno", "stop_cementerio"), 8),
        BusLine("275", "275", "Provincial", "Astillero ↔ Plaza San Martín",
            listOf("stop_ensenada_astillero", "stop_ensenada_centro", "stop_calle_1_42", "stop_estacion_tren", "stop_plaza_san_martin"), 15),
        BusLine("214", "214", "Provincial", "Berisso ↔ Hosp. San Juan de Dios",
            listOf("stop_berisso_los_talas", "stop_berisso_centro", "stop_berisso_puente_roma", "stop_plaza_san_martin", "stop_hosp_ninos", "stop_hosp_san_juan"), 10),
        BusLine("307", "307", "Provincial", "Río Santiago ↔ Cementerio",
            listOf("stop_ensenada_astillero", "stop_ensenada_centro", "stop_estacion_tren", "stop_plaza_moreno", "stop_cementerio"), 10),
        BusLine("202", "202", "Provincial", "Berisso ↔ Estación La Plata",
            listOf("stop_berisso_centro", "stop_berisso_puente_roma", "stop_unlp_medicina", "stop_estacion_tren"), 12),
        BusLine("215", "215", "Provincial", "Tolosa ↔ Melchor Romero",
            listOf("stop_tolosa", "stop_estacion_tren", "stop_plaza_san_martin", "stop_san_carlos", "stop_melchor_romero"), 15),
        BusLine("418", "418", "Provincial", "Berazategui ↔ Terminal La Plata",
            listOf("stop_villa_elisa", "stop_city_bell", "stop_gonnet", "stop_terminal_bus"), 20),
        BusLine("414", "414", "Provincial", "Florencio Varela ↔ Terminal La Plata",
            listOf("stop_estacion_tren", "stop_terminal_bus"), 20),
        BusLine("129", "129", "Provincial", "Retiro ↔ Terminal por Autopista",
            listOf("stop_rotonda_autopista", "stop_terminal_bus", "stop_plaza_italia"), 15),
        BusLine("195", "195", "Provincial", "CABA Retiro ↔ Terminal y Plaza San Martín",
            listOf("stop_rotonda_autopista", "stop_terminal_bus", "stop_plaza_san_martin"), 15),
        BusLine("338", "338", "Provincial", "La Plata ↔ San Isidro por Ruta 4",
            listOf("stop_estacion_tren", "stop_terminal_bus", "stop_estadio_unico", "stop_san_carlos"), 15),
        BusLine("unlp", "Rondín Universitario UNLP", "Especial", "Circuito Facultades del Bosque UNLP",
            listOf("stop_plaza_rocha", "stop_plaza_san_martin", "stop_calle_1_42", "stop_unlp_bosque", "stop_unlp_informatica", "stop_unlp_medicina"), 12)
    )

    private fun normalize(value: String): String = Normalizer.normalize(value, Normalizer.Form.NFD)
        .replace(Regex("\\p{M}+"), "").lowercase().trim()

    fun search(query: String): List<BusLine> {
        val needle = normalize(query)
        return lines.filter { normalize(it.name + " " + it.kind).contains(needle) }
    }

    /**
     * Buscador optimizado para la cuadrícula de calles y diagonales de La Plata.
     * Busca coincidencias por nombre de línea, tipo, intersecciones (ej: "7 y 50", "60 y 137"),
     * diagonales ("Diag. 74") y puntos de interés (facultades, hospitales, plazas).
     */
    fun searchPlatense(query: String): List<BusLine> {
        val clean = normalize(query)
            .replace("diagonal", "diag")
            .replace("avenida", "av")
            .replace("camino", "cno")

        if (clean.isBlank()) return lines

        // 1. Coincidencia directa por línea o tipo
        val matchedLines = lines.filter { normalize(it.name + " " + it.kind + " " + it.headsign).contains(clean) }.toMutableSet()

        // 2. Coincidencia por paradas o intersecciones de la cuadrícula
        val matchingStops = stops.values.filter { stop ->
            val normName = normalize(stop.name)
            val normAddr = normalize(stop.address)
                .replace("diagonal", "diag")
                .replace("avenida", "av")
                .replace("calle", "")
            normName.contains(clean) || normAddr.contains(clean)
        }

        for (stop in matchingStops) {
            val serving = lines.filter { it.stopIds.contains(stop.id) }
            matchedLines.addAll(serving)
        }

        return matchedLines.toList()
    }

    val alerts = listOf(
        TransitAlert(
            id = "alert_1",
            title = "Obras viales en Av. 7 e/ 44 y 46",
            description = "Desvío preventivo por Calle 8 para Líneas 506, Norte y 273 en sentido descendente.",
            lineId = "506",
            lineName = "506, Norte, 273",
            isDetour = true
        ),
        TransitAlert(
            id = "alert_2",
            title = "Rondín UNLP: Servicio reforzado",
            description = "Salidas cada 8-10 min en horario de cursada entre Estación de Trenes y Facultades del Bosque.",
            lineId = "unlp",
            lineName = "Rondín UNLP",
            isDetour = false
        ),
        TransitAlert(
            id = "alert_3",
            title = "Renovación de calzada en Diag. 74 y 12",
            description = "Tránsito restringido hacia Plaza Moreno. Líneas 561 y Oeste circulan por Calle 14.",
            lineId = "561",
            lineName = "561 y Oeste",
            isDetour = true
        )
    )

    fun getStopsForLine(lineId: String): List<BusStop> {
        val line = lines.find { it.id.equals(lineId, ignoreCase = true) } ?: return emptyList()
        return line.stopIds.mapNotNull { stops[it] }
    }

    fun calculateArrivals(stopId: String, calendar: Calendar = Calendar.getInstance()): List<NextArrival> {
        val currentMinutes = calendar.get(Calendar.HOUR_OF_DAY) * 60 + calendar.get(Calendar.MINUTE)
        val currentSeconds = calendar.get(Calendar.SECOND)

        val serving = lines.filter { it.stopIds.contains(stopId) }
        val arrivals = mutableListOf<NextArrival>()

        for (line in serving) {
            val freq = line.frequencyMin
            val stopSeq = line.stopIds.indexOf(stopId)
            val offset = (stopSeq * 3 + line.id.hashCode().let { if (it < 0) -it else it } % 7) % freq

            for (k in -1..4) {
                val candidateMin = (currentMinutes / freq + k) * freq + offset
                val diffMin = candidateMin - currentMinutes
                val etaSec = diffMin * 60 - currentSeconds

                if (etaSec in -30..2700) {
                    val arrMinutesTotal = (currentMinutes * 60 + currentSeconds + etaSec) / 60
                    val hh = ((arrMinutesTotal / 60) % 24).let { if (it < 10) "0$it" else "$it" }
                    val mm = (arrMinutesTotal % 60).let { if (it < 10) "0$it" else "$it" }

                    arrivals.add(
                        NextArrival(
                            lineId = line.id,
                            lineName = line.name,
                            headsign = line.headsign,
                            scheduledTime = "$hh:$mm",
                            etaMinutes = kotlin.math.max(0, etaSec / 60),
                            etaSeconds = kotlin.math.max(0, etaSec)
                        )
                    )
                }
            }
        }

        return arrivals.sortedBy { it.etaSeconds }
    }
}

data class TransitAlert(
    val id: String,
    val title: String,
    val description: String,
    val lineId: String? = null,
    val lineName: String? = null,
    val isDetour: Boolean = true
)

data class SubeEstimation(
    val balance: Double,
    val fareComunal: Double = 371.13,
    val fareProvincial: Double = 413.44,
    val emergencyLimit: Double = -480.0,
    val tripsComunal: Int = 0,
    val remainingWithEmergency: Double = 0.0
) {
    companion object {
        fun calculate(balance: Double): SubeEstimation {
            val totalUsable = balance - (-480.0)
            val trips = if (totalUsable > 0) (totalUsable / 371.13).toInt() else 0
            return SubeEstimation(
                balance = balance,
                fareComunal = 371.13,
                fareProvincial = 413.44,
                emergencyLimit = -480.0,
                tripsComunal = trips,
                remainingWithEmergency = kotlin.math.max(0.0, totalUsable)
            )
        }
    }
}

