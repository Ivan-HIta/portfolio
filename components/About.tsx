import Section from './Section';
import { profile } from '@/data/profile';
import { FadeUp } from './Motion';

/*
 * The About section provides a short narrative and highlights. It
 * illustrates the candidate’s strengths with a short lead paragraph and
 * bullet points. Each part animates into view using FadeUp.
 */
export default function About() {
  return (
    <Section id="about" title="About me">
      <div className="grid md:grid-cols-[1.2fr_.8fr] gap-4">
        <FadeUp>
          <p className="text-zinc-300">{profile.about.lead}</p>
        </FadeUp>

        <FadeUp delay={0.05}>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
            <h3 className="font-bold">Highlights</h3>
            <ul className="mt-3 list-disc pl-5 text-zinc-400 space-y-2">
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
