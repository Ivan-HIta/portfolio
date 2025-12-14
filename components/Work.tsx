import Section from "./Section";
import { profile } from "@/data/profile";
import { Item, Stagger } from "./Motion";

export default function Work() {
  return (
    <Section id="work" title="Work">
      <Stagger>
        <div className="grid md:grid-cols-3 gap-4">
          {profile.work.map((w) => (
            <Item key={w.title}>
              <div className="rounded-2xl border border-white/10 bg-white/5 overflow-hidden shadow">
                <div className="h-36 bg-gradient-to-b from-white/10 to-transparent" />
                <div className="p-5">
                  <h3 className="font-bold">{w.title}</h3>
                  <p className="text-zinc-400 mt-2">{w.subtitle}</p>
                  <div className="flex flex-wrap gap-2 mt-3 text-xs text-zinc-400">
                    {w.tags.map((t) => (
                      <span key={t}>{t}</span>
                    ))}
                  </div>
                  <div className="flex gap-3 mt-4 text-sm font-bold">
                    {w.links.code && (
                      <a
                        className="underline"
                        href={w.links.code}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Code
                      </a>
                    )}
                    {w.links.demo && (
                      <a
                        className="underline"
                        href={w.links.demo}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Demo
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </Item>
          ))}
        </div>
      </Stagger>
    </Section>
  );
}
