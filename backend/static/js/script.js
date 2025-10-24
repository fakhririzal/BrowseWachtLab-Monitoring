// === Ambil elemen dari DOM ===
const addCourseBtn = document.getElementById("addCourseBtn");
const addCourseFloating = document.getElementById("addCourseFloating");
const addCourseModal = document.getElementById("addCourseModal");
const submitCourse = document.getElementById("submitCourse");
const courseList = document.getElementById("courseList");
const noCourse = document.getElementById("noCourse");
const coursesContainer = document.getElementById("coursesContainer");
const lecturerNameInput = document.getElementById("lecturerName");
const courseTitleInput = document.getElementById("courseTitle");
const copyIcon = document.getElementById("copyIcon");

let courses = [];
let currentGeneratedCode = "";

// === Modal Control ===
function showAddModal() {
  addCourseModal.classList.remove("hidden");
}

function closeModal() {
  addCourseModal.classList.add("hidden");
  lecturerNameInput.value = "";
  courseTitleInput.value = "";
  currentGeneratedCode = "";
}

addCourseBtn.addEventListener("click", showAddModal);
addCourseFloating.addEventListener("click", showAddModal);
addCourseModal.addEventListener("click", (e) => {
  if (e.target === addCourseModal) closeModal();
});

// === Copy Kode + Notifikasi di pojok kanan bawah ===
copyIcon.addEventListener("click", () => {
  if (!currentGeneratedCode) {
    alert("Kode course akan muncul otomatis setelah course berhasil dibuat.");
    return;
  }

  navigator.clipboard.writeText(currentGeneratedCode);
  copyIcon.style.transform = "scale(1.25)";
  setTimeout(() => (copyIcon.style.transform = "scale(1)"), 250);
  showCopyNotif();
});

function showCopyNotif() {
  const notif = document.createElement("div");
  notif.classList.add("copy-toast");
  notif.textContent = "✅ Course code has been copied!";
  document.body.appendChild(notif);
  setTimeout(() => notif.classList.add("show"), 10);
  setTimeout(() => {
    notif.classList.remove("show");
    setTimeout(() => notif.remove(), 400);
  }, 2500);
}

// === Submit Course ===
submitCourse.addEventListener("click", async () => {
  const lecturer = lecturerNameInput.value.trim();
  const title = courseTitleInput.value.trim();

  if (lecturer && title) {
    try {
      const response = await fetch("http://localhost:5000/dosen_dashboard", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          nama: lecturer, // field sesuai backend Flask
          course_name: title,
        }),
      });

      const result = await response.json();

      if (response.ok) {
        // Ambil kode course yang dikirim backend
        currentGeneratedCode = result.course_code || "";

        alert(
          (result.message || "Course berhasil ditambahkan!") +
            (currentGeneratedCode ? `\nKode: ${currentGeneratedCode}` : "")
        );

        await loadCoursesFromDB(); // reload data dari DB
        closeModal();
      } else {
        alert(result.error || "Gagal menambahkan course!");
      }
    } catch (error) {
      console.error("Error saat mengirim data:", error);
      alert("Terjadi kesalahan koneksi ke server Flask.");
    }
  } else {
    alert("Please fill all fields before submitting!");
  }
});

// === Render daftar course ===
function renderCourses() {
  if (courses.length > 0) {
    noCourse.classList.add("hidden");
    courseList.classList.remove("hidden");
    coursesContainer.innerHTML = "";

    courses.forEach((c) => {
      const card = document.createElement("div");
      card.classList.add("course-card");
      card.innerHTML = `
        <h3>${c.title}</h3>
        <p><strong>${c.lecturer}</strong></p>
        <p>Course Code: ${c.code}</p>
        <button class="delete-btn" data-code="${c.code}">Delete</button>
      `;
      coursesContainer.appendChild(card);
    });

    // Event delete per course
    document.querySelectorAll(".delete-btn").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const courseCode = e.target.getAttribute("data-code");
        if (confirm("Yakin ingin menghapus course ini?")) {
          await deleteCourse(courseCode);
        }
      });
    });
  } else {
    noCourse.classList.remove("hidden");
    courseList.classList.add("hidden");
  }
}

// === Hapus Course dari DB ===
async function deleteCourse(courseCode) {
  try {
    const res = await fetch(
      `http://localhost:5000/api/delete-course/${courseCode}`,
      {
        method: "DELETE",
        credentials: "include",
      }
    );

    const result = await res.json();

    if (res.ok) {
      alert(result.message);
      courses = courses.filter((c) => c.code !== courseCode);
      renderCourses();
    } else {
      alert(result.error || "Gagal menghapus course!");
    }
  } catch (error) {
    console.error("Gagal menghapus course:", error);
    alert("Terjadi kesalahan koneksi ke server Flask.");
  }
}

// === Ambil data course dari backend ===
async function loadCoursesFromDB() {
  try {
    const response = await fetch(
      "http://localhost:5000/dosen_dashboard?data=true",
      {
        method: "GET",
        credentials: "include",
      }
    );

    if (!response.ok) throw new Error("Gagal mengambil data dari server");

    const data = await response.json();

    if (!data || data.length === 0) {
      courses = [];
      renderCourses();
    } else {
      courses = data.map((item) => ({
        code: item.course_code, // ambil langsung dari DB
        title: item.course_name,
        lecturer: item.nama || item.name || "Tidak diketahui",
      }));
      renderCourses();
    }
  } catch (error) {
    console.error("Error loadCoursesFromDB:", error);
    alert("Gagal mengambil data dari server Flask.");
  }
}

// Jalankan saat halaman selesai dimuat
window.addEventListener("DOMContentLoaded", loadCoursesFromDB);
