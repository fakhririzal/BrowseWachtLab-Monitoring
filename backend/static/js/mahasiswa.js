// === Ambil elemen dari DOM ===
const addCourseBtn = document.getElementById("addCourseBtn");
const addCourseFloating = document.getElementById("addCourseFloating");
const addCourseModal = document.getElementById("addCourseModal");
const submitCourse = document.getElementById("submitCourse");
const courseList = document.getElementById("courseList");
const noCourse = document.getElementById("noCourse");
const courseCodeInput = document.getElementById("courseCode");
const coursesContainer = document.getElementById("coursesContainer");

let courses = [];
let joinedCourses = [];

// === Modal Control ===
function showAddModal() {
  addCourseModal.classList.remove("hidden");
}

function closeModal() {
  addCourseModal.classList.add("hidden");
  courseCodeInput.value = "";
}

addCourseBtn.addEventListener("click", showAddModal);
addCourseFloating.addEventListener("click", showAddModal);
addCourseModal.addEventListener("click", (e) => {
  if (e.target === addCourseModal) closeModal();
});

// === Load awal saat halaman dimuat ===
document.addEventListener("DOMContentLoaded", () => {
  loadCourses();
  loadJoinedCourses(); // pastikan data join diambil dari DB
});

// === Ambil semua course dari server ===
function loadCourses() {
  fetch("/api/mahasiswa")
    .then((response) => response.json())
    .then((data) => {
      courses = data;
      renderCourses();
    })
    .catch((error) => console.error("Gagal memuat data courses:", error));
}

// === Ambil daftar course yang sudah diikuti mahasiswa ===
function loadJoinedCourses() {
  fetch("/api/joined-courses/1") // mahasiswa_id sementara = 1
    .then((res) => res.json())
    .then((data) => {
      joinedCourses = data;
      renderJoinedCourses();
    })
    .catch((err) => console.error("Gagal memuat joined courses:", err));
}

// === Mahasiswa join course berdasarkan course_code ===
submitCourse.addEventListener("click", () => {
  const code = courseCodeInput.value.trim().toUpperCase(); // kode huruf besar semua

  if (!code) {
    alert("Masukkan kode course terlebih dahulu!");
    return;
  }

  // Cari course dengan kode yang sesuai
  const course = courses.find((c) => c.course_code === code);

  if (course) {
    fetch("/api/join-course", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mahasiswa_id: 1, // sementara ID mahasiswa = 1
        course_code: course.course_code, // ✅ gunakan course_code
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.error) {
          alert(data.error);
        } else {
          alert(data.message || "Berhasil bergabung dengan course!");
          joinedCourses.push(course);
          renderJoinedCourses();
          closeModal();
        }
      })
      .catch((err) => console.error("Gagal join course:", err));
  } else {
    alert("Kode course tidak ditemukan!");
  }
});

// === Render daftar course yang sudah di-join ===
function renderJoinedCourses() {
  if (joinedCourses.length > 0) {
    noCourse.classList.add("hidden");
    courseList.classList.remove("hidden");

    coursesContainer.innerHTML = "";

    joinedCourses.forEach((c) => {
      const card = document.createElement("div");
      card.classList.add("course-card");
      card.innerHTML = `
        <h3>${c.course_name}</h3>
        <p><strong>Dosen:</strong> ${c.nama}</p>
        <p><strong>Course Code:</strong> ${c.course_code}</p> <!-- ✅ ubah jadi course_code -->
      `;
      coursesContainer.appendChild(card);
    });
  } else {
    noCourse.classList.remove("hidden");
    courseList.classList.add("hidden");
  }
}

// === Render awal jika belum ada data ===
function renderCourses() {
  if (courses.length === 0) {
    noCourse.classList.remove("hidden");
    courseList.classList.add("hidden");
  }
}
