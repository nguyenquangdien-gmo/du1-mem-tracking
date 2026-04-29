const DashboardUI = {
    initDashboard: async function() {
        this.loadStats();
        this.loadRecentProjects();
        this.loadAvailableMembers();
        this.setupEventListeners();
    },

    loadStats: async () => {
        try {
            const [projects, members, idleMembers, tasks] = await Promise.all([
                api.get('/projects'),
                api.get('/members'),
                api.get('/members?available_only=true'),
                api.get('/tasks')
            ]);

            if (projects?.success) document.getElementById('stat-total-projects').textContent = projects.data.length;
            if (members?.success) document.getElementById('stat-active-members').textContent = members.data.length;
            
            if (idleMembers?.success) {
                document.getElementById('stat-idle-members').textContent = idleMembers.data.length;
            }
            
            if (tasks?.success) {
                const today = new Date().toISOString().split('T')[0];
                const overdue = tasks.data.filter(t => t.deadline && t.deadline < today && !['done', 'archived'].includes(t.status));
                document.getElementById('stat-overdue-tasks').textContent = overdue.length;
            }
        } catch (err) { console.error('Failed to load stats', err); }
    },

    loadRecentProjects: async () => {
        const container = document.getElementById('dashboard-project-list');
        if (!container) return;
        
        try {
            const resp = await api.get('/projects?limit=5');
            if (resp?.success && resp.data && resp.data.length > 0) {
                container.innerHTML = resp.data.map(p => `
                    <a href="projects.html?id=${p.id}" class="list-group-item list-group-item-action border-0 px-0 d-flex justify-content-between align-items-center">
                        <div>
                            <div class="fw-bold text-dark">${UI.esc(p.name)}</div>
                            <div class="d-flex align-items-center gap-2 mt-1">
                                <span class="badge status-${p.status} rounded-pill fw-normal" style="font-size:0.65rem">${p.status.toUpperCase()}</span>
                                <span onclick="event.preventDefault(); event.stopPropagation(); window.location.href='projects.html?id=${p.id}&tab=tasks'" class="badge bg-light text-dark border rounded-pill fw-normal text-decoration-none" style="font-size:0.65rem; cursor: pointer;" title="Xem danh sách tasks">
                                    <i class="bi bi-list-task text-primary me-1"></i>${p.task_count || 0} tasks
                                </span>
                                ${p.overdue_task_count !== undefined ? `<span onclick="event.preventDefault(); event.stopPropagation(); window.location.href='projects.html?id=${p.id}&tab=tasks&taskFilter=overdue'" class="badge ${p.overdue_task_count > 0 ? 'bg-danger' : 'bg-secondary'} rounded-pill fw-normal text-decoration-none text-white" style="font-size:0.65rem; cursor: pointer;" title="Xem các task trễ hạn"><i class="bi bi-exclamation-triangle me-1"></i>${p.overdue_task_count} trễ</span>` : ''}
                            </div>
                        </div>
                        <i class="bi bi-chevron-right text-secondary"></i>
                    </a>
                `).join('');
            } else {
                container.innerHTML = '<div class="text-center py-4 text-muted">Chưa có dự án nào</div>';
            }
        } catch (err) { 
            console.error('Failed to load recent projects', err);
            container.innerHTML = '<div class="text-center py-4 text-danger">Không thể tải dữ liệu</div>'; 
        }
    },

    loadAvailableMembers: async () => {
        const container = document.getElementById('dashboard-available-members');
        if (!container) return;

        try {
            const resp = await api.get('/members?available_only=true');
            if (resp?.success && resp.data && resp.data.length > 0) {
                const sorted = [...resp.data].sort((a, b) => {
                    const nameA = a.full_name.trim().split(/\s+/).pop().toLowerCase();
                    const nameB = b.full_name.trim().split(/\s+/).pop().toLowerCase();
                    const cmp = nameA.localeCompare(nameB, 'vi');
                    return cmp !== 0 ? cmp : a.full_name.localeCompare(b.full_name, 'vi');
                });

                container.innerHTML = sorted.map(m => `
                    <div class="list-group-item border-0 px-0 d-flex align-items-center">
                        <div class="rounded-pill p-3 me-3 text-white fw-bold d-flex align-items-center justify-content-center" 
                             style="width:40px; height:40px; font-size:0.9rem; background:${UI.colorFromName(m.full_name)}">
                            ${UI.initials(m.full_name)}
                        </div>
                        <div class="overflow-hidden">
                            <div class="fw-bold text-dark text-truncate">${UI.esc(m.full_name)} <i class="bi bi-info-circle text-primary ms-1 cursor-pointer" style="cursor: pointer;" onclick="UI.showMemberDetails(${m.id})"></i></div>
                            <div class="small text-secondary text-truncate">${UI.esc(m.department_code || 'N/A')}</div>
                        </div>
                    </div>
                `).join('');
            } else {
                container.innerHTML = '<div class="text-center py-4 text-muted">Chưa có thành viên nào rảnh</div>';
            }
        } catch (err) { 
            console.error('Failed to load available members', err);
            container.innerHTML = '<div class="text-center py-4 text-danger">Không thể tải dữ liệu</div>'; 
        }
    },

    renderSearchResults: function(data) {
        const host = document.getElementById('search-results-dropdown');
        if (!data || (data.members.length === 0 && data.projects.length === 0 && (!data.tasks || data.tasks.length === 0))) {
            host.innerHTML = '<div class="text-center py-3 text-muted">Không tìm thấy kết quả</div>';
            host.style.display = 'block';
            return;
        }

        let html = '<div class="list-group list-group-flush">';
        if (data.members.length) {
            html += '<div class="px-3 py-2 small fw-bold text-primary text-uppercase">Thành viên</div>';
            data.members.forEach(m => {
                html += `
                <a href="members.html?q=${encodeURIComponent(m.full_name)}" class="list-group-item list-group-item-action border-0 rounded-3 d-flex align-items-center gap-3">
                    <div class="rounded bg-primary text-white d-flex align-items-center justify-content-center fw-bold" style="width:32px;height:32px;font-size:0.8rem">
                        ${UI.initials(m.full_name)}
                    </div>
                    <div>
                        <div class="fw-bold small">${UI.esc(m.full_name)}</div>
                        <div class="text-secondary small" style="font-size:0.75rem">${UI.esc(m.default_role || 'Member')}</div>
                    </div>
                </a>`;
            });
        }
        if (data.projects.length) {
            html += '<div class="px-3 py-2 mt-2 small fw-bold text-primary text-uppercase">Dự án</div>';
            data.projects.forEach(p => {
                html += `
                <a href="projects.html?id=${p.id}&filter=true" class="list-group-item list-group-item-action border-0 rounded-3 d-flex align-items-center gap-3">
                    <div class="rounded bg-light text-primary d-flex align-items-center justify-content-center fw-bold border" style="width:32px;height:32px">📁</div>
                    <div>
                        <div class="fw-bold small">${UI.esc(p.name)}</div>
                        <div class="text-secondary small" style="font-size:0.75rem">${UI.esc(p.status)}</div>
                    </div>
                </a>`;
            });
        }
        if (data.tasks && data.tasks.length) {
            html += '<div class="px-3 py-2 mt-2 small fw-bold text-primary text-uppercase">Tasks</div>';
            data.tasks.forEach(t => {
                html += `
                <a href="projects.html?id=${t.project_id}&tab=tasks" class="list-group-item list-group-item-action border-0 rounded-3 d-flex align-items-center gap-3">
                    <div class="rounded bg-light text-primary d-flex align-items-center justify-content-center fw-bold border" style="width:32px;height:32px">📋</div>
                    <div>
                        <div class="fw-bold small">${UI.esc(t.name)}</div>
                        <div class="text-secondary small" style="font-size:0.75rem">${UI.esc(t.status)} - Ưu tiên: ${UI.esc(t.priority)}</div>
                    </div>
                </a>`;
            });
        }
        html += '</div>';
        host.innerHTML = html;
        host.style.display = 'block';
    },

    setupEventListeners: function() {
        const searchInput = document.getElementById('global-search');
        if (searchInput) {
            const searchDropdown = document.getElementById('search-results-dropdown');
            searchInput.addEventListener('input', DashboardUtils.debounce(async (e) => {
                const q = e.target.value.trim();
                if (q.length < 2) { searchDropdown.style.display = 'none'; return; }
                try {
                    const results = await api.get(`/search?q=${q}`);
                    if (results?.success) this.renderSearchResults(results.data);
                } catch (e) { console.error(e); }
            }, 300));

            document.addEventListener('click', (e) => {
                if (!searchDropdown.contains(e.target) && e.target !== searchInput) {
                    searchDropdown.style.display = 'none';
                }
            });
        }
        
        const quickAddProj = document.getElementById('btn-quick-add-project');
        if (quickAddProj) {
            quickAddProj.onclick = () => {
                if (window.location.pathname.includes('projects.html')) {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('project-modal')) || new bootstrap.Modal(document.getElementById('project-modal'));
                    modal.show();
                } else window.location.href = 'projects.html?action=create';
            };
        }
        
        const quickAddMember = document.getElementById('btn-quick-add-member');
        if (quickAddMember) {
            quickAddMember.onclick = () => {
                if (window.location.pathname.includes('members.html')) {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('member-modal')) || new bootstrap.Modal(document.getElementById('member-modal'));
                    modal.show();
                } else window.location.href = 'members.html?action=create';
            };
        }
    }
};

const DashboardUtils = {
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => { clearTimeout(timeout); func(...args); };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};


