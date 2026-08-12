import "./globals.css";

export const metadata = {
  title: "Booking SaaS",
  description: "Availability, calendars, appointments, staff, reminders, and payments."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
