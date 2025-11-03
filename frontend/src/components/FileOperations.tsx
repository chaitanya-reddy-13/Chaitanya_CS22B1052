import { ChangeEvent, useRef, useState } from "react";

type FileOperationsProps = {
  onUpload: (file: File) => Promise<void>;
  onExport: () => Promise<void>;
};

const FileOperations = ({ onUpload, onExport }: FileOperationsProps) => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await onUpload(file);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (err) {
      setError((err as Error).message ?? "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">Data Ops</h3>
      <div className="mt-4 grid gap-3 text-sm md:grid-cols-2">
        <label className="flex flex-col gap-2 text-slate-300">
          Upload CSV (tick or OHLC)
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            disabled={uploading}
            className="rounded-lg border border-dashed border-slate-700 bg-slate-900/70 p-2 text-xs text-slate-400 focus:border-sky-400 focus:outline-none"
          />
          {error ? <span className="text-xs text-red-400">{error}</span> : null}
        </label>

        <div className="flex flex-col justify-between gap-2">
          <p className="text-xs text-slate-400">
            Download processed data for the current symbol/timeframe as CSV.
          </p>
          <button
            onClick={onExport}
            className="self-start rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:bg-slate-700"
          >
            Export CSV
          </button>
        </div>
      </div>
    </div>
  );
};

export default FileOperations;
