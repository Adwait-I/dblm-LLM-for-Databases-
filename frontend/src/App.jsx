import { Database, Send, Loader2, Table2, ArrowRight } from 'lucide-react'
import Prism from 'prismjs'
import 'prismjs/components/prism-sql'
import { useEffect, useRef, useState } from 'react'
import { askQuestion, fetchHealth, fetchTables } from './api'
import './index.css'

/* ------------------------------------------------------------------ */
/* Sidebar — schema explorer                                          */
/* ------------------------------------------------------------------ */
function Sidebar({ tables, isOpen }) {
  return (
    <aside
      className={`
        fixed left-0 top-0 bottom-0 z-30 w-72
        bg-surface-50 border-r border-surface-300
        flex flex-col transition-transform duration-300
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0 lg:static lg:shrink-0
      `}
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-5 py-4 border-b border-surface-300">
        <Database className="w-5 h-5 text-brand-400" />
        <h2 className="text-sm font-semibold tracking-wide uppercase text-white/70">
          Schema Explorer
        </h2>
      </div>

      {/* Table list */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-1">
        {tables.length === 0 && (
          <p className="text-xs text-white/30 px-2 py-4">Loading schema…</p>
        )}
        {tables.map((t) => (
          <div
            key={t.name}
            className="group px-3 py-2.5 rounded-lg hover:bg-surface-200 transition-colors cursor-default"
          >
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Table2 className="w-4 h-4 text-brand-300 group-hover:text-brand-400 transition-colors" />
                <span className="text-sm font-medium text-white/90">{t.name}</span>
              </span>
              <span className="text-[11px] tabular-nums text-white/30">
                {t.row_count} rows
              </span>
            </div>
            <div className="mt-1 flex items-center gap-2 text-[11px] text-white/30">
              <span>{t.column_count} cols</span>
              <span>·</span>
              <span>PK: {t.primary_keys?.join(', ') || '—'}</span>
            </div>
          </div>
        ))}
      </div>
    </aside>
  )
}

/* ------------------------------------------------------------------ */
/* SQL code block                                                     */
/* ------------------------------------------------------------------ */
function SqlBlock({ sql }) {
  const ref = useRef(null)

  useEffect(() => {
    if (ref.current) Prism.highlightElement(ref.current)
  }, [sql])

  return (
    <pre className="rounded-lg bg-surface-100 border border-surface-300 p-4 overflow-x-auto text-sm">
      <code ref={ref} className="language-sql">
        {sql}
      </code>
    </pre>
  )
}

/* ------------------------------------------------------------------ */
/* Results table                                                      */
/* ------------------------------------------------------------------ */
function ResultsTable({ columns, rows }) {
  if (!columns || columns.length === 0) return null

  return (
    <div className="overflow-x-auto rounded-lg border border-surface-300">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-surface-200">
            {columns.map((col) => (
              <th
                key={col}
                className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-brand-300 border-b border-surface-300"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={i}
              className="border-b border-surface-200 hover:bg-surface-100/50 transition-colors"
            >
              {row.map((cell, j) => (
                <td key={j} className="px-4 py-2.5 text-white/80 font-mono text-xs">
                  {cell === null ? <span className="text-white/20 italic">NULL</span> : String(cell)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Typing indicator                                                   */
/* ------------------------------------------------------------------ */
function TypingIndicator() {
  return (
    <div className="flex items-center gap-3 px-5 py-4">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-xs font-bold">
        Q
      </div>
      <div className="glass rounded-2xl px-5 py-3 flex items-center gap-1.5">
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Chat message                                                       */
/* ------------------------------------------------------------------ */
function ChatMessage({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 px-5 py-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-8 h-8 shrink-0 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-xs font-bold shadow-lg shadow-brand-500/20">
          Q
        </div>
      )}

      <div className={`max-w-2xl space-y-3 ${isUser ? 'items-end' : ''}`}>
        {/* Text bubble */}
        {isUser ? (
          <div className="bg-brand-600 text-white rounded-2xl rounded-br-md px-5 py-3 text-sm shadow-lg shadow-brand-600/20">
            {message.text}
          </div>
        ) : (
          <div className="space-y-4">
            {message.error && (
              <div className="glass rounded-2xl px-5 py-3 border-accent-rose/30 text-accent-rose text-sm">
                ⚠ {message.error}
              </div>
            )}

            {message.sql && (
              <div className="space-y-2">
                <p className="text-xs font-medium text-white/40 uppercase tracking-wider">
                  Generated SQL
                </p>
                <SqlBlock sql={message.sql} />
              </div>
            )}

            {message.columns && message.rows && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-medium text-white/40 uppercase tracking-wider">
                    Results
                  </p>
                  <span className="text-[11px] text-white/30 tabular-nums">
                    {message.row_count} row{message.row_count !== 1 ? 's' : ''}
                    {message.execution_time_ms != null && (
                      <> · {message.execution_time_ms}ms</>
                    )}
                    {message.attempts > 1 && (
                      <> · {message.attempts} attempts</>
                    )}
                  </span>
                </div>
                <ResultsTable columns={message.columns} rows={message.rows} />
              </div>
            )}
          </div>
        )}
      </div>

      {isUser && (
        <div className="w-8 h-8 shrink-0 rounded-full bg-surface-300 flex items-center justify-center text-xs font-bold text-white/60">
          U
        </div>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Suggested queries                                                  */
/* ------------------------------------------------------------------ */
const SUGGESTIONS = [
  'How many employees are in each department?',
  'Show me the top 5 highest paid employees',
  'Which employees have dependents?',
  'List all departments and their locations',
]

function SuggestedQueries({ onSelect }) {
  return (
    <div className="flex flex-col items-center justify-center flex-1 px-6 py-12 space-y-8">
      {/* Hero */}
      <div className="text-center space-y-3">
        <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center glow">
          <Database className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-brand-300 to-accent-cyan bg-clip-text text-transparent">
          QueryMind
        </h1>
        <p className="text-white/40 max-w-md text-sm">
          Ask questions about your database in plain English. I'll write the SQL and fetch results for you.
        </p>
      </div>

      {/* Suggestion chips */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onSelect(s)}
            className="group text-left glass rounded-xl px-4 py-3 text-sm text-white/60 hover:text-white hover:border-brand-500/40 transition-all duration-200 cursor-pointer"
          >
            <span className="flex items-center justify-between gap-2">
              <span>{s}</span>
              <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 text-brand-400 transition-opacity" />
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Main App                                                           */
/* ------------------------------------------------------------------ */
export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [tables, setTables] = useState([])
  const [health, setHealth] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const chatEndRef = useRef(null)
  const inputRef = useRef(null)

  // Load schema + health on mount
  useEffect(() => {
    fetchTables().then(setTables).catch(console.error)
    fetchHealth().then(setHealth).catch(console.error)
  }, [])

  // Auto-scroll on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function handleSubmit(e) {
    e?.preventDefault()
    const question = input.trim()
    if (!question || loading) return

    setInput('')
    setMessages((prev) => [...prev, { role: 'user', text: question }])
    setLoading(true)

    try {
      const result = await askQuestion(question)
      setMessages((prev) => [...prev, { role: 'assistant', ...result }])
    } catch (err) {
      const detail = err.response?.data?.detail || err.message
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', error: detail },
      ])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  function handleSuggestion(text) {
    setInput(text)
    // Submit on next tick so input is set
    setTimeout(() => {
      setInput('')
      setMessages((prev) => [...prev, { role: 'user', text }])
      setLoading(true)
      askQuestion(text)
        .then((result) =>
          setMessages((prev) => [...prev, { role: 'assistant', ...result }])
        )
        .catch((err) => {
          const detail = err.response?.data?.detail || err.message
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', error: detail },
          ])
        })
        .finally(() => setLoading(false))
    }, 0)
  }

  const hasMessages = messages.length > 0

  return (
    <div className="flex h-dvh overflow-hidden">
      {/* Sidebar */}
      <Sidebar tables={tables} isOpen={sidebarOpen} />

      {/* Overlay for mobile sidebar */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="flex items-center gap-3 px-5 py-3 border-b border-surface-300 bg-surface-50/80 backdrop-blur-sm shrink-0">
          <button
            type="button"
            className="lg:hidden p-2 rounded-lg hover:bg-surface-200 transition-colors text-white/60"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            <Database className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center">
              <Database className="w-4 h-4 text-white" />
            </div>
            <h1 className="text-lg font-semibold text-white">QueryMind</h1>
          </div>

          <div className="ml-auto flex items-center gap-2">
            {health && (
              <span className="flex items-center gap-1.5 text-xs text-white/30">
                <span
                  className={`w-2 h-2 rounded-full ${
                    health.status === 'healthy' ? 'bg-accent-green' : 'bg-accent-amber'
                  }`}
                />
                {health.status === 'healthy' ? 'Connected' : 'Degraded'}
              </span>
            )}
          </div>
        </header>

        {/* Chat area */}
        <div className="flex-1 overflow-y-auto">
          {!hasMessages ? (
            <SuggestedQueries onSelect={handleSuggestion} />
          ) : (
            <div className="max-w-4xl mx-auto">
              {messages.map((msg, i) => (
                <ChatMessage key={i} message={msg} />
              ))}
              {loading && <TypingIndicator />}
              <div ref={chatEndRef} />
            </div>
          )}
        </div>

        {/* Input bar */}
        <div className="shrink-0 border-t border-surface-300 bg-surface-50/80 backdrop-blur-sm px-5 py-4">
          <form
            onSubmit={handleSubmit}
            className="max-w-4xl mx-auto flex items-center gap-3"
          >
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your database…"
              disabled={loading}
              className="flex-1 bg-surface-100 border border-surface-300 rounded-xl px-4 py-3 text-sm text-white placeholder-white/30 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500/30 transition-all disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="w-11 h-11 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:bg-surface-300 disabled:text-white/20 flex items-center justify-center transition-all duration-200 cursor-pointer disabled:cursor-not-allowed shadow-lg shadow-brand-600/20 disabled:shadow-none"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </form>
          <p className="text-center text-[11px] text-white/20 mt-2">
            Powered by Qwen 2.5 Coder · Read-only queries · Self-correcting pipeline
          </p>
        </div>
      </main>
    </div>
  )
}
