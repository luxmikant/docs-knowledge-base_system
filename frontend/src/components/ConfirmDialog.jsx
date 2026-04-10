export default function ConfirmDialog({ isOpen, title, message, confirmText, cancelText, onConfirm, onCancel, isDestructive }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-content confirm-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
        </div>

        <div className="modal-body">
          <p>{message}</p>
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onCancel}>
            {cancelText || 'Cancel'}
          </button>
          <button
            className={isDestructive ? 'btn-danger' : 'btn-primary'}
            onClick={onConfirm}
          >
            {confirmText || 'Confirm'}
          </button>
        </div>
      </div>
    </div>
  );
}
