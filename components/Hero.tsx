import { profile } from '@/data/profile';
import { FadeUp } from './Motion';

/*
 * Hero introduce a la persona detrás del portfolio. Muestra el nombre,
 * headline, roles y un panel de contacto básico con ubicación y redes.
 * Incluye llamadas a la acción para explorar los proyectos y descargar el CV.
 */
export default function Hero() {
  return (
    <section id="home" className="pt-14 pb-10">
      <div className="mx-auto w-[min(1100px,92%)] grid md:grid-cols-[1.2fr_.8fr] gap-8 items-center">
        <div>
          <FadeUp>
            <p className="text-zinc-400">Hola, soy</p>
          </FadeUp>
          <FadeUp delay={0.05}>
            <h1 className="text-4xl md:text-5xl font-extrabold leading-tight mt-2">
              <span className="text-accent">{profile.name}</span>
            </h1>
          </FadeUp>
          <FadeUp delay={0.1}>
            <p className="text-zinc-300 mt-3 font-semibold max-w-prose">
              {profile.headline}
            </p>
          </FadeUp>
          <FadeUp delay={0.15}>
            <ul className="mt-4 space-y-2 text-zinc-400 font-semibold">
              {profile.roles.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          </FadeUp>

          <FadeUp delay={0.2}>
            <div className="mt-6 flex flex-wrap gap-3">
              <a className="px-5 py-2 rounded-xl bg-accent font-bold shadow hover:bg-accent-hover transition" href="#work">
                Ver proyectos
              </a>
              <a className="px-5 py-2 rounded-xl border border-white/10 font-bold hover:bg-white/5 transition" href="/cv.pdf" target="_blank" rel="noreferrer">
                Descargar CV
              </a>
              <a className="px-5 py-2 rounded-xl border border-white/10 font-bold hover:bg-white/5 transition" href={`mailto:${profile.email}`}>Hablemos</a>
            </div>
          </FadeUp>
        </div>

        <FadeUp delay={0.1}>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
            <div className="text-zinc-300 font-bold">Contacto</div>
            <div className="mt-3 text-zinc-400 text-sm space-y-2">
              <div>{profile.location}</div>
              <a className="underline break-all" href={`mailto:${profile.email}`}>{profile.email}</a>
              <div className="flex gap-3 pt-2">
                {profile.links.linkedin && (
                  <a className="underline" href={profile.links.linkedin} target="_blank" rel="noreferrer">
                    LinkedIn
                  </a>
                )}
                {profile.links.github && (
                  <a className="underline" href={profile.links.github} target="_blank" rel="noreferrer">
                    GitHub
                  </a>
                )}
              </div>
            </div>
          </div>
        </FadeUp>
      </div>
    </section>
  );
}