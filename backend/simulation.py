import driveboard
import math

class Simulator:
    def __init__(self, svg_output_filename=None):
        self.x = 0.0
        self.y = 0.0
        self.f = 8000.0
        self.i = 0
        self.minutes = 0.0
        self.dist = 0.0
        self.MINIMUM_PULSE_TICKS = driveboard.MINIMUM_PULSE_TICKS
        self.MAXIMUM_PULSE_TICKS = driveboard.MAXIMUM_PULSE_TICKS
        self.PULSE_SECONDS = driveboard.PULSE_SECONDS
        self.ACCELERATION = driveboard.ACCELERATION

        if svg_output_filename:
            self.filename = svg_output_filename
            import cairo
            w, h = 1220, 610
            mm_to_points = 72 / 25.4
            surf = cairo.SVGSurface(self.filename, w*mm_to_points, h*mm_to_points)
            self.cr = cairo.Context(surf)
            self.cr.scale(mm_to_points, mm_to_points)
        else:
            self.cr = None

    def homing(self):
        self.x = 0.0
        self.y = 0.0
        
    def air_on(self):
        pass

    def air_off(self):
        pass

    def feedrate(self, f):
        self.f = f

    def intensity(self, v):
        self.i = v

    def move(self, x, y):
        self._move(x, y)

    def raster_move(self, x, y, data):
        self._move(x, y, raster_data=data)

    def _move(self, x, y, raster_data=None):
        dist = math.hypot(self.x-x, self.y-y)
        self.dist += dist
        self.minutes += dist / self.f

        cr = self.cr
        if cr:
            cr.set_line_width(0.1)
            if raster_data is not None: # raster move
                cr.set_source_rgba(0.0, 0.0, 0.0, 0.5)
            elif self.i == 0: # travel move
                cr.set_line_width(0.05)
                cr.set_source_rgba(0.0, 0.0, 1.0, 0.5)
            else: # lasing move
                cr.set_source_rgba(1.0, 0.0, 0.0, 0.5)
            cr.move_to(self.x, self.y)
            cr.line_to(x, y)
            cr.close_path()
            cr.stroke()

        self.x = x
        self.y = y

    def report(self):
        print
        print 'Simulation results:'
        print 'distance %.0fm' % (self.dist / 1000.0)
        print 'duration %.1f minutes (without accelerations)' % self.minutes
        if self.cr:
            print 'output saved to: %r' % self.filename

