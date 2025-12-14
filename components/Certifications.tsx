import Section from "./Section";
import { profile } from "@/data/profile";
import { Item, Stagger } from "./Motion";

export default function Certifications() {
  return (
    <Section id="certifications" title="International Certifications">
      <Stagger>
        <div className="grid md:grid-cols-2 gap-4">
          {profile.certifications.map((c) => (
            <Item key={c.title}>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-5 flex items-center gap-3">
                <div className="size-9 rounded-xl bg-white/10 border border-white/10" />
                <div>
                  <div className="font-bold">{c.title}</div>
                  <div className="text-zinc-400 text-sm">{c.issuer}</div>
                </div>
              </div>
            </Item>
          ))}
        </div>
      </Stagger>
    </Section>
  );
}
