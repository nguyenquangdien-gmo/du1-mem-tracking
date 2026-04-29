const ProjectsUI = {
    init: async function() {
        await this.loadMembers();
        await this.loadProjects();
        this.initDragDrop();
        
        const projForm = document.getElementById('project-form');
        if (projForm) projForm.onsubmit = (e) => this.saveProject(e);

        const btnCreate = document.getElementById('btn-create-project');
        if (btnCreate) btnCreate.onclick = () => this.openProjectModal();

        const taskForm = document.getElementById('task-form');
        if (taskForm) taskForm.onsubmit = (e) => this.saveTask(e);
    },

    currentProjectId: null,

    loadMembers: async function() {
        const container = document.getElementById('members-pool');
        if (!container) return;
        const resp = await api.get('/members');
        if (resp?.success) {
            const sorted = [...resp.data].sort((a, b) => {
                const nameA = a.full_name.trim().split(/\s+/).pop().toLowerCase();
                const nameB = b.full_name.trim().split(/\s+/).pop().toLowerCase();
                const cmp = nameA.localeCompare(nameB, 'vi');
                return cmp !== 0 ? cmp : a.full_name.localeCompare(b.full_name, 'vi');
            });

            container.innerHTML = sorted.map(m => `
                <div class="list-group-item list-group-item-action border-0 rounded-3 mb-2 d-flex align-items-center ${UI.hasPermission('write', 'projects') ? 'draggable shadow-sm bg-white cursor-grab' : 'bg-light'} " 
                     data-id="${m.id}" data-other-roles='${JSON.stringify(m.other_roles || [])}'>
                    <div class="rounded-circle me-3 text-white fw-bold d-flex align-items-center justify-content-center" 
                         style="width:36px; height:36px; font-size:0.8rem; background:${UI.colorFromName(m.full_name)}">
                        ${UI.initials(m.full_name)}
                    </div>
                    <div class="overflow-hidden">
                        <div class="fw-bold small text-dark text-truncate m-name">${UI.esc(m.full_name)} <i class="bi bi-info-circle text-primary ms-1 cursor-pointer" style="cursor: pointer;" onclick="UI.showMemberDetails(${m.id})"></i></div>
                        <div class="small text-secondary text-truncate" style="font-size:0.7rem">
                            ${UI.esc(m.department_code || 'N/A')}
                        </div>
                    </div>
                </div>
            `).join('');

            const filter = document.getElementById('member-filter');
            if (filter) {
                filter.oninput = (e) => {
                    const q = e.target.value.toLowerCase();
                    container.querySelectorAll('.draggable').forEach(card => {
                        const text = card.innerText.toLowerCase();
                        card.style.display = text.includes(q) ? 'flex' : 'none';
                    });
                };
            }
        }
    },

    loadProjects: async function() {
        const container = document.getElementById('projects-container');
        if (!container) return;
        const resp = await api.get('/projects');
        if (resp?.success) {
            const urlParams = new URLSearchParams(window.location.search);
            const filterId = urlParams.get('filter') === 'true' ? urlParams.get('id') : null;
            let projectsToRender = resp.data;
            if (filterId) projectsToRender = resp.data.filter(p => p.id == filterId);

            container.innerHTML = projectsToRender.map(p => {
                const statusClass = `status-${p.status}`;
                return `
                <div class="col-md-6 col-xl-4 dropzone-col mb-4">
                    <div class="glass-card project-card h-100 border-2 shadow-sm" data-id="${p.id}" data-end-date="${p.expected_end_date || ''}">
                        <div class="p-4 h-100 d-flex flex-column">
                            <div class="d-flex justify-content-between align-items-start mb-3">
                                <div>
                                    <div class="d-flex align-items-center gap-2 mb-2">
                                        <div class="badge ${statusClass} rounded-pill">${p.status.toUpperCase()}</div>
                                        ${p.is_important ? '<i class="bi bi-star-fill text-warning" title="Dự án quan trọng"></i>' : ''}
                                    </div>
                                    <h5 class="fw-bold text-dark mb-1">${UI.esc(p.name)}</h5>
                                    <div class="small text-secondary"><i class="bi bi-building me-1"></i>${UI.esc(p.department_name || 'N/A')}</div>
                                </div>
                                <div class="dropdown">
                                    <button class="btn btn-sm btn-light rounded-pill" type="button" data-bs-toggle="dropdown">
                                        <i class="bi bi-three-dots-vertical"></i>
                                    </button>
                                    <ul class="dropdown-menu dropdown-menu-end shadow border-0">
                                        <li><a class="dropdown-item" href="#" onclick='ProjectsUI.showProjectDetails(${p.id}, "${UI.esc(p.name)}")'>🔍 Chi tiết dự án</a></li>
                                        ${UI.hasPermission('write', 'projects') ? `
                                            <li><a class="dropdown-item" href="#" onclick='ProjectsUI.openProjectModal(${JSON.stringify(p).replace(/'/g, "&#39;")})'>✏️ Sửa thông tin</a></li>
                                            <li><a class="dropdown-item text-danger" href="#" onclick="ProjectsUI.deleteProject(${p.id})">🗑️ Xóa dự án</a></li>
                                        ` : ''}
                                    </ul>
                                </div>
                            </div>
                            
                            <div class="project-info mt-2 pb-3 border-bottom border-light">
                                <div class="d-flex align-items-center mb-2">
                                    <div class="rounded-circle bg-primary-subtle text-primary d-flex align-items-center justify-content-center me-2" style="width:24px;height:24px;font-size:0.7rem">
                                        <i class="bi bi-person-badge"></i>
                                    </div>
                                    <span class="small text-dark fw-medium">PM: ${UI.esc(p.pm_name || 'Chưa phân công')}</span>
                                </div>
                                <div class="d-flex gap-3 small text-secondary mb-2">
                                    <span><i class="bi bi-calendar-event me-1"></i>${UI.fmtDate(p.start_date)}</span>
                                    <span><i class="bi bi-calendar-check me-1"></i>${UI.fmtDate(p.expected_end_date)}</span>
                                </div>
                                <div class="d-flex align-items-center gap-2 mt-1">
                                    <a href="javascript:;" onclick='ProjectsUI.showProjectDetails(${p.id}, "${UI.esc(p.name)}", "tasks-tab")' class="badge bg-light text-dark border rounded-pill fw-normal text-decoration-none" style="font-size:0.65rem">
                                        <i class="bi bi-list-task text-primary me-1"></i>${p.task_count || 0} tasks
                                    </a>
                                    ${p.overdue_task_count !== undefined ? `<a href="javascript:;" onclick='ProjectsUI.showProjectDetails(${p.id}, "${UI.esc(p.name)}", "tasks-tab", "overdue")' class="badge ${p.overdue_task_count > 0 ? 'bg-danger' : 'bg-secondary'} rounded-pill fw-normal text-decoration-none text-white" style="font-size:0.65rem"><i class="bi bi-exclamation-triangle me-1"></i>${p.overdue_task_count} trễ</a>` : ''}
                                </div>
                            </div>

                            <div class="p-members my-3 d-flex flex-wrap gap-2 flex-grow-1 p-members-list dropzone" id="p-members-${p.id}" data-id="${p.id}" data-end-date="${p.expected_end_date || ''}" style="min-height:80px">
                                 <!-- Members -->
                            </div>
                            
                            <div class="mt-auto pt-3 border-top border-light d-flex justify-content-between align-items-center">
                                <small class="text-secondary opacity-75"><i class="bi bi-plus-circle me-1"></i>Kéo thả member</small>
                                <a href="javascript:;" class="small fw-bold text-primary text-decoration-none" onclick='ProjectsUI.showProjectDetails(${p.id}, "${UI.esc(p.name)}")'>Chi tiết &rarr;</a>
                            </div>
                        </div>
                    </div>
                </div>
                `;
            }).join('');
            projectsToRender.forEach(p => this.loadProjectAssignments(p.id));
            this.initDragDrop();
            const autoOpenId = urlParams.get('id');
            const targetTab = urlParams.get('tab') === 'tasks' ? 'tasks-tab' : null;
            const taskFilter = urlParams.get('taskFilter');
            if (autoOpenId) {
                const p = resp.data.find(x => x.id == autoOpenId);
                if (p) this.showProjectDetails(p.id, p.name, targetTab, taskFilter);
            }
        }
    },

    loadProjectAssignments: async function(projectId) {
        const container = document.getElementById(`p-members-${projectId}`);
        if (!container) return;
        const resp = await api.get(`/projects/${projectId}/members`);
        if (resp?.success) {
            container.innerHTML = resp.data.map(am => `
                <div class="avatar-small rounded-circle border border-white shadow-sm d-flex align-items-center justify-content-center text-white fw-bold draggable-member" 
                     data-member-id="${am.member_id}" data-project-id="${projectId}"
                     data-assignment='${JSON.stringify(am).replace(/'/g, "&apos;")}'
                     title="${UI.esc(am.member_name)}: ${UI.esc(am.role || '')}\n${UI.esc(am.description || '')}"
                     style="width:32px; height:32px; font-size:0.7rem; background:${UI.colorFromName(am.member_name || '?')}">
                    ${UI.initials(am.member_name || '?')}
                </div>
            `).join('');
            this.initDropzones();
        }
    },

    showProjectDetails: async function(projectId, projectName, tabId = null, filter = null) {
        this.currentProjectId = projectId;
        this.initialTaskFilter = filter;
        const modalEl = document.getElementById('project-details-modal');
        const listContainer = document.getElementById('details-member-list');
        document.getElementById('details-project-name').innerText = projectName;
        listContainer.innerHTML = '<tr><td colspan="6" class="text-center py-4">Đang tải...</td></tr>';
        
        if (tabId) {
            const tabBtn = document.getElementById(tabId);
            if (tabBtn) {
                bootstrap.Tab.getOrCreateInstance(tabBtn).show();
                if (tabId === 'tasks-tab') this.loadProjectTasks();
            }
        } else {
            const firstTab = document.querySelector('#projectDetailsTabs button:first-child');
            if (firstTab) bootstrap.Tab.getOrCreateInstance(firstTab).show();
        }

        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();

        const resp = await api.get(`/projects/${projectId}/members`);
        if (resp?.success) {
            if (resp.data.length === 0) {
                listContainer.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">Chưa có thành viên nào</td></tr>';
                return;
            }
            // Sort by last name
            const sorted = [...resp.data].sort((a, b) => {
                const nameA = (a.member_name || '').trim().split(/\s+/).pop().toLowerCase();
                const nameB = (b.member_name || '').trim().split(/\s+/).pop().toLowerCase();
                const cmp = nameA.localeCompare(nameB, 'vi');
                return cmp !== 0 ? cmp : (a.member_name || '').localeCompare(b.member_name || '', 'vi');
            });

            listContainer.innerHTML = sorted.map((am, index) => `
                <tr>
                    <td class="ps-3 text-secondary small">${index + 1}</td>
                    <td>
                        <div class="d-flex align-items-center">
                            <div class="rounded-circle me-2 text-white fw-bold d-flex align-items-center justify-content-center" 
                                 style="width:28px; height:28px; font-size:0.7rem; background:${UI.colorFromName(am.member_name)}">
                                ${UI.initials(am.member_name)}
                            </div>
                            <div class="fw-bold small">${UI.esc(am.member_name)} <i class="bi bi-info-circle text-primary ms-1 cursor-pointer" style="cursor: pointer;" onclick="UI.showMemberDetails(${am.member_id})"></i></div>
                        </div>
                    </td>
                    <td><span class="badge bg-light text-dark border small">${UI.esc(am.role)}</span></td>
                    <td style="width: 220px; min-width: 220px;">
                        <div class="text-secondary d-flex flex-column" style="font-size:0.75rem; line-height: 1.2; height: 2.4rem; overflow: hidden;" title="${UI.esc(am.description || '')}">
                            ${(() => {
                                const desc = am.description || '';
                                if (!desc) return '—';
                                const rawLines = desc.split(/\r?\n/).filter(l => l.trim().length > 0);
                                const processedLines = rawLines.slice(0, 2).map(line => {
                                    const words = line.trim().split(/\s+/);
                                    if (words.length > 5) return words.slice(0, 5).join(' ') + '...';
                                    return line.trim();
                                });
                                const line1 = processedLines[0] || '';
                                const line2 = processedLines[1] || (rawLines.length > 2 ? '...' : '');
                                return `<div class="text-truncate" style="height:1.2rem; display:block;">${UI.esc(line1)}</div><div class="text-truncate" style="height:1.2rem; display:block;">${UI.esc(line2) || '&nbsp;'}</div>`;
                            })()}
                        </div>
                    </td>
                    <td class="small text-dark">${UI.fmtDate(am.expected_end_date)}</td>
                    <td class="text-end pe-3">
                        <div class="d-flex justify-content-end gap-1">
                            ${UI.hasPermission('write', 'projects') ? `
                                <button class="btn btn-sm btn-light p-1" onclick='ProjectsUI.editAssignment(${JSON.stringify(am).replace(/'/g, "&apos;")})' title="Sửa">✏️</button>
                                <button class="btn btn-sm btn-light p-1 text-danger" onclick="ProjectsUI.deleteAssignment(${projectId}, ${am.member_id})" title="Xóa">🗑️</button>
                            ` : ''}
                        </div>
                    </td>
                </tr>
            `).join('');
        }
    },

    initDragDrop: function() {
        if (!UI.hasPermission('write', 'projects')) return;
        const pool = document.getElementById('members-pool');
        if (pool) {
            if (pool.sortable) pool.sortable.destroy();
            pool.sortable = new Sortable(pool, { 
                group: { name: 'members', pull: 'clone', put: false }, 
                sort: false, 
                animation: 150,
                onEnd: (evt) => {
                    // Logic when item is dropped
                }
            });
        }
        this.initDropzones();
    },

    initDropzones: function() {
        if (!UI.hasPermission('write', 'projects')) return;

        document.querySelectorAll('.dropzone').forEach(el => {
            if (el.sortable) el.sortable.destroy();
            el.sortable = new Sortable(el, { 
                group: { name: 'project-members', pull: true, put: ['members'] },
                animation: 150,
                // Handle adding from pool
                onAdd: (evt) => {
                    if (evt.from.id === 'members-pool') {
                        const memberId = evt.item.dataset.id;
                        const projectId = el.dataset.id;
                        
                        // Prevent duplicate but open Edit dialog
                        const existingIcon = el.querySelector(`[data-member-id="${memberId}"]`);
                        if (existingIcon) {
                            evt.item.remove();
                            const assignment = JSON.parse(existingIcon.dataset.assignment);
                            this.editAssignment(assignment);
                            return;
                        }

                        const memberName = evt.item.querySelector('.m-name').textContent;
                        const projectName = el.closest('.project-card').querySelector('h5').textContent;
                        const projectEndDate = el.dataset.endDate;
                        
                        // Temporary icon
                        const initials = UI.initials(memberName);
                        const color = UI.colorFromName(memberName);
                        const placeholder = document.createElement('div');
                        placeholder.className = "avatar-small rounded-circle border border-white shadow-sm d-flex align-items-center justify-content-center text-white fw-bold";
                        placeholder.style = `width:32px; height:32px; font-size:0.7rem; background:${color}`;
                        placeholder.innerHTML = initials;
                        el.appendChild(placeholder);
                        
                        evt.item.remove();
                        this.openAssignmentDialog(memberId, projectId, memberName, projectName, evt.item, projectEndDate);
                    }
                },
                // Handle dragging OUT to remove
                onEnd: (evt) => {
                    // If dropped outside any project members list
                    if (!evt.to.classList.contains('p-members-list')) {
                        const memberId = evt.item.dataset.memberId;
                        const projectId = evt.item.dataset.projectId;
                        if (!memberId || !projectId) return; // Not an existing member icon

                        UI.confirmDialog(`Gỡ thành viên này khỏi dự án?`).then(async (confirmed) => {
                            if (confirmed) {
                                const resp = await api.delete(`/projects/${projectId}/members/${memberId}`);
                                if (resp?.success) {
                                    evt.item.remove();
                                    UI.toast('Đã gỡ member', 'info');
                                } else {
                                    this.loadProjectAssignments(projectId);
                                    UI.handleError(resp.error);
                                }
                            } else {
                                this.loadProjectAssignments(projectId);
                            }
                        });
                    }
                }
            });
        });
    },


    openAssignmentDialog: function(memberId, projectId, memberName, projectName, memberData, projectEndDate, isEdit = false, existingAssignment = null) {
        document.getElementById('assign-member-id').value = memberId;
        document.getElementById('assign-project-id').value = projectId;
        document.getElementById('assignment-text').innerText = isEdit ? `Sửa phân công: ${memberName}` : `Giao ${memberName} vào dự án ${projectName}`;
        
        let otherRoles = [];
        if (isEdit) {
            otherRoles = existingAssignment.other_roles || [];
        } else {
            otherRoles = JSON.parse(memberData.dataset.otherRoles || '[]');
        }

        const roleSelect = document.getElementById('assign-role-select');
        let rolesHtml = '';
        otherRoles.forEach(r => { rolesHtml += `<option value="${UI.esc(r)}">${UI.esc(r)}</option>`; });
        rolesHtml += `<option value="custom">+ Khác...</option>`;
        roleSelect.innerHTML = rolesHtml;
        
        const customField = document.getElementById('assign-role-custom');
        customField.value = '';
        customField.style.display = roleSelect.value === 'custom' ? 'block' : 'none';
        roleSelect.onchange = (e) => {
            customField.style.display = e.target.value === 'custom' ? 'block' : 'none';
            if (e.target.value === 'custom') customField.focus();
        };

        if (isEdit) {
            if (otherRoles.includes(existingAssignment.role)) {
                roleSelect.value = existingAssignment.role;
                customField.style.display = 'none';
            } else {
                roleSelect.value = 'custom';
                customField.value = existingAssignment.role;
                customField.style.display = 'block';
            }
            document.getElementById('assign-description').value = existingAssignment.description || '';
            document.getElementById('assign-end-date').value = UI.fmtDate(existingAssignment.expected_end_date);
        } else {
            document.getElementById('assign-description').value = '';
            document.getElementById('assign-end-date').value = projectEndDate || '';
        }

        const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('assignment-modal'));
        modal.show();
        
        const errorEl = document.getElementById('role-error');
        errorEl.style.display = 'none';
        customField.classList.remove('is-invalid');

        document.getElementById('assignment-form').onsubmit = async (e) => {
            e.preventDefault();
            let role = (roleSelect.value === 'custom' ? customField.value : roleSelect.value).trim();
            if (!role) {
                errorEl.style.display = 'block';
                if (roleSelect.value === 'custom') customField.classList.add('is-invalid');
                return;
            }
            errorEl.style.display = 'none';
            customField.classList.remove('is-invalid');
            const payload = {
                member_id: parseInt(memberId), 
                role: role, 
                description: document.getElementById('assign-description').value,
                expected_end_date: document.getElementById('assign-end-date').value
            };
            
            const resp = isEdit 
                ? await api.patch(`/projects/${projectId}/members/${memberId}`, payload)
                : await api.post(`/projects/${projectId}/members`, payload);

            if (resp?.success) { 
                this.loadProjectAssignments(projectId); 
                if (isEdit) {
                    // Refresh details modal if it's open
                    this.showProjectDetails(projectId, projectName);
                }
                modal.hide();
                UI.toast(isEdit ? 'Đã cập nhật thành công' : 'Đã gán member thành công', 'success');
            } else {
                this.loadProjectAssignments(projectId);
                UI.handleError(resp.error || {message: 'Lỗi'});
            }
        };

        const modalEl = document.getElementById('assignment-modal');
        modalEl.addEventListener('hidden.bs.modal', () => {
            if (!isEdit) this.loadProjectAssignments(projectId);
        }, { once: true });
    },

    editAssignment: async function(assignment) {
        // We need the member's other_roles to populate the dropdown
        const memberResp = await api.get(`/members/${assignment.member_id}`);
        if (memberResp?.success) {
            const member = memberResp.data;
            const projectName = document.getElementById('details-project-name').innerText;
            this.openAssignmentDialog(
                assignment.member_id, 
                assignment.project_id, 
                assignment.member_name, 
                projectName, 
                null, 
                null, 
                true, 
                {...assignment, other_roles: member.other_roles}
            );
        }
    },

    deleteAssignment: async function(projectId, memberId) {
        UI.confirmDialog('Gỡ thành viên này khỏi dự án?').then(async (confirmed) => {
            if (confirmed) {
                const resp = await api.delete(`/projects/${projectId}/members/${memberId}`);
                if (resp?.success) {
                    UI.toast('Đã gỡ member', 'success');
                    this.loadProjectAssignments(projectId);
                    const projectName = document.getElementById('details-project-name').innerText;
                    this.showProjectDetails(projectId, projectName);
                } else UI.handleError(resp.error || {message: 'Lỗi'});
            }
        });
    },

    openProjectModal: async function(project = null) {
        const modalEl = document.getElementById('project-modal');
        if (!modalEl) return;
        
        // Load Depts & PMs
        const [deptsResp, mResp] = await Promise.all([api.get('/departments'), api.get('/members')]);
        
        if (deptsResp?.success) {
            const sortedDepts = [...deptsResp.data].sort((a, b) => a.name.localeCompare(b.name, 'vi'));
            document.getElementById('proj-dept').innerHTML = '<option value="">Chọn phòng ban...</option>' + 
                sortedDepts.map(d => `<option value="${d.id}">${UI.esc(d.name)}</option>`).join('');
        }
        if (mResp?.success) {
            const sortedPMs = [...mResp.data].sort((a, b) => {
                const nameA = a.full_name.trim().split(/\s+/).pop().toLowerCase();
                const nameB = b.full_name.trim().split(/\s+/).pop().toLowerCase();
                const cmp = nameA.localeCompare(nameB, 'vi');
                return cmp !== 0 ? cmp : a.full_name.localeCompare(b.full_name, 'vi');
            });
            document.getElementById('proj-pm').innerHTML = '<option value="">Chọn PM...</option>' + 
                sortedPMs.map(m => `<option value="${m.id}">${UI.esc(m.full_name)}</option>`).join('');
        }

        document.getElementById('modal-title-proj').innerText = project ? 'Sửa dự án' : 'Tạo dự án mới';
        document.getElementById('proj-id').value = project ? project.id : '';
        document.getElementById('proj-name').value = project ? project.name : '';
        document.getElementById('proj-desc').value = project ? (project.description || '') : '';
        document.getElementById('proj-status').value = project ? project.status : 'planning';
        document.getElementById('proj-dept').value = project ? project.department_id : '';
        document.getElementById('proj-pm').value = project ? project.pm_id : '';
        document.getElementById('proj-is-important').checked = project ? (project.is_important === 1 || project.is_important === true) : false;
        document.getElementById('proj-chatops-group-id').value = project ? (project.chatops_group_id || '') : '';
        
        // Dates handling
        let dateContainer = document.getElementById('proj-dates-row');
        if (!dateContainer) {
            dateContainer = document.createElement('div');
            dateContainer.id = 'proj-dates-row';
            dateContainer.className = 'row mb-3';
            dateContainer.innerHTML = `
                <div class="col-md-6">
                    <label class="form-label small fw-bold">Ngày bắt đầu</label>
                    <input type="date" class="form-control rounded-3" id="proj-start-date">
                </div>
                <div class="col-md-6">
                    <label class="form-label small fw-bold">Kết thúc dự kiến</label>
                    <input type="date" class="form-control rounded-3" id="proj-end-date">
                </div>
            `;
            document.getElementById('proj-pm').closest('.row').after(dateContainer);
        }

        if (project) {
            document.getElementById('proj-start-date').value = UI.fmtDate(project.start_date);
            document.getElementById('proj-end-date').value = UI.fmtDate(project.expected_end_date);
        } else {
            // Defaults: Today and Today + 1 Month
            const today = new Date();
            const nextMonth = new Date();
            nextMonth.setMonth(today.getMonth() + 1);
            
            document.getElementById('proj-start-date').value = today.toISOString().split('T')[0];
            document.getElementById('proj-end-date').value = nextMonth.toISOString().split('T')[0];
        }
        
        bootstrap.Modal.getOrCreateInstance(modalEl).show();
    },

    saveProject: async function(e) {
        e.preventDefault();
        const id = document.getElementById('proj-id').value;
        const payload = {
            name: document.getElementById('proj-name').value,
            description: document.getElementById('proj-desc').value,
            status: document.getElementById('proj-status').value,
            department_id: parseInt(document.getElementById('proj-dept').value),
            pm_id: parseInt(document.getElementById('proj-pm').value),
            is_important: document.getElementById('proj-is-important').checked ? 1 : 0,
            chatops_group_id: document.getElementById('proj-chatops-group-id').value.trim() || null,
            start_date: document.getElementById('proj-start-date').value || null,
            expected_end_date: document.getElementById('proj-end-date').value || null
        };
        const resp = id ? await api.patch(`/projects/${id}`, payload) : await api.post('/projects', payload);
        if (resp?.success) {
            bootstrap.Modal.getInstance(document.getElementById('project-modal')).hide();
            this.loadProjects();
            UI.toast('Lưu dự án thành công', 'success');
        } else {
            UI.handleError(resp.error || {message: 'Lỗi'});
        }
    },

    quickAddDept: function() {
        Components.showQuickDept(async (newDept) => {
            const deptsResp = await api.get('/departments');
            if (deptsResp?.success) {
                const html = '<option value="">Chọn phòng ban...</option>' + 
                    deptsResp.data.map(d => `<option value="${d.id}">${UI.esc(d.name)}</option>`).join('');
                document.getElementById('proj-dept').innerHTML = html;
                document.getElementById('proj-dept').value = newDept.id;
            }
        });
    },

    quickAddMember: function() {
        Components.showQuickMember(async (newMember) => {
            const mResp = await api.get('/members');
            if (mResp?.success) {
                const html = '<option value="">Chọn PM...</option>' + 
                    mResp.data.map(m => `<option value="${m.id}">${UI.esc(m.full_name)}</option>`).join('');
                document.getElementById('proj-pm').innerHTML = html;
                document.getElementById('proj-pm').value = newMember.id;
            }
        });
    },

    deleteProject: async function(id) {
        UI.confirmDialog('Xóa dự án này?').then(async (confirmed) => {
            if (confirmed) {
                const resp = await api.delete(`/projects/${id}`);
                if (resp?.success) {
                    this.loadProjects();
                    UI.toast('Đã xóa dự án', 'success');
                } else UI.handleError(resp.error || {message: 'Lỗi'});
            }
        });
    },

    notifyTask: async function(taskId, mode) {
        const loading = UI.loading('Đang gửi thông báo...');
        try {
            const resp = await api.post(`/tasks/${taskId}/notify?mode=${mode}`);
            loading.close();
            if (resp?.success) {
                const members = resp.data || [];
                const msg = members.length > 0 
                    ? `Đã gửi thông báo cho: ${members.join(', ')}` 
                    : (resp.message || 'Đã gửi thông báo');
                UI.toast(msg, 'success', 5000);
                // Refresh task list to update "notified" status if needed (though not shown in UI yet)
                this.loadProjectTasks();
            } else {
                UI.handleError(resp.error || {message: 'Lỗi'});
            }
        } catch (err) {
            loading.close();
            UI.handleError(err);
        }
    },

    loadProjectTasks: async function() {
        const pid = this.currentProjectId;
        if (!pid) return;
        const container = document.getElementById('details-task-list');
        container.innerHTML = '<tr><td colspan="6" class="text-center py-4">Đang tải...</td></tr>';
        
        const resp = await api.get(`/tasks?project_id=${pid}`);
        if (resp?.success) {
            this.currentProjectTasks = resp.data || [];
            
            const assigneesMap = {};
            this.currentProjectTasks.forEach(t => {
                t.members.forEach(m => assigneesMap[m.id] = m.full_name);
            });
            const assigneeSelect = document.getElementById('task-filter-assignee');
            if (assigneeSelect) {
                assigneeSelect.innerHTML = '<option value="">Tất cả Assignee</option>' + 
                    Object.entries(assigneesMap).map(([id, name]) => `<option value="${id}">${UI.esc(name)}</option>`).join('');
                assigneeSelect.value = '';
            }

            const statusSelect = document.getElementById('task-filter-status');
            if (statusSelect) {
                statusSelect.value = this.initialTaskFilter || '';
                this.initialTaskFilter = null;
            }

            this.filterProjectTasks();
        } else {
            container.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-danger">Lỗi tải dữ liệu</td></tr>';
        }
    },

    filterProjectTasks: function() {
        const statusFilter = document.getElementById('task-filter-status')?.value;
        const assigneeFilter = document.getElementById('task-filter-assignee')?.value;
        let tasks = this.currentProjectTasks || [];
        
        if (statusFilter) {
            if (statusFilter === 'overdue') {
                tasks = tasks.filter(t => t.deadline && new Date(t.deadline) < new Date(new Date().setHours(0,0,0,0)) && !['done', 'archived'].includes(t.status));
            } else {
                tasks = tasks.filter(t => t.status === statusFilter);
            }
        }
        if (assigneeFilter) {
            tasks = tasks.filter(t => t.members.some(m => m.id == assigneeFilter));
        }
        
        this.renderProjectTasks(tasks);
    },

    renderProjectTasks: function(tasks) {
        const container = document.getElementById('details-task-list');
        if (!tasks || tasks.length === 0) {
            container.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">Không có task nào phù hợp</td></tr>';
            return;
        }
        
        container.innerHTML = tasks.map(t => {
            const assignees = t.members.map(m => `
                <span class="badge bg-primary-subtle text-primary border me-1 small fw-normal" title="${UI.esc(m.full_name)}" style="cursor:pointer;" onclick="UI.showMemberDetails(${m.id})">
                    ${UI.initials(m.full_name)}
                </span>
            `).join('');
            const isOverdue = t.deadline && new Date(t.deadline) < new Date(new Date().setHours(0,0,0,0)) && !['done', 'archived'].includes(t.status);
            const deadlineColor = isOverdue ? 'text-danger fw-bold' : 'text-secondary';
            
            return `
            <tr>
                <td style="width: 220px; min-width: 220px;">
                    <div class="fw-bold small text-dark mb-1">${UI.esc(t.name)}</div>
                    <div class="text-secondary d-flex flex-column" style="font-size:0.75rem; line-height: 1.2; height: 2.4rem; overflow: hidden;" title="${UI.esc(t.description || '')}">
                        ${(() => {
                            const desc = t.description || '';
                            if (!desc) return '';
                            const rawLines = desc.split(/\r?\n/).filter(l => l.trim().length > 0);
                            const processedLines = rawLines.slice(0, 2).map(line => {
                                const words = line.trim().split(/\s+/);
                                if (words.length > 5) return words.slice(0, 5).join(' ') + '...';
                                return line.trim();
                            });
                            const line1 = processedLines[0] || '';
                            const line2 = processedLines[1] || (rawLines.length > 2 ? '...' : '');
                            return `<div class="text-truncate" style="height:1.2rem; display:block;">${UI.esc(line1)}</div><div class="text-truncate" style="height:1.2rem; display:block;">${UI.esc(line2) || '&nbsp;'}</div>`;
                        })()}
                    </div>
                </td>
                <td><div class="d-flex flex-wrap">${assignees || '—'}</div></td>
                <td class="small text-secondary">${UI.fmtDate(t.start_date)}</td>
                <td class="small ${deadlineColor}">${UI.fmtDate(t.deadline)}</td>
                <td><span class="badge status-${t.status} rounded-pill fw-normal" style="font-size:0.65rem">${t.status.toUpperCase()}</span></td>
                <td>
                    ${t.jira_link ? `<a href="${t.jira_link}" target="_blank" class="btn btn-sm btn-light rounded-circle shadow-sm p-1 text-primary" style="width:28px;height:28px;display:inline-flex;align-items:center;justify-content:center" title="Mở Jira"><i class="bi bi-box-arrow-up-right"></i></a>` : '—'}
                </td>
                <td class="text-end pe-3">
                    <div class="d-flex justify-content-end gap-1">
                        ${UI.hasPermission('write', 'projects') ? `
                            <div class="dropup d-inline-block">
                                <button class="btn btn-sm btn-light p-1" type="button" data-bs-toggle="dropdown" title="Gửi thông báo ChatOps">🔔</button>
                                <ul class="dropdown-menu dropdown-menu-end shadow border-0" style="font-size:0.8rem">
                                    <li><a class="dropdown-item" href="#" onclick="ProjectsUI.notifyTask(${t.id}, 'all')">📢 Gửi tất cả member</a></li>
                                    <li><a class="dropdown-item" href="#" onclick="ProjectsUI.notifyTask(${t.id}, 'new')">🆕 Chỉ gửi member mới</a></li>
                                </ul>
                            </div>
                            <button class="btn btn-sm btn-light p-1" onclick='ProjectsUI.openTaskModal(${JSON.stringify(t).replace(/'/g, "&apos;")})' title="Sửa">✏️</button>
                            <button class="btn btn-sm btn-light p-1 text-danger" onclick="ProjectsUI.deleteTask(${t.id})" title="Xóa">🗑️</button>
                        ` : ''}
                    </div>
                </td>
            </tr>
            `;
        }).join('');
    },

    openTaskModal: async function(task = null) {
        const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('task-modal'));
        const form = document.getElementById('task-form');
        form.reset();
        
        document.getElementById('task-id').value = task ? task.id : '';
        document.getElementById('task-project-id').value = this.currentProjectId;
        document.getElementById('task-modal-title').innerText = task ? 'Sửa Task' : 'Tạo Task mới';
        
        if (!task) {
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('task-start-date').value = today;
            document.getElementById('task-deadline').value = today;
        }

        if (task) {
            document.getElementById('task-name').value = task.name;
            document.getElementById('task-description').value = task.description || '';
            document.getElementById('task-start-date').value = task.start_date || '';
            document.getElementById('task-deadline').value = task.deadline || '';
            document.getElementById('task-status').value = task.status;
            document.getElementById('task-priority').value = task.priority;
            document.getElementById('task-jira-link').value = task.jira_link || '';
        }

        // Load project members for assignees
        const assigneesList = document.getElementById('task-assignees-list');
        assigneesList.innerHTML = '<div class="small text-secondary p-2 w-100">Đang tải thành viên...</div>';
        
        const mResp = await api.get(`/projects/${this.currentProjectId}/members`);
        if (mResp?.success) {
            const selectedIds = task ? task.members.map(m => m.id) : [];
            assigneesList.innerHTML = mResp.data.map(m => `
                <div class="m-1">
                    <input type="checkbox" class="btn-check" name="member_ids" value="${m.member_id}" id="chk-m-${m.member_id}" ${selectedIds.includes(m.member_id) ? 'checked' : ''} autocomplete="off">
                    <label class="btn btn-sm btn-outline-primary rounded-pill px-3 py-1" for="chk-m-${m.member_id}" style="font-size:0.75rem">
                        ${UI.esc(m.member_name)}
                    </label>
                </div>
            `).join('') || '<div class="small text-muted p-2 w-100 text-center">Dự án chưa có thành viên</div>';
        }

        modal.show();
    },

    saveTask: async function(e) {
        e.preventDefault();
        const form = e.target;
        const id = document.getElementById('task-id').value;
        const memberIds = Array.from(form.querySelectorAll('input[name="member_ids"]:checked')).map(cb => parseInt(cb.value));
        
        const data = {
            name: document.getElementById('task-name').value,
            description: document.getElementById('task-description').value,
            project_id: parseInt(document.getElementById('task-project-id').value),
            start_date: document.getElementById('task-start-date').value || null,
            deadline: document.getElementById('task-deadline').value || null,
            status: document.getElementById('task-status').value,
            priority: document.getElementById('task-priority').value,
            jira_link: document.getElementById('task-jira-link').value || null,
            member_ids: memberIds
        };

        const resp = id ? await api.patch(`/tasks/${id}`, data) : await api.post('/tasks', data);
        if (resp?.success) {
            bootstrap.Modal.getInstance(document.getElementById('task-modal')).hide();
            UI.toast(id ? 'Đã cập nhật task' : 'Đã tạo task thành công', 'success');
            this.loadProjectTasks();
        } else UI.handleError(resp.error || {message: 'Lỗi'});
    },

    deleteTask: async function(id) {
        UI.confirmDialog('Xóa task này?').then(async (confirmed) => {
            if (confirmed) {
                const resp = await api.delete(`/tasks/${id}`);
                if (resp?.success) {
                    this.loadProjectTasks();
                    UI.toast('Đã xóa task', 'success');
                } else UI.handleError(resp.error || {message: 'Lỗi'});
            }
        });
    }
};


