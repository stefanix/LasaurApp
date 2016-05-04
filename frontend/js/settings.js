
var app_settings = {
  work_area_dimensions: [1220,610],
  max_seek_speed: 8000,
  default_feedrate: 1500,
  default_intensity: 30,
  num_digits: 2, 
  max_num_queue_items: 24,
  max_segment_length: 5.0,
  table_offset: [5,5],  // has to match firmware
  air_assist_enabled: false,
  custom_buttons: [{
    icon: 'fire',
    title: 'Kompressor',
    toggle: true,
    default_on: false,
    gcode_enable: 'M82',
    gcode_disable: 'M83',
    enable_message: 'Kompressor an',
    disable_message: 'Kompressor aus'
  }]
};


///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

// calculate preview height from work_area aspect ratio
// preview with is fixed to 610
app_settings.canvas_dimensions = 
    [665, Math.floor(app_settings.work_area_dimensions[1]*
                     (665.0/app_settings.work_area_dimensions[0]))]

app_settings.to_physical_scale = 
    app_settings.work_area_dimensions[0]/app_settings.canvas_dimensions[0];

app_settings.to_canvas_scale = 1.0/app_settings.to_physical_scale;
     
