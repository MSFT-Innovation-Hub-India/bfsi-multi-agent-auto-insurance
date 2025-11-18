import './globals.css'

export const metadata = {
  title: 'Global Trust Auto Care',
  description: 'Your trusted auto insurance partner',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans">{children}</body>
    </html>
  )
}
