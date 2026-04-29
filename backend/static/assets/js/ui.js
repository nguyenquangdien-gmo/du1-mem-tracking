// Shared UI helpers: toast, modal, formatting.
const UI = (() => {
  let toastHost = null;

  function ensureToastHost() {
    if (!toastHost) {
      toastHost = document.createElement("div");
      toastHost.className = "toast-host";
      document.body.appendChild(toastHost);
    }
    return toastHost;
  }

  function toast(message, type = "info", duration = 2800) {
    const host = ensureToastHost();
    const el = document.createElement("div");
    el.className = "toast" + (type === "error" ? " error" : type === "success" ? " success" : "");
    el.textContent = message;
    host.appendChild(el);
    setTimeout(() => {
      el.style.opacity = "0";
      el.style.transition = "opacity .3s";
      setTimeout(() => el.remove(), 300);
    }, duration);
  }

  function handleError(err) {
    console.error(err);
    const msg = (err && (err.message || err.code)) || "Có lỗi xảy ra";
    toast(msg, "error");
  }

  function esc(s) {
    if (s === null || s === undefined) return "";
    return String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c]));
  }

  function initials(name) {
    if (!name) return "?";
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }

  function colorFromName(name) {
    const colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6", "#6366f1", "#f97316"];
    let h = 0;
    for (const c of (name || "")) h = (h * 31 + c.charCodeAt(0)) >>> 0;
    return colors[h % colors.length];
  }

  function avatarHTML(name) {
    const color = colorFromName(name || "");
    return `<span class="avatar" title="${esc(name || "")}" style="background:${color}">${esc(initials(name))}</span>`;
  }

  function avatarStack(members, max = 5) {
    const list = members || [];
    const count = list.length;
    const items = list.slice(0, max);
    let html = '<div class="avatar-stack">';
    items.forEach(m => html += avatarHTML(m.member_name || m.full_name));
    if (count > max) html += `<span class="avatar-more">+${count - max}</span>`;
    html += '</div>';
    return html;
  }

  function hasPermission(action, resource = "") {
    const user = auth.getUser();
    if (!user) return false;
    const role = user.role;
    
    if (role === "admin") return true;
    if (role === "pm") {
      // PM can manage Projects and Members
      if (resource === "projects" || resource === "members") return true;
      if (action === "read") return true;
      return false;
    }
    // Member is read-only
    return action === "read";
  }

  function applyPermissions() {
    document.querySelectorAll("[data-action]").forEach(el => {
      const action = el.getAttribute("data-action");
      const resource = el.getAttribute("data-resource");
      if (!hasPermission(action, resource)) {
        el.style.display = "none";
      }
    });
  }

  function fmtDate(d) {
    if (!d) return "—";
    try {
      const dt = typeof d === "string" ? new Date(d) : d;
      if (isNaN(dt.getTime())) return String(d);
      const yyyy = dt.getFullYear();
      const mm = String(dt.getMonth() + 1).padStart(2, "0");
      const dd = String(dt.getDate()).padStart(2, "0");
      return `${yyyy}-${mm}-${dd}`;
    } catch {
      return String(d);
    }
  }

  function daysUntil(dateStr) {
    if (!dateStr) return null;
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return null;
    const today = new Date(); today.setHours(0, 0, 0, 0);
    return Math.ceil((d.getTime() - today.getTime()) / 86400000);
  }

  // Modal singleton -----------------------------------------------------
  function openModal({ title, bodyHTML, confirmText = "Xác nhận", cancelText = "Huỷ", onConfirm, onOpen }) {
    return new Promise((resolve) => {
      const backdrop = document.createElement("div");
      backdrop.className = "ui-modal-backdrop open";
      backdrop.innerHTML = `
        <div class="ui-modal" role="dialog">
          <div class="ui-modal-header">
            <h3>${esc(title)}</h3>
            <button class="close" aria-label="close">×</button>
          </div>
          <div class="ui-modal-body">${bodyHTML || ""}</div>
          <div class="ui-modal-footer">
            <button class="btn btn-cancel">${esc(cancelText)}</button>
            <button class="btn btn-primary btn-confirm">${esc(confirmText)}</button>
          </div>
        </div>`;
      document.body.appendChild(backdrop);
      const close = (val) => { backdrop.remove(); resolve(val); };
      backdrop.querySelector(".close").onclick = () => close(null);
      backdrop.querySelector(".btn-cancel").onclick = () => close(null);
      backdrop.querySelector(".btn-confirm").onclick = async () => {
        try {
          const res = onConfirm ? await onConfirm(backdrop) : true;
          if (res !== false) close(res);
        } catch (e) {
          handleError(e);
        }
      };
      backdrop.addEventListener("click", (e) => { if (e.target === backdrop) close(null); });
      if (onOpen) onOpen(backdrop);
    });
  }

  async function confirmDialog(message, title = "Xác nhận") {
    return new Promise((resolve) => {
      openModal({
        title,
        bodyHTML: `<p>${esc(message)}</p>`,
        confirmText: "Đồng ý",
        cancelText: "Huỷ",
        onConfirm: () => true,
      }).then((v) => resolve(v === true));
    });
  }

  function loading(message = "Đang xử lý...") {
    const backdrop = document.createElement("div");
    backdrop.className = "ui-modal-backdrop open loading-backdrop";
    backdrop.style.zIndex = "9999";
    backdrop.innerHTML = `
      <div class="glass-card text-center p-4" style="min-width: 200px">
        <div class="spinner-border text-primary mb-3" role="status"></div>
        <div class="fw-bold">${esc(message)}</div>
      </div>`;
    document.body.appendChild(backdrop);
    return {
      close: () => backdrop.remove()
    };
  }

  function qs(name, def = null) {
    const v = new URL(location.href).searchParams.get(name);
    return v === null ? def : v;
  }

  async function showMemberDetails(memberId) {
    if (window.event) window.event.stopPropagation();
    try {
        const resp = await api.get('/members/' + memberId + '/assignments');
        if (resp && resp.success) {
            const data = resp.data;
            const m = data.member;
            const projects = data.projects || [];
            
            const existingModal = document.getElementById('global-member-details-modal');
            if (existingModal) existingModal.remove();
            
            const rolesHtml = (m.other_roles || []).map(r => `<span class="badge bg-primary-subtle text-primary border border-primary-subtle me-1">${esc(r)}</span>`).join('');
            
            let projectsHtml = '';
            if (projects.length > 0) {
                projectsHtml = `
                <div class="mt-4 pt-3 border-top">
                    <div class="small fw-bold text-secondary text-uppercase mb-2">Dự án đang tham gia (${data.stats.active_projects})</div>
                    <div class="list-group list-group-flush border rounded-3 overflow-hidden">
                        ${projects.map(p => `
                            <div class="list-group-item d-flex justify-content-between align-items-center py-2 px-3">
                                <div>
                                    <div class="fw-bold small text-dark">${esc(p.project_name)}</div>
                                    <div class="text-secondary" style="font-size: 0.75rem">${esc(p.role || 'Thành viên')}</div>
                                </div>
                                <div class="text-end">
                                    <div class="badge bg-light text-dark border fw-normal" style="font-size: 0.7rem">${fmtDate(p.expected_end_date)}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>`;
            } else {
                projectsHtml = `
                <div class="mt-4 pt-3 border-top">
                    <div class="small fw-bold text-secondary text-uppercase mb-2">Dự án đang tham gia</div>
                    <div class="text-center py-3 bg-light rounded-3 text-muted small">Đang không tham gia dự án nào</div>
                </div>`;
            }

            const html = `
            <div class="modal fade" id="global-member-details-modal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content border-0 shadow-lg">
                        <div class="modal-header bg-light border-0">
                            <h5 class="modal-title fw-bold">Thông tin thành viên</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body p-4">
                            <div class="d-flex align-items-center mb-4 pb-3 border-bottom">
                                <div class="rounded-pill p-3 me-3 text-white fw-bold d-flex align-items-center justify-content-center" 
                                     style="width:64px; height:64px; font-size:1.8rem; background:${colorFromName(m.full_name)}">
                                    ${initials(m.full_name)}
                                </div>
                                <div>
                                    <div class="h4 mb-1 fw-bold text-dark">${esc(m.full_name)}</div>
                                    <div class="text-secondary"><i class="bi bi-envelope me-1"></i>${esc(m.email)}</div>
                                    ${m.phone ? `<div class="text-secondary mt-1"><i class="bi bi-telephone me-1"></i>${esc(m.phone)}</div>` : ''}
                                </div>
                            </div>
                            <div class="row mb-2">
                                <div class="col-4 text-secondary small fw-bold">Phòng ban</div>
                                <div class="col-8 fw-bold small">${esc(m.department_name || m.department_code || 'N/A')}</div>
                            </div>
                            <div class="row mb-2">
                                <div class="col-4 text-secondary small fw-bold">Role chính</div>
                                <div class="col-8 small">${esc(m.default_role || 'Chưa có')}</div>
                            </div>
                            <div class="row">
                                <div class="col-4 text-secondary small fw-bold">Các Role khác</div>
                                <div class="col-8">${rolesHtml || '<span class="text-muted small">Chưa phân role</span>'}</div>
                            </div>
                            ${projectsHtml}
                        </div>
                        <div class="modal-footer border-0 pt-0">
                            <button type="button" class="btn btn-light rounded-pill px-4" data-bs-dismiss="modal">Đóng</button>
                        </div>
                    </div>
                </div>
            </div>`;
            document.body.insertAdjacentHTML('beforeend', html);
            const modalEl = document.getElementById('global-member-details-modal');
            const bsModal = new bootstrap.Modal(modalEl);
            bsModal.show();
            modalEl.addEventListener('hidden.bs.modal', () => modalEl.remove());
        }
    } catch (e) { handleError(e); }
  }

  return { toast, handleError, esc, avatarHTML, avatarStack, hasPermission, applyPermissions, fmtDate, daysUntil, openModal, confirmDialog, loading, initials, qs, colorFromName, showMemberDetails };
})();

window.UI = UI;
