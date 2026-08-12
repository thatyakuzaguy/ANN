import "./globals.css";

export const metadata = {
  title: "SaaS CRM",
  description: "Tenant-scoped accounts, contacts, deals, activities, billing, and dashboards."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
