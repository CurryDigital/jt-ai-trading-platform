import React from 'react';

export function WorkspaceHeader({ section, title, description, tabs, activeTab, onTab, meta }) {
  return (
    <section className="workspace-header" aria-label={`${title} workspace`}>
      <div className="workspace-heading-row">
        <div className="workspace-heading-copy">
          <div className="workspace-eyebrow">{section}</div>
          <div className="workspace-title-line">
            <h1>{title}</h1>
            {meta && <div className="workspace-heading-meta">{meta}</div>}
          </div>
          {description && <p>{description}</p>}
        </div>
        {tabs?.length > 0 && (
          <nav className="workspace-tabs" aria-label={`${section} sections`}>
            {tabs.map(tab => (
              <button
                key={tab.id}
                type="button"
                onClick={() => onTab(tab.id)}
                className={activeTab === tab.id ? 'active' : ''}
                aria-current={activeTab === tab.id ? 'page' : undefined}
                title={`${tab.label} (${tab.key})`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        )}
      </div>
    </section>
  );
}

export function Panel({ title, subtitle, right, action, children, className = '', flush = false }) {
  const headerAction = right ?? action;
  return (
    <section className={`workspace-panel ${className}`}>
      {(title || headerAction) && (
        <header className="workspace-panel-header">
          <div>
            {title && <h2>{title}</h2>}
            {subtitle && <p>{subtitle}</p>}
          </div>
          {headerAction && <div className="workspace-panel-actions">{headerAction}</div>}
        </header>
      )}
      <div className={flush ? 'workspace-panel-flush' : 'workspace-panel-body'}>{children}</div>
    </section>
  );
}

export function FilterBar({ children, right, className = '' }) {
  return (
    <div className={`workspace-filterbar ${className}`}>
      <div className="workspace-filterbar-main">{children}</div>
      {right && <div className="workspace-filterbar-right">{right}</div>}
    </div>
  );
}

export function LoadingState({ label = 'Loading data…' }) {
  return (
    <div className="workspace-state" role="status">
      <span className="workspace-spinner" />
      <span>{label}</span>
    </div>
  );
}

export function EmptyState({ title, detail }) {
  return (
    <div className="workspace-state workspace-empty">
      <strong>{title}</strong>
      {detail && <span>{detail}</span>}
    </div>
  );
}

export function DataTable({
  columns,
  rows,
  rowKey,
  onRowClick,
  selectedKey,
  sort,
  onSort,
  empty = 'No records match this view.',
  minWidth = 760,
  ariaLabel = 'Data table',
  dense = false,
  rowClassName,
}) {
  return (
    <div className="jt-table-wrap" role="region" aria-label={`${ariaLabel}. Scroll horizontally for all columns.`} tabIndex={0}>
      <table className={`jt-table ${dense ? 'jt-table-dense' : ''}`} style={{ minWidth }}>
        <thead>
          <tr>
            {columns.map(col => {
              const columnSortKey = col.sortKey || (col.sortable ? col.key : null);
              const sortable = Boolean(onSort && columnSortKey);
              const active = sortable && sort?.key === columnSortKey;
              return (
                <th
                  key={col.key || col.label}
                  className={`${col.align === 'right' || col.numeric ? 'num' : ''} ${col.className || ''}`}
                  style={col.width ? { width: col.width } : undefined}
                  aria-sort={active ? (sort.dir === 'asc' ? 'ascending' : 'descending') : undefined}
                >
                  {sortable ? (
                    <button type="button" onClick={() => onSort(columnSortKey)} className="jt-sort-button">
                      {col.label}<span aria-hidden="true">{active ? (sort.dir === 'asc' ? ' ↑' : ' ↓') : ''}</span>
                    </button>
                  ) : col.label}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr><td colSpan={columns.length} className="jt-table-empty">{empty}</td></tr>
          ) : rows.map((row, index) => {
            const key = rowKey ? rowKey(row, index) : row.id ?? index;
            const clickable = Boolean(onRowClick);
            return (
              <tr
                key={key}
                onClick={clickable ? () => onRowClick(row) : undefined}
                className={`${clickable ? 'clickable' : ''} ${selectedKey != null && selectedKey === key ? 'selected' : ''} ${typeof rowClassName === 'function' ? rowClassName(row, index) : rowClassName || ''}`}
              >
                {columns.map(col => {
                  const value = col.render ? col.render(row, index) : row[col.key];
                  return (
                    <td
                      key={col.key || col.label}
                      className={`${col.align === 'right' || col.numeric ? 'num' : ''} ${typeof col.cellClassName === 'function' ? col.cellClassName(row, index) : col.cellClassName || ''}`}
                      title={col.title ? col.title(row, index) : undefined}
                    >
                      {value == null || value === '' ? '—' : value}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
