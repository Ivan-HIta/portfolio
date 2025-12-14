import Section from './Section';
import { profile } from '@/data/profile';
import { Item, Stagger } from './Motion';

/*
 * Services (experience) section lists the high level services or areas of
 * expertise. Each item is animated with a small stagger for a polished
 * entrance as the user scrolls.
 */
export default function Services() {
  return (
    <Section id="experience" title="Services">
      <Stagger>
        <div className="grid md:grid-cols-3 gap-4">
          {profile.services.map((s) => (
            <Item key={s.title}>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow">
                <h3 className="font-bold">{s.title}</h3>
                <p className="text-zinc-400 mt-2">{s.desc}</p>
              </div>
            </Item>
          ))}
        </div>
      </Stagger>
    </Section>
  );
}
