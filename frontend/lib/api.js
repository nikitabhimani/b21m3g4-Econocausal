const apiBaseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8001/api").replace(/\/$/, "");

export function apiUrl(path) {
  return `${apiBaseUrl}/${path.replace(/^\//, "")}`;
}

export async function apiJson(path, options) {
  const response = await fetch(apiUrl(path), options);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `API request failed (${response.status})`);
  }
  return response.json();
}
