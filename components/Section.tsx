import React from 'react';

/*
 * Section is a simple wrapper that provides consistent padding and a
 * container width for each section of the page. It accepts an id for
 * anchoring, a title and an optional subtitle. Children should be the
 * actual content of the section.
 */
export default function Section({
  id,
  title,
  subtitle,
  children
}: {
  id: string;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="py-16">
      <div className="mx-auto w-[min(1100px,92%)]">
        <h2 className="text-2xl font-bold">{title}</h2>
        {subtitle && <p className="text-zinc-400 mt-2">{subtitle}</p>}
        <div className="mt-6">{children}</div>
      </div>
    </section>
  );
}
