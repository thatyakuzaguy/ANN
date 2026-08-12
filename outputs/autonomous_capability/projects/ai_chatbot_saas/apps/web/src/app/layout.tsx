import "./globals.css";

export const metadata = {
  title: "AI Chatbot SaaS",
  description: "Tenant chat, conversations, messages, model providers, usage limits, and support handoff."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
