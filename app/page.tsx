import Navbar from '@/components/Navbar';
import Hero from '@/components/Hero';
import Services from '@/components/Services';
import About from '@/components/About';
import Skills from '@/components/Skills';
import Work from '@/components/Work';
import Certifications from '@/components/Certifications';
import Footer from '@/components/Footer';

/*
 * The main page pulls together all of the sections of the portfolio. Each
 * section is implemented as a separate component to keep things
 * modular and readable. When adding new sections, import them here and
 * insert them into the markup below.
 */
export default function Page() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <Services />
        <About />
        <Skills />
        <Work />
        <Certifications />
        <Footer />
      </main>
    </>
  );
}
