import { redirect } from 'next/navigation';
import { cookies } from 'next/headers';

export default function Home() {
  const session = cookies().get('gmit_session');
  if (session) {
    redirect('/dashboard');
  }
  redirect('/login');
}
