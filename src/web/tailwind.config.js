/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#e8f4f8",
          100: "#cce4ed",
          200: "#99c9db",
          300: "#66adca",
          400: "#3392b8",
          500: "#165c7d",
          600: "#12506d",
          700: "#0e445d",
          800: "#0a384d",
          900: "#062c3d",
        },
        accent: {
          50: "#fdf2ed",
          100: "#f9e0d1",
          200: "#f3c1a3",
          300: "#eda275",
          400: "#e78347",
          500: "#7d3716",
          600: "#6b2f13",
          700: "#592710",
          800: "#471f0d",
          900: "#35170a",
        },
        ink: {
          // Backgrounds para dark theme (MeraKia)
          950: "#06131a",
          900: "#0a1c26",
          800: "#0e2532",
          700: "#122e3e",
          600: "#16374a",
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'glow-radial':
          'radial-gradient(circle at 30% 30%, rgba(22,92,125,0.18), transparent 60%)',
      },
      boxShadow: {
        glow: '0 0 60px -10px rgba(22, 92, 125, 0.45)',
      },
    },
  },
  plugins: [],
};
