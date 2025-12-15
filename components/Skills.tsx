import Section from './Section';
import { profile } from '@/data/profile';
import { Item, Stagger } from './Motion';

/*
 * Skills muestra tus habilidades en forma de chips. Estas se animan con
 * un efecto escalonado al entrar en vista para crear dinamismo.
 */
export default function Skills() {
  return (
    <Section id="skills" title="Skills" subtitle="Key tools and technologies">
      <Stagger>
        <div className="flex flex-wrap gap-2">
          {profile.skills.map((s) => (
            <Item key={s}>
              <span className="px-3 py-2 rounded-full border border-white/10 bg-white/5 text-xs font-semibold">
                {s}
              </span>
            </Item>
          ))}
        </div>
      </Stagger>
    </Section>
  );
}