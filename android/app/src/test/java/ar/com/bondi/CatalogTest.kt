package ar.com.bondi
import org.junit.Assert.*
import org.junit.Test

class CatalogTest {
    @Test fun includesRequestedScope() {
        assertEquals(19, Catalog.lines.size)
        assertEquals(19, Catalog.lines.map { it.id }.toSet().size)
    }

    @Test fun searchIgnoresAccentsAndCase() {
        assertEquals("unlp", Catalog.search("RONDIN").single().id)
        assertEquals(8, Catalog.search("comunal").size)
        assertTrue(Catalog.search("no-existe").isEmpty())
    }

    @Test fun includesStopsAndRoutes() {
        assertTrue(Catalog.stops.size >= 30)
        val line506Stops = Catalog.getStopsForLine("506")
        assertTrue(line506Stops.isNotEmpty())
        assertTrue(line506Stops.any { it.name == "Plaza Moreno" })
    }

    @Test fun calculatesNextArrivalsWithCountdown() {
        val arrivals = Catalog.calculateArrivals("stop_plaza_moreno")
        assertTrue(arrivals.isNotEmpty())
        val first = arrivals.first()
        assertTrue(first.etaSeconds >= 0)
        assertTrue(first.lineName.isNotEmpty())
        assertTrue(first.scheduledTime.matches(Regex("\\d{2}:\\d{2}")))
    }
}
