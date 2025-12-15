import { projects } from '@/data/projects';
import type { Project } from '@/data/projects';
import { notFound } from 'next/navigation';
import { Metadata } from 'next';

/**
 * Genera las rutas estáticas para todos los proyectos. Next.js usará
 * esta función para prerenderizar las páginas de cada caso de estudio
 * en tiempo de construcción.
 */
export async function generateStaticParams() {
  return projects.map((p) => ({ slug: p.slug }));
}

/**
 * Genera metadatos específicos por proyecto para mejorar SEO y
 * compartir en redes. Ajusta el título y descripción para cada caso.
 */
export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  const project = projects.find((p) => p.slug === params.slug);
  if (!project) return {};
  return {
    title: `${project.title} | Caso de estudio`,
    description: project.summary
  };
}

export default function ProjectPage({ params }: { params: { slug: string } }) {
  const project = projects.find((p) => p.slug === params.slug);
  if (!project) {
    notFound();
  }
  // Tipo de assert para TypeScript: project no será undefined aquí
  const p = project as Project;
  return (
    <main className="mx-auto w-[min(1100px,92%)] py-16">
      <a href="#work" className="underline text-sm text-zinc-400 hover:text-white">
        ← Volver
      </a>
      <h1 className="text-3xl md:text-4xl font-extrabold mt-4">{p.title}</h1>
      <p className="text-zinc-400 mt-2 max-w-prose">{p.summary}</p>

      <section className="mt-8 space-y-6">
        <div>
          <h2 className="text-xl font-bold mb-2">Contexto</h2>
          <p className="text-zinc-300 leading-relaxed whitespace-pre-line">{p.context}</p>
        </div>
        <div>
          <h2 className="text-xl font-bold mb-2">Acciones</h2>
          <ul className="list-disc pl-5 space-y-2 text-zinc-300 text-sm">
            {p.actions.map((a, idx) => (
              <li key={idx}>{a}</li>
            ))}
          </ul>
        </div>
        <div>
          <h2 className="text-xl font-bold mb-2">Resultados</h2>
          <ul className="list-disc pl-5 space-y-2 text-zinc-300 text-sm">
            {p.results.map((r, idx) => (
              <li key={idx}>{r}</li>
            ))}
          </ul>
        </div>
        <div>
          <h2 className="text-xl font-bold mb-2">Stack tecnológico</h2>
          <div className="flex flex-wrap gap-2 text-xs text-zinc-300">
            {p.stack.map((s) => (
              <span key={s} className="px-3 py-1 rounded-full border border-white/10 bg-white/5">
                {s}
              </span>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}