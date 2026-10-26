import type { PropsWithChildren } from 'react'

type StatusBadgeProps = PropsWithChildren

export function StatusBadge({ children }: StatusBadgeProps) {
  return <span className="status-badge" role="status" aria-live="polite"><i aria-hidden="true" />{children}</span>
}
