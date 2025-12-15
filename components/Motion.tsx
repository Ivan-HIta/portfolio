"use client";

import { motion, useScroll, useSpring } from 'framer-motion';

/*
 * Motion helpers basados en Framer Motion. Estos pequeños componentes
 * envuelven animaciones comunes para mantener una coherencia visual y
 * evitar repetir lógica en cada componente. Puedes ajustar la duración y
 * la curvatura de las transiciones aquí para cambiar el feeling global.
 */

export const FadeUp = ({
  children,
  delay = 0
}: {
  children: React.ReactNode;
  delay?: number;
}) => (
  <motion.div
    initial={{ opacity: 0, y: 14 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, margin: '-80px' }}
    transition={{ duration: 0.55, ease: 'easeOut', delay }}
  >
    {children}
  </motion.div>
);

export const Stagger = ({ children }: { children: React.ReactNode }) => (
  <motion.div
    initial="hidden"
    whileInView="show"
    viewport={{ once: true, margin: '-80px' }}
    variants={{
      hidden: { opacity: 0 },
      show: { opacity: 1, transition: { staggerChildren: 0.08 } }
    }}
  >
    {children}
  </motion.div>
);

export const Item = ({ children }: { children: React.ReactNode }) => (
  <motion.div
    variants={{
      hidden: { opacity: 0, y: 14 },
      show: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.45, ease: 'easeOut' }
      }
    }}
  >
    {children}
  </motion.div>
);

/**
 * ScrollProgress es un componente opcional que muestra una barra de
 * progreso en la parte superior indicando el avance de la página. Se
 * apoya en useScroll y useSpring de framer-motion para animar
 * suavemente el ancho de la barra en función del scroll.
 */
export function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  const width = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001
  });
  return (
    <motion.div
      className="fixed top-0 left-0 h-1 bg-accent z-50"
      style={{ scaleX: width, transformOrigin: '0%' }}
    />
  );
}