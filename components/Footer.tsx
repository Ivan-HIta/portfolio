import { profile } from "@/data/profile";

export default function Footer() {
  return (
    <footer className="border-t border-white/10 py-8">
      <div className="mx-auto w-[min(1100px,92%)] flex flex-wrap gap-4 items-center justify-between text-zinc-400">
        <span>© {new Date().getFullYear()} {profile.name}</span>
        <div className="flex gap-4 font-semibold">
          <a className="underline" href={profile.links.linkedin} target="_blank" rel="noreferrer">
            LinkedIn
          </a>
          <a className="underline" href={profile.links.github} target="_blank" rel="noreferrer">
            GitHub
          </a>
          <a className="underline" href={`mailto:${profile.email}`}>
            Email
          </a>
        </div>
      </div>
    </footer>
  );
}
