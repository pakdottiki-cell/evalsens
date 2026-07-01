document.addEventListener("DOMContentLoaded", () => {
  const csrfTokenMeta = document.querySelector("meta[name='csrf-token']");
  const csrfToken = csrfTokenMeta ? csrfTokenMeta.getAttribute("content") : "";
  const loadingOverlay = document.getElementById("loadingOverlay");

  const showLoading = () => {
    if (loadingOverlay) loadingOverlay.classList.add("active");
  };

  const hideLoading = () => {
    if (loadingOverlay) loadingOverlay.classList.remove("active");
  };

  const roleButtons = document.querySelectorAll("[data-role-toggle]");
  const roleInput = document.getElementById("roleInput");

  roleButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      roleButtons.forEach((item) => item.classList.remove("active"));
      btn.classList.add("active");
      if (roleInput) roleInput.value = btn.dataset.role;
    });
  });

  const togglePassword = document.querySelector("[data-toggle='password']");
  if (togglePassword) {
    togglePassword.addEventListener("click", () => {
      const target = document.getElementById(togglePassword.dataset.target);
      const icon = togglePassword.querySelector("i");
      if (!target) return;

      if (target.type === "password") {
        target.type = "text";
        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");
      } else {
        target.type = "password";
        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");
      }
    });
  }

  document.querySelectorAll(".star-rating").forEach((group) => {
    const labels = group.querySelectorAll(".star-label");
    const radios = group.querySelectorAll("input[type='radio']");
    const caption = document.getElementById(group.dataset.captionTarget);

    const render = (value, hover = false) => {
      labels.forEach((label) => {
        const labelValue = parseInt(label.dataset.value, 10);
        label.classList.remove("active", "hover");
        if (value && labelValue <= value) {
          label.classList.add(hover ? "hover" : "active");
        }
      });

      if (caption) {
        if (value === 1) caption.textContent = "Poor";
        else if (value === 2) caption.textContent = "Fair";
        else if (value === 3) caption.textContent = "Satisfactory";
        else if (value === 4) caption.textContent = "Very Satisfactory";
        else if (value === 5) caption.textContent = "Outstanding";
        else caption.textContent = "Click a star to rate";
      }
    };

    let selected = 0;
    radios.forEach((radio) => {
      if (radio.checked) selected = parseInt(radio.value, 10);
    });
    render(selected);

    labels.forEach((label) => {
      label.addEventListener("mouseenter", () => render(parseInt(label.dataset.value, 10), true));
      label.addEventListener("mouseleave", () => render(selected));
      label.addEventListener("click", () => {
        const value = parseInt(label.dataset.value, 10);
        selected = value;
        const radio = group.querySelector(`input[value='${value}']`);
        if (radio) radio.checked = true;
        render(selected);
      });
    });
  });

  document.querySelectorAll("[data-comment-counter]").forEach((textarea) => {
    const counter = document.getElementById(textarea.dataset.commentCounter);
    const update = () => {
      if (counter) counter.textContent = `${textarea.value.length} characters`;
    };
    textarea.addEventListener("input", update);
    update();
  });

  document.querySelectorAll("form[data-confirm-submit='true']").forEach((form) => {
    form.addEventListener("submit", (event) => {
      const message = form.dataset.confirmMessage || "Are you sure?";
      if (!window.confirm(message)) {
        event.preventDefault();
      }
    });
  });

  document.querySelectorAll(".toast").forEach((toastEl) => {
    const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
    toast.show();
  });

  const fetchJson = async (url, options = {}) => {
    showLoading();
    try {
      const response = await fetch(url, options);
      return await response.json();
    } finally {
      hideLoading();
    }
  };

  const dashboardChart = document.getElementById("dashboardSentimentChart");
  if (dashboardChart) {
    fetchJson(dashboardChart.dataset.api)
      .then((data) => {
        new Chart(dashboardChart, {
          type: "doughnut",
          data: {
            labels: ["Positive", "Negative", "Neutral"],
            datasets: [{
              data: [data.positive_pct, data.negative_pct, data.neutral_pct],
              backgroundColor: ["#16A34A", "#DC2626", "#D97706"]
            }]
          },
          options: {
            plugins: { legend: { position: "bottom" } }
          }
        });
      })
      .catch(console.error);
  }

  const trendBarChart = document.getElementById("trendBarChart");
  if (trendBarChart) {
    fetchJson(trendBarChart.dataset.api)
      .then((data) => {
        const labels = data.trend_data.map((item) => item.label);
        const positive = data.trend_data.map((item) => item.positive_pct);
        const negative = data.trend_data.map((item) => item.negative_pct);

        new Chart(trendBarChart, {
          type: "bar",
          data: {
            labels,
            datasets: [
              { label: "Positive %", data: positive, backgroundColor: "#16A34A" },
              { label: "Negative %", data: negative, backgroundColor: "#DC2626" }
            ]
          },
          options: {
            responsive: true,
            scales: { y: { beginAtZero: true, max: 100 } }
          }
        });
      })
      .catch(console.error);
  }

  const facultyRatingsChart = document.getElementById("facultyRatingsBarChart");
  if (facultyRatingsChart) {
    fetchJson(facultyRatingsChart.dataset.api)
      .then((rows) => {
        new Chart(facultyRatingsChart, {
          type: "bar",
          data: {
            labels: rows.map((row) => row.faculty_name),
            datasets: [{
              label: "Average Rating",
              data: rows.map((row) => row.average_rating),
              backgroundColor: "#0D9488"
            }]
          },
          options: {
            indexAxis: "y",
            responsive: true,
            scales: {
              x: { beginAtZero: true, max: 5 }
            }
          }
        });
      })
      .catch(console.error);
  }

  document.querySelectorAll(".facultySentimentPie").forEach((canvas) => {
    new Chart(canvas, {
      type: "pie",
      data: {
        labels: ["Positive", "Negative", "Neutral"],
        datasets: [{
          data: [
            parseFloat(canvas.dataset.positive),
            parseFloat(canvas.dataset.negative),
            parseFloat(canvas.dataset.neutral)
          ],
          backgroundColor: ["#16A34A", "#DC2626", "#D97706"]
        }]
      },
      options: {
        plugins: {
          legend: { position: "bottom" }
        }
      }
    });
  });

  const refreshKeywordsBtn = document.getElementById("refreshKeywordsBtn");
  if (refreshKeywordsBtn) {
    refreshKeywordsBtn.addEventListener("click", async () => {
      const facultyId = refreshKeywordsBtn.dataset.facultyId;
      const semesterId = refreshKeywordsBtn.dataset.semesterId;

      refreshKeywordsBtn.disabled = true;
      refreshKeywordsBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i>Refreshing';

      try {
        const response = await fetch("/api/refresh-keywords", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
          },
          body: JSON.stringify({
            faculty_id: parseInt(facultyId, 10),
            semester_id: parseInt(semesterId, 10)
          })
        });

        if (response.ok) {
          window.location.reload();
        } else {
          alert("Failed to refresh keywords.");
        }
      } catch (error) {
        console.error(error);
        alert("Error while refreshing keywords.");
      } finally {
        refreshKeywordsBtn.disabled = false;
        refreshKeywordsBtn.innerHTML = '<i class="fa-solid fa-rotate me-1"></i>Refresh Keywords';
      }
    });
  }
});