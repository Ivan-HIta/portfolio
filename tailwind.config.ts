import type { Config } from 'tailwindcss';

// Tailwind configuration. Activamos el modo oscuro controlado por
// clases y registramos los directorios a escanear. Extendemos la paleta
// con un color de acento para uniformidad en botones y enlaces. Si
// deseas utilizar otro color principal, basta con cambiar los valores
// aquí. Los componentes emplean estas variables a través de las
// clases de Tailwind.
const config: Config = {
  darkMode: 'class',
  content: ['./app/**/*.{js,ts,jsx,tsx}', './components/**/*.{js,ts,jsx,tsx}', './data/**/*.{ts,js}'],
  theme: {
    extend: {
      colors: {
        accent: {
          DEFAULT: '#4F46E5',
          hover: '#6366F1'
        }
      }
    }
  },
  plugins: []
};

export default config;