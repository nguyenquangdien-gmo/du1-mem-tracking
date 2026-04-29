// Render top navbar + sidebar on every page. Handles global search.
const Layout = (() => {
  function renderShell(activeMenu) {
    const app = document.createElement("div");
    app.className = "app";
    app.innerHTML = `
      <header class="topbar">
        <a href="index.html" class="logo">MEMBER TRACKING</a>
        <div class="spacer"></div>
        <div class="search">
          <input id="global-search" type="text" placeholder="🔍 Tìm member, project, task..." autocomplete="off" />
          <div id="search-results" class="search-results"></div>
        </div>
        <div class="text-muted text-sm">Admin</div>
      </header>
      <div class="main">
        <aside class="sidebar">
          <nav>
            <a href="index.html" data-menu="dashboard">📊 Dashboard</a>
            <a href="projects.html" data-menu="projects">📁 Projects</a>
            <a href="tasks.html" data-menu="tasks">✅ Tasks</a>
            <a href="members.html" data-menu="members">👥 Members</a>
            <a href="departments.html" data-menu="departments">🏢 Departments</a>
          </nav>
          <h5>Quick add</h5>
          <div style="padding: 0 12px;">
            <button class="btn btn-small" id="quick-project" style="width:100%;margin-bottom:6px">+ Project</button>
            <button class="btn btn-small" id="quick-task" style="width:100%;margin-bottom:6px">+ Task</button>
            <button class="btn btn-small" id="quick-member" style="width:100%">+ Member</button>
          </div>
        </aside>
        <main class="content" id="content"></main>
      </div>
    `;
    document.body.insertBefore(app, document.body.firstChild);

    // Set active
    if (activeMenu) {
      const link = app.querySelector(`[data-menu="${activeMenu}"]`);
      if (link) link.classList.add("active");
    }

    // Global search wiring
    const input = document.getElementById("global-search");
    const results = document.getElementById("search-results");
    let t = null;
    input.addEventListener("input", () => {
      clearTimeout(t);
      const q = input.value.trim();
      if (!q) { results.classList.remove("open"); results.innerHTML = ""; return; }
      t = setTimeout(async () => {
        try {
          const resp = await API.search(q, "all", 6);
          renderSearchResults(resp.data, results);
        } catch (e) { console.warn(e); }
      }, 200);
    });
    document.addEventListener("click", (e) => {
      if (!results.contains(e.target) && e.target !== input) {
        results.classList.remove("open");
      }
    });

    document.getElementById("quick-project").onclick = () => openQuickCreate("project");
    document.getElementById("quick-task").onclick = () => openQuickCreate("task");
    document.getElementById("quick-member").onclick = () => openQuickCreate("member");
  }

  function renderSearchResults(data, host) {
    let html = "";
    const total = (data.members.length + data.projects.length + data.tasks.length);
    if (total === 0) { host.innerHTML = `<div style="padding:14px;color:#6b7280">Không có kết quả</div>`; host.classList.add("open"); return; }
    if (data.members.length) {
      html += `<h4>Members (${data.members.length})</h4>`;
      for (const m of data.members) html += `<div class="item" onclick="location.href='member-detail.html?id=${m.id}'">${UI.avatarHTML(m.full_name)} <strong>${UI.esc(m.full_name)}</strong> — ${UI.esc(m.department || "")} · ${UI.esc(m.default_role || "")}</div>`;
    }
    if (data.projects.length) {
      html += `<h4>Projects (${data.projects.length})</h4>`;
      for (const p of data.projects) html += `<div class="item" onclick="location.href='project-detail.html?id=${p.id}'">📁 <strong>${UI.esc(p.name)}</strong> · ${UI.esc(p.status)}</div>`;
    }
    if (data.tasks.length) {
      html += `<h4>Tasks (${data.tasks.length})</h4>`;
      for (const t of data.tasks) html += `<div class="item" onclick="location.href='project-detail.html?id=${t.project_id}'">✅ ${UI.esc(t.name)} <span class="badge">${UI.esc(t.status)}</span></div>`;
    }
    host.innerHTML = html;
    host.classList.add("open");
  }

  async function openQuickCreate(kind) {
    if (kind === "member") return Forms.memberForm();
    if (kind === "project") return Forms.projectForm();
    if (kind === "task") return Forms.taskForm();
  }

  return { renderShell };
})();

window.Layout = Layout;
