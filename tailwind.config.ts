import type { Config } from "tailwindcss";

// Tailwind configuration enables dark mode and scans the app and component
// directories for class names. It uses a very lightweight extend section
// because additional styles are handled directly in the components. When you
// add new components or pages, ensure their paths are listed in the `content`
// array so Tailwind can tree‑shake unused styles.
const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {}
  },
  plugins: []
};

export default config;
