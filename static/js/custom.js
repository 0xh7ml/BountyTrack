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

function handleAction(url) {
  const csrfToken = getCsrfToken();

  axios.post(url, {
          csrfmiddlewaretoken: csrfToken
      },
      {
          headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
          },
      })
      .then(response => {
          // Handle successful response
          const message = response.data.message;
          const status = response.data.status;

          // Use SweetAlert to display the message
          if (status === 'success') {
              Swal.fire({
                  icon: 'success',
                  title: 'Success',
                  text: message,
                  confirmButtonText: 'OK'
              }).then(() => {
                  location.reload(); // Reload the page to reflect changes
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
          // Handle error
          console.error(error);
          Swal.fire({
              icon: 'error',
              title: 'Error',
              text: 'An error occurred. Please try again later.',
              confirmButtonText: 'OK'
          });
      });
}
function resetForm() {
  window.location.href = '/reports/';
}