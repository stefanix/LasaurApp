
function library_clear() {
  $('#library_content').html("")
}

function library_ready() {
  library_update()
}

function library_update() {
  request_get({
    url:'/listing_library',
    success: function (data) {
      var html = '<table class="table table-hover table-condensed">'
      html += '<thead><tr><td>Name</td></tr></thead><tbody>'
      data.reverse()
      for (var i = 0; i < data.length; i++) {
        html += '<tr style="cursor:pointer"><td>'+data[i]+'</td></tr>'
      }
      html += '</tbody></table>'
      $('#library_content').html(html)
      // load action
      $('#library_content table tbody tr').click(function(e){
        var jobname = $(this).children('td').text()
        import_open(jobname, true)
        $('#library_modal').modal('toggle')
        return false
      })
    }
  })
}
