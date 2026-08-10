import Section from './Section';
import { profile } from '@/data/profile';
import { Item, Stagger } from './Motion';

export default function Work() {
  return (
    <Section id="work" title="Selected Work">
      <Stagger>
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {profile.work.map((w, index) => (
            <Item key={w.slug}>
              <article className="group flex h-full flex-col overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] shadow-lg shadow-black/10 transition hover:-translate-y-1 hover:border-cyan-300/40 hover:bg-white/[0.07]">
                <div className="h-2 bg-gradient-to-r from-cyan-400 via-blue-500 to-violet-500" aria-hidden="true" />
                <div className="flex flex-1 flex-col p-5">
                  <div className="mb-4 flex items-center justify-between gap-3 text-xs uppercase tracking-[0.18em] text-cyan-200/80">
                    <span>{String(index + 1).padStart(2, '0')}</span>
                    <span>Case study</span>
                  </div>
                  <h3 className="text-lg font-semibold leading-snug text-white">{w.title}</h3>
                  <p className="mt-3 text-sm leading-6 text-zinc-400">{w.subtitle}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {w.tags.map((t) => (
                      <span key={t} className="rounded-full border border-white/10 bg-black/10 px-2.5 py-1 text-xs text-zinc-300">
                        {t}
                      </span>
                    ))}
                  </div>
                  <div className="mt-auto flex flex-wrap items-center gap-4 pt-6 text-sm font-semibold">
                    <a className="underline underline-offset-4 hover:text-cyan-200" href={'/work/' + w.slug}>
                      View case
                    </a>
                    {w.links?.code ? (
                      <a
                        className="inline-flex items-center gap-1 text-cyan-200 hover:text-white"
                        href={w.links.code}
                        target="_blank"
                        rel="noreferrer"
                      >
                        GitHub <span aria-hidden="true">↗</span>
                      </a>
                    ) : null}
                  </div>
                </div>
              </article>
            </Item>
          ))}
        </div>
      </Stagger>
    </Section>
  );
}
