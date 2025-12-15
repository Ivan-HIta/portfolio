import Section from './Section';
import { profile } from '@/data/profile';
import { FadeUp } from './Motion';

/*
 * Approach section conveys how you build machine learning systems.  It
 * highlights engineering maturity and your philosophy, signalling to
 * recruiters that you treat models as production software.  Each bullet
 * point is animated with FadeUp for a smooth reveal.
 */
export default function Approach() {
  return (
    <Section id="approach" title="How I build ML systems">
      <FadeUp>
        <ul className="list-disc pl-5 space-y-3 text-zinc-300 text-sm">
          {profile.approach.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </FadeUp>
    </Section>
  );
}