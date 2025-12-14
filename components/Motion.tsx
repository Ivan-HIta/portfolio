"use client";

import { motion } from 'framer-motion';

/*
 * Motion helpers based on Framer Motion. These small components wrap
 * common animations used throughout the portfolio. They ensure
 * consistent timing and easing while keeping the markup clean.
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
      show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: 'easeOut' } }
    }}
  >
    {children}
  </motion.div>
);
