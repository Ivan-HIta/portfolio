import './globals.css';
import type { Metadata } from 'next';

/*
 * The root layout defines the HTML skeleton for all pages. It imports the
 * global styles and sets up the default metadata for the site. The
 * children prop contains the contents of the current route.
 */
export const metadata: Metadata = {
  title: 'Portfolio | Iván Moisés Hita Cahuantzi',
  description: 'Data Science & AI portfolio'
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
