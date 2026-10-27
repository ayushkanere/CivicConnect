/**
 * CivicConnect Main JavaScript
 * Handles navigation, interactive components, client-side validation, and copy utilities.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Menu Toggle
  const navToggle = document.getElementById('nav-toggle');
  const navMenu = document.getElementById('nav-menu');
  if (navToggle && navMenu) {
    navToggle.addEventListener('click', () => {
      const isExpanded = navToggle.getAttribute('aria-expanded') === 'true';
      navToggle.setAttribute('aria-expanded', !isExpanded);
      navMenu.classList.toggle('is-open');
    });
  }

  // 2. Copy Report ID Utility
  const copyButtons = document.querySelectorAll('.btn-copy-id');
  copyButtons.forEach(btn => {
    btn.addEventListener('click', async () => {
      const targetId = btn.getAttribute('data-id');
      if (!targetId) return;

      try {
        await navigator.clipboard.writeText(targetId);
        const originalText = btn.innerHTML;
        btn.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
          Copied!
        `;
        btn.classList.add('btn-accent');

        setTimeout(() => {
          btn.innerHTML = originalText;
          btn.classList.remove('btn-accent');
        }, 2200);
      } catch (err) {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = targetId;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        btn.textContent = 'Copied!';
      }
    });
  });

  // 3. Form Validation, Live Character Counter & Submit Guard
  const reportForm = document.getElementById('report-form');
  const descInput = document.getElementById('description');
  const descCounter = document.getElementById('desc-counter');
  const areaInput = document.getElementById('area');
  const photoInput = document.getElementById('photo');

  if (descInput && descCounter) {
    const updateCount = () => {
      const currentLen = descInput.value.length;
      descCounter.textContent = `${currentLen} / 500 characters`;
      if (currentLen > 500 || currentLen < 10) {
        descCounter.style.color = 'var(--color-danger)';
      } else {
        descCounter.style.color = 'var(--text-subtle)';
      }
    };
    descInput.addEventListener('input', updateCount);
    updateCount();
  }

  // Photo size pre-validation
  if (photoInput) {
    photoInput.addEventListener('change', () => {
      const file = photoInput.files[0];
      if (file) {
        // 2 MB limit = 2097152 bytes
        if (file.size > 2 * 1024 * 1024) {
          alert('Selected image exceeds the 2 MB limit. Please select a smaller photo.');
          photoInput.value = '';
          return;
        }
        const ext = file.name.split('.').pop().toLowerCase();
        if (!['jpg', 'jpeg', 'png', 'webp'].includes(ext)) {
          alert('Invalid file format. Please upload a JPG, PNG, or WEBP image.');
          photoInput.value = '';
        }
      }
    });
  }

  // Client-side report submission validation & double submit guard
  if (reportForm) {
    reportForm.addEventListener('submit', (e) => {
      const descVal = descInput ? descInput.value.trim() : '';
      const areaVal = areaInput ? areaInput.value.trim() : '';

      // Check character limits
      if (descVal.length < 10 || descVal.length > 500) {
        alert('Description must be between 10 and 500 characters.');
        e.preventDefault();
        return;
      }
      if (areaVal.length < 3 || areaVal.length > 80) {
        alert('Area / locality must be between 3 and 80 characters.');
        e.preventDefault();
        return;
      }

      // Check for phone number patterns (privacy safeguard)
      const phoneRegex = /(?:(?:\+|00)\d{1,3}[-.\s]*)?(?:\(?\d{2,5}\)?[-.\s]*)?\d{3,4}[-.\s]*\d{3,4}/;
      if (phoneRegex.test(descVal) || phoneRegex.test(areaVal)) {
        const confirmPersonal = confirm(
          "Notice: A phone number pattern was detected. For your privacy, we recommend removing direct phone numbers or personal contact info. Proceed anyway?"
        );
        if (!confirmPersonal) {
          e.preventDefault();
          return;
        }
      }

      const submitBtn = reportForm.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `
          <svg class="spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="animation: spin 1s linear infinite; margin-right: 8px;">
            <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
            <path d="M12 2a10 10 0 0 1 10 10"></path>
          </svg>
          Submitting Report...
        `;
      }
    });
  }

  // 4. Verification Note Requirement for "Resolved" status in Admin
  const statusSelect = document.querySelector('select[name="status-status"]');
  const noteTextarea = document.querySelector('textarea[name="status-note"]');
  const statusForm = document.getElementById('status-update-form');

  if (statusForm && statusSelect && noteTextarea) {
    statusForm.addEventListener('submit', (e) => {
      if (statusSelect.value === 'Resolved' && !noteTextarea.value.trim()) {
        e.preventDefault();
        alert('Mandatory Verification Note Required: You must specify a verification note explaining how the report was inspected or resolved.');
        noteTextarea.focus();
      }
    });
  }
});
