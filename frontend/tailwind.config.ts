import type { Config } from "tailwindcss";

export default <Partial<Config>>{
  content: [
    "./components/**/*.{vue,js,ts}",
    "./layouts/**/*.vue",
    "./pages/**/*.vue",
    "./app.vue",
    "./error.vue",
  ],
  theme: {
    extend: {
      colors: {
        // Paleta oficial de marca Tribu Paridas (ver guía de marca).
        gold: {
          DEFAULT: "#C9A35A", // Dorado Suave — acento principal
          dark: "#A9803C",
          light: "#E8CF9D", // Dorado Champagne
        },
        vanilla: "#F7F2E7", // fondo
        nude: {
          DEFAULT: "#EAD9C9", // Nude Claro
          rose: "#DCC1B2", // Nude Rosado
        },
        taupe: "#CBB8AB", // Taupe Claro
        ink: "#3A2E1F", // marrón cálido oscuro (en vez de negro puro)
        muted: "#8A7A66",
        line: "#E6D9C8",
      },
      fontFamily: {
        display: ["\"Playfair Display\"", "ui-serif", "Georgia", "serif"],
        sans: ["Montserrat", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      borderRadius: {
        xl2: "1.25rem",
        xl3: "1.75rem",
      },
      boxShadow: {
        soft: "0 2px 16px rgba(58, 46, 31, 0.08)",
        card: "0 4px 24px rgba(201, 163, 90, 0.15)",
      },
    },
  },
  plugins: [],
};
