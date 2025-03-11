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

  axios.post(url,{
      csrfmiddlewaretoken: csrfToken
  },
  {
      headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
      },

  })
  .then(response => {
      // Handle successful response
      location.reload(); // Reload the page to reflect changes
  })
  .catch(error => {
      // Handle error
      console.error(error);
  });
}

function resetForm() {
  window.location.href = '/reports/';
}