import * as api from "./api.js";
import { renderCourseList, renderCourseView, renderCourseContent, renderTest, renderCert } from "./ui.js";

let session = null;
let courses = [];
let currentCourseId = null;

const who = document.querySelector("#who");
const coursesBox = document.querySelector("#courses");
const view = document.querySelector("#view");

function setWho() {
  who.textContent = session ? `${session.name} (${session.role})` : "не вошли";
}

async function loadCourses() {
  courses = await api.getCourses();
  renderCourseList(coursesBox, courses, openCourse);
}

async function openCourse(courseId) {
  currentCourseId = courseId;
  const course = await api.getCourse(courseId);
  const test = session ? await api.getTest(courseId) : null;
  const analytics = session ? await api.getAnalytics(session.id, courseId) : null;

  renderCourseView(view, course, test, analytics);
  renderCourseContent(view.querySelector("#content"), course);

  renderTest(view.querySelector("#test"), test, async (answers, resBox) => {
    if (!session) return;
    const r = await api.submitAttempt(session.id, courseId, answers);
    resBox.innerHTML = `<div class="item">Результат: <b>${r.percent}%</b> (${r.points}/${r.max_points})</div>`;
  });

  const certBox = view.querySelector("#cert");
  certBox.innerHTML = session ? `<button class="btn" id="certBtn">Сгенерировать сертификат</button>` : "";
  const btn = view.querySelector("#certBtn");
  if (btn) {
    btn.onclick = async () => {
      try {
        const cert = await api.createCertificate(session.id, courseId);
        renderCert(certBox, cert);
      } catch (e) {
        certBox.innerHTML = `<div class="item">Не удалось создать сертификат</div>`;
      }
    };
  }
}

document.querySelector("#login").onclick = async () => {
  const name = document.querySelector("#name").value.trim();
  const role = document.querySelector("#role").value;
  if (!name) return alert("Введите имя");
  session = await api.login(name, role);
  setWho();
  if (currentCourseId) openCourse(currentCourseId);
};

setWho();
await loadCourses();