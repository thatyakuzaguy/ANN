import "./globals.css";

export const metadata = {
  title: "LMS SaaS",
  description: "Courses, lessons, modules, enrollments, student progress, certificates, and billing."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
