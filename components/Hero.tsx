import { profile } from '@/data/profile';
import { FadeUp } from './Motion';

/*
 * Hero introduces the person behind the portfolio. It displays the name,
 * headline, roles and a simple contact panel with location, email and
 * social links. Animations are handled via the FadeUp helper.
 */
export default function Hero() {
  return (
    <section id="home" className="pt-14 pb-10">
      <div className="mx-auto w-[min(1100px,92%)] grid md:grid-cols-[1.2fr_.8fr] gap-8 items-center">
        <div>
          <FadeUp>
            <p className="text-zinc-400">Hi,</p>
          </FadeUp>
          <FadeUp delay={0.05}>
            <h1 className="text-4xl md:text-5xl font-extrabold leading-tight mt-2">
              I&apos;m <span className="text-indigo-400">{profile.name}</span>
            </h1>
          </FadeUp>
          <FadeUp delay={0.1}>
            <p className="text-zinc-300 mt-3 font-semibold">{profile.headline}</p>
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
              <a className="px-4 py-2 rounded-xl bg-indigo-500 font-bold shadow" href="#work">
                Ver proyectos
              </a>
              <a className="px-4 py-2 rounded-xl border border-white/10 font-bold" href="#certifications">
                Certificaciones
              </a>
            </div>
          </FadeUp>
        </div>

        <FadeUp delay={0.1}>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
            <div className="text-zinc-300 font-bold">Contacto</div>
            <div className="mt-3 text-zinc-400 text-sm space-y-2">
              <div>{profile.location}</div>
              <a className="underline" href={`mailto:${profile.email}`}>{profile.email}</a>
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
