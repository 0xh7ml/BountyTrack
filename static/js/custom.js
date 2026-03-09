// Initialize the date range picker
// This code is used to initialize the date range picker
  $(function() {
    $('#daterange').daterangepicker({
      autoUpdateInput: false,
      locale: {
        cancelLabel: 'Clear'
      }
    });

    $('#daterange').on('apply.daterangepicker', function(ev, picker) {
      $(this).val(picker.startDate.format('YYYY-MM-DD') + ' - ' + picker.endDate.format('YYYY-MM-DD'));
    });

    $('#daterange').on('cancel.daterangepicker', function(ev, picker) {
      $(this).val('');
    });
  });


// Delete function
function getCsrfToken() {
  return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// ─── Summernote Auto-Init ─────────────────────────────────────────────────────
$(function() {
  $('.summernote-editor').summernote({
    height: 250,
    toolbar: [
      ['style', ['bold', 'italic', 'underline', 'strikethrough', 'clear']],
      ['para',  ['ul', 'ol', 'paragraph']],
      ['insert',['link', 'picture', 'codeview']],
      ['view',  ['fullscreen', 'help']]
    ],
    callbacks: {
      onImageUpload: function(files) {
        uploadSummernoteImage(files[0], $(this));
      }
    }
  });
});

// ─── Summernote Image Upload ──────────────────────────────────────────────────
function uploadSummernoteImage(file, $editor) {
  var csrfToken = getCsrfToken();
  var formData  = new FormData();
  formData.append('image', file);
  formData.append('csrfmiddlewaretoken', csrfToken);
  fetch('/upload/image/', { method: 'POST', body: formData })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (data.url) {
        $editor.summernote('insertImage', data.url);
      }
    })
    .catch(function(err) { console.error('Image upload error:', err); });
}

function handleAction(url) {
  const csrfToken = getCsrfToken();

  Swal.fire({
      title: 'Are you sure?',
      text: 'This action cannot be undone.',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#d33',
      cancelButtonColor: '#3085d6',
      confirmButtonText: 'Yes, delete it!',
  }).then((result) => {
      if (!result.isConfirmed) return;

      axios.post(url, {
              csrfmiddlewaretoken: csrfToken
          },
          {
              headers: {
                  'Content-Type': 'application/x-www-form-urlencoded'
              },
          })
          .then(response => {
              const message = response.data.message;
              const status  = response.data.status;

              if (status === 'success') {
                  Swal.fire({
                      icon: 'success',
                      title: 'Deleted!',
                      text: message,
                      confirmButtonText: 'OK'
                  }).then(() => {
                      location.reload();
                  });
              } else {
                  Swal.fire({
                      icon: 'error',
                      title: 'Error',
                      text: message,
                      confirmButtonText: 'OK'
                  });
              }
          })
          .catch(error => {
              console.error(error);
              Swal.fire({
                  icon: 'error',
                  title: 'Error',
                  text: 'An error occurred. Please try again later.',
                  confirmButtonText: 'OK'
              });
          });
  });
}

function resetForm() {
  window.location.href = '/reports/';
}


// ─── Follow / Unfollow Program ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  const followBtn = document.getElementById('followBtn');
  if (followBtn) {
    followBtn.addEventListener('click', function () {
      const url        = this.dataset.url;
      const csrfToken  = getCsrfToken();

      axios.post(url, { csrfmiddlewaretoken: csrfToken }, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      }).then(response => {
        const status     = response.data.status;
        const icon       = document.getElementById('followIcon');
        const text       = document.getElementById('followText');
        const btn        = document.getElementById('followBtn');

        if (status === 'followed') {
          text.textContent = 'Unfollow Program';
          icon.className   = 'fas fa-heart-broken mr-1';
          btn.classList.remove('btn-outline-primary');
          btn.classList.add('btn-outline-danger');
          btn.dataset.following = 'true';
        } else {
          text.textContent = 'Follow Program';
          icon.className   = 'fas fa-heart mr-1';
          btn.classList.remove('btn-outline-danger');
          btn.classList.add('btn-outline-primary');
          btn.dataset.following = 'false';
        }
      }).catch(err => {
        console.error(err);
      });
    });
  }
});


// ─── Comment Edit (inline) ───────────────────────────────────────────────────
function editComment(commentId, btn) {
  const bodyDiv  = document.getElementById('comment-body-' + commentId);
  const original = bodyDiv.innerHTML;

  // Build inline editor
  const editArea = document.createElement('textarea');
  editArea.className = 'form-control mb-2';
  editArea.rows = 4;
  editArea.value = bodyDiv.innerText.trim();

  const saveBtn   = document.createElement('button');
  saveBtn.className = 'btn btn-primary btn-sm mr-1';
  saveBtn.textContent = 'Save';

  const cancelBtn = document.createElement('button');
  cancelBtn.className = 'btn btn-secondary btn-sm';
  cancelBtn.textContent = 'Cancel';

  bodyDiv.innerHTML = '';
  bodyDiv.appendChild(editArea);
  bodyDiv.appendChild(saveBtn);
  bodyDiv.appendChild(cancelBtn);

  cancelBtn.addEventListener('click', function () {
    bodyDiv.innerHTML = original;
  });

  saveBtn.addEventListener('click', function () {
    const newBody    = editArea.value.trim();
    const csrfToken  = getCsrfToken();
    const formData   = new FormData();
    formData.append('body', newBody);
    formData.append('csrfmiddlewaretoken', csrfToken);

    fetch('/comments/edit/' + commentId + '/', {
      method: 'POST',
      body: formData
    }).then(r => r.json()).then(data => {
      if (data.status === 'updated') {
        bodyDiv.innerHTML = '<p>' + data.body + '</p>';
      } else {
        bodyDiv.innerHTML = original;
      }
    }).catch(() => {
      bodyDiv.innerHTML = original;
    });
  });
}


// ─── Comment Delete ──────────────────────────────────────────────────────────
function deleteComment(commentId, url) {
  Swal.fire({
    title: 'Delete this comment?',
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#d33',
    confirmButtonText: 'Delete',
  }).then(result => {
    if (!result.isConfirmed) return;
    const csrfToken = getCsrfToken();
    const formData  = new FormData();
    formData.append('csrfmiddlewaretoken', csrfToken);

    fetch(url, { method: 'POST', body: formData })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'deleted') {
          const el = document.getElementById('comment-' + commentId);
          if (el) el.remove();
        }
      }).catch(console.error);
  });
}
