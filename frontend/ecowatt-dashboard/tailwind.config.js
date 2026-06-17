/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        grid: "#d9e2dc",
        ink: "#14231b",
        energy: "#0f9f6e",
        warning: "#e6a700",
        panel: "#f7faf8",
      },
    },
  },
  plugins: [],
};
