import './style.css';
export const metadata = { title: 'Bondi · La Plata', description: 'Transporte público del Gran La Plata' };
export default function Layout({ children }) {
  return <html lang="es-AR"><body>{children}</body></html>;
}
