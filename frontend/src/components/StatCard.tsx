interface StatCardProps {
  label: string;
  value: React.ReactNode;
  helper?: string;
}

const StatCard = ({ label, value, helper }: StatCardProps) => (
  <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 shadow">
    <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
    <p className="mt-2 text-2xl font-semibold text-sky-200">{value}</p>
    {helper ? <p className="mt-2 text-xs text-slate-400">{helper}</p> : null}
  </div>
);

export default StatCard;

