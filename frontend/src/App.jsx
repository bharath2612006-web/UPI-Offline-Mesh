import { useCallback, useEffect, useState } from 'react'

const API = import.meta.env.VITE_API_BASE_URL ?? '';
const money = n => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(Number(n || 0))
const shortId = value => value ? `${value.slice(0, 8)}…` : '—'

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.detail || data.reason || `Request failed (${response.status})`)
  return data
}

function Icon({ children }) { return <span className="icon" aria-hidden="true">{children}</span> }

export default function App() {
  const [accounts, setAccounts] = useState([])
  const [transactions, setTransactions] = useState([])
  const [devices, setDevices] = useState([])
  const [form, setForm] = useState({ sender: 'alice@offline', receiver: 'bob@offline', amount: '500', pin: '1234' })
  const [busy, setBusy] = useState('')
  const [notice, setNotice] = useState({ type: '', text: '' })
  const [lastPacket, setLastPacket] = useState(null)

  const refresh = useCallback(async () => {
    try {
      const [a, t, d] = await Promise.all([
        request('/api/accounts'), request('/api/transactions'), request('/api/mesh/state')
      ])
      setAccounts(a); setTransactions(t); setDevices(d)
    } catch (e) {
      setNotice({ type: 'error', text: `Backend unavailable: ${e.message}. Start FastAPI on port 8080.` })
    }
  }, [])

  useEffect(() => {
    refresh()
    const timer = setInterval(refresh, 6000)
    return () => clearInterval(timer)
  }, [refresh])

  async function runAction(label, path, body) {
    setBusy(label); setNotice({ type: '', text: '' })
    try {
      const result = await request(path, {
        method: 'POST',
        ...(body ? { body: JSON.stringify(body) } : {})
      })
      if (result.packet) setLastPacket(result.packet)
      setNotice({ type: 'success', text: label === 'send' ? 'Encrypted payment packet injected into the offline mesh.' : `${label} completed successfully.` })
      await refresh()
      return result
    } catch (e) {
      setNotice({ type: 'error', text: e.message })
    } finally { setBusy('') }
  }

  function submitPayment(e) {
    e.preventDefault()
    const amount = Number(form.amount)
    if (!Number.isFinite(amount) || amount <= 0) {
      setNotice({ type: 'error', text: 'Enter an amount greater than zero.' }); return
    }
    if (form.sender === form.receiver) {
      setNotice({ type: 'error', text: 'Sender and receiver must be different.' }); return
    }
    runAction('send', '/api/demo/send', { ...form, amount })
  }

  const totalBalance = accounts.reduce((sum, a) => sum + Number(a.balance || 0), 0)
  const settledCount = transactions.filter(t => t.status === 'SETTLED').length
  const queuedCount = devices.reduce((sum, d) => sum + d.packetCount, 0)

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><Icon>◈</Icon></div><div><strong>meshpay</strong><small>OFFLINE NETWORK</small></div></div>
      <div className="nav-label">WORKSPACE</div>
      <a className="nav-item active" href="#overview"><Icon>▦</Icon> Overview</a>
      <a className="nav-item" href="#payment"><Icon>↗</Icon> Send payment</a>
      <a className="nav-item" href="#network"><Icon>⌘</Icon> Mesh network</a>
      <a className="nav-item" href="#activity"><Icon>≡</Icon> Transactions</a>
      <div className="sidebar-bottom"><div className="connection-dot"></div><div><strong>Simulation mode</strong><small>Not connected to UPI rails</small></div></div>
    </aside>

    <main className="main">
      <header className="topbar">
        <div><div className="eyebrow">PAYMENT INFRASTRUCTURE / DEMO</div><h1>Network overview</h1></div>
        <div className="top-actions"><span className="live-pill"><i/> LOCAL ENVIRONMENT</span><button className="icon-button" onClick={refresh} title="Refresh">↻</button><div className="avatar">BU</div></div>
      </header>

      {notice.text && <div className={`notice ${notice.type}`} role="status">{notice.text}<button onClick={() => setNotice({type:'',text:''})}>×</button></div>}

      <section className="metrics" id="overview">
        <article className="metric-card"><div className="metric-top"><span>Total demo balance</span><span className="metric-icon blue">₹</span></div><strong>{money(totalBalance)}</strong><small>Across {accounts.length} demo accounts</small></article>
        <article className="metric-card"><div className="metric-top"><span>Settled transactions</span><span className="metric-icon green">✓</span></div><strong>{settledCount}</strong><small>Recorded in the ledger</small></article>
        <article className="metric-card"><div className="metric-top"><span>Packets in mesh</span><span className="metric-icon purple">⌘</span></div><strong>{queuedCount}</strong><small>Copies held by virtual devices</small></article>
      </section>

      <section className="content-grid">
        <article className="panel payment-panel" id="payment">
          <div className="panel-heading"><div><div className="eyebrow">OFFLINE TRANSFER</div><h2>Initiate payment</h2></div><span className="secure-tag">⌑ Encrypted</span></div>
          <p className="muted">Create an encrypted payment packet while the sender is offline. Settlement happens after a bridge device reconnects.</p>
          <form onSubmit={submitPayment}>
            <label>FROM ACCOUNT<select value={form.sender} onChange={e => setForm({...form, sender:e.target.value})}>{accounts.map(a => <option key={a.id} value={a.upiId}>{a.name} · {a.upiId}</option>)}</select></label>
            <div className="transfer-arrow">↓</div>
            <label>TO ACCOUNT<select value={form.receiver} onChange={e => setForm({...form, receiver:e.target.value})}>{accounts.map(a => <option key={a.id} value={a.upiId}>{a.name} · {a.upiId}</option>)}</select></label>
            <div className="form-row">
              <label>AMOUNT (INR)<input type="number" min="1" step="0.01" value={form.amount} onChange={e => setForm({...form, amount:e.target.value})} required /></label>
              <label>DEMO PIN<input type="password" inputMode="numeric" minLength="4" maxLength="8" value={form.pin} onChange={e => setForm({...form, pin:e.target.value})} required /></label>
            </div>
            <button className="primary-button" disabled={!!busy || accounts.length < 2}>{busy === 'send' ? 'Encrypting packet…' : '↗  Create offline payment'}</button>
          </form>
          {lastPacket && <div className="packet-note"><strong>Latest packet created</strong><code>{shortId(lastPacket.packetId)}</code><small>TTL: {lastPacket.ttl} hops · Ciphertext generated</small></div>}
          <div className="warning-note">Demo only: this does not connect to banks, NPCI or real UPI accounts. Never enter a real UPI PIN.</div>
        </article>

        <article className="panel network-panel" id="network">
          <div className="panel-heading"><div><div className="eyebrow">PEER-TO-PEER SIMULATION</div><h2>Mesh network</h2></div><span className="device-count">{devices.length} DEVICES</span></div>
          <p className="muted">Packets propagate between virtual devices through gossip rounds. The bridge device can upload packets to the backend.</p>
          <div className="device-list">{devices.map(d => <div className="device" key={d.deviceId}>
            <div className={`device-symbol ${d.hasInternet ? 'bridge' : ''}`}>{d.hasInternet ? '⇧' : '▣'}</div>
            <div className="device-info"><strong>{d.deviceId}</strong><small>{d.hasInternet ? 'Internet bridge' : 'Offline peer'}</small></div>
            <div className="device-packets">{d.packetCount}<small>packets</small></div>
            <span className={`status ${d.hasInternet ? 'online' : 'offline'}`}>{d.hasInternet ? 'ONLINE' : 'OFFLINE'}</span>
          </div>)}</div>
          <div className="mesh-actions">
            <button className="secondary-button" disabled={!!busy} onClick={() => runAction('gossip', '/api/mesh/gossip')}>⤳ Run gossip round</button>
            <button className="primary-button" disabled={!!busy} onClick={() => runAction('bridge upload', '/api/mesh/flush')}>⇧ Upload via bridge</button>
            <button className="text-button" disabled={!!busy} onClick={() => runAction('reset', '/api/mesh/reset')}>Reset network</button>
          </div>
        </article>
      </section>

      <section className="panel accounts-panel">
        <div className="panel-heading"><div><div className="eyebrow">DEMO LEDGER</div><h2>Account balances</h2></div><span className="subtle-count">{accounts.length} ACCOUNTS</span></div>
        <div className="table-wrap"><table><thead><tr><th>ACCOUNT HOLDER</th><th>UPI ID</th><th>AVAILABLE BALANCE</th><th>STATUS</th></tr></thead><tbody>
          {accounts.map(a => <tr key={a.id}><td><div className="holder"><span className="holder-avatar">{a.name?.[0]}</span><strong>{a.name}</strong></div></td><td className="mono">{a.upiId}</td><td className="amount">{money(a.balance)}</td><td><span className="status online">ACTIVE</span></td></tr>)}
          {!accounts.length && <tr><td colSpan="4" className="empty">Waiting for backend data…</td></tr>}
        </tbody></table></div>
      </section>

      <section className="panel activity-panel" id="activity">
        <div className="panel-heading"><div><div className="eyebrow">RECENT ACTIVITY</div><h2>Transaction history</h2></div><span className="subtle-count">LATEST 20</span></div>
        <div className="table-wrap"><table><thead><tr><th>TRANSACTION</th><th>FROM</th><th>TO</th><th>AMOUNT</th><th>STATUS</th><th>TIME</th></tr></thead><tbody>
          {transactions.map(t => <tr key={t.id}><td className="mono">#{t.id} · {shortId(t.packetHash)}</td><td>{t.sender}</td><td>{t.receiver}</td><td className="amount">{money(t.amount)}</td><td><span className={`status ${t.status === 'SETTLED' ? 'online' : 'offline'}`}>{t.status}</span></td><td className="muted">{new Date(t.createdAt).toLocaleString()}</td></tr>)}
          {!transactions.length && <tr><td colSpan="6" className="empty">No settled transactions yet. Create a payment and upload it through the bridge.</td></tr>}
        </tbody></table></div>
      </section>
      <footer>MESHPAY SIMULATION <span>Built with React + FastAPI</span><span>Educational prototype · Not real UPI</span></footer>
    </main>
  </div>
}
