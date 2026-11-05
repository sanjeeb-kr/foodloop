/**
 * main.js - Vanilla JavaScript for FoodLoop Frontend
 * Handles interactive controls, confirmation modals, flash dismissal,
 * and Chart.js initialization for analytics reports.
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Auto-dismiss flash alerts after 5 seconds
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach((alert) => {
    setTimeout(() => {
      alert.style.transition = "opacity 0.5s ease";
      alert.style.opacity = "0";
      setTimeout(() => alert.remove(), 500);
    }, 5000);
  });

  // 2. Generic Confirmation Handler for state-changing forms (claims, cancels, deletes)
  const confirmForms = document.querySelectorAll("form[data-confirm]");
  confirmForms.forEach((form) => {
    form.addEventListener("submit", (e) => {
      const message = form.getAttribute("data-confirm") || "Are you sure you want to proceed?";
      if (!confirm(message)) {
        e.preventDefault();
      }
    });
  });
});

/**
 * Chart rendering helper using Chart.js
 * Invoked by analytics.html using Jinja tojson data
 */
function initAnalyticsCharts(categoryData, statusData, monthlyTrends) {
  // Chart 1: Collected Servings by Category (Doughnut / Bar)
  const categoryCtx = document.getElementById("categoryChart");
  if (categoryCtx && categoryData && categoryData.length > 0) {
    const labels = categoryData.map((d) => {
      const formatted = d.category.replace(/_/g, " ");
      return formatted.charAt(0).toUpperCase() + formatted.slice(1);
    });
    const values = categoryData.map((d) => d.total_servings);

    new Chart(categoryCtx, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: [
            "#2d6a4f",
            "#52b788",
            "#74c69d",
            "#b7e4c7",
            "#1b4332"
          ],
          borderWidth: 2,
          borderColor: "#ffffff"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom" },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.label}: ${ctx.raw.toLocaleString()} servings rescued`
            }
          }
        }
      }
    });
  }

  // Chart 2: Donations by Status (Bar Chart)
  const statusCtx = document.getElementById("statusChart");
  if (statusCtx && statusData && statusData.length > 0) {
    const labels = statusData.map((d) => d.status.charAt(0).toUpperCase() + d.status.slice(1));
    const counts = statusData.map((d) => d.count);
    
    // Status color mapping
    const statusColorMap = {
      available: "#15803d",
      claimed: "#b45309",
      collected: "#1d4ed8",
      cancelled: "#b91c1c",
      expired: "#4b5563"
    };
    const bgColors = statusData.map((d) => statusColorMap[d.status] || "#6b7280");

    new Chart(statusCtx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{
          label: "Donation Listings",
          data: counts,
          backgroundColor: bgColors,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { precision: 0 }
          }
        }
      }
    });
  }

  // Chart 3: Monthly Collection Trends (Line Chart)
  const trendsCtx = document.getElementById("monthlyTrendsChart");
  if (trendsCtx && monthlyTrends && monthlyTrends.length > 0) {
    const months = monthlyTrends.map((d) => d.month);
    const servings = monthlyTrends.map((d) => d.total_servings);

    new Chart(trendsCtx, {
      type: "line",
      data: {
        labels: months,
        datasets: [{
          label: "Servings Collected",
          data: servings,
          borderColor: "#2d6a4f",
          backgroundColor: "rgba(45, 106, 79, 0.12)",
          fill: true,
          tension: 0.3,
          pointRadius: 5,
          pointBackgroundColor: "#1b4332"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "top" }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { precision: 0 }
          }
        }
      }
    });
  }
}
