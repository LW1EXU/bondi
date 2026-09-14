import './style.css';

export const metadata = {
  title: 'Bondi · La Plata',
  description: 'Transporte público del Gran La Plata. Paradas, frecuencias y horarios en tiempo real.',
  manifest: '/manifest.json',
  icons: {
    icon: '/icon.svg',
    apple: '/icon.svg',
  },
};

export const viewport = {
  themeColor: '#18382B',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function Layout({ children }) {
  return (
    <html lang="es-AR">
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#18382B" />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                  navigator.serviceWorker.register('/sw.js').then(
                    function(reg) { console.log('Bondi SW registrado con éxito:', reg.scope); },
                    function(err) { console.log('Bondi SW error:', err); }
                  );
                });
              }
            `,
          }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
