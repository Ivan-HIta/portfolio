import Section from './Section';
import { profile } from '@/data/profile';
import { Item, Stagger } from './Motion';

/*
 * La sección de servicios lista las áreas de expertise de manera resumida.
 * Cada elemento aparece con una animación sutil cuando entra en viewport.
 */
export default function Services() {
  return (
    <Section id="services" title="Services">
      <Stagger>
        <div className="grid md:grid-cols-3 gap-4">
          {profile.services.map((s) => (
            <Item key={s.title}>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow">
                <h3 className="font-bold">{s.title}</h3>
                <p className="text-zinc-400 mt-2 text-sm leading-relaxed">{s.desc}</p>
              </div>
            </Item>
          ))}
        </div>
      </Stagger>
    </Section>
  );
}