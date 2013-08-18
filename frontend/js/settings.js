
var app_settings = {
  work_area_dimensions: [400,210],
  max_seek_speed: 8000,
  num_digits: 2, 
  max_num_queue_items: 24,
}


///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

// calculate preview height from work_area aspect ratio
// preview with is fixed to 610
app_settings.preview_dimensions = 
	[610, Math.floor(app_settings.work_area_dimensions[1]*
		             (610.0/app_settings.work_area_dimensions[0]))]

app_settings.to_physical_dimensions = 
	app_settings.work_area_dimensions[0]/app_settings.preview_dimensions[0];
	 
