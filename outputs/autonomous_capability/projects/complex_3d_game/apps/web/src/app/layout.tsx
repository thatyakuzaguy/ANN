import "./globals.css";

export const metadata = {
  title: "3D Pong Arena",
  description: "Playable 3D Pong game with score and AI opponent"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
