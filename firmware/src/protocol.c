




#define REF_RELATIVE 0
#define REF_ABSOLUTE 1

#define OFFSET_TABLE 0
#define OFFSET_CUSTOM 1


#define CMD_NONE
#define CMD_SEEK
#define CMD_FEED
#define CMD_DWELL
#define CMD_RASTER
#define CMD_HOMING

#define CMD_REF_RELATIVE
#define CMD_REF_ABSOLUTE

#define CMD_SET_OFFSET_TABLE
#define CMD_SET_OFFSET_CUSTOM
#define CMD_DEF_OFFSET_TABLE
#define CMD_DEF_OFFSET_CUSTOM
#define CMD_SEL_OFFSET_TABLE
#define CMD_SEL_OFFSET_CUSTOM

#define CMD_AIR_ENABLE
#define CMD_AIR_DISABLE
#define CMD_AUX1_ENABLE
#define CMD_AUX1_DISABLE
#define CMD_AUX2_ENABLE
#define CMD_AUX_DISABLE

#define CMD_GET_STATUS


#define PARAM_TARGET_X
#define PARAM_TARGET_Y
#define PARAM_TARGET_Z
#define PARAM_FEEDRATE
#define PARAM_INTENSITY
#define PARAM_DURATION
#define PARAM_PIXEL_WIDTH


#define PARAM_MAX_DATA_LENGTH 4


typedef struct {
  uint8_t status_code;             // return codes
  uint8_t ref_mode;                // {REF_RELATIVE, REF_ABSOLUTE}
  double feedrate;                 // mm/min {F}
  double position[3];              // projected position once all scheduled motions will have been executed
  double target[3];                // X,Y,Z params accumulated
  double offsets[6];               // coord system offsets [table_X,table_Y,table_Z, custom_X,custom_Y,custom_Z]
  uint8_t offselect;               // {OFFSET_TABLE, OFFSET_CUSTOM}
  uint8_t intensity;               // 0-255 percentage
  double duration;                 // pierce duration
  double pixel_width;              // raster pixel width in mm
} state_t;
static state_t st;

typedef struct {
  uint8_t chars[PARAM_MAX_DATA_LENGTH];
  uint8_t count;
} data_t;
static data_t pdata;

uint8_t cmd_current;
uint8_t param_current;

uint8_t line_checksum_ok_already;
static volatile bool position_update_requested;  // make sure to update to stepper position on next occasion



void protocol_init() {
  memset(&st, 0, sizeof(st));
  st.feedrate = CONFIG_FEEDRATE;
  st.ref_mode = REF_ABSOLUTE;
  st.intensity = 0;   
  st.offselect = OFFSET_TABLE;
  // table offset
  st.offsets[X_AXIS] = CONFIG_X_ORIGIN_OFFSET;
  st.offsets[Y_AXIS] = CONFIG_Y_ORIGIN_OFFSET;
  st.offsets[Z_AXIS] = CONFIG_Z_ORIGIN_OFFSET;
  // custom offset
  st.offsets[3+X_AXIS] = CONFIG_X_ORIGIN_OFFSET;
  st.offsets[3+Y_AXIS] = CONFIG_Y_ORIGIN_OFFSET;
  st.offsets[3+Z_AXIS] = CONFIG_Z_ORIGIN_OFFSET;
  position_update_requested = false;
  line_checksum_ok_already = false; 
}


void protocol_loop() {
  uint8_t chr;
  while(true) {
    chr = serial_read()
    if(chr < 128) {  /////////////////////////////// marker
      if(pdata.count > 0) {
        on_param();
        pdata.count = 0;
      }
      if(chr > 64 && chr < 91) {  ///////// command
        // chr is in [A-Z]
        on_cmd();
        memcpy(st.position, st.target, sizeof(st.target));  //position = target
        cmd_current = chr;
      } else if(chr > 96 && chr < 123) {  //parameter
        // chr is in [a-z]
        param_current = chr;
      } else {
        st.status_code = STATUS_UNSUPPORTED_MARKER
      }
    } else {  //////////////////////////////////////// data
      // chr is in [128,255]
      pdata.count++;
      if(pdata.count < PARAM_MAX_DATA_LENGTH) {
        pdata.chars[pdata.count] = chr;
      } else {
        st.status_code = STATUS_TOO_MUCH_DATA
      }
    }
  }
}



inline void on_cmd() {
  switch(cmd_current) {
    case CMD_NONE:
      break;
    case CMD_SEEK: case CMD_FEED: case CMD_RASTER:
        uint8_t nominal_intensity = 0;
        uint16_t pixel_width = 0;
        if(cmd_current == CMD_FEED) {
          nominal_intensity = st.intensity;
        } else if() {
          nominal_intensity = st.intensity;
          pixel_width = st.pixel_width;
        }
        planner_line( target[X_AXIS] + st.offsets[3*st.offselect+X_AXIS], 
                      target[Y_AXIS] + st.offsets[3*st.offselect+Y_AXIS], 
                      target[Z_AXIS] + st.offsets[3*st.offselect+Z_AXIS], 
                      st.feedrate, nominal_intensity, pixel_width );
      break;
    case CMD_DWELL:
      planner_dwell(st.duration, st.intensity);
      break;
    case CMD_SET_FEEDRATE:
      st.feedrate = 
      break;
    case CMD_SET_INTENSITY:

      break;
    case CMD_REF_RELATIVE:
      st.ref_mode = REF_RELATIVE;
      break;
    case CMD_REF_ABSOLUTE:
      st.ref_mode = REF_ABSOLUTE;
      break;
    case CMD_HOMING:
      stepper_homing_cycle();
      // now that we are at the physical home
      // zero all the position vectors
      clear_vector(st.position);
      clear_vector(target);
      planner_set_position(0.0, 0.0, 0.0);
      // move head to g54 offset
      st.offselect = OFFSET_G54;
      target[X_AXIS] = 0;
      target[Y_AXIS] = 0;
      target[Z_AXIS] = 0;         
      planner_line( target[X_AXIS] + st.offsets[3*st.offselect+X_AXIS], 
                    target[Y_AXIS] + st.offsets[3*st.offselect+Y_AXIS], 
                    target[Z_AXIS] + st.offsets[3*st.offselect+Z_AXIS], 
                    st.seek_rate, 0, 0 );
      break;
    case CMD_SET_OFFSET_TABLE: case CMD_SET_OFFSET_CUSTOM:
      // set offset to current position
      uint8_t cs = OFFSET_TABLE;
      if(CMD_SET_OFFSET_CUSTOM) {
        cs = OFFSET_CUSTOM;
      }
      st.offsets[3*cs+X_AXIS] = st.position[X_AXIS] + st.offsets[3*st.offselect+X_AXIS];
      st.offsets[3*cs+Y_AXIS] = st.position[Y_AXIS] + st.offsets[3*st.offselect+Y_AXIS];
      st.offsets[3*cs+Z_AXIS] = st.position[Z_AXIS] + st.offsets[3*st.offselect+Z_AXIS];
      target[X_AXIS] = 0;
      target[Y_AXIS] = 0;
      target[Z_AXIS] = 0;   
      break;
    case CMD_DEF_OFFSET_TABLE: case CMD_DEF_OFFSET_CUSTOM:
      // set offset to target
      uint8_t cs = OFFSET_TABLE;
      if(CMD_SET_OFFSET_CUSTOM) {
        cs = OFFSET_CUSTOM;
      }
      st.offsets[3*cs+X_AXIS] = target[X_AXIS];
      st.offsets[3*cs+Y_AXIS] = target[Y_AXIS];
      st.offsets[3*cs+Z_AXIS] = target[Z_AXIS];
      // Set target in ref to new coord system so subsequent moves are calculated correctly.
      target[X_AXIS] = (st.position[X_AXIS] + st.offsets[3*st.offselect+X_AXIS]) - st.offsets[3*cs+X_AXIS];
      target[Y_AXIS] = (st.position[Y_AXIS] + st.offsets[3*st.offselect+Y_AXIS]) - st.offsets[3*cs+Y_AXIS];
      target[Z_AXIS] = (st.position[Z_AXIS] + st.offsets[3*st.offselect+Z_AXIS]) - st.offsets[3*cs+Z_AXIS];
      break;
    case CMD_SEL_OFFSET_TABLE: 
      st.offselect = OFFSET_TABLE;
      break;
    case CMD_SEL_OFFSET_CUSTOM:
      st.offselect = OFFSET_CUSTOM;
      break;
    case CMD_AIR_ENABLE:
      planner_control_air_assist_enable();
      break;
    case CMD_AIR_DISABLE:
      planner_control_air_assist_disable();
      break;
    case CMD_AUX1_ENABLE:
      planner_control_aux1_assist_enable();
      break;
    case CMD_AUX1_DISABLE:
      planner_control_aux1_assist_disable();
      break;
    case CMD_AUX2_ENABLE:
      planner_control_aux2_assist_enable();
      break;
    case CMD_AUX2_DISABLE:
      planner_control_aux2_assist_disable();
      break;
    default:
      st.status_code = STATUS_UNSUPPORTED_COMMAND;
  }
}



inline void on_param() {
  if(pdata.count == 4) {
    double val = num_from_chars( pdata.chars[0], pdata.chars[1], 
                                 pdata.chars[2], pdata.chars[3] );
    switch(param_current) {
      case PARAM_TARGET_X:
        st.target[X_AXIS] = val;
        break;
      case PARAM_TARGET_Y:
        st.target[Y_AXIS] = val;
        break;
      case PARAM_TARGET_Z:
        st.target[Z_AXIS] = val;
        break;
      case PARAM_FEEDRATE:
        st.feedrate = val;
        break;
      case PARAM_INTENSITY:
        st.intensity = val;
        break;
      case PARAM_DURATION:
        st.duration = val;
        break;
      case PARAM_PIXEL_WIDTH:
        st.pixel_width = val;
        break;
      default:
        st.status_code = STATUS_INVALID_PARAMETER;
    }
  } else {
    st.status_code = STATUS_INVALID_DATA;
  }
}


inline double num_from_chars(uint8_t char0, uint8_t char1, uint8_t char2, uint8_t char3) {
  // chars expected to be extended ascii [128,255]
  // 28bit total, three decimals are restored
  // number is in [-134217.728, 134217.727] 
  return ((((char3-128)*2097152+(char2-128)*16384+(char1-128)*128+(char0-128))-134217728)/1000.0);
}

// inline void chars_from_num(num, uint8_t* char0, uint8_t* char1, uint8_t* char2, uint8_t* char3) {
//   // num to be [-134217.728, 134217.727]
//   // three decimals are retained
//   uint32_t num = lround(num*1000 + 134217728);
//   char0 = (num&127)+128
//   char1 = ((num&(127<<7))>>7)+128
//   char2 = ((num&(127<<14))>>14)+128
//   char3 = ((num&(127<<21))>>21)+128
//   return char3, char2, char1, char0
// }

// IN PYTHON
// def double_from_chars_4(char3, char2, char1, char0):
//     # chars expected to be extended ascii [128,255]
//     return ((((char3-128)*128*128*128 + (char2-128)*128*128 + (char1-128)*128 + (char0-128) )- 2**27)/1000.0)
//
// def chars4_from_double(num):
//     # num to be [-134217.728, 134217.727]
//     # three decimals are retained
//     num = int(round( (num*1000) + (2**27)))
//     char0 = (num&127)+128
//     char1 = ((num&(127<<7))>>7)+128
//     char2 = ((num&(127<<14))>>14)+128
//     char3 = ((num&(127<<21))>>21)+128
//     return char3, char2, char1, char0
//
// def check(val):
//     char3, char2, char1, char0 = chars4_from_double(val)
//     val2 = double_from_chars_4(char3, char2, char1, char0)
//     print "assert %s == %s" % (val, val2)
//     # assert val == val2
//
// check(13925.2443)

