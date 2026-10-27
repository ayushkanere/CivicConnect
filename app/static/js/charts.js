/**
 * CivicConnect Charts using Chart.js
 * Visualizes status distribution and category breakdown computed live from database records.
 */

function initCivicDashboard(statusCounts, categoryCounts) {
  // 1. Status Distribution (Doughnut Chart)
  const statusCtx = document.getElementById('statusChart');
  if (statusCtx && typeof Chart !== 'undefined') {
    const statusLabels = Object.keys(statusCounts);
    const statusData = Object.values(statusCounts);

    const statusColors = {
      'Submitted': '#64748B',     // Slate
      'Under Review': '#F59E0B',  // Amber
      'In Progress': '#6366F1',   // Indigo
      'Resolved': '#10B981'       // Green
    };

    const backgroundColors = statusLabels.map(s => statusColors[s] || '#94A3B8');

    new Chart(statusCtx, {
      type: 'doughnut',
      data: {
        labels: statusLabels,
        datasets: [{
          data: statusData,
          backgroundColor: backgroundColors,
          borderWidth: 2,
          borderColor: '#FFFFFF',
          hoverOffset: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              boxWidth: 14,
              font: {
                family: 'Inter',
                size: 13,
                weight: '500'
              },
              padding: 16
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const val = context.parsed;
                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                return ` ${context.label}: ${val} report(s) (${pct}%)`;
              }
            }
          }
        },
        cutout: '65%'
      }
    });
  }

  // 2. Category Breakdown (Horizontal/Vertical Bar Chart)
  const categoryCtx = document.getElementById('categoryChart');
  if (categoryCtx && typeof Chart !== 'undefined') {
    const categoryLabels = Object.keys(categoryCounts);
    const categoryData = Object.values(categoryCounts);

    new Chart(categoryCtx, {
      type: 'bar',
      data: {
        labels: categoryLabels,
        datasets: [{
          label: 'Total Reports',
          data: categoryData,
          backgroundColor: '#0F766E',
          hoverBackgroundColor: '#115E59',
          borderRadius: 6,
          maxBarThickness: 36
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              precision: 0,
              font: { family: 'Inter', size: 12 }
            },
            grid: { color: '#E2E8F0' }
          },
          x: {
            ticks: {
              font: { family: 'Inter', size: 11 },
              maxRotation: 45,
              minRotation: 20
            },
            grid: { display: false }
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function(context) {
                return ` Reports: ${context.parsed.y}`;
              }
            }
          }
        }
      }
    });
  }
}
