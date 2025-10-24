// === Ambil elemen dari DOM ===
const addTaskBtns = document.querySelectorAll(".add-btn");
const popupOverlay = document.getElementById("popupOverlay");
const cancelBtn = document.getElementById("cancelBtn");
const saveBtn = document.getElementById("saveBtn");
const uploadArea = document.getElementById("fileUploadArea");
const taskFileInput = document.getElementById("taskFile");
const fileList = document.getElementById("fileList");
const dashboardContent = document.getElementById("dashboardContent");

const taskTitle = document.getElementById("taskTitle");
const taskDesc = document.getElementById("taskDesc");
const taskDeadline = document.getElementById("taskDeadline");

// Mode edit
let editMode = false;
let currentTaskItem = null;
let currentCourseCode = null; // ✅ ganti dari courseId ke courseCode

// Event: tombol +Add Task
addTaskBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    currentCourseCode = btn.dataset.courseCode; // ✅ ubah atribut data
    console.log("Course Code selected:", currentCourseCode); // Debug log
    openPopup();
  });
});

// Event: tombol cancel popup
cancelBtn.addEventListener("click", () => {
  popupOverlay.style.display = "none";
  resetForm();
});

// Event: klik area upload
uploadArea.addEventListener("click", () => taskFileInput.click());

// Event: pilih file
taskFileInput.addEventListener("change", (e) =>
  showSelectedFiles(e.target.files)
);

// Drag & drop
uploadArea.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadArea.style.background = "#e6effa";
});
uploadArea.addEventListener("dragleave", () => {
  uploadArea.style.background = "#f8fbff";
});
uploadArea.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadArea.style.background = "#f8fbff";
  taskFileInput.files = e.dataTransfer.files;
  showSelectedFiles(e.dataTransfer.files);
});

// Tampilkan nama file
function showSelectedFiles(files) {
  fileList.innerHTML = "";
  for (let i = 0; i < files.length; i++) {
    const li = document.createElement("li");
    li.textContent = "📁 " + files[i].name;
    fileList.appendChild(li);
  }
}

// Buka popup Add/Edit
function openPopup(task = null) {
  popupOverlay.style.display = "flex";
  if (task) {
    editMode = true;
    currentTaskItem = task;
    taskTitle.value = task.dataset.title;
    taskDesc.value = task.dataset.desc;
    taskDeadline.value = task.dataset.deadline;

    // Tampilkan file yang ada
    try {
      const files = JSON.parse(task.dataset.files || "[]");
      fileList.innerHTML = "";
      files.forEach((file) => {
        const li = document.createElement("li");
        li.textContent = "📁 " + file;
        fileList.appendChild(li);
      });
    } catch (e) {
      console.error("Error parsing files JSON:", e);
      fileList.innerHTML = "";
    }
  } else {
    editMode = false;
    currentTaskItem = null;
    resetForm();
  }
}

// Simpan task
saveBtn.addEventListener("click", async () => {
  const title = taskTitle.value.trim();
  const desc = taskDesc.value.trim();
  const deadline = taskDeadline.value;

  // Validasi input
  if (!title) {
    alert("Harap isi judul tugas!");
    return;
  }

  if (!deadline) {
    alert("Harap isi deadline tugas!");
    return;
  }

  if (!currentCourseCode) {
    alert(
      "Course Code tidak ditemukan! Silakan refresh halaman dan coba lagi."
    );
    return;
  }

  // Kumpulkan nama file
  const files = [];
  const fileItems = fileList.querySelectorAll("li");
  fileItems.forEach((item) => {
    files.push(item.textContent.replace("📁 ", ""));
  });
  const fileJson = JSON.stringify(files);

  // ✅ ubah field ke course_code
  const taskData = {
    course_code: currentCourseCode,
    title,
    description: desc,
    deadline,
    file: fileJson,
  };

  console.log("Sending task data:", taskData); // Debug log

  try {
    let response;
    if (editMode && currentTaskItem) {
      const taskId = currentTaskItem.dataset.taskId;
      console.log("Updating task with ID:", taskId);

      response = await fetch(`/api/task/${taskId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(taskData),
      });
    } else {
      console.log("Creating new task");

      response = await fetch("/api/task", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(taskData),
      });
    }

    const result = await response.json();
    console.log("Server response:", result);

    if (response.ok) {
      window.location.reload();
    } else {
      alert(result.error || "Terjadi kesalahan");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("Terjadi kesalahan saat menyimpan task: " + error.message);
  }
});

// Reset form popup
function resetForm() {
  taskTitle.value = "";
  taskDesc.value = "";
  taskDeadline.value = "";
  taskFileInput.value = "";
  fileList.innerHTML = "";
  uploadArea.style.background = "#f8fbff";
  editMode = false;
  currentTaskItem = null;
}

// Event delegation untuk tombol edit dan hapus
dashboardContent.addEventListener("click", async (e) => {
  if (e.target.classList.contains("edit-btn")) {
    e.stopPropagation();
    const taskItem = e.target.closest(".task-item");
    openPopup(taskItem);
  }

  if (e.target.classList.contains("delete-btn")) {
    e.stopPropagation();
    const taskItem = e.target.closest(".task-item");
    const taskId = taskItem.dataset.taskId;

    if (confirm("Apakah Anda yakin ingin menghapus task ini?")) {
      try {
        const response = await fetch(`/api/task/${taskId}`, {
          method: "DELETE",
          credentials: "include",
        });
        const result = await response.json();

        if (response.ok) {
          taskItem.remove();
        } else {
          alert(result.error || "Gagal menghapus task");
        }
      } catch (error) {
        console.error("Error:", error);
        alert("Terjadi kesalahan saat menghapus task");
      }
    }
  }
});
