import React, { useState, useCallback, useRef } from 'react';

let _nextId = 0;

const STYLE = {
  info:    'bg-blue-500/15 text-blue-200 ring-1 ring-blue-500/25',
  success: 'bg-emerald-500/15 text-emerald-200 ring-1 ring-emerald-500/25',
  warning: 'bg-amber-500/15 text-amber-200 ring-1 ring-amber-500/25',
  error:   'bg-rose-500/15 text-rose-200 ring-1 ring-rose-500/25',
};

export function useToasts(maxVisible = 5) {
  const [toasts, setToasts] = useState([]);
  const timersRef = useRef({});

  const dismiss = useCallback((id) => {
    clearTimeout(timersRef.current[id]);
    delete timersRef.current[id];
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const push = useCallback((msg, level = 'info', durationMs = 6000) => {
    const id = ++_nextId;
    setToasts(prev => [...prev.slice(-(maxVisible - 1)), { id, msg, level }]);
    timersRef.current[id] = setTimeout(() => dismiss(id), durationMs);
    return id;
  }, [dismiss, maxVisible]);

  return { toasts, push, dismiss };
}

export const ToastContainer = ({ toasts, dismiss }) => {
  if (!toasts.length) return null;
  return (
    <div className="fixed bottom-4 right-4 z-[999] flex flex-col gap-1.5 max-w-xs pointer-events-none">
      {toasts.map(t => (
        <div
          key={t.id}
          onClick={() => dismiss(t.id)}
          className={`pointer-events-auto px-3 py-2 rounded-lg text-[11px] font-semibold cursor-pointer shadow-lg backdrop-blur-lg animate-slide-in ${STYLE[t.level] || STYLE.info}`}
        >
          {t.msg}
        </div>
      ))}
    </div>
  );
};
