import Section from './Section';
import { profile } from '@/data/profile';
import { Item, Stagger } from './Motion';

/*
 * Skills section displays the candidate’s skills as a series of chips. A
 * subtle stagger animation makes them appear in succession when
 * scrolled into view.
 */
export default function Skills() {
  return (
    <Section id="skills" title="Skills" subtitle="Chips, rápido de escanear.">
      <Stagger>
        <div className="flex flex-wrap gap-2">
          {profile.skills.map((s) => (
            <Item key={s}>
              <span className="px-3 py-2 rounded-full border border-white/10 bg-white/5 text-sm font-semibold">
                {s}
              </span>
            </Item>
          ))}
        </div>
      </Stagger>
    </Section>
  );
}
