const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getDashboard() {
  const response = await fetch(`${API_URL}/dashboard`, { cache: "no-store" });
  if (!response.ok) throw new Error("Unable to load dashboard");
  return response.json();
}
