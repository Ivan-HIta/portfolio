import Section from './Section';
import { profile } from '@/data/profile';
import { Item, Stagger } from './Motion';

/*
 * Work renderiza tarjetas de proyectos destacados. Cada tarjeta enlaza a
 * una página dinámica donde se describen con detalle. El subtítulo y
 * etiquetas resumen el contexto del caso.
 */
export default function Work() {
  return (
    <Section id="work" title="Work">
      <Stagger>
        <div className="grid md:grid-cols-3 gap-4">
          {profile.work.map((w) => (
            <Item key={w.slug}>
              <div className="rounded-2xl border border-white/10 bg-white/5 overflow-hidden shadow flex flex-col justify-between">
                <div>
                  {/* imagen placeholder, aquí podrías añadir imágenes representativas */}
                  <div className="h-36 bg-gradient-to-b from-white/10 to-transparent" />
                  <div className="p-5">
                    <h3 className="font-bold text-base">{w.title}</h3>
                    <p className="text-zinc-400 mt-2 text-sm">{w.subtitle}</p>
                    <div className="flex flex-wrap gap-2 mt-3 text-xs text-zinc-400">
                      {w.tags.map((t) => (
                        <span key={t}>{t}</span>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="px-5 pb-4 pt-2">
                  <a
                    className="underline text-sm font-bold hover:text-white"
                    href={`/work/${w.slug}`}
                  >
                    View case
                  </a>
                </div>
              </div>
            </Item>
          ))}
        </div>
      </Stagger>
    </Section>
  );
}