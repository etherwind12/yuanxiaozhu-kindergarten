import { useEffect, useRef, useState } from 'react'

import { assistantApi } from '../api'
import { errMsg } from '../api/client'
import { useAuth } from '../store/auth'

const QUICK = ['园所资产总体情况', '有多少玩具', '7 天内要消毒的资产有哪些', '哪些借用逾期未还']

export default function Assistant() {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const bodyRef = useRef(null)

  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight
  }, [messages, open])

  const send = async (preset) => {
    const question = (preset ?? text).trim()
    if (!question || busy) return
    setText('')
    setMessages((m) => [...m, { role: 'user', reply: question }])
    setBusy(true)
    try {
      const res = await assistantApi.chat(question)
      setMessages((m) => [...m, { role: 'bot', ...res }])
    } catch (e) {
      setMessages((m) => [...m, { role: 'bot', reply: errMsg(e) }])
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <button className="ai-fab" onClick={() => setOpen((o) => !o)} title="AI 资产助手" aria-label="AI 资产助手">
        {open ? '×' : 'AI'}
      </button>

      {open && (
        <div className="ai-panel">
          <header className="ai-head">
            <div>
              <b>园小助 AI 助手</b>
              <span className="ai-sub">问问资产与园务数据</span>
            </div>
            <button
              className="ai-clear"
              onClick={() => setMessages([])}
              disabled={!messages.length}
              title="清空聊天记录"
            >
              清空
            </button>
          </header>

          <div className="ai-body" ref={bodyRef}>
            <div className="ai-msg bot">
              <div className="ai-bubble">
                你好，{user?.full_name || user?.username}。我可以帮你查询资产、借还、巡检与盘点数据。
                <div className="ai-chips">
                  {QUICK.map((q) => (
                    <button key={q} className="ai-chip" onClick={() => send(q)}>{q}</button>
                  ))}
                </div>
              </div>
            </div>

            {messages.map((m, i) => (
              <div key={i} className={`ai-msg ${m.role}`}>
                <div className="ai-bubble">
                  {m.reply}
                  {!!m.data?.length && (
                    <div className="ai-facts">
                      {m.data.map((d) => (
                        <div className="ai-fact" key={d.label}><span>{d.label}</span><b>{d.value}</b></div>
                      ))}
                    </div>
                  )}
                  {!!m.chart?.length && (
                    <div className="ai-chart">
                      {m.chart.map((c) => {
                        const max = Math.max(1, ...m.chart.map((x) => x.count))
                        return (
                          <div className="ai-chart-row" key={c.name}>
                            <span className="muted">{c.name}</span>
                            <div className="bar" style={{ width: `${Math.max((c.count / max) * 100, 3)}%` }} />
                            <span className="muted">{c.count}</span>
                          </div>
                        )
                      })}
                    </div>
                  )}
                  {!!m.table?.rows?.length && (
                    <table className="ai-table">
                      <thead><tr>{m.table.columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
                      <tbody>
                        {m.table.rows.map((row, ri) => (
                          <tr key={ri}>{row.map((cell, ci) => <td key={ci}>{cell}</td>)}</tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                  {!!m.examples?.length && (
                    <div className="ai-chips">
                      {m.examples.map((q) => (
                        <button key={q} className="ai-chip" onClick={() => send(q)}>{q}</button>
                      ))}
                    </div>
                  )}
                  {m.mode === 'llm' && <div className="ai-mode">由 DeepSeek 生成</div>}
                </div>
              </div>
            ))}
            {busy && <div className="ai-msg bot"><div className="ai-bubble">正在查询…</div></div>}
          </div>

          <div className="ai-foot">
            <input
              value={text}
              placeholder="输入问题，如「有多少玩具」"
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') send() }}
            />
            <button className="btn btn-primary btn-sm" onClick={() => send()} disabled={busy}>发送</button>
          </div>
        </div>
      )}
    </>
  )
}
