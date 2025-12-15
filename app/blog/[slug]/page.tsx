import { posts } from '@/data/posts';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import { notFound } from 'next/navigation';

interface Props {
  params: { slug: string };
}

export function generateStaticParams() {
  return posts.map((p) => ({ slug: p.slug }));
}

export function generateMetadata({ params }: Props) {
  const post = posts.find((p) => p.slug === params.slug);
  if (!post) return {};
  return {
    title: `${post.title} | Portfolio`,
    description: post.summary,
  };
}

export default function BlogPostPage({ params }: Props) {
  const post = posts.find((p) => p.slug === params.slug);
  if (!post) return notFound();
  return (
    <>
      <Navbar />
      <main className="mx-auto w-[min(800px,90%)] pt-14 pb-10">
        <h1 className="text-3xl md:text-4xl font-bold mb-2 text-zinc-100">{post.title}</h1>
        <p className="text-sm text-zinc-400 mb-6">{new Date(post.date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
        {post.content.map((para, idx) => (
          <p key={idx} className="text-zinc-300 leading-relaxed mb-4 whitespace-pre-line">
            {para}
          </p>
        ))}
      </main>
      <Footer />
    </>
  );
}