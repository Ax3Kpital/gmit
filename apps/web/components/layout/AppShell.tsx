import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

interface Props {
  title: string;
  children: React.ReactNode;
}

export function AppShell({ title, children }: Props) {
  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      <Sidebar />
      <TopBar title={title} />
      <main
        className="pt-14"
        style={{ marginLeft: '52px', minHeight: '100vh' }}
      >
        {children}
      </main>
    </div>
  );
}
