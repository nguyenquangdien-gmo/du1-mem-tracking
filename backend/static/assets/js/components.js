
const Components = {
    injectSidebar: function(activeId) {
        const container = document.getElementById('sidebar-container');
        if (!container) return;

        const user = auth.getUser();
        const role = user ? user.role : 'member';

        const navItems = [
            { id: 'nav-dashboard', text: '📊 Dashboard', href: 'index.html' },
            { id: 'nav-departments', text: '🏢 Phòng ban', href: 'departments.html', adminOnly: true },
            { id: 'nav-projects', text: '📁 Dự án', href: 'projects.html' },
            { id: 'nav-members', text: '👥 Thành viên', href: 'members.html' },
            { id: 'nav-calendar', text: '📅 Lịch làm việc', href: 'calendar.html' },
            { id: 'nav-roles', text: '🎭 Quản lý Role', href: 'roles.html', adminOnly: true },
            { id: 'nav-users', text: '👤 Quản lý User', href: 'users.html', adminOnly: true },
            { id: 'nav-settings', text: '⚙️ Cấu hình hệ thống', href: 'settings.html', adminOnly: true }
        ];

        const filteredItems = navItems.filter(item => {
            if (item.adminOnly && role !== 'admin') return false;
            return true;
        });

        container.innerHTML = `
            <aside class="sidebar bg-white border-end shadow-sm">
                <div class="sidebar-header p-4">
                    <div class="logo d-flex align-items-center" onclick="location.href='index.html'" style="cursor:pointer">
                        <div class="logo-icon bg-primary rounded-3 me-2" style="width:32px;height:32px;"></div>
                        <span class="logo-text h5 mb-0 fw-bold text-dark">Member<span class="text-primary">Track</span></span>
                    </div>
                </div>
                <nav class="nav flex-column p-2">
                    ${filteredItems.map(item => `
                        <a href="${item.href}" id="${item.id}" class="nav-link py-3 px-4 rounded-3 mb-1 ${item.id === activeId ? 'active bg-primary text-white' : 'text-secondary hover-bg-light'}">
                            ${item.text}
                        </a>
                    `).join('')}
                </nav>
                <div class="sidebar-footer mt-auto p-4 border-top">
                    <div class="user-profile d-flex align-items-center mb-3">
                        <div class="avatar-small rounded-circle bg-primary-subtle text-primary d-flex align-items-center justify-content-center fw-bold me-2" style="width:36px;height:36px;font-size:0.8rem">
                            ${UI.initials(user ? (user.full_name || user.username) : 'U')}
                        </div>
                        <div class="user-info overflow-hidden">
                            <div class="small fw-bold text-dark text-truncate">${UI.esc(user ? (user.full_name || user.username) : 'User')}</div>
                            <div class="text-secondary" style="font-size:0.75rem">${UI.esc(role.toUpperCase())}</div>
                        </div>
                    </div>
                    <button class="btn btn-outline-danger w-100 rounded-pill" onclick="auth.logout()">
                        <i class="bi bi-box-arrow-right"></i> Đăng xuất
                    </button>
                </div>
            </aside>
        `;
    },

    // Quick Add Helpers using standard Bootstrap Modals for consistency
    _getModalHTML: function(id, title, formId, fields) {
        return `
            <div class="modal fade quick-add-modal" id="${id}" tabindex="-1" style="z-index: 1070;">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content border-0 shadow-lg rounded-4">
                        <div class="modal-header border-0 pb-0">
                            <h5 class="modal-title fw-bold">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="${formId}">
                                ${fields}
                                <div class="d-flex justify-content-end gap-2 mt-4">
                                    <button type="button" class="btn btn-light rounded-pill px-4" data-bs-dismiss="modal">Hủy</button>
                                    <button type="submit" class="btn btn-primary rounded-pill px-4">Lưu lại</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    showQuickDept: function(callback) {
        let modalEl = document.getElementById('quick-dept-modal');
        if (!modalEl) {
            const fields = `
                <div class="mb-3">
                    <label class="form-label small fw-bold">Tên phòng ban</label>
                    <input type="text" class="form-control rounded-3" id="qd-name" required>
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">Mã phòng ban</label>
                    <input type="text" class="form-control rounded-3" id="qd-code" required placeholder="VD: DEV, HR...">
                </div>
            `;
            const html = this._getModalHTML('quick-dept-modal', 'Thêm phòng ban mới', 'quick-dept-form', fields);
            document.body.insertAdjacentHTML('beforeend', html);
            modalEl = document.getElementById('quick-dept-modal');
        }
        
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        document.getElementById('quick-dept-form').onsubmit = async (e) => {
            e.preventDefault();
            const payload = { 
                name: document.getElementById('qd-name').value, 
                code: document.getElementById('qd-code').value 
            };
            const resp = await api.post('/departments', payload);
            if (resp?.success) {
                modal.hide();
                UI.toast("Đã thêm phòng ban!");
                if (callback) callback(resp.data);
            } else Dialogs.alert(resp.error?.message || "Lỗi");
        };
        modal.show();
    },

    showQuickMember: function(callback) {
        let modalEl = document.getElementById('quick-member-modal');
        if (!modalEl) {
            const fields = `
                <div class="mb-3">
                    <label class="form-label small fw-bold">Họ và tên</label>
                    <input type="text" class="form-control rounded-3" id="qm-name" required>
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">Email</label>
                    <input type="email" class="form-control rounded-3" id="qm-email" required>
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">Phòng ban</label>
                    <select id="qm-dept" class="form-select rounded-3" required></select>
                </div>
            `;
            const html = this._getModalHTML('quick-member-modal', 'Thêm nhân viên mới', 'quick-member-form', fields);
            document.body.insertAdjacentHTML('beforeend', html);
            modalEl = document.getElementById('quick-member-modal');
        }

        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        // Load Depts
        api.get('/departments').then(resp => {
            if (resp?.success) {
                document.getElementById('qm-dept').innerHTML = resp.data.map(d => `<option value="${d.id}">${UI.esc(d.name)}</option>`).join('');
            }
        });

        document.getElementById('quick-member-form').onsubmit = async (e) => {
            e.preventDefault();
            const payload = {
                full_name: document.getElementById('qm-name').value,
                email: document.getElementById('qm-email').value,
                department_id: parseInt(document.getElementById('qm-dept').value),
                default_role: "Staff"
            };
            const resp = await api.post('/members', payload);
            if (resp?.success) {
                modal.hide();
                UI.toast("Đã thêm nhân viên!");
                if (callback) callback(resp.data);
            } else Dialogs.alert(resp.error?.message || "Lỗi");
        };
        modal.show();
    },

    showQuickRole: function(callback) {
        let modalEl = document.getElementById('quick-role-modal');
        if (!modalEl) {
            const fields = `
                <div class="mb-3">
                    <label class="form-label small fw-bold">Tên Role</label>
                    <input type="text" class="form-control rounded-3" id="qr-name" required>
                </div>
            `;
            const html = this._getModalHTML('quick-role-modal', 'Thêm Role mới', 'quick-role-form', fields);
            document.body.insertAdjacentHTML('beforeend', html);
            modalEl = document.getElementById('quick-role-modal');
        }

        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        document.getElementById('quick-role-form').onsubmit = async (e) => {
            e.preventDefault();
            const resp = await api.post('/roles', { name: document.getElementById('qr-name').value, description: "Quick add" });
            if (resp?.success) {
                modal.hide();
                UI.toast("Đã thêm Role!");
                if (callback) callback(resp.data);
            } else Dialogs.alert(resp.error?.message || "Lỗi");
        };
        modal.show();
    }
};

// Global Alert/Confirm Replacement with jQuery UI
const Dialogs = {
    alert: function(message, title = "Thông báo") {
        return new Promise(resolve => {
            $("<div></div>").html(message).dialog({
                title: title,
                resizable: false,
                modal: true,
                close: function() {
                    $(this).dialog("destroy").remove();
                    resolve();
                },
                buttons: {
                    "OK": function() {
                        $(this).dialog("close");
                    }
                }
            });
        });
    },
    confirm: function(message, title = "Xác nhận") {
        return new Promise(resolve => {
            let confirmed = false;
            $("<div></div>").html(message).dialog({
                title: title,
                resizable: false,
                modal: true,
                close: function() {
                    $(this).dialog("destroy").remove();
                    resolve(confirmed);
                },
                buttons: {
                    "Xác nhận": function() {
                        confirmed = true;
                        $(this).dialog("close");
                    },
                    "Hủy": function() {
                        $(this).dialog("close");
                    }
                }
            });
        });
    },
    prompt: function(label, title = "Nhập thông tin", defaultValue = "") {
        return new Promise(resolve => {
            const inputId = 'prompt-input-' + Math.random().toString(36).substr(2, 9);
            const html = `<div class="p-2"><label class="form-label small fw-bold">${label}</label><input type="text" id="${inputId}" class="form-control" value="${defaultValue}"></div>`;
            let val = null;
            $("<div></div>").html(html).dialog({
                title: title,
                resizable: false,
                modal: true,
                close: function() {
                    $(this).dialog("destroy").remove();
                    resolve(val);
                },
                buttons: {
                    "OK": function() {
                        val = document.getElementById(inputId).value;
                        $(this).dialog("close");
                    },
                    "Hủy": function() {
                        $(this).dialog("close");
                    }
                }
            });
        });
    }
};

// Overwrite window.alert and window.confirm? Maybe explicitly call Dialogs.alert
window.nativeAlert = window.alert;
window.nativeConfirm = window.confirm;
// window.alert = (msg) => Dialogs.alert(msg); // Optional: be careful with sync behavior
