import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// Anchor content globs to this config's directory rather than the process CWD.
// Otherwise building from the repository root resolves them against the wrong
// directory, Tailwind finds no source files, and the bundle ships with no styles —
// a silent failure that only shows up visually.
const here = dirname(fileURLToPath(import.meta.url));

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    join(here, "index.html"),
    join(here, "src/**/*.{js,ts,jsx,tsx}"),
  ],
  theme: {
    extend: {
      colors: {
        greenfin: {
          50: "#f0fdf4",
          100: "#dcfce7",
          200: "#bbf7d0",
          300: "#86efac",
          400: "#4ade80",
          500: "#22c55e",
          600: "#16a34a",
          700: "#15803d",
          800: "#166534",
          900: "#14532d",
        },
      },
    },
  },
  plugins: [],
};
