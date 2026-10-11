import { useEffect, useRef, useState, type FormEvent } from "react";
import { X, Radio } from "lucide-react";
import { request, type Monitor, type MonitorInput } from "../services/api";

export default function MonitorForm({
  monitor,
  onClose,
  onSave,
}: {
  monitor: Monitor | null;
  onClose: () => void;
  onSave: (data: MonitorInput) => Promise<void>;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [endpoints, setEndpoints] = useState<Record<string, string>>({});
  const [name, setName] = useState(monitor?.name ?? "");
  const [url, setUrl] = useState(monitor?.url ?? "");
  const [interval, setInterval] = useState(monitor?.check_interval ?? 60);
  const [active, setActive] = useState(monitor?.is_active ?? true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  useEffect(() => {
    dialog.current?.showModal();
    request<Record<string, string>>("/example-endpoints")
      .then(setEndpoints)
      .catch((e) => setError(e.message));
  }, []);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await onSave({ name, url, check_interval: interval, is_active: active });
      onClose();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }
  return (
    <dialog
      ref={dialog}
      onCancel={(e) => {
        if (saving) e.preventDefault();
        else onClose();
      }}
      className="modal"
    >
      <form onSubmit={submit}>
        <div className="modal-heading">
          <span className="icon-box purple">
            <Radio size={22} />
          </span>
          <button
            type="button"
            className="icon-button"
            aria-label="Close dialog"
            disabled={saving}
            onClick={onClose}
          >
            <X size={20} />
          </button>
        </div>
        <h2>{monitor ? "Edit endpoint" : "Add an endpoint"}</h2>
        <p className="muted">
          Good visibility starts with a simple health check.
        </p>
        <label>
          Monitor name
          <input
            autoFocus
            required
            maxLength={100}
            placeholder="e.g. GitHub API"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </label>
        <label>
          Public API endpoint
          <input
            type="url"
            required
            maxLength={2048}
            list="example-endpoints"
            placeholder="https://your-api.com/health"
            value={url}
            readOnly={Boolean(monitor)}
            onChange={(e) => setUrl(e.target.value)}
          />
          <datalist id="example-endpoints">
            {Object.entries(endpoints).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </datalist>
        </label>
        <p className="field-help">
          {monitor
            ? "Endpoint addresses are fixed to preserve their history. Create a new monitor for a different URL."
            : "Paste a public HTTP or HTTPS URL, or choose an example. Local and private network addresses are blocked."}
        </p>
        <label>
          Check interval (seconds)
          <input
            required
            type="number"
            min={30}
            max={86400}
            value={interval}
            onChange={(e) => setInterval(Number(e.target.value))}
          />
        </label>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={active}
            onChange={(e) => setActive(e.target.checked)}
          />
          Enable automatic monitoring
        </label>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <div className="modal-footer">
          <button
            type="button"
            className="button"
            disabled={saving}
            onClick={onClose}
          >
            Cancel
          </button>
          <button className="button primary" disabled={saving}>
            {saving ? "Saving…" : monitor ? "Save changes" : "Create monitor"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
