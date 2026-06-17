import { NextRequest } from "next/server";

const API_URL = (process.env.API_URL || "http://localhost:8000").replace(/\/$/, "");

async function proxy(request: NextRequest, params: { path: string[] }) {
  const path = params.path.join("/");
  const search = request.nextUrl.search;
  const url = `${API_URL}/api/${path}${search}`;

  const init: RequestInit = {
    method: request.method,
    headers: { "Content-Type": "application/json" },
  };

  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.text();
  }

  const res = await fetch(url, init);

  return new Response(res.body, {
    status: res.status,
    headers: {
      "Content-Type": res.headers.get("Content-Type") || "application/json",
      "Cache-Control": "no-cache",
      "X-Accel-Buffering": "no",
    },
  });
}

export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(request, params);
}

export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(request, params);
}
