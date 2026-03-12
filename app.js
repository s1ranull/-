import { api } from "./api.js";

const app = document.getElementById("app");
const who = document.getElementById("who");
const logoutBtn = document.getElementById("logoutBtn");
const adminLink = document.getElementById("adminLink");
const toast = document.getElementById("toast");

function esc(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function showToast(text) {
  toast.textContent = text;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2200);
}

function setSession(token, user) {
  localStorage.setItem("token", token);
  localStorage.setItem("user", JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}

function getUser() {
  try { return JSON.parse(localStorage.getItem("user")); } catch { return null; }
}

function setTopbar() {
  const u = getUser();
  who.textContent = u ? `${u.username} (${u.role})` : "не вошли";
  logoutBtn.style.display = u ? "inline-block" : "none";
  adminLink.style.display = u && u.role === "admin" ? "inline-block" : "none";
}

logoutBtn.onclick = () => {
  clearSession();
  setTopbar();
  location.hash = "#/login";
};

async function requireAuth() {
  const token = localStorage.getItem("token");
  if (!token) {
    location.hash = "#/login";
    return null;
  }
  try {
    const u = await api.me();
    localStorage.setItem("user", JSON.stringify(u));
    setTopbar();
    return u;
  } catch {
    clearSession();
    setTopbar();
    location.hash = "#/login";
    return null;
  }
}

function h(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}



function viewLogin() {
  app.innerHTML = "";
  const node = h(`
    <div class="grid">
      <section class="card">
        <div class="h1">Вход</div>

        <div class="field">
          <label>Username</label>
          <input id="u" placeholder="например: ilya"/>
        </div>
        <div class="field">
          <label>Password</label>
          <input id="p" type="password" placeholder="пароль"/>
        </div>
        <button class="btn primary" id="loginBtn">Войти</button>

        <div class="hr"></div>

        <div class="h1" style="font-size:22px;">Регистрация</div>
        <div class="field">
          <label>New username</label>
          <input id="ru" placeholder="например: student1"/>
        </div>
        <div class="field">
          <label>New password</label>
          <input id="rp" type="password" placeholder="пароль"/>
        </div>
        <button class="btn ghost" id="regBtn">Создать аккаунт</button>

        <div class="hr"></div>
        <div class="muted">Демо-админ: <b>admin</b> / <b>admin123</b></div>
      </section>

      <section class="card">
        <div class="h1">Платформа</div>
        <div class="muted">Материал → тест → статистика → сертификат.</div>
      </section>
    </div>
  `);

  node.querySelector("#loginBtn").onclick = async () => {
    const username = node.querySelector("#u").value.trim();
    const password = node.querySelector("#p").value;
    try {
      const res = await api.login(username, password);
      setSession(res.token, res.user);
      setTopbar();
      showToast("Вход выполнен");
      location.hash = "#/courses";
    } catch (e) {
      showToast(`Ошибка: ${e.message}`);
    }
  };

  node.querySelector("#regBtn").onclick = async () => {
    const username = node.querySelector("#ru").value.trim();
    const password = node.querySelector("#rp").value;
    try {
      await api.register(username, password);
      showToast("Аккаунт создан");
      node.querySelector("#u").value = username;
      node.querySelector("#p").focus();
    } catch (e) {
      showToast(`Ошибка: ${e.message}`);
    }
  };

  app.appendChild(node);
}

async function viewCourses() {
  const u = await requireAuth();
  if (!u) return;

  app.innerHTML = "";
  const node = h(`
    <div class="grid">
      <section class="card">
        <div class="h1">Курсы</div>
        <div class="hr"></div>
        <div class="list" id="list"></div>
      </section>

      <section class="card" id="right">
        <div class="h1">Выбери курс</div>
        <div class="muted">Сначала материал, потом тест.</div>
      </section>
    </div>
  `);

  const list = node.querySelector("#list");
  const right = node.querySelector("#right");

  const courses = await api.courses();
  courses.forEach((c) => {
    const item = h(`
      <div class="item">
        <div style="display:flex; justify-content:space-between; gap:10px; align-items:flex-start;">
          <div>
            <div style="font-weight:900; font-family:Georgia,serif;">${esc(c.title)}</div>
            <div class="muted">${esc(c.description)}</div>
            <div class="pills"><span class="pill">${esc(c.type)}</span></div>
          </div>
          <button class="btn ghost">Открыть</button>
        </div>
      </div>
    `);
    item.querySelector("button").onclick = () => openCourse(c.id, right);
    list.appendChild(item);
  });

  app.appendChild(node);
}

function renderCourseContent(contentEl, c) {
  if (c.type === "video") {
    const url = c.video_url || "";
    const isMp4 = url.toLowerCase().endsWith(".mp4");

    const videoBlock = isMp4
      ? `<video controls style="width:100%; border-radius:16px; border:1px solid rgba(25,35,40,.14); background:#000;">
           <source src="${url}" type="video/mp4" />
         </video>`
      : `<iframe
           src="${url}"
           style="width:100%; aspect-ratio:16/9; border-radius:16px; border:1px solid rgba(25,35,40,.14); background:#000;"
           allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
           allowfullscreen
         ></iframe>`;

    contentEl.innerHTML = `
      <div class="list">
        <div class="item">${videoBlock}</div>
        ${c.notes ? `<div class="item">${c.notes}</div>` : ``}
      </div>
    `;
    return;
  }

  if (c.type === "text") {
    contentEl.innerHTML = `<div class="item">${c.text ?? ""}</div>`;
    return;
  }

  const steps = c.steps || [];
  contentEl.innerHTML = `
    <div class="item">
      ${c.notes ? `<div style="margin-bottom:10px;">${c.notes}</div>` : ``}
      ${steps.map((s) => `
        <label style="display:flex; gap:10px; align-items:center; margin-top:8px;">
          <input type="checkbox" style="width:auto;">
          <span>${esc(s)}</span>
        </label>
      `).join("")}
    </div>
  `;
}


function renderTest({ t, courseId, mount }) {
  const testBox = mount.querySelector("#testBox");
  if (!t) {
    testBox.innerHTML = `<div class="muted">У этого курса нет теста.</div>`;
    return;
  }

  testBox.innerHTML = "";

  const header = document.createElement("div");
  header.innerHTML = `
    <div class="h1" style="font-size:22px;">${esc(t.title)}</div>
    <div class="muted" id="liveStat">0/${t.questions.length} ответов</div>
  `;
  testBox.appendChild(header);

  const form = document.createElement("form");
  form.className = "list";

  const hintState = new Map();
  const liveStat = header.querySelector("#liveStat");

  function countAnswered() {
    let ans = 0;
    t.questions.forEach((q, i) => {
      if (q.kind === "choice") {
        const checked = form.querySelectorAll(`input[name="q_${i}"]:checked`).length;
        if (checked > 0) ans++;
      } else {
        const v = (form.querySelector(`input[name="q_${i}"]`)?.value || "").trim();
        if (v.length > 0) ans++;
      }
    });
    return ans;
  }

  function tick() {
    liveStat.textContent = `${countAnswered()}/${t.questions.length} ответов`;
  }

  t.questions.forEach((q, i) => {
    if (q.kind === "choice") {
      const isSingle = (q.select_mode ?? "multi") === "single";
      const inputType = isSingle ? "radio" : "checkbox";

      const item = document.createElement("div");
      item.className = "item";
      item.innerHTML = `
        <div style="display:flex; justify-content:space-between; gap:10px; align-items:flex-start;">
          <b>${i + 1}. ${esc(q.prompt)}</b>
          ${q.has_hint ? `<button type="button" class="btn ghost" data-hint="${i}">Подсказка</button>` : ``}
        </div>
        <div style="margin-top:10px;">
          ${(q.options || []).map((opt, idx) => `
            <label style="display:flex; gap:10px; align-items:center; margin-top:8px;">
              <input type="${inputType}" name="q_${i}" value="${idx}" style="width:auto;">
              <span>${esc(opt)}</span>
            </label>
          `).join("")}
        </div>
        <div class="hintwrap" id="hint_${i}"></div>
      `;
      form.appendChild(item);
    } else {
      const item = document.createElement("div");
      item.className = "item";
      item.innerHTML = `
        <div style="display:flex; justify-content:space-between; gap:10px; align-items:flex-start;">
          <b>${i + 1}. ${esc(q.prompt)}</b>
          ${q.has_hint ? `<button type="button" class="btn ghost" data-hint="${i}">Подсказка</button>` : ``}
        </div>
        <div style="margin-top:10px;">
          <input name="q_${i}" placeholder="Ответ..." />
        </div>
        <div class="hintwrap" id="hint_${i}"></div>
      `;
      form.appendChild(item);
    }
  });

  form.addEventListener("click", async (ev) => {
    const btn = ev.target.closest("[data-hint]");
    if (!btn) return;

    const qi = Number(btn.dataset.hint);
    const place = form.querySelector(`#hint_${qi}`);
    if (!place) return;

    if (hintState.has(qi)) {
      place.innerHTML = `<div class="hintbox">${esc(hintState.get(qi))}</div>`;
      return;
    }

    try {
      btn.disabled = true;
      const r = await api.hint(courseId, qi);
      hintState.set(qi, r.hint);
      place.innerHTML = `<div class="hintbox">${esc(r.hint)}</div>`;
    } catch {
      place.innerHTML = `<div class="hintbox">Подсказка недоступна</div>`;
    } finally {
      btn.disabled = false;
    }
  });

  const submitBtn = document.createElement("button");
  submitBtn.className = "btn primary";
  submitBtn.type = "submit";
  submitBtn.textContent = "Отправить тест";

  const res = document.createElement("div");
  res.style.marginTop = "10px";

  form.appendChild(submitBtn);
  testBox.appendChild(form);
  testBox.appendChild(res);

  form.addEventListener("input", tick);
  form.addEventListener("change", tick);

  form.onsubmit = async (e) => {
    e.preventDefault();

    const answers = t.questions.map((q, i) => {
      if (q.kind === "choice") {
        return [...form.querySelectorAll(`input[name="q_${i}"]:checked`)].map(x => Number(x.value));
      }
      return form.querySelector(`input[name="q_${i}"]`)?.value || "";
    });

    try {
      const r = await api.submitAttempt(courseId, answers);

      const stats = r.analytics ?? (await api.analytics(courseId));
      const ac = mount.querySelector("#analyticsCard");
      if (ac) {
        ac.innerHTML = `
          Попыток: <b>${stats.attempts}</b><br/>
          Лучший: <b>${stats.best ?? "-"}</b> • Средний: <b>${stats.avg ?? "-"}</b> • Последний: <b>${stats.last ?? "-"}</b>
        `;
      }

      const ok = r.percent >= 70;
      res.innerHTML = `
        <div class="item ${ok ? "good" : "bad"}">
          <b>Результат:</b> ${r.percent}% (${r.points}/${r.max_points})
        </div>
      `;

      showToast("Готово");
    } catch (err) {
      showToast(`Ошибка: ${err.message}`);
    }
  };

  tick();
}

async function openCourse(courseId, mount) {
  const c = await api.course(courseId);
  const t = await api.test(courseId);
  const hasTest = !!t;

  const a = hasTest ? await api.analytics(courseId) : null;

  const analyticsHtml = hasTest ? `
    <div class="hr"></div>
    <div class="h1" style="font-size:22px;">Статистика</div>
    <div class="item" id="analyticsCard">
      Попыток: <b>${a.attempts}</b><br/>
      Лучший: <b>${a.best ?? "-"}</b> • Средний: <b>${a.avg ?? "-"}</b> • Последний: <b>${a.last ?? "-"}</b>
    </div>
  ` : "";

  const certHtml = hasTest ? `
    <div class="hr"></div>
    <div class="h1" style="font-size:22px;">Сертификат</div>
    <div class="muted">Выдаётся, если лучший результат ≥ 70%.</div>
    <button class="btn primary" id="certBtn">Сгенерировать</button>
    <div id="certBox" style="margin-top:10px;"></div>
  ` : "";

  mount.innerHTML = `
    <div class="h1">${esc(c.title)}</div>
    <div class="muted">${esc(c.description)}</div>

    <div class="hr"></div>
    <div class="h1" style="font-size:22px;">Материал</div>
    <div id="content"></div>

    <div class="hr"></div>
    <div class="h1" style="font-size:22px;">Тест</div>
    <div id="testBox"></div>

    ${analyticsHtml}
    ${certHtml}
  `;

  renderCourseContent(mount.querySelector("#content"), c);
  renderTest({ t, courseId, mount });

  if (hasTest) {
    mount.querySelector("#certBtn").onclick = async () => {
      const box = mount.querySelector("#certBox");
      try {
        const cert = await api.certificate(courseId);
        box.innerHTML = `
          <div class="item">
            Student: <b>${esc(cert.student)}</b><br/>
            Course: <b>${esc(cert.course)}</b><br/>
            Score: <b>${cert.percent}%</b><br/>
            <span class="muted">${esc(cert.issued_at)}</span>
          </div>
        `;
      } catch (e) {
        box.innerHTML = "";
        showToast(`Сертификат: ${e.message}`);
      }
    };
  }
}



async function viewAdmin() {
  const u = await requireAuth();
  if (!u) return;

  if (u.role !== "admin") {
    app.innerHTML = `<section class="card"><div class="h1">Нет доступа</div></section>`;
    return;
  }

  const courses = await api.courses();
  const summary = await api.adminSummary();

  app.innerHTML = "";
  const node = h(`
    <div class="grid">
      <section class="card">
        <div class="h1">Курсы</div>
        <div class="hr"></div>
        <div class="item">Courses: <b>${summary.courses}</b> • Tests: <b>${summary.tests}</b> • Attempts: <b>${summary.attempts}</b></div>

        <div class="hr"></div>

        <div class="field">
          <label>Выбери курс для редактирования</label>
          <select id="coursePick"></select>
        </div>

        <div style="display:flex; gap:10px; flex-wrap:wrap;">
          <button class="btn ghost" id="newCourseBtn" type="button">Новый курс</button>
          <button class="btn primary" id="saveCourseBtn" type="button">Сохранить курс</button>
          <button class="btn ghost" id="deleteCourseBtn" type="button">Удалить курс</button>
        </div>

        <div class="hr"></div>

        <div class="field"><label>ID (пусто = создаст новый)</label><input id="courseId" placeholder="(оставь пустым для нового)"/></div>

        <div class="field">
          <label>Тип</label>
          <select id="courseType">
            <option value="video">video</option>
            <option value="text">text</option>
            <option value="interactive">interactive</option>
          </select>
        </div>

        <div class="field"><label>Название</label><input id="courseTitle" /></div>
        <div class="field"><label>Описание</label><input id="courseDesc" /></div>

        <div class="field" id="courseExtra"></div>

        <div class="hr"></div>
        <div class="h1" style="font-size:22px;">Копирование</div>

        <div class="field"><label>Скопировать тест: откуда</label><select id="fromTest"></select></div>
        <div class="field"><label>Скопировать тест: куда</label><select id="toTest"></select></div>
        <button class="btn ghost" id="cloneTestBtn" type="button">Скопировать тест</button>

        <div class="hr"></div>

        <div class="field"><label>Скопировать вопрос: курс-источник</label><select id="fromQ"></select></div>
        <div class="field"><label>Вопрос</label><select id="qPick"></select></div>
        <div class="field"><label>Скопировать вопрос: курс-получатель</label><select id="toQ"></select></div>
        <button class="btn ghost" id="cloneQBtn" type="button">Скопировать вопрос</button>
      </section>

      <section class="card">
        <div class="h1">Тесты</div>
        <div class="muted">Создай новый тест или обнови существующий.</div>
        <div class="hr"></div>

        <div class="field"><label>Курс</label><select id="testCoursePick"></select></div>

        <div style="display:flex; gap:10px; flex-wrap:wrap;">
          <button class="btn ghost" id="newTestBtn" type="button">Новый тест</button>
          <button class="btn primary" id="saveTestBtn" type="button">Сохранить тест</button>
        </div>

        <div class="hr"></div>

        <div class="field">
          <label>Тип теста</label>
          <select id="testType">
            <option value="multi">варианты</option>
            <option value="open">открытые ответы</option>
          </select>
        </div>

        <div class="field"><label>Название теста</label><input id="testTitle"/></div>
        <div class="field"><label>Лимит времени (мин, можно 0)</label><input id="timeMin" type="number" min="0" value="10"/></div>

        <div class="hr"></div>
        <div class="h1" style="font-size:22px;">Вопросы</div>
        <div id="qList" class="list"></div>
        <button class="btn ghost" id="addQ" type="button">Добавить вопрос</button>

        <div class="hr"></div>
        <textarea id="tjson" rows="10" spellcheck="false"></textarea>
      </section>
    </div>
  `);


  const coursePick = node.querySelector("#coursePick");
  const testCoursePick = node.querySelector("#testCoursePick");
  const fromTest = node.querySelector("#fromTest");
  const toTest = node.querySelector("#toTest");
  const fromQ = node.querySelector("#fromQ");
  const toQ = node.querySelector("#toQ");

  courses.forEach(c => {
    const opt = `<option value="${c.id}">${esc(c.title)}</option>`;
    coursePick.insertAdjacentHTML("beforeend", opt);
    testCoursePick.insertAdjacentHTML("beforeend", opt);
    fromTest.insertAdjacentHTML("beforeend", opt);
    toTest.insertAdjacentHTML("beforeend", opt);
    fromQ.insertAdjacentHTML("beforeend", opt);
    toQ.insertAdjacentHTML("beforeend", opt);
  });

  
  const courseId = node.querySelector("#courseId");
  const courseType = node.querySelector("#courseType");
  const courseTitle = node.querySelector("#courseTitle");
  const courseDesc = node.querySelector("#courseDesc");
  const courseExtra = node.querySelector("#courseExtra");

  function renderCourseExtra() {
    const t = courseType.value;
    if (t === "video") {
      courseExtra.innerHTML = `
        <label>Video URL (embed)</label>
        <input id="videoUrl" placeholder="https://www.youtube-nocookie.com/embed/..."/>
        <label style="margin-top:10px;">Конспект (HTML можно)</label>
        <textarea id="notes" rows="5"></textarea>
      `;
    } else if (t === "text") {
      courseExtra.innerHTML = `
        <label>Текст урока (HTML можно)</label>
        <textarea id="text" rows="6"></textarea>
      `;
    } else {
      courseExtra.innerHTML = `
        <label>Конспект (HTML можно)</label>
        <textarea id="notes" rows="4"></textarea>
        <label style="margin-top:10px;">Шаги (по одному в строке)</label>
        <textarea id="steps" rows="5"></textarea>
      `;
    }
  }

  courseType.onchange = renderCourseExtra;
  renderCourseExtra();

  async function loadCourse(cid) {
    const c = await api.course(cid);
    courseId.value = c.id;
    courseType.value = c.type;
    courseTitle.value = c.title;
    courseDesc.value = c.description;
    renderCourseExtra();

    if (c.type === "video") {
      node.querySelector("#videoUrl").value = c.video_url || "";
      node.querySelector("#notes").value = c.notes || "";
    } else if (c.type === "text") {
      node.querySelector("#text").value = c.text || "";
    } else {
      node.querySelector("#notes").value = c.notes || "";
      node.querySelector("#steps").value = (c.steps || []).join("\n");
    }
  }

  coursePick.onchange = () => loadCourse(coursePick.value);
  await loadCourse(coursePick.value);

  node.querySelector("#newCourseBtn").onclick = () => {
    courseId.value = "";
    courseType.value = "video";
    courseTitle.value = "";
    courseDesc.value = "";
    renderCourseExtra();
    showToast("Новый курс: заполни поля и нажми «Сохранить курс»");
  };

  node.querySelector("#saveCourseBtn").onclick = async () => {
    try {
      const id = courseId.value.trim() || null;
      const type = courseType.value;

      const payload = {
        type,
        title: courseTitle.value.trim(),
        description: courseDesc.value.trim(),
      };

      if (!payload.title || !payload.description) throw new Error("Нужно название и описание");

      if (type === "video") {
        payload.video_url = node.querySelector("#videoUrl").value.trim();
        payload.notes = node.querySelector("#notes").value;
      } else if (type === "text") {
        payload.text = node.querySelector("#text").value;
      } else {
        payload.notes = node.querySelector("#notes").value;
        payload.steps = node.querySelector("#steps").value.split("\n").map(s => s.trim()).filter(Boolean);
      }

      if (id) await api.adminUpdateCourse(id, payload);
      else await api.adminCreateCourse(payload);

      showToast("Курс сохранён");
      await viewAdmin();
    } catch (e) {
      showToast(`Ошибка: ${e.message}`);
    }
  };

  node.querySelector("#deleteCourseBtn").onclick = async () => {
    const id = courseId.value.trim();
    if (!id) return showToast("Сначала выбери курс (ID должен быть заполнен)");
    try {
      await api.adminDeleteCourse(id);
      showToast("Курс удалён");
      await viewAdmin();
    } catch (e) {
      showToast(`Ошибка: ${e.message}`);
    }
  };


  node.querySelector("#cloneTestBtn").onclick = async () => {
    try {
      await api.adminCloneTest(fromTest.value, toTest.value);
      showToast("Тест скопирован");
    } catch (e) {
      showToast(`Ошибка: ${e.message}`);
    }
  };

  const qPick = node.querySelector("#qPick");

  async function refreshQuestionPick() {
    qPick.innerHTML = "";
    try {
      const t = await api.adminGetTest(fromQ.value);
      if (!t || !t.questions || t.questions.length === 0) {
        qPick.innerHTML = `<option value="-1">Нет вопросов</option>`;
        return;
      }
      t.questions.forEach((q, i) => {
        qPick.insertAdjacentHTML("beforeend", `<option value="${i}">${i}: ${esc(q.prompt)}</option>`);
      });
    } catch {
      qPick.innerHTML = `<option value="-1">Ошибка чтения теста</option>`;
    }
  }

  fromQ.onchange = refreshQuestionPick;
  await refreshQuestionPick();

  node.querySelector("#cloneQBtn").onclick = async () => {
    const idx = Number(qPick.value);
    if (idx < 0) return showToast("Нет вопроса для копирования");
    try {
      await api.adminCloneQuestion(fromQ.value, idx, toQ.value);
      showToast("Вопрос скопирован");
    } catch (e) {
      showToast(`Ошибка: ${e.message}`);
    }
  };


  const testType = node.querySelector("#testType");
  const testTitle = node.querySelector("#testTitle");
  const timeMin = node.querySelector("#timeMin");
  const qList = node.querySelector("#qList");
  const tjson = node.querySelector("#tjson");

  let state = null;

  function blankState(type = "multi") {
    return {
      id: null,
      test_type: type,
      title: "",
      time_limit_sec: 10 * 60,
      questions: type === "multi"
        ? [{ prompt: "", options: ["A","B"], correct_indexes: [0], select_mode: "single", hint: "", explanation: "" }]
        : [{ prompt: "", keywords: ["ключ"], hint: "", explanation: "" }],
    };
  }

  function renderQuestions() {
    qList.innerHTML = "";
    state.questions.forEach((q, idx) => {
      const wrap = document.createElement("div");
      wrap.className = "item";

      if (state.test_type === "multi") {
        wrap.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center; gap:10px;">
            <b>Вопрос ${idx + 1}</b>
            <button class="btn ghost" data-del="${idx}" type="button">Удалить</button>
          </div>
          <div class="field"><label>Текст</label><input data-prompt="${idx}" value="${esc(q.prompt)}"/></div>
          <div class="field"><label>Варианты (строка=вариант)</label><textarea data-options="${idx}" rows="4">${(q.options||[]).map(esc).join("\n")}</textarea></div>
          <div class="field"><label>Правильные индексы (0 или 0,2)</label><input data-corr="${idx}" value="${(q.correct_indexes||[]).join(",")}"/></div>
          <div class="field"><label>Режим</label>
            <select data-mode="${idx}">
              <option value="single" ${q.select_mode==="single"?"selected":""}>single</option>
              <option value="multi" ${q.select_mode!=="single"?"selected":""}>multi</option>
            </select>
          </div>
          <div class="field"><label>Подсказка</label><input data-hint="${idx}" value="${esc(q.hint||"")}"/></div>
          <div class="field"><label>Объяснение</label><textarea data-expl="${idx}" rows="3">${esc(q.explanation||"")}</textarea></div>
        `;
      } else {
        wrap.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center; gap:10px;">
            <b>Вопрос ${idx + 1}</b>
            <button class="btn ghost" data-del="${idx}" type="button">Удалить</button>
          </div>
          <div class="field"><label>Текст</label><input data-prompt="${idx}" value="${esc(q.prompt)}"/></div>
          <div class="field"><label>Ключевые слова (через запятую)</label><input data-keys="${idx}" value="${(q.keywords||[]).map(esc).join(", ")}"/></div>
          <div class="field"><label>Подсказка</label><input data-hint="${idx}" value="${esc(q.hint||"")}"/></div>
          <div class="field"><label>Объяснение</label><textarea data-expl="${idx}" rows="3">${esc(q.explanation||"")}</textarea></div>
        `;
      }

      qList.appendChild(wrap);
    });

    tjson.value = JSON.stringify(state, null, 2);
  }

  function readFromUI() {
    state.test_type = testType.value;
    state.title = testTitle.value.trim();
    const m = Number(timeMin.value || 0);
    state.time_limit_sec = m > 0 ? Math.floor(m * 60) : null;

    state.questions = state.questions.map((q, idx) => {
      const prompt = node.querySelector(`[data-prompt="${idx}"]`)?.value ?? q.prompt;

      if (state.test_type === "multi") {
        const optionsText = node.querySelector(`[data-options="${idx}"]`)?.value ?? "";
        const options = optionsText.split("\n").map(s => s.trim()).filter(Boolean);

        const corrText = node.querySelector(`[data-corr="${idx}"]`)?.value ?? "";
        const correct_indexes = corrText.split(",").map(s => s.trim()).filter(Boolean).map(Number).filter(Number.isFinite);

        const select_mode = node.querySelector(`[data-mode="${idx}"]`)?.value ?? "multi";
        const hint = node.querySelector(`[data-hint="${idx}"]`)?.value ?? "";
        const explanation = node.querySelector(`[data-expl="${idx}"]`)?.value ?? "";

        return { prompt, options, correct_indexes, select_mode, hint, explanation };
      } else {
        const keysText = node.querySelector(`[data-keys="${idx}"]`)?.value ?? "";
        const keywords = keysText.split(",").map(s => s.trim()).filter(Boolean);
        const hint = node.querySelector(`[data-hint="${idx}"]`)?.value ?? "";
        const explanation = node.querySelector(`[data-expl="${idx}"]`)?.value ?? "";
        return { prompt, keywords, hint, explanation };
      }
    });

    tjson.value = JSON.stringify(state, null, 2);
  }

  async function loadTest(courseId) {
    const t = await api.adminGetTest(courseId);
    if (!t) {
      state = blankState("multi");
    } else {
      state = {
        id: t.id ?? null,
        test_type: t.test_type,
        title: t.title ?? "",
        time_limit_sec: t.time_limit_sec ?? null,
        questions: (t.questions ?? []).map(q => ({ ...q })),
      };
    }
    testType.value = state.test_type;
    testTitle.value = state.title;
    timeMin.value = state.time_limit_sec ? String(Math.ceil(state.time_limit_sec / 60)) : "0";
    renderQuestions();
  }

  node.querySelector("#newTestBtn").onclick = () => {
    state = blankState(testType.value);
    testTitle.value = "";
    timeMin.value = "10";
    renderQuestions();
    showToast("Новый тест: заполни и нажми «Сохранить тест»");
  };

  node.querySelector("#addQ").onclick = () => {
    readFromUI();
    if (state.test_type === "multi") {
      state.questions.push({ prompt:"", options:["A","B"], correct_indexes:[0], select_mode:"single", hint:"", explanation:"" });
    } else {
      state.questions.push({ prompt:"", keywords:["ключ"], hint:"", explanation:"" });
    }
    renderQuestions();
  };

  node.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-del]");
    if (!btn) return;
    readFromUI();
    const idx = Number(btn.dataset.del);
    state.questions.splice(idx, 1);
    renderQuestions();
  });

  node.querySelector("#saveTestBtn").onclick = async () => {
    try {
      readFromUI();
      if (!state.title) throw new Error("Нужно название теста");
      if (!state.questions.length) throw new Error("Добавь хотя бы 1 вопрос");

      const payload = {
        id: state.id ?? undefined,
        test_type: state.test_type,
        title: state.title,
        time_limit_sec: state.time_limit_sec,
        questions: state.questions,
      };

      const saved = await api.adminUpsertTest(testCoursePick.value, payload);
      state.id = saved.id;
      showToast("Тест сохранён");
      await viewAdmin();
    } catch (e) {
      showToast(`Ошибка: ${e.message}`);
    }
  };

  testCoursePick.onchange = () => loadTest(testCoursePick.value);
  state = blankState("multi");
  await loadTest(testCoursePick.value);

  app.appendChild(node);
}


async function router() {
  setTopbar();
  const hash = location.hash || "#/login";
  const route = hash.replace("#", "");

  if (route.startsWith("/login")) return viewLogin();
  if (route.startsWith("/courses")) return viewCourses();
  if (route.startsWith("/admin")) return viewAdmin();

  location.hash = "#/login";
}

window.addEventListener("hashchange", router);
router();