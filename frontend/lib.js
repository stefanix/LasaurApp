

(function($){
  $.fn.uxmessage = function(kind, text, max_length) {
    if (max_length == undefined) {
        max_length = 100
    }

    if (max_length !== false && text.length > max_length) {
      text = text.slice(0,max_length) + '\n...'
    }

    text = text.replace(/\n/g,'<br>')

    if (kind == 'notice') {
      $('#log_content').prepend('<div class="log_item log_notice well" style="display:none">' + text + '</div>')
      $('#log_content').children('div').first().show('blind')
      if ($("#log_content").is(':hidden')) {
        $().toastmessage('showToast',
          {text: text, sticky: false, position: 'top-left', type: 'notice'}
        )
      }
    } else if (kind == 'success') {
      $('#log_content').prepend('<div class="log_item log_success well" style="display:none">' + text + '</div>')
      $('#log_content').children('div').first().show('blind')
      if ($("#log_content").is(':hidden')) {
        $().toastmessage('showToast',
          {text: text, sticky: false, position: 'top-left', type: 'success'}
        )
      }
    } else if (kind == 'warning') {
      $('#log_content').prepend('<div class="log_item log_warning well" style="display:none">' + text + '</div>')
      $('#log_content').children('div').first().show('blind')
      if ($("#log_content").is(':hidden')) {
        $().toastmessage('showToast',
          {text: text, sticky: false, position: 'top-left', type: 'warning'}
        )
      }
    } else if (kind == 'error') {
      $('#log_content').prepend('<div class="log_item log_error well" style="display:none">' + text + '</div>')
      $('#log_content').children('div').first().show('blind');
      if ($("#log_content").is(':hidden')) {
        $().toastmessage('showToast',
          {text: text, sticky: false, position: 'top-left', type: 'error'}
        )
      }
    }

    while ($('#log_content').children('div').length > 200) {
      $('#log_content').children('div').last().remove()
    }

  };
})(jQuery);



function get_request(args) {
  // args items: url, success, error, complete
  $.ajax({
    type: "GET",
    url: args.url,
    dataType: "json",
    username: "laser",
    password: "laser",
    statusCode: {
      400: function(s) {
        // alert(JSON.stringify(s))
        if ('responseText' in s) {
          r = s.responseText;
          var error_txt = r.slice(r.indexOf('<pre>')+5,r.lastIndexOf('</pre>'))
          $().uxmessage('error', error_txt)
        }
      },
      401: function() {
        $().uxmessage('error', "Wrong password/username.")
      }
    },
    success: function (data) {
      if ('success' in args) {
        args.success(data)
      }
    },
    error: function (data) {
      if ('error' in args) {
        args.error(data)
      }
    },
    complete: function (data) {
      if ('complete' in args) {
        args.complete(data)
      }
    }
  })
}



function post_request(args) {
  // args items: url, data, success, error, complete
  $.ajax({
    type: "POST",
    url: args.url,
    data: {'load_request':JSON.stringify(args.data)},
    dataType: "json",
    username: "laser",
    password: "laser",
    statusCode: {
      400: function(s) {
        // alert(JSON.stringify(s))
        if ('responseText' in s) {
          r = s.responseText;
          var error_txt = r.slice(r.indexOf('<pre>')+5,r.lastIndexOf('</pre>'))
          $().uxmessage('error', error_txt)
        }
      },
      401: function() {
        $().uxmessage('error', "Wrong password/username.")
      }
    },
    success: function (data) {
      if ('success' in args) {
        args.success(data)
      }
    },
    error: function (data) {
      $().uxmessage('error', args.url)
      if ('error' in args) {
        args.error(data)
      }
    },
    complete: function (data) {
      if ('complete' in args) {
        args.complete(data)
      }
    }
  })
}





// function send_job(job, success_msg, progress) {
//   if (true) {
//     if ('vector' in job || 'raster' in job) {
//       // $().uxmessage('notice', JSON.stringify(job), Infinity);
//       $.ajax({
//         type: "POST",
//         url: "/job",
//         data: {'job_data':JSON.stringify(job)},
//         // dataType: "json",
//         success: function (data) {
//           if (data == "__ok__") {
//             $().uxmessage('success', success_msg);
//             if (progress = true) {
//               // show progress bar, register live updates
//               if ($("#progressbar").children().first().width() == 0) {
//                 $("#progressbar").children().first().width('5%');
//                 $("#progressbar").show();
//                 app_progress_flag = true;
//                 setTimeout(update_progress, 2000);
//               }
//             }
//           } else {
//             $().uxmessage('error', "Backend error: " + data);
//           }
//         },
//         error: function (data) {
//           // alert(JSON.stringify(data))
//           $().uxmessage('error', "Timeout. LasaurApp server down?");
//           if ("responseText" in data) {
//             $().uxmessage('error', data.responseText, Infinity);
//           }
//         },
//         complete: function (data) {
//           // future use
//         }
//       });
//     } else {
//       $().uxmessage('error', "No job data.");
//     }
//   } else {
//     $().uxmessage('warning', "Not ready, request ignored.");
//   }
// }



function send_relative_move(x, y, z, seekrate, success_msg) {
  var job = {
    "vector":{
      "passes":[
        {
          "paths":[0],
          "relative":true,
          "seekrate":seekrate
        }
      ],
      "paths":[
        [
          [[x,y,z]]
        ]
      ],
      "noreturn": true
    }
  }
  send_job(job, success_msg, false);
}





function generate_download(filename, filedata) {
  $.ajax({
    type: "POST",
    url: "/stash_download",
    data: {'filedata': filedata},
    success: function (data) {
      window.open("/download/" + data + "/" + filename, '_blank');
    },
    error: function (data) {
      $().uxmessage('error', "Timeout. LasaurApp server down?");
    },
    complete: function (data) {
      // future use
    }
  });
}



function job_from_path(path, seekrate, feedrate, air_assist, success_msg) {
  // Args:
  //     path: [[[0,-10, 0],],]
  //         list of polylines, list of points, list of coordinates
  //     seekrate:
  //     feedrate:
  //     air_assist: one of "feed", "pass", "off"
  var job = {
    "vector":{
      "passes":[
        {
          "paths":[0],
          "seekrate":seekrate,
          "feedrate":feedrate,
          "air_assist": air_assist
        }
      ],
      "paths":[path]
    }
  }
  // json stringify while limiting numbers to 3 decimals
  var json_job = JSON.stringify(job,
    function(key, val) {
      return val.toFixed ? Number(val.toFixed(3)) : val
    })
  post_request({
    url:'/run',
    data: {'job':json_job},
    success: function (jobname) {
      $().uxmessage('notice', success_msg)
    }
  })
}
