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
        <p className="subtitle">Conocé las {totalLines} líneas del transporte público del Gran La Plata.</p>

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

      <aside role="status">
        <strong>Versión preliminar:</strong> Estamos preparando los recorridos oficiales. El catálogo inicial cubre las 19 líneas solicitadas y requiere verificación de fuentes, ramales y horarios.
        {isFallback && <span className="tag-offline">Catálogo local disponible</span>}
      </aside>

      {groups.map((group) => (
        <section key={`${group.type}-${group.company}`} className="group-section">
          <h2>{group.type} · {group.company || 'Empresa por verificar'}</h2>
          <div className="lines">
            {group.lines.map((line) => (
              <article key={line.id}>
                <strong>{line.name}</strong>
                <span>{line.verified ? 'Verificada' : 'Pendiente de verificación'}</span>
              </article>
            ))}
          </div>
        </section>
      ))}

      <footer>
        <p>Bondi · Información de transporte público del Gran La Plata en construcción.</p>
        <p>Catálogo offline disponible en Android. Sin estimaciones en tiempo real por el momento.</p>
      </footer>
    </main>
  );
}
