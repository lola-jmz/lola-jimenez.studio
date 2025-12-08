import type { Metadata } from "next";
import { Montserrat, Pacifico } from "next/font/google";
import "./globals.css";

const montserrat = Montserrat({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap'
});

const pacifico = Pacifico({
  weight: '400',
  subsets: ['latin'],
  variable: '--font-heading',
  display: 'swap'
});

export const metadata: Metadata = {
  title: "Lola Jiménez Studio",
  description: "Contenido exclusivo de Lola Jiménez - Fotografías premium y experiencias únicas",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${montserrat.variable} ${pacifico.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
