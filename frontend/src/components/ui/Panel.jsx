export function Panel({ title, subtitle, actions, children }) {
  return (
    <section className="panel p-4 md:p-5">
      <header className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h2 className="panel-title">{title}</h2>
          {subtitle ? <p className="mt-1 text-sm text-slate-400">{subtitle}</p> : null}
        </div>
        {actions ? <div>{actions}</div> : null}
      </header>
      {children}
    </section>
  )
}
