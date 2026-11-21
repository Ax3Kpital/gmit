import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { serverFetch } from '@/lib/server-api';

interface NotificationStatus {
  email_configured: boolean;
  telegram_configured: boolean;
  smtp_host: string;
  notification_email: string;
  telegram_chat_id: string;
}

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span
      className="inline-block w-2 h-2 rounded-full mr-2 flex-shrink-0"
      style={{ background: ok ? 'var(--up)' : 'var(--line)' }}
    />
  );
}

function ConfigBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl overflow-hidden" style={{ border: '1px solid var(--line)' }}>
      <div className="px-5 py-3" style={{ background: 'var(--panel)', borderBottom: '1px solid var(--line)' }}>
        <h3 className="text-sm font-medium" style={{ color: 'var(--text)' }}>{title}</h3>
      </div>
      <div className="p-5 space-y-4" style={{ background: 'var(--bg)' }}>
        {children}
      </div>
    </div>
  );
}

function EnvRow({ name, value, secret }: { name: string; value: string; secret?: boolean }) {
  return (
    <div className="flex items-start gap-2">
      <code className="text-xs mono flex-shrink-0 px-2 py-0.5 rounded"
        style={{ background: 'var(--panel)', color: 'var(--accent)', border: '1px solid var(--line)' }}>
        {name}
      </code>
      <span className="text-xs" style={{ color: 'var(--muted)' }}>
        {secret ? '••••••••' : value}
      </span>
    </div>
  );
}

export default async function SettingsPage() {
  const session = cookies().get('gmit_session');
  if (!session) redirect('/login');

  const status = await serverFetch<NotificationStatus>('/api/notifications/status');

  const emailOk = status?.email_configured ?? false;
  const telegramOk = status?.telegram_configured ?? false;

  return (
    <AppShell title="Setări">
      <div className="p-5 space-y-6 max-w-3xl mx-auto">

        {/* Notification channel status */}
        <ConfigBlock title="Notification Channels">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <StatusDot ok={emailOk} />
              <span className="text-sm" style={{ color: 'var(--text)' }}>Email (SMTP)</span>
              <span className="text-xs ml-auto" style={{ color: emailOk ? 'var(--up)' : 'var(--muted)' }}>
                {emailOk ? `→ ${status?.notification_email}` : 'not configured'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <StatusDot ok={telegramOk} />
              <span className="text-sm" style={{ color: 'var(--text)' }}>Telegram</span>
              <span className="text-xs ml-auto" style={{ color: telegramOk ? 'var(--up)' : 'var(--muted)' }}>
                {telegramOk ? `chat_id: ${status?.telegram_chat_id}` : 'not configured'}
              </span>
            </div>
          </div>
          {!emailOk && !telegramOk && (
            <p className="text-xs mt-2" style={{ color: 'var(--muted)' }}>
              Configure at least one channel in <code style={{ color: 'var(--accent)' }}>.env</code> to receive alert and briefing notifications.
            </p>
          )}
        </ConfigBlock>

        {/* Email setup guide */}
        <ConfigBlock title="Email Setup (SMTP)">
          <p className="text-xs leading-relaxed" style={{ color: 'var(--muted)' }}>
            Works with any SMTP provider: Gmail, Outlook, SendGrid, Resend, Mailgun, Brevo.
          </p>
          <div className="space-y-2">
            <EnvRow name="SMTP_HOST" value="smtp.gmail.com" />
            <EnvRow name="SMTP_PORT" value="587" />
            <EnvRow name="SMTP_USER" value="your@gmail.com" />
            <EnvRow name="SMTP_PASSWORD" value="App Password (not your Google password)" secret />
            <EnvRow name="SMTP_FROM_ADDRESS" value='GMIT Terminal <your@gmail.com>' />
            <EnvRow name="NOTIFICATION_EMAIL" value="your@gmail.com" />
          </div>
          <div className="mt-3 p-3 rounded-lg text-xs" style={{ background: 'rgba(61,156,240,0.07)', border: '1px solid rgba(61,156,240,0.2)', color: 'var(--muted)' }}>
            <strong style={{ color: 'var(--accent)' }}>Gmail:</strong> enable 2FA → Google Account → Security → App passwords → generate one for "Mail"
          </div>
        </ConfigBlock>

        {/* Telegram setup guide */}
        <ConfigBlock title="Telegram Setup">
          <p className="text-xs leading-relaxed" style={{ color: 'var(--muted)' }}>
            Free, instant, no business approval required. Takes 2 minutes to set up.
          </p>
          <ol className="space-y-2 text-xs" style={{ color: 'var(--muted)' }}>
            <li className="flex gap-2">
              <span className="mono font-bold flex-shrink-0" style={{ color: 'var(--accent)' }}>1.</span>
              <span>Open Telegram → search <strong style={{ color: 'var(--text)' }}>@BotFather</strong> → send <code style={{ color: 'var(--accent)' }}>/newbot</code> → follow prompts → copy the token</span>
            </li>
            <li className="flex gap-2">
              <span className="mono font-bold flex-shrink-0" style={{ color: 'var(--accent)' }}>2.</span>
              <span>Send <code style={{ color: 'var(--accent)' }}>/start</code> to your new bot, then message <strong style={{ color: 'var(--text)' }}>@userinfobot</strong> to get your chat ID</span>
            </li>
            <li className="flex gap-2">
              <span className="mono font-bold flex-shrink-0" style={{ color: 'var(--accent)' }}>3.</span>
              <span>Add to .env and restart:</span>
            </li>
          </ol>
          <div className="space-y-2">
            <EnvRow name="TELEGRAM_BOT_TOKEN" value="1234567890:ABCdef..." secret />
            <EnvRow name="TELEGRAM_CHAT_ID" value="123456789" />
          </div>
        </ConfigBlock>

        {/* What gets notified */}
        <ConfigBlock title="What Gets Notified">
          <div className="space-y-3 text-xs" style={{ color: 'var(--muted)' }}>
            <div className="flex items-start gap-3">
              <span style={{ color: 'var(--warn)' }}>⚡</span>
              <div>
                <strong style={{ color: 'var(--text)' }}>Alert events</strong> — fired immediately when a price threshold or COT extreme rule triggers. Deduped once per rule per day.
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span style={{ color: 'var(--accent)' }}>📊</span>
              <div>
                <strong style={{ color: 'var(--text)' }}>Daily briefing</strong> — sent every day at 07:00 UTC with regime classification, key moves, COT highlights and watchlist.
              </div>
            </div>
          </div>
        </ConfigBlock>

        {/* Cloud deployment guide */}
        <ConfigBlock title="Cloud Deployment">
          <p className="text-xs leading-relaxed" style={{ color: 'var(--muted)' }}>
            GMIT ships as a Docker Compose stack. Deploy to any VPS (Hetzner CX11 €4/mo, DigitalOcean Droplet $6/mo) in minutes.
          </p>
          <div className="space-y-2 text-xs">
            <div className="flex gap-2 items-start">
              <code className="mono flex-shrink-0" style={{ color: 'var(--accent)' }}>1.</code>
              <span style={{ color: 'var(--muted)' }}>SSH into your VPS, install Docker + Docker Compose</span>
            </div>
            <div className="flex gap-2 items-start">
              <code className="mono flex-shrink-0" style={{ color: 'var(--accent)' }}>2.</code>
              <span style={{ color: 'var(--muted)' }}>Clone repo, copy .env.example → .env, fill in values including <code>DOMAIN=</code></span>
            </div>
            <div className="flex gap-2 items-start">
              <code className="mono flex-shrink-0" style={{ color: 'var(--accent)' }}>3.</code>
              <span style={{ color: 'var(--muted)' }}>Point your domain A record at the VPS IP</span>
            </div>
            <div className="flex gap-2 items-start">
              <code className="mono flex-shrink-0" style={{ color: 'var(--accent)' }}>4.</code>
              <span style={{ color: 'var(--muted)' }}>Run <code style={{ color: 'var(--accent)' }}>./deploy.sh</code> — builds images, runs migrations, starts Caddy with auto-HTTPS</span>
            </div>
          </div>
          <div className="mt-3 p-3 rounded-lg text-xs" style={{ background: 'rgba(62,207,142,0.07)', border: '1px solid rgba(62,207,142,0.2)', color: 'var(--muted)' }}>
            <strong style={{ color: 'var(--up)' }}>Caddy</strong> handles HTTPS automatically via Let&apos;s Encrypt — no cert management needed.
          </div>
        </ConfigBlock>

      </div>
    </AppShell>
  );
}
