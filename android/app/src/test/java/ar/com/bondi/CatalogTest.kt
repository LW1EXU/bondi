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
}
