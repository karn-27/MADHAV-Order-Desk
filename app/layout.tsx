import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = {title:'MADHAV · Order Desk',description:'A calm, owner-approved chat-to-order workspace for small businesses.'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
