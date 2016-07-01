
function queue_clear() {
  $('#queue_content').html("")
}

function queue_ready() {
  queue_update()
}

function queue_update() {
  get_request({
    url:'/listing',
    success: function (data) {
      console.log(data)
      $().uxmessage('success', "listing successful.");
    }
  });
}
