"use client";

import { useEffect, useMemo, useState } from 'react';

/*
 * Navbar implementa una barra de navegación fija con scroll‑spy. Observa
 * cada sección de la página y resalta el enlace correspondiente al
 * desplazarse. En pantallas pequeñas se colapsa a un menú hamburguesa.
 */

const sections = [
  { id: 'home', label: 'Home' },
  { id: 'services', label: 'Services' },
  { id: 'about', label: 'About' },
  { id: 'approach', label: 'Approach' },
  { id: 'skills', label: 'Skills' },
  { id: 'work', label: 'Work' },
  { id: 'certifications', label: 'Certifications' }
];

export default function Navbar() {
  const [active, setActive] = useState('home');
  const [open, setOpen] = useState(false);
  const ids = useMemo(() => sections.map((s) => s.id), []);

  useEffect(() => {
    const els = ids
      .map((id) => document.getElementById(id))
      .filter(Boolean) as HTMLElement[];
    const obs = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible?.target?.id) setActive(visible.target.id);
      },
      { rootMargin: '-45% 0px -50% 0px', threshold: [0.01, 0.1, 0.2, 0.4, 0.6] }
    );
    els.forEach((el) => obs.observe(el));
    return () => obs.disconnect();
  }, [ids]);

  return (
    <header className="sticky top-0 z-40 backdrop-blur border-b border-white/10 bg-zinc-950/60">
      <div className="mx-auto w-[min(1100px,92%)] py-3 flex items-center gap-4">
        <a href="#home" className="font-bold tracking-tight flex items-center gap-1">
          <span className="text-accent">●</span>
          <span>Portfolio</span>
        </a>

        <button
          className="ml-auto md:hidden px-3 py-2 rounded-xl border border-white/10"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-label="Toggle navigation"
        >
          ☰
        </button>

        <nav
          className={`ml-auto md:flex items-center gap-4 ${open ? 'flex flex-wrap' : 'hidden md:flex'}`}
        >
          {sections.map((s) => (
            <a
              key={s.id}
              href={`#${s.id}`}
              onClick={() => setOpen(false)}
              className={`text-sm font-semibold transition py-1 ${
                active === s.id ? 'text-white' : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              {s.label}
            </a>
          ))}
          {/* External link to the blog page */}
          <a
            href="/blog"
            onClick={() => setOpen(false)}
            className="text-sm font-semibold transition py-1 text-zinc-400 hover:text-zinc-200"
          >
            Blog
          </a>
        </nav>
      </div>
    </header>
  );
}