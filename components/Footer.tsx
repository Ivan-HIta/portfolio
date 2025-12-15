import { profile } from '@/data/profile';

/*
 * Footer concluye la página con enlaces a redes y contacto. Muestra
 * automáticamente el año actual y el nombre del profesional.
 */
export default function Footer() {
  return (
    <footer className="border-t border-white/10 py-8" id="contact">
      <div className="mx-auto w-[min(1100px,92%)] flex flex-wrap gap-4 items-center justify-between text-zinc-400 text-sm">
        <span>
          © {new Date().getFullYear()} {profile.name}
        </span>
        <div className="flex gap-4 font-semibold">
          {profile.links.linkedin && (
            <a className="underline" href={profile.links.linkedin} target="_blank" rel="noreferrer">
              LinkedIn
            </a>
          )}
          {profile.links.github && (
            <a className="underline" href={profile.links.github} target="_blank" rel="noreferrer">
              GitHub
            </a>
          )}
          <a className="underline" href={`mailto:${profile.email}`}>Email</a>
        </div>
      </div>
    </footer>
  );
}