import Section from './Section';
import { posts } from '@/data/posts';
import Link from 'next/link';
import { FadeUp } from './Motion';

/*
 * Blog section lists all published posts.  Each card displays the title,
 * summary and date of the post, with a link to the full article.  Posts
 * are sorted by date descending.
 */
export default function Blog() {
  const sorted = posts.slice().sort((a, b) => (a.date > b.date ? -1 : 1));
  return (
    <Section id="blog" title="Blog">
      <div className="grid md:grid-cols-2 gap-6">
        {sorted.map((post, index) => (
          <FadeUp key={post.slug} delay={index * 0.05}>
            <Link href={`/blog/${post.slug}`} className="block rounded-xl border border-white/10 bg-white/5 p-5 hover:bg-white/10 transition">
              <h3 className="font-bold text-zinc-100 mb-1">{post.title}</h3>
              <p className="text-xs text-zinc-400 mb-2">{new Date(post.date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</p>
              <p className="text-sm text-zinc-300">{post.summary}</p>
            </Link>
          </FadeUp>
        ))}
      </div>
    </Section>
  );
}