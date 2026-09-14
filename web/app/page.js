export const dynamic = 'force-dynamic';
export default async function Home() {
  let groups = [], error = false;
  try {
    const response = await fetch(`${process.env.BACKEND_URL || 'http://localhost:8000'}/api/v1/lines`, { cache: 'no-store', signal: AbortSignal.timeout(5000) });
    if (!response.ok) throw new Error('API');
    groups = await response.json();
  } catch { error = true; }
  return <main><header><span className="brand">bondi<span>↗</span></span><span>LA PLATA Y ALREDEDORES</span></header>
    <section><p className="eyebrow">TU CIUDAD, MÁS CERCA</p><h1>El próximo viaje<br/>empieza acá.</h1>
    <p>Conocé las líneas del Gran La Plata.</p></section>
    <aside role="status">Estamos preparando los recorridos. El catálogo inicial todavía requiere verificación de fuentes, ramales y horarios.</aside>
    {error ? <p role="alert">No pudimos conectar con el servicio. Intentá nuevamente en unos minutos.</p> :
      groups.map(group => <section key={`${group.type}-${group.company}`}><h2>{group.type} · {group.company || 'Empresa por verificar'}</h2>
        <div className="lines">{group.lines.map(line => <article key={line.id}><strong>{line.name}</strong><span>{line.verified ? 'Verificada' : 'Pendiente de verificación'}</span></article>)}</div></section>)}
    <footer>Bondi · Información de transporte en construcción. Sin estimaciones en tiempo real por el momento.</footer>
  </main>;
}
