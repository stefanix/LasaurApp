$(document).ready(function(){

  // G-Code Canvas Preview
  var icanvas = new Canvas('#import_canvas');
  var gcodereader = new GcodeReader();
  icanvas.background('ffffff'); 
  // file upload form
  $('#svg_upload_button').button();
  $('#svg_upload_button').click(function(e){
    var input = $('#svg_upload_file').get(0)
    if (typeof window.FileReader !== 'function') {
      $().uxmessage('error', "This requires a modern browser with File API support.");
    } else if (!input.files) {
      $().uxmessage('error', "This browser does not support the files property.");
    } else if (!input.files[0]) {
      $().uxmessage('notice', "No file was selected.");      
    } else {
      $().uxmessage('notice', input.files[0]);
      var fr = new FileReader()
      fr.onload = gotSvgData
      fr.readAsText(input.files[0])
    }
    
    function gotSvgData(e) {
      $().uxmessage('notice', "gotSvgData called ...");
      var svgdata = e.target.result
      //alert(svgdata)
      
      //       $('#import_results').text(gcodedata);
      //       
      //       
      //      $().uxmessage('notice', "rendering SVG with cakejs ...");
      //       //$('#import_results').text(svgdata);
      //             
      //       var svgroot = $.parseXML(svgdata).documentElement
      // var boundarys = SVGReader.parse(svgroot, {
      //     width: 610,
      //     height: 310        
      // })
      // 
      // var gcode = GcodeWriter.write(boundarys)
      // 
      //       gcodereader.parse(gcode, 0.5);
      //       gcodereader.draw(icanvas);       
      // 
      // //alert(JSON.stringify(svgNode));
      // alert(svgNode.toSource())      
      
    }
    
  	e.preventDefault();		
  });


  $("#import_to_queue").button();  
  $("#import_to_queue").click(function(e) {
    var gcodedata = $('#import_results').text();
    var fullpath = $('#svg_upload_file').val();
    var filename = fullpath.split('\\').pop().split('/').pop();
    add_to_job_queue(gcodedata, filename);
	  $().uxmessage('notice', "file added to laser job queue");    
  	return false;
  });


});  // ready
