import React from 'react';

/*
 * Section sirve de contenedor para cada bloque del sitio. Aporta un
 * padding uniforme y un ancho máximo para centrar el contenido. Recibe
 * un id para el ancla de navegación y un título opcional y subtítulo.
 */
export default function Section({
  id,
  title,
  subtitle,
  children
}: {
  id: string;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="py-16">
      <div className="mx-auto w-[min(1100px,92%)]">
        {title && <h2 className="text-2xl font-bold">{title}</h2>}
        {subtitle && <p className="text-zinc-400 mt-2">{subtitle}</p>}
        <div className="mt-6">{children}</div>
      </div>
    </section>
  );
}