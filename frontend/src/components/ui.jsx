export function Card({ title, extra, children, className = '' }) {
  return (
    <section className={`card ${className}`}>
      {(title || extra) && (
        <header className="card-head">
          <h3>{title}</h3>
          <div>{extra}</div>
        </header>
      )}
      <div className="card-body">{children}</div>
    </section>
  )
}

export function Button({ children, variant = 'primary', size = 'md', ...rest }) {
  return (
    <button className={`btn btn-${variant} btn-${size}`} {...rest}>
      {children}
    </button>
  )
}

export function Field({ label, children, required, hint }) {
  return (
    <label className="field">
      <span className="field-label">
        {label}
        {required && <i className="req">*</i>}
      </span>
      {hint && <span className="field-hint">{hint}</span>}
      {children}
    </label>
  )
}

export function Tag({ children, tone = 'default' }) {
  return <span className={`tag tag-${tone}`}>{children}</span>
}

export function Empty({ text = '暂无数据' }) {
  return <div className="empty">{text}</div>
}

export function Loading({ text = '加载中…' }) {
  return <div className="page-loading">{text}</div>
}

export function fmtDate(v) {
  return v ? String(v).slice(0, 10) : '—'
}

export function fmtTime(v) {
  if (!v) return '—'
  const s = String(v)
  const iso = s.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(s) ? s : `${s}Z`
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return s.replace('T', ' ').slice(0, 16)
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}
