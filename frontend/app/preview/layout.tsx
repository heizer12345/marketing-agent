/** Preview routes scroll inside the app shell (root main uses overflow-hidden). */
export default function PreviewLayout({ children }: { children: React.ReactNode }) {
  return <div className="flex flex-col flex-1 min-h-0 h-full w-full">{children}</div>;
}
