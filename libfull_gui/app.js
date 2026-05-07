(function () {
  "use strict";

  const state = {
    apiBase: localStorage.getItem("libful.gui.apiBase") || "/api/v1",
    username: localStorage.getItem("libful.gui.username") || "",
    password: sessionStorage.getItem("libful.gui.password") || "",
  };

  const $ = (selector) => document.querySelector(selector);
  const byId = (id) => document.getElementById(id);

  const escapeHtml = (value) =>
    String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");

  const compact = (data) => {
    const out = {};
    Object.entries(data).forEach(([key, value]) => {
      if (value !== "" && value !== null && value !== undefined) {
        out[key] = value;
      }
    });
    return out;
  };

  const formData = (form) => compact(Object.fromEntries(new FormData(form).entries()));

  const toNumber = (value) => {
    if (value === "" || value === null || value === undefined) return undefined;
    return Number(value);
  };

  const toIso = (value) => {
    if (!value) return undefined;
    return new Date(value).toISOString();
  };

  const formatDate = (value) => {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString("uk-UA", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const buildQuery = (params = {}) => {
    const search = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== "" && value !== null && value !== undefined) {
        search.set(key, value);
      }
    });
    const query = search.toString();
    return query ? `?${query}` : "";
  };

  const authHeader = () => {
    if (!state.username && !state.password) return {};
    const bytes = new TextEncoder().encode(`${state.username}:${state.password}`);
    let binary = "";
    bytes.forEach((byte) => {
      binary += String.fromCharCode(byte);
    });
    return { Authorization: `Basic ${btoa(binary)}` };
  };

  const endpoint = (path) => {
    const base = state.apiBase.replace(/\/+$/, "");
    const suffix = path.startsWith("/") ? path : `/${path}`;
    return `${base}${suffix}`;
  };

  async function api(path, options = {}) {
    const headers = {
      Accept: "application/json",
      ...authHeader(),
      ...(options.headers || {}),
    };

    if (options.body !== undefined) {
      headers["Content-Type"] = "application/json";
    }

    const response = await fetch(endpoint(path), {
      ...options,
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    });

    if (response.status === 204) return null;

    const text = await response.text();
    const payload = text ? JSON.parse(text) : null;

    if (!response.ok) {
      const detail = payload?.detail;
      const message = Array.isArray(detail)
        ? detail.map((item) => item.msg || JSON.stringify(item)).join("; ")
        : detail || `HTTP ${response.status}`;
      throw new Error(message);
    }

    return payload;
  }

  function notify(message, type = "ok") {
    const notice = byId("notice");
    notice.textContent = message;
    notice.className = type === "error" ? "notice error" : "notice";
    notice.hidden = false;
    window.clearTimeout(notify.timer);
    notify.timer = window.setTimeout(() => {
      notice.hidden = true;
    }, 5200);
  }

  async function withNotice(action, success) {
    try {
      const result = await action();
      if (success) notify(success);
      return result;
    } catch (error) {
      notify(error.message || "Помилка запиту", "error");
      throw error;
    }
  }

  function badge(value, extra = "") {
    const label = value ?? "";
    return `<span class="badge ${escapeHtml(extra || label)}">${escapeHtml(label)}</span>`;
  }

  function renderTable(targetId, columns, rows, actions) {
    const target = byId(targetId);
    if (!rows || rows.length === 0) {
      target.innerHTML = '<div class="empty">Немає записів</div>';
      return;
    }

    const head = columns.map((column) => `<th>${escapeHtml(column.label)}</th>`).join("");
    const actionHead = actions ? "<th>Дії</th>" : "";
    const body = rows
      .map((row) => {
        const cells = columns
          .map((column) => {
            const raw = typeof column.value === "function" ? column.value(row) : row[column.value];
            const value = column.html ? raw : escapeHtml(raw);
            return `<td class="${column.wrap ? "wrap" : ""}">${value ?? ""}</td>`;
          })
          .join("");
        const actionCell = actions ? `<td><div class="row-actions">${actions(row)}</div></td>` : "";
        return `<tr>${cells}${actionCell}</tr>`;
      })
      .join("");

    target.innerHTML = `<table><thead><tr>${head}${actionHead}</tr></thead><tbody>${body}</tbody></table>`;
  }

  function renderUsers(rows) {
    renderTable(
      "users-table",
      [
        { label: "ID", value: "id" },
        { label: "Username", value: "username" },
        { label: "Ім'я", value: (row) => `${row.first_name} ${row.last_name}` },
        { label: "Email", value: "email" },
        { label: "Телефон", value: "phone" },
        {
          label: "Ролі",
          html: true,
          value: (row) => (row.roles || []).map((role) => badge(role.name)).join(" "),
        },
      ],
      rows,
      (row) =>
        `<button data-action="delete-user" data-username="${escapeHtml(row.username)}">Видалити</button>`
    );
  }

  function renderSimple(target, rows, nameKey, deleteAction) {
    renderTable(
      target,
      [
        { label: "ID", value: "id" },
        { label: "Назва", value: nameKey, wrap: true },
      ],
      rows,
      (row) => `<button data-action="${deleteAction}" data-id="${row.id}">Видалити</button>`
    );
  }

  function renderBooks(rows) {
    renderTable(
      "books-table",
      [
        { label: "ID", value: "id" },
        { label: "Назва", value: "title", wrap: true },
        { label: "Автор ID", value: "author_id" },
        { label: "Жанр ID", value: "genre_id" },
        { label: "Рік", value: "publish_year" },
        { label: "ISBN", value: "isbn" },
      ],
      rows,
      (row) =>
        `<button data-action="count-copies" data-id="${row.id}">Примірники</button><button data-action="delete-book" data-id="${row.id}">Видалити</button>`
    );
  }

  function renderCopies(rows) {
    renderTable(
      "copies-table",
      [
        { label: "ID", value: "id" },
        { label: "Книга ID", value: "book_id" },
        { label: "Інв. номер", value: "inventory_number" },
        { label: "Статус", html: true, value: (row) => badge(row.status) },
        { label: "Створено", value: (row) => formatDate(row.created_at) },
      ],
      rows,
      (row) => `<button data-action="delete-copy" data-id="${row.id}">Видалити</button>`
    );
  }

  function renderRents(target, rows) {
    renderTable(
      target,
      [
        { label: "ID", value: "id" },
        { label: "Примірник", value: "book_copy_id" },
        { label: "Читач", value: "user_id" },
        { label: "Видано", value: (row) => formatDate(row.rented_at) },
        { label: "Дедлайн", value: (row) => formatDate(row.due_at) },
        { label: "Повернено", value: (row) => formatDate(row.returned_at) },
        { label: "Статус", html: true, value: (row) => badge(row.return_status || "активна", row.returned_at ? row.return_status : "borrowed") },
        { label: "Нотатки", value: "notes", wrap: true },
      ],
      rows,
      (row) =>
        `<button data-action="preview-fines" data-id="${row.id}">Штрафи</button>`
    );
  }

  function renderFines(rows, preview = false) {
    renderTable(
      "fines-table",
      [
        { label: "ID", value: (row) => row.id || "-" },
        { label: "Видача", value: (row) => row.book_rent_id || "-" },
        { label: "Читач", value: (row) => row.user_id || "-" },
        { label: "Тип", value: "fine_type" },
        { label: "Сума", value: (row) => `${row.amount_uah} грн` },
        { label: "Днів", value: (row) => row.days_overdue ?? "" },
        { label: "Стан", html: true, value: (row) => badge(row.paid_at ? "оплачено" : "не оплачено", row.paid_at ? "paid" : "unpaid") },
        { label: "Нотатки", value: "notes", wrap: true },
      ],
      rows,
      preview
        ? null
        : (row) => row.paid_at ? "" : `<button data-action="pay-fine" data-id="${row.id}">Оплатити</button>`
    );
  }

  async function loadUsers(params) {
    const hasFilters = params && Object.keys(compact(params)).length > 0;
    const rows = hasFilters
      ? await api(`/users/search${buildQuery({ ...params, limit: 100, offset: 0 })}`)
      : await api("/users/?limit=100&offset=0");
    renderUsers(rows);
    return rows;
  }

  async function loadCatalog() {
    const [authors, genres, books] = await Promise.all([
      api("/authors/?limit=100&offset=0"),
      api("/genres/?limit=100&offset=0"),
      api("/books/?limit=100&offset=0"),
    ]);
    renderSimple("authors-table", authors, "full_name", "delete-author");
    renderSimple("genres-table", genres, "name", "delete-genre");
    renderBooks(books);
    return { authors, genres, books };
  }

  async function loadCopies(params = {}) {
    const rows = await api(`/book-copies/${buildQuery({ ...params, limit: 100, offset: 0 })}`);
    renderCopies(rows);
    return rows;
  }

  async function loadHistory(params = {}) {
    const rows = await api(`/book-rents/history${buildQuery({ ...params, limit: 100, offset: 0 })}`);
    renderRents("rents-table", rows);
    return rows;
  }

  async function loadOverdue(params = {}) {
    const rows = await api(`/book-rents/overdue${buildQuery({ ...params, limit: 100, offset: 0 })}`);
    renderRents("rents-table", rows);
    return rows;
  }

  async function loadFines(params = {}) {
    const rows = await api(`/book-rents/fines${buildQuery({ ...params, limit: 100, offset: 0 })}`);
    renderFines(rows);
    return rows;
  }

  async function loadRoles() {
    const rows = await api("/roles/");
    renderTable("roles-table", [{ label: "ID", value: "id" }, { label: "Роль", value: "name" }], rows);
    return rows;
  }

  async function refreshOverview() {
    const [users, books, copies, overdue] = await Promise.all([
      api("/users/?limit=100&offset=0"),
      api("/books/?limit=100&offset=0"),
      api("/book-copies/?limit=100&offset=0"),
      api("/book-rents/overdue?limit=100&offset=0"),
    ]);
    byId("stat-users").textContent = users.length;
    byId("stat-books").textContent = books.length;
    byId("stat-copies").textContent = copies.length;
    byId("stat-overdue").textContent = overdue.length;
    const history = await api("/book-rents/history?limit=8&offset=0");
    const fines = await api("/book-rents/fines?is_paid=false&limit=8&offset=0");
    renderRents("overview-history", history);
    renderFines(fines);
    byId("overview-fines").innerHTML = byId("fines-table").innerHTML;
  }

  function bindForm(id, handler) {
    byId(id).addEventListener("submit", async (event) => {
      event.preventDefault();
      await handler(event.currentTarget, event.submitter);
    });
  }

  function bindForms() {
    bindForm("connection-form", async (form) => {
      const data = formData(form);
      state.apiBase = data.apiBase || "/api/v1";
      state.username = data.username || "";
      state.password = data.password || "";
      localStorage.setItem("libful.gui.apiBase", state.apiBase);
      localStorage.setItem("libful.gui.username", state.username);
      sessionStorage.setItem("libful.gui.password", state.password);
      notify("Підключення збережено");
      await withNotice(() => refreshOverview());
    });

    bindForm("user-form", async (form) => {
      const data = formData(form);
      const payload = {
        username: data.username,
        first_name: data.first_name,
        last_name: data.last_name,
        email: data.email,
        phone: data.phone,
        password: data.password,
        roles: data.role ? [data.role] : [],
      };
      delete payload.role;
      await withNotice(() => api("/users/", { method: "POST", body: compact(payload) }), "Користувача створено");
      form.reset();
      await loadUsers();
    });

    bindForm("user-search-form", async (form) => {
      await withNotice(() => loadUsers(formData(form)));
    });

    bindForm("check-in-form", async (form) => {
      const data = formData(form);
      await withNotice(
        () => api("/check-ins/", { method: "POST", body: { user_id: toNumber(data.user_id) } }),
        "Візит зареєстровано"
      );
      form.reset();
    });

    bindForm("author-form", async (form) => {
      await withNotice(() => api("/authors/", { method: "POST", body: formData(form) }), "Автора додано");
      form.reset();
      await loadCatalog();
    });

    bindForm("genre-form", async (form) => {
      await withNotice(() => api("/genres/", { method: "POST", body: formData(form) }), "Жанр додано");
      form.reset();
      await loadCatalog();
    });

    bindForm("book-form", async (form) => {
      const data = formData(form);
      const payload = compact({
        title: data.title,
        author_id: toNumber(data.author_id),
        genre_id: toNumber(data.genre_id),
        publish_year: toNumber(data.publish_year),
        isbn: data.isbn,
      });
      await withNotice(() => api("/books/", { method: "POST", body: payload }), "Книгу додано");
      form.reset();
      await loadCatalog();
    });

    bindForm("book-search-form", async (form) => {
      const rows = await withNotice(() => api(`/books/search${buildQuery({ ...formData(form), limit: 100, offset: 0 })}`));
      renderBooks(rows);
    });

    bindForm("copy-form", async (form) => {
      const data = formData(form);
      await withNotice(
        () =>
          api("/book-copies/", {
            method: "POST",
            body: {
              book_id: toNumber(data.book_id),
              inventory_number: data.inventory_number,
              status: data.status,
            },
          }),
        "Примірник додано"
      );
      form.reset();
      await loadCopies();
    });

    bindForm("copy-filter-form", async (form) => {
      await withNotice(() => loadCopies(formData(form)));
    });

    bindForm("issue-form", async (form) => {
      const data = formData(form);
      const payload = compact({
        book_copy_id: toNumber(data.book_copy_id),
        user_id: toNumber(data.user_id),
        due_at: toIso(data.due_at),
        notes: data.notes,
      });
      await withNotice(() => api("/book-rents/issue", { method: "POST", body: payload }), "Книгу видано");
      form.reset();
      await loadHistory();
    });

    bindForm("return-form", async (form) => {
      const data = formData(form);
      const payload = compact({
        return_status: data.return_status,
        returned_at: toIso(data.returned_at),
        notes: data.notes,
      });
      await withNotice(
        () => api(`/book-rents/${data.book_rent_id}/return`, { method: "POST", body: payload }),
        "Повернення збережено"
      );
      form.reset();
      await loadHistory();
    });

    bindForm("deadline-form", async (form) => {
      const data = formData(form);
      await withNotice(
        () =>
          api(`/book-rents/${data.book_rent_id}/deadline`, {
            method: "PATCH",
            body: { due_at: toIso(data.due_at) },
          }),
        "Дедлайн змінено"
      );
      form.reset();
      await loadHistory();
    });

    bindForm("history-filter-form", async (form) => {
      await withNotice(() => loadHistory(formData(form)));
    });

    bindForm("fine-filter-form", async (form) => {
      await withNotice(() => loadFines(formData(form)));
    });

    bindForm("fine-preview-form", async (form) => {
      const data = formData(form);
      const rows = await withNotice(() =>
        api(`/book-rents/${data.book_rent_id}/fines/preview${buildQuery({ return_status: data.return_status })}`)
      );
      renderFines(rows, true);
    });

    bindForm("role-form", async (form, submitter) => {
      const data = formData(form);
      const method = submitter?.value === "remove" ? "DELETE" : "PUT";
      await withNotice(
        () => api(`/users/${encodeURIComponent(data.username)}/roles/${data.role_name}`, { method }),
        method === "DELETE" ? "Роль прибрано" : "Роль додано"
      );
      await loadUsers();
    });
  }

  async function deleteResource(path, success, after) {
    if (!window.confirm("Видалити запис?")) return;
    await withNotice(() => api(path, { method: "DELETE" }), success);
    if (after) await after();
  }

  function bindActions() {
    document.addEventListener("click", async (event) => {
      const button = event.target.closest("button[data-action]");
      if (!button) return;
      const { action, id, username } = button.dataset;

      try {
        if (action === "refresh-overview") await withNotice(() => refreshOverview());
        if (action === "load-users") await withNotice(() => loadUsers());
        if (action === "load-catalog") await withNotice(() => loadCatalog());
        if (action === "load-copies") await withNotice(() => loadCopies());
        if (action === "load-history") await withNotice(() => loadHistory());
        if (action === "load-overdue") await withNotice(() => loadOverdue(formData(byId("history-filter-form"))));
        if (action === "load-fines") await withNotice(() => loadFines());
        if (action === "load-unpaid-fines") {
          const rows = await withNotice(() => api("/book-rents/fines?is_paid=false&limit=8&offset=0"));
          renderTable(
            "overview-fines",
            [
              { label: "ID", value: "id" },
              { label: "Читач", value: "user_id" },
              { label: "Сума", value: (row) => `${row.amount_uah} грн` },
              { label: "Тип", value: "fine_type" },
            ],
            rows
          );
        }
        if (action === "load-roles") await withNotice(() => loadRoles());
        if (action === "delete-user") await deleteResource(`/users/${encodeURIComponent(username)}`, "Користувача видалено", loadUsers);
        if (action === "delete-author") await deleteResource(`/authors/${id}`, "Автора видалено", loadCatalog);
        if (action === "delete-genre") await deleteResource(`/genres/${id}`, "Жанр видалено", loadCatalog);
        if (action === "delete-book") await deleteResource(`/books/${id}`, "Книгу видалено", loadCatalog);
        if (action === "delete-copy") await deleteResource(`/book-copies/${id}`, "Примірник видалено", loadCopies);
        if (action === "count-copies") {
          const result = await withNotice(() => api(`/books/${id}/copies/count`));
          notify(`Книга #${result.book_id}: ${result.copies_count} примірників`);
        }
        if (action === "preview-fines") {
          document.querySelector('[data-tab="fines"]').click();
          const rows = await withNotice(() => api(`/book-rents/${id}/fines/preview`));
          renderFines(rows, true);
        }
        if (action === "pay-fine") {
          await withNotice(() => api(`/book-rents/fines/${id}/pay`, { method: "POST" }), "Штраф оплачено");
          await loadFines(formData(byId("fine-filter-form")));
        }
      } catch (_) {
        /* withNotice already displayed the error */
      }
    });
  }

  function bindTabs() {
    document.querySelectorAll(".tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        document.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
        document.querySelectorAll(".view").forEach((item) => item.classList.remove("active"));
        tab.classList.add("active");
        byId(tab.dataset.tab).classList.add("active");
      });
    });
  }

  function hydrateConnection() {
    byId("api-base").value = state.apiBase;
    byId("auth-user").value = state.username;
    byId("auth-pass").value = state.password;
  }

  document.addEventListener("DOMContentLoaded", async () => {
    hydrateConnection();
    bindTabs();
    bindForms();
    bindActions();
    if (state.username || state.password) {
      try {
        await refreshOverview();
      } catch (error) {
        notify(error.message || "Не вдалося підключитися до API", "error");
      }
    }
  });
})();
