
function queue_clear() {
  $('#queue_content').html("")
}

function queue_ready() {
  queue_update()
}

function queue_update() {
  request_get({
    url:'/listing',
    success: function (data) {
      var html = '<table class="table table-hover table-condensed">'
      html += '<thead><tr><td>Name</td></tr></thead><tbody>'
      data.reverse()
      for (var i = 0; i < data.length; i++) {
        html += '<tr style="cursor:pointer"><td>'+data[i]+'</td></tr>'
      }
      html += '</tbody></table>'
      $('#queue_content').html(html)
      // load action
      $('#queue_content table tbody tr').click(function(e){
        var jobname = $(this).children('td').text()
        import_open(jobname)
        $('#queue_modal').modal('toggle')
        return false
      })
    }
  })
}
