export function el(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}

export function renderCourseList(box, courses, onOpen) {
  box.innerHTML = "";
  courses.forEach(c => {
    const node = el(`
      <div class="item">
        <b>${c.title}</b>
        <div style="opacity:.75">${c.description}</div>
        <div style="margin-top:8px; display:flex; justify-content:space-between; align-items:center;">
          <span class="pill">${c.type}</span>
          <button class="btn">Открыть</button>
        </div>
      </div>
    `);
    node.querySelector("button").onclick = () => onOpen(c.id);
    box.appendChild(node);
  });
}

export function renderCourseView(box, course, test, analytics) {
  box.innerHTML = `
    <h2 style="margin:0">${course.title}</h2>
    <div style="opacity:.75">${course.description}</div>
    <div style="margin-top:8px">
      <span class="pill">course: ${course.type}</span>
      <span class="pill">test: ${test ? test.test_type : "нет"}</span>
    </div>
    <hr/>
    <div id="content"></div>
    <hr/>
    <div id="test"></div>
    <hr/>
    <h3>Аналитика</h3>
    <div class="item">Попыток: <b>${analytics?.attempts ?? 0}</b>, лучший: <b>${analytics?.best ?? "-"}</b></div>
    <hr/>
    <div id="cert"></div>
  `;
}

export function renderCourseContent(container, course) {
  if (course.type === "video") {
    container.innerHTML = `<div class="item"><a style="color:#c8d0ff" href="${course.video_url}" target="_blank">Открыть материал</a></div>`;
  } else if (course.type === "text") {
    container.innerHTML = `<div class="item">${course.text}</div>`;
  } else {
    container.innerHTML = `<div class="item">${(course.steps||[]).map(s=>`• ${s}`).join("<br/>")}</div>`;
  }
}

export function renderTest(container, test, onSubmit) {
  if (!test) { container.innerHTML = `<div style="opacity:.75">У этого курса нет теста.</div>`; return; }

  const qs = test.questions || [];
  container.innerHTML = `
    <h3>${test.title}</h3>
    <form id="f" class="list">
      ${qs.map((q, i) => {
        if (test.test_type === "multi") {
          return `
            <div class="item">
              <b>${i+1}. ${q.prompt}</b>
              ${(q.options||[]).map((opt, idx) => `
                <label style="display:flex;gap:10px;align-items:center;margin-top:6px">
                  <input type="checkbox" name="q_${i}" value="${idx}" style="width:auto">
                  <span>${opt}</span>
                </label>
              `).join("")}
            </div>
          `;
        }
        return `
          <div class="item">
            <b>${i+1}. ${q.prompt}</b>
            <input name="q_${i}" placeholder="Ваш ответ">
          </div>
        `;
      }).join("")}
      <button class="btn" type="submit">Отправить</button>
    </form>
    <div id="res" style="margin-top:10px;"></div>
  `;

  container.querySelector("#f").onsubmit = (e) => {
    e.preventDefault();

    let answers;
    if (test.test_type === "multi") {
      answers = qs.map((_, i) =>
        [...container.querySelectorAll(`input[name="q_${i}"]:checked`)].map(x => Number(x.value))
      );
    } else {
      answers = qs.map((_, i) => container.querySelector(`input[name="q_${i}"]`).value);
    }
    onSubmit(answers, container.querySelector("#res"));
  };
}

export function renderCert(container, cert) {
  container.innerHTML = `
    <div class="item">
      <b>Сертификат</b><br/>
      ${cert.student_name} — “${cert.course_title}” — <b>${cert.percent}%</b><br/>
      <small style="opacity:.75">${cert.issued_at}</small>
    </div>
  `;
}