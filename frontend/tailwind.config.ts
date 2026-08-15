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
        pink: {
          DEFAULT: "#F05A83",
          dark: "#D8446C",
          light: "#FDE7ED",
        },
        cream: "#FFF5F7",
        ink: "#171717",
        muted: "#6B6B6B",
        line: "#EEEEEE",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      borderRadius: {
        xl2: "1.25rem",
        xl3: "1.75rem",
      },
      boxShadow: {
        soft: "0 2px 16px rgba(23, 23, 23, 0.06)",
        card: "0 4px 24px rgba(240, 90, 131, 0.08)",
      },
    },
  },
  plugins: [],
};
