import { defineConfig, loadEnv, type Plugin, type ViteDevServer } from "vite";
import react from "@vitejs/plugin-react";

// Local dev only: serve api/ask.ts at /api/ask the way Vercel does in production (Web Request -> Response),
// so the live Ask path can be tested end to end. The key comes from web/.env.local, which git ignores.
function askApi(): Plugin {
  return {
    name: "ask-api-dev",
    configureServer(server: ViteDevServer) {
      server.middlewares.use("/api/ask", async (req, res) => {
        try {
          const chunks: Buffer[] = [];
          for await (const c of req) chunks.push(c as Buffer);
          const mod = await server.ssrLoadModule("/api/ask.ts");
          const headers = new Headers();
          for (const [k, v] of Object.entries(req.headers)) if (typeof v === "string") headers.set(k, v);
          const r: Response = await mod.POST(new Request(`http://${req.headers.host}/api/ask`, { method: req.method, headers, body: req.method === "POST" ? Buffer.concat(chunks) : undefined }));
          res.statusCode = r.status;
          r.headers.forEach((v, k) => res.setHeader(k, v));
          res.end(Buffer.from(await r.arrayBuffer()));
        } catch (e) {
          server.config.logger.error(String(e));
          res.statusCode = 500;
          res.end(JSON.stringify({ error: "dev_handler" }));
        }
      });
    },
  };
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  for (const k of ["ANTHROPIC_API_KEY", "ASK_MODEL"]) if (env[k] && !process.env[k]) process.env[k] = env[k];
  return {
    plugins: [react(), askApi()],
    server: { port: 5199 },
    build: {
      chunkSizeWarningLimit: 700,
      rollupOptions: { output: { manualChunks: (id) => (id.includes("/src/data/") ? "data" : id.includes("node_modules") ? "vendor" : undefined) } },
    },
  };
});
