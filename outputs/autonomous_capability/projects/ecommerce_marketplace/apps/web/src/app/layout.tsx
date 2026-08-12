import "./globals.css";

export const metadata = {
  title: "Marketplace SaaS",
  description: "Product catalog, carts, sellers, vendors, buyers, orders, payments, and moderation."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
