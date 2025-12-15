import Navbar from '@/components/Navbar';
import Blog from '@/components/Blog';
import Footer from '@/components/Footer';

export const metadata = {
  title: 'Blog | Portfolio',
  description: 'Technical essays on AI and machine learning engineering',
};

/*
 * This route renders the blog listing page.  It reuses the Blog
 * component and wraps it with the Navbar and Footer for a consistent
 * look and feel across pages.
 */
export default function BlogPage() {
  return (
    <>
      <Navbar />
      <main>
        <Blog />
      </main>
      <Footer />
    </>
  );
}