import type { Config } from "tailwindcss";

// Palette sourced from adtech-measurement/docs/styleguide/colors.json
// (Databricks Extended Brand Guidelines).
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        databricks: {
          orange: "#FF3621",
          dark: "#1B3139",
          lava: {
            300: "#FABFBA",
            400: "#FF9E94",
            500: "#FF5F46",
            600: "#FF3621",
            700: "#BD2B26",
            800: "#801C17",
          },
          navy: {
            300: "#C4CCD6",
            400: "#90A5B1",
            500: "#618794",
            600: "#1B5162",
            700: "#143D4A",
            800: "#1B3139",
            900: "#0B2026",
          },
          oat: {
            light: "#F9F7F4",
            medium: "#EEEDE9",
          },
          gray: {
            navigation: "#303F47",
            text: "#5A6F77",
            lines: "#DCE0E2",
          },
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
