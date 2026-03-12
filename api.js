const API = "http://127.0.0.1:8000/api";

function authHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function req(path, options = {}) {
  const r = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
      ...authHeaders(),
    },
  });

  if (!r.ok) {
    let msg = `${r.status} ${r.statusText}`;
    try {
      const data = await r.json();
      msg = data.detail || msg;
    } catch {}
    throw new Error(msg);
  }
  return r.json();
}

export const api = {
  register: (username, password) =>
    req("/register", { method: "POST", body: JSON.stringify({ username, password }) }),
  login: (username, password) =>
    req("/login", { method: "POST", body: JSON.stringify({ username, password }) }),
  me: () => req("/me"),

  courses: () => req("/courses"),
  course: (id) => req(`/courses/${id}`),
  test: (courseId) => req(`/courses/${courseId}/test`),

  hint: (courseId, qIndex) => req(`/courses/${courseId}/test/hint/${qIndex}`),
  submitAttempt: (courseId, answers) =>
    req("/attempts", { method: "POST", body: JSON.stringify({ course_id: courseId, answers }) }),
  analytics: (courseId) => req(`/analytics?course_id=${encodeURIComponent(courseId)}`),

  certificate: (courseId) =>
    req(`/certificates?course_id=${encodeURIComponent(courseId)}`, { method: "POST" }),

  // admin: summary
  adminSummary: () => req("/admin/summary"),

  // admin: courses
  adminCreateCourse: (payload) =>
    req("/admin/courses", { method: "POST", body: JSON.stringify(payload) }),
  adminUpdateCourse: (id, payload) =>
    req(`/admin/courses/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  adminDeleteCourse: (id) =>
    req(`/admin/courses/${id}`, { method: "DELETE" }),

  // admin: tests
  adminGetTest: (courseId) => req(`/admin/tests/${courseId}`),
  adminUpsertTest: (courseId, payload) =>
    req(`/admin/tests/${courseId}`, { method: "PUT", body: JSON.stringify(payload) }),

  // Prototype actions
  adminCloneTest: (fromId, toId) =>
    req("/admin/clone-test", {
      method: "POST",
      body: JSON.stringify({ from_course_id: fromId, to_course_id: toId }),
    }),

  adminCloneQuestion: (fromId, questionIndex, toId) =>
    req("/admin/clone-question", {
      method: "POST",
      body: JSON.stringify({
        from_course_id: fromId,
        question_index: questionIndex,
        to_course_id: toId,
      }),
    }),
};