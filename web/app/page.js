import BondiMap from './components/BondiMap';

export const dynamic = 'force-dynamic';

const DEFAULT_GROUPS = [
  {
    type: 'Comunal',
    company: 'Líneas Municipales de La Plata',
    lines: [
      { id: '506', name: '506', verified: false },
      { id: '518', name: '518', verified: false },
      { id: '520', name: '520', verified: false },
      { id: '561', name: '561', verified: false },
      { id: 'este', name: 'Este', verified: false },
      { id: 'oeste', name: 'Oeste', verified: false },
      { id: 'norte', name: 'Norte', verified: false },
      { id: 'sur', name: 'Sur', verified: false },
    ],
  },
  {
    type: 'Provincial',
    company: 'Líneas Provinciales e Interurbanas',
    lines: [
      { id: '273', name: '273', verified: false },
      { id: '275', name: '275', verified: false },
      { id: '214', name: '214', verified: false },
      { id: '307', name: '307', verified: false },
      { id: '202', name: '202', verified: false },
      { id: '215', name: '215', verified: false },
      { id: '418', name: '418', verified: false },
      { id: '414', name: '414', verified: false },
      { id: '129', name: '129', verified: false },
      { id: '195', name: '195', verified: false },
    ],
  },
  {
    type: 'Especial',
    company: 'Universidad Nacional de La Plata',
    lines: [
      { id: 'unlp', name: 'Rondín Universitario UNLP', verified: false },
    ],
  },
];

export default async function Home() {
  let groups = [];
  let isFallback = false;

  try {
    const response = await fetch(`${process.env.BACKEND_URL || 'http://localhost:8000'}/api/v1/lines`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(3000),
    });
    if (!response.ok) throw new Error('API unreachable');
    groups = await response.json();
    if (!Array.isArray(groups) || groups.length === 0) {
      groups = DEFAULT_GROUPS;
      isFallback = true;
    }
  } catch {
    groups = DEFAULT_GROUPS;
    isFallback = true;
  }

  const totalLines = groups.reduce((acc, g) => acc + (g.lines ? g.lines.length : 0), 0);

  return (
    <main>
      <header>
        <span className="brand">bondi<span>↗</span></span>
        <div className="header-meta">
          <span>LA PLATA Y ALREDEDORES</span>
          <a href="https://github.com/LW1EXU/bondi" target="_blank" rel="noreferrer" className="repo-link">
            GitHub ↗
          </a>
        </div>
      </header>

      <section className="hero">
        <p className="eyebrow">TU CIUDAD, MÁS CERCA</p>
        <h1>El próximo viaje<br />empieza acá.</h1>
        <p className="subtitle">
          Consultá las paradas, recorridos y horarios estimados con cuenta regresiva en vivo para las {totalLines} líneas del Gran La Plata.
        </p>

        <div className="hero-actions">
          <a
            href="https://github.com/LW1EXU/bondi/releases/download/v0.1.0-alpha.1/bondi-0.1.0-alpha.1.apk"
            className="btn-primary"
            download
          >
            📲 Descargar APK Android (v0.1.0-alpha.1)
          </a>
          <a
            href="https://github.com/LW1EXU/bondi/releases/tag/v0.1.0-alpha.1"
            className="btn-secondary"
            target="_blank"
            rel="noreferrer"
          >
            Notas de la versión
          </a>
        </div>
      </section>

      {/* Interactive Map Section */}
      <section className="map-section">
        <div className="section-title-row">
          <div>
            <span className="eyebrow">MAPA INTERACTIVO EN TIEMPO REAL</span>
            <h2>Paradas y Próximas Llegadas de Micros</h2>
            <p>Hacé clic en cualquier parada para ver qué líneas pasan y el contador de cuánto falta para el próximo micro.</p>
          </div>
        </div>

        <BondiMap />
      </section>

      <aside role="status">
        <strong>Versión preliminar:</strong> Estamos preparando los recorridos oficiales. El catálogo cubre las 19 líneas solicitadas y los horarios son estimaciones programadas con frecuencia regular.
        {isFallback && <span className="tag-offline">Catálogo local disponible</span>}
      </aside>

      <section className="catalog-section">
        <div className="section-title-row">
          <div>
            <span className="eyebrow">DIRECTORIO DE TRANSPORTE</span>
            <h2>Catálogo de Líneas del Gran La Plata</h2>
          </div>
        </div>

        {groups.map((group) => (
          <div key={`${group.type}-${group.company}`} className="group-section">
            <h3>{group.type} · {group.company || 'Empresa por verificar'}</h3>
            <div className="lines">
              {group.lines.map((line) => (
                <article key={line.id}>
                  <strong>{line.name}</strong>
                  <span>{line.verified ? 'Verificada' : 'Catálogo activo'}</span>
                </article>
              ))}
            </div>
          </div>
        ))}
      </section>

      <footer>
        <p>Bondi · Transporte público del Gran La Plata (La Plata, Berisso, Ensenada).</p>
        <p>Catálogo offline disponible en Android. Horarios y frecuencias orientativos.</p>
      </footer>
    </main>
  );
}
