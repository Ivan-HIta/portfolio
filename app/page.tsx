import Navbar from '@/components/Navbar';
import Hero from '@/components/Hero';
import Services from '@/components/Services';
import About from '@/components/About';
import Skills from '@/components/Skills';
import Work from '@/components/Work';
import Certifications from '@/components/Certifications';
import Footer from '@/components/Footer';
import Approach from '@/components/Approach';
import Blog from '@/components/Blog';

/*
 * Página principal que reúne todas las secciones del portfolio. Cada
 * sección es un componente separado para mantener el código modular.
 */
export default function Page() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <Services />
        <About />
        <Approach />
        <Skills />
        <Work />
        <Certifications />
        {/* Optionally showcase recent blog posts on the home page */}
        <Blog />
      </main>
      <Footer />
    </>
  );
}