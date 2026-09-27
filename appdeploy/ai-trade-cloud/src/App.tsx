import { useEffect, useState } from 'react';
import { api } from '@appdeploy/client';

type Status = {
  mode: string;
  liveMoneyLocked: boolean;
  strategy: string;
  symbol: string;
  timeframe: string;
  exitMode: string;
  engineStatus: string;
  brokerConnected: boolean;
  lastTick: string | null;
  lastAction: string | null;
  lastError: string | null;
  credentials: Record<string, boolean>;
  scheduler: string;
  recentEvents: Array<{ at: string; result: string; detail?: string }>;
};

function App() {
  const [status, setStatus] = useState<Status | null>(null);
  const [error, setError] = useState('');
  const load = async () => {
    try {
      const res = await api.get('/api/status');
      setStatus(res.data);
      setError('');
    } catch {
      setError('Không đọc được trạng thái cloud.');
    }
  };
  useEffect(() => {
    void load();
    const id = setInterval(() => void load(), 30000);
    return () => clearInterval(id);
  }, []);
  const ready = status && Object.values(status.credentials).every(Boolean);
  return (
    <main className="shell">
      <section className="hero">
        <div>
          <p className="eyebrow">AI-TRADE CLOUD</p>
          <h1>MT5 DEMO tự động, không cần PC</h1>
          <p className="sub">
            Trend Following phản ứng theo nến đóng. Live-money bị khóa cứng.
          </p>
        </div>
        <button onClick={() => void load()}>Làm mới</button>
      </section>
      {error && <div className="alert">{error}</div>}
      {!status ? (
        <div className="card">Đang đọc trạng thái…</div>
      ) : (
        <>
          <section className="grid">
            <div className="card">
              <span>Chế độ</span>
              <strong>{status.mode}</strong>
              <small>
                {status.liveMoneyLocked ? '🔒 Live money locked' : 'Cảnh báo'}
              </small>
            </div>
            <div className="card">
              <span>Engine</span>
              <strong>{status.engineStatus}</strong>
              <small>
                {status.brokerConnected
                  ? 'Broker connected'
                  : 'Broker chưa kết nối'}
              </small>
            </div>
            <div className="card">
              <span>Strategy</span>
              <strong>
                {status.symbol} · {status.timeframe}
              </strong>
              <small>{status.exitMode}</small>
            </div>
            <div className="card">
              <span>Scheduler</span>
              <strong>{status.scheduler}</strong>
              <small>
                {status.lastTick
                  ? new Date(status.lastTick).toLocaleString()
                  : 'Chưa chạy tick'}
              </small>
            </div>
          </section>
          <section className="card wide">
            <h2>Cấu hình an toàn</h2>
            <div className="secretGrid">
              {Object.entries(status.credentials).map(([key, value]) => (
                <div key={key} className="secret">
                  <span>{key}</span>
                  <b>{value ? '✓ Đã cấu hình' : '• Chưa cấu hình'}</b>
                </div>
              ))}
            </div>
            <p className={ready ? 'ok' : 'muted'}>
              {ready
                ? 'Secret đã đủ. Cron vẫn chỉ giao dịch tài khoản MT5 DEMO.'
                : 'Thiếu secret nên engine tự khóa, không thể gửi lệnh.'}
            </p>
          </section>
          <section className="card wide">
            <h2>Hoạt động gần nhất</h2>
            <p>
              <b>Hành động:</b> {status.lastAction ?? 'Chưa có'}
            </p>
            {status.lastError && (
              <p className="danger">
                <b>Lỗi:</b> {status.lastError}
              </p>
            )}
            <div className="events">
              {status.recentEvents.length ? (
                status.recentEvents.map((event, i) => (
                  <div className="event" key={i}>
                    <time>{new Date(event.at).toLocaleString()}</time>
                    <b>{event.result}</b>
                    <span>{event.detail ?? ''}</span>
                  </div>
                ))
              ) : (
                <p className="muted">Chưa có event.</p>
              )}
            </div>
          </section>
        </>
      )}
    </main>
  );
}
export default App;
