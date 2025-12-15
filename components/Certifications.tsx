import Section from './Section';
import { profile } from '@/data/profile';
import { Item, Stagger } from './Motion';

/*
 * La sección de certificaciones muestra cursos y credenciales. Cada
 * elemento incluye título y entidad emisora.
 */
export default function Certifications() {
  return (
    <Section id="certifications" title="Certificaciones">
      <Stagger>
        <div className="grid md:grid-cols-2 gap-4">
          {profile.certifications.map((c) => (
            <Item key={c.title}>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-5 flex items-start gap-3">
                <div className="size-8 rounded-xl bg-white/10 border border-white/10" />
                <div>
                  <div className="font-bold text-sm">{c.title}</div>
                  <div className="text-zinc-400 text-xs mt-1">{c.issuer}</div>
                </div>
              </div>
            </Item>
          ))}
        </div>
      </Stagger>
    </Section>
  );
}