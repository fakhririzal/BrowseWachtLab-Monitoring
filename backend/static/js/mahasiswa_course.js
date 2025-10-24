document.addEventListener("DOMContentLoaded", () => {
  setInterval(refreshTasks, 5000); // auto-refresh tiap 5 detik
});

function refreshTasks() {
  const courseCards = document.querySelectorAll(".course-card");
  courseCards.forEach((card) => {
    const code = card.dataset.course;
    fetch(`/api/refresh-course/${code}`)
      .then((res) => res.json())
      .then((data) => {
        const container = card.querySelector(".task-list");
        container.innerHTML = ""; // kosongkan task list

        if (
          !data.modules ||
          data.modules.length === 0 ||
          data.modules[0].tasks.length === 0
        ) {
          container.innerHTML = `<p class="empty">Belum ada task dari dosen.</p>`;
          return;
        }

        data.modules[0].tasks.forEach((task) => {
          const el = document.createElement("div");
          el.classList.add("task-card");
          el.innerHTML = `
            <h3>${task.title}</h3>
            <p>${task.description || "Tidak ada deskripsi"}</p>
            <p><strong>Dibuka:</strong> ${task.open}</p>
            <p><strong>Deadline:</strong> ${task.due}</p>
          `;
          container.appendChild(el);
        });
      })
      .catch((err) => console.error("Error refresh:", err));
  });
}
