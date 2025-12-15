import Section from './Section';
import { profile } from '@/data/profile';
import { FadeUp } from './Motion';

/*
 * La sección About ofrece una narración breve de tu trayectoria y destaca
 * puntos fuertes mediante bullets. Cada parte utiliza animaciones FadeUp.
 */
export default function About() {
  return (
    <Section id="about" title="About">
      <div className="grid md:grid-cols-[1.2fr_.8fr] gap-4">
        <FadeUp>
          <p className="text-zinc-300 leading-relaxed whitespace-pre-line">{profile.about.lead}</p>
        </FadeUp>
        <FadeUp delay={0.05}>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
            <h3 className="font-bold">Destacados</h3>
            <ul className="mt-3 list-disc pl-5 text-zinc-400 space-y-2 text-sm">
              {profile.about.bullets.map((b) => (
                <li key={b}>{b}</li>
              ))}
            </ul>
          </div>
        </FadeUp>
      </div>
    </Section>
  );
}