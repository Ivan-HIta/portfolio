import './globals.css';
import type { Metadata } from 'next';
import { profile } from '@/data/profile';
import { ScrollProgress } from '@/components/Motion';

/*
 * Metadatos globales para SEO y social preview. Ajusta title,
 * description y keywords según tu propuesta de valor. Las propiedades
 * Open Graph y Twitter facilitan una vista previa atractiva al compartir
 * tu enlace en redes sociales.
 */
export const metadata: Metadata = {
  title: `${profile.name} | Data & Risk Leader`,
  description:
    'Portfolio premium de Iván Hita, líder en ciencia de datos y riesgo crediticio. Descubre casos de éxito en modelos de crédito, segmentación, NLP y fraude.',
  keywords: [
    'ciencia de datos',
    'riesgo crediticio',
    'machine learning',
    'XGBoost',
    'Logistic Regression',
    'MLP',
    'NLP',
    'fraude',
    'banca',
    'México'
  ],
  openGraph: {
    title: `${profile.name} | Data & Risk Leader`,
    description:
      'Portfolio premium de Iván Hita, líder en ciencia de datos y riesgo crediticio.',
    url: 'https://yourdomain.com',
    locale: 'es_MX',
    type: 'website'
  },
  twitter: {
    card: 'summary_large_image',
    title: `${profile.name} | Data & Risk Leader`,
    description:
      'Portfolio premium de Iván Hita, líder en ciencia de datos y riesgo crediticio.'
  }
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className="dark">
      <body>
        {/* Barra de progreso de scroll */}
        <ScrollProgress />
        {children}
      </body>
    </html>
  );
}