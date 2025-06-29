import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default ({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  return defineConfig({
    plugins: [react()],
    define: {
      'process.env': env
    },
    server: {
      host: '0.0.0.0', // Esto hace que escuche en todas las interfaces de red (tu IP local incluida)
      port: 5173,      // O el puerto que uses (por defecto 5173)
    }
  });
}
