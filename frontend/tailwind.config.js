/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Pitch-black canvas — explicitly NOT a near-black gray.
        base: "#000000",
        // Tactical neon accent tokens. Used through CSS vars by Shadcn primitives.
        "tactical-cyan": "#00f0ff",
        "tactical-amber": "#ffb000",
        "tactical-green": "#39ff14",
        "tactical-red": "#ff003c",
        "tactical-grid": "#0a1a1f",
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        neon: "0 0 8px rgba(0, 240, 255, 0.6), 0 0 16px rgba(0, 240, 255, 0.3)",
      },
    },
  },
  plugins: [],
};
