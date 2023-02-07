"""Gouge model.

"""

import logging
import re
import math
import numpy
import time

from util import format_inches, format_feet_inches, fill_range
from fairing import FairCurve


class Gouge(object):
    """Class to digitally loft a canoe hull design."""

    def __init__(self, filename=None):
        """Initialize Gouge object, optionally read from filename."""
        self.title = "Gouge"
        self.hull_thickness = 0.25   # add to forms
        self.station_positions = {}  # index by station
        self.heights = {}            # heights for butt lines
        self.sheer_height = {}       # height of sheer line indexed by station
        self.profile_height = {}     # height values indexed by station
        self.breadths = {}           # tuples [w, y] indexed by station, sorted sheer to bottom
        self.sheer_breadth = {}      # breadth of sheer line indexed by station
        self.bow_profile = []        # tuples [x, y] from bow to bottom
        self.stern_profile = []      # tuples [x, y] from stern to bottom
        # Data formatting
        self.units = 'inches'
        self.cell_width = 10
        self.decimal_places = 5
        # Initialize stored values for lazy calculation
        self._reset_lazy_calcs()
        #
        if (filename is not None):
            self.read(filename)

    def _reset_lazy_calcs(self):
        # Initialize/reset values for lazy eval
        self._bow_station = None
        self._stern_station = None
        self._mid_station = None
        self._max_width = None
        self._bottom_height = None
        self._breadth_fairers = {}
        self._profile_fairer = None
        self._outline_at_height_fairers = {}
        self._sheer_profile_fairer = None
        self._sheer_breadth_fairer = None

    def _set_bow_stern_stations(self):
        # Lowest (by sort) station label is bow, highest is stern."""
        s = sorted(self.station_positions.keys())
        self._bow_station = s[0]
        self._stern_station = s[-1]
        self._set_max_width_and_station()

    def _set_max_width_and_station(self):
        # Widest point and station in all data
        max_width = 0.001
        station = None
        for s in self.stations:
            for x, y in self.breadths[s]:
                if (x > max_width):
                    max_width = x
                    station = s
        self._max_width = max_width
        self._mid_station = station
        logging.info("mid_station = %d" % station)

    @property
    def stations(self):
        """List of station indexes from bow to stern (low to high)."""
        return(sorted(self.station_positions.keys()))

    @property
    def bow_station(self):
        """Station index of station closest to bow."""
        if (self._bow_station is None):
            self._set_bow_stern_stations()
        return(self._bow_station)

    @property
    def stern_station(self):
        """Station index of station closest to stern."""
        if (self._stern_station is None):
            self._set_bow_stern_stations()
        return(self._stern_station)

    @property
    def mid_station(self):
        """Station index of mid station (widest breadth)."""
        if (self._mid_station is None):
            self._set_max_width_and_station()
        return(self._mid_station)

    @property
    def max_width(self):
        """Maximum width, defines mid station."""
        if (self._max_width is None):
            self._set_max_width_and_station()
        return(self._max_width)

    @property
    def upside_down(self):
        """True if the hull model is upside-down (y at bottom > y at bow/stern)."""
        return(self.profile_height[0] > self.profile_height[1])

    @property
    def bottom_height(self):
        """Height of the bottom (lowest point) in the hull.

        Assumed to be on centerline, in profile. Accounts for the possiblity
        that the hull may be drawn upside down in the mode.
        """
        compare = (lambda a, b: a < b) if self.upside_down else (lambda a, b: a > b)
        if (self._bottom_height is None):
            h = self.profile_height[0]
            for s in self.stations:
                if compare(self.profile_height[s], h):
                    h = self.profile_height[s]
            self._bottom_height = h
        return(self._bottom_height)

    def normalize(self):
        """Normalize model: stern at x=0, hull bottom at y=0, bow x +ve, up y +ve."""
        bow_x = self.bow_profile[0][0]
        stern_x = self.stern_profile[0][0]
        scale = 1.0 if (bow_x > stern_x) else -1.0
        if (stern_x != 0.0 or scale != 1.0):
            logging.info("normalize: adjusting x by %f, scaling by %f" % (-stern_x, scale))
            self.offset_scale_length(-stern_x, scale)
        bottom_y = self.bottom_height
        scale = 1.0 if self.upside_down else -1.0
        if (bottom_y != 0.0 or scale != 1.0):
            logging.info("normalize: adjusting y by %f, scaling by %f" % (-bottom_y, scale))
            self.offset_scale_vertical(-bottom_y, scale)
        self._reset_lazy_calcs()

    def read(self, filename):
        """Read hull model data from filename."""
        with open(filename, 'r') as f:
            section = None
            in_data = False
            for line in f:
                if (line.startswith('##')):
                    section = line.rstrip()
                    in_data = False
                    data = []
                elif (line.startswith('```')):
                    if (in_data):
                        # End of data
                        if (section == '## Heights'):
                            self.read_heights(data)
                        elif (section == '## Half-Breadths'):
                            self.read_breadths(data)
                        elif (section == '## End Profiles'):
                            self.read_end_profiles(data)
                        else:
                            logging.warn("Ignoring unknown section %s" % (section))
                    elif (len(data) > 0):
                        raise Exception("Multiple data blocks in section %s" % (section))
                    else:
                        in_data = True
                elif (in_data):
                    data.append(line.rstrip())

    def read_heights(self, data):
        """Read table of heights which include sheer (first) and bottom/profile (last).

        Sets the self.station_positions hash which maps station labels (integer) into
        positions along the x or length axis.
        """
        title_line = re.split('\s+', data.pop(0))
        title = title_line.pop(0)
        if (title != 'Station'):
            raise Exception("First line of breadths must start with Station, got '%s'" % (title))
        stations = [int(x) for x in title_line]
        # OPTIONAL Positions line (else assume 1' spacing)
        if (data[0].startswith('Position')):
            position_line = re.split('\s+', data.pop(0))
            position_line.pop(0)  # already checked this, discard
            for station in stations:
                self.station_positions[station] = self.parse_dimension(position_line.pop(0))
        else:
            # no explicit positions line, 1' spacing assumed
            for s in stations:
                self.station_positions[s] = float(s) * 12.0
        # Sheer line
        sheer_line = re.split('\s+', data.pop(0))
        title = sheer_line.pop(0)
        if (title != 'Sheer'):
            raise Exception("Second line of breadths must start with Sheer or Position, got '%s'" % (title))
        for station in stations:
            self.sheer_height[station] = self.parse_dimension(sheer_line.pop(0))
        # Profile line (last)
        profile_line = re.split('\s+', data.pop())
        title = profile_line.pop(0)
        if (title != 'Profile'):
            raise Exception("Last line of breadths must start with Profile, got '%s'" % (title))
        for station in stations:
            self.profile_height[station] = self.parse_dimension(profile_line.pop(0))
        # Rest of lines
        for s in stations:
            self.heights[s] = []
        for line in data:
            entries = re.split('\s+', line)
            butt = self.parse_dimension(entries.pop(0))
            for station in stations:
                height = self.parse_dimension(entries.pop(0))
                height = None if height is None else -height
                self.heights[station].append([butt, height])

    def read_breadths(self, data):
        """Read table of half-breadths.

        First line must be "Stations #n #n-1 ... #0"
        Checks that the set of stations is the same as the set of stations already read from the table
        of heights in read_heights().
        """
        title_line = re.split('\s+', data.pop(0))
        title = title_line.pop(0)
        if (title != 'Station'):
            raise Exception("First line of breadths must start with Station, got '%s'" % (title))
        stations = [int(x) for x in title_line]
        if (set(stations) != set(self.stations)):
            raise Exception("Stations in breadths don't match stations in heights!")
        # Sheer line
        sheer_line = re.split('\s+', data.pop(0))
        title = sheer_line.pop(0)
        if (title != 'Sheer'):
            raise Exception("Second line of breadths must start with Sheer, got '%s'" % (title))
        for station in stations:
            self.sheer_breadth[station] = self.parse_dimension(sheer_line.pop(0))
        # Rest of lines
        for s in stations:
            self.breadths[s] = []
        for line in data:
            entries = re.split('\s+', line)
            vertical = self.parse_dimension(entries.pop(0))
            for station in stations:
                horizontal = self.parse_dimension(entries.pop(0))
                if (horizontal is not None):
                    self.breadths[station].append([horizontal, vertical])

    def read_end_profiles(self, data):
        """Read table of end profiles.

        First line must be "Stations #sr #br"
        Remaining          "Height   #l   #l"

        Where sr and br are the reference stations for stern and bow respectively
        and the #l are horizontal distances at the give heights from the stations.
        """
        title_line = re.split('\s+', data.pop(0))
        title = title_line.pop(0)
        if (title != 'Station'):
            raise Exception("First line of end profile must start with Station, got '%s'" % (title))
        if (len(title_line) != 2):
            raise Exception("Must have two reference stations for end profiles, got %d" % (len(title)))
        sr, br = title_line
        srl = self.station_positions[int(sr)]
        brl = self.station_positions[int(br)]
        flip = 1.0 if (brl < srl) else -1.0  # Handle bow-stern oreintation along x
        for line in data:
            entries = re.split('\s+', line)
            vertical = self.parse_dimension(entries.pop(0))
            x = self.parse_dimension(entries.pop(0))
            if (x is not None):
                self.stern_profile.append([srl + x * flip, vertical])
            x = self.parse_dimension(entries.pop(0))
            if (x is not None):
                self.bow_profile.append([brl - x * flip, vertical])

    def _format_label(self, label, left_align=True):
        """Make fixed-width label string."""
        fmt = '%' + ('-' if left_align else '') + str(self.cell_width) + 's'
        return(fmt % str(label))

    def _format_dimension(self, x, left_align=False):
        """Make fixed-width string for dimension x."""
        if (x is None):
            return(self._format_label('-', left_align))
        fmt = ('%' + ('-' if left_align else '') + str(self.cell_width) +
               '.' + str(self.decimal_places) + 'f')
        return(fmt % x)

    def write(self, filename):
        """Write hull model data to filename."""
        with open(filename, 'w') as fh:
            fh.write("# " + self.title + "\n\n")
            fh.write("Date: " + time.asctime(time.localtime()) + "\n")
            fh.write("Units: " + self.units + "\n\n")
            fh.write(self.md_table("Heights", self.heights_table()))
            fh.write(self.md_table("Half-Breadths", self.breadths_table()))
            fh.write(self.md_table("End Profiles", self.end_profiles_table()))

    def title_line(self, stations):
        """Title line with station numbers for write_heights and write_breadths."""
        # Station numbers
        title_line = [self._format_label('Station')]
        for s in stations:
            title_line.append(self._format_label(s, left_align=False))
        return(title_line)

    def md_table(self, name, lines):
        """Markdown string of table section `name` for `lines`."""
        s = "## " + name + "\n\n```\n"
        for line in lines:
            s += ' '.join(line) + "\n"
        s += "```\n\n"
        return(s)

    def heights_table(self):
        """Table of heights which include sheer (first) and bottom/profile (last).

        One column for each value in the self.station_positions hash which maps station
        labels (integer) into positions along the x or length axis.
        """
        # Station numbers
        stations = list(reversed(self.stations))
        lines = [self.title_line(stations)]
        # Station positions
        pos_line = [self._format_label('Position')]
        for s in stations:
            pos_line.append(self._format_dimension(self.station_positions[s]))
        lines.append(pos_line)
        # Sheer line
        sheer_line = [self._format_label('Sheer')]
        for s in stations:
            sheer_line.append(self._format_dimension(self.sheer_height[s]))
        lines.append(sheer_line)
        # Skip butts as we don't user them
        # Profile line
        profile_line = [self._format_label('Profile')]
        for s in stations:
            profile_line.append(self._format_dimension(self.profile_height[s]))
        lines.append(profile_line)
        return(lines)

    def breadths_table(self):
        """Table of half-breadths.

        Like write_heights() write one column for each value in the self.station_positions
        hash which maps station labels (integer) into positions along the x or length axis.
        """
        # Station numbers
        stations = list(reversed(self.stations))
        lines = [self.title_line(stations)]
        # Sheer line
        sheer_line = [self._format_label('Sheer')]
        for s in stations:
            sheer_line.append(self._format_dimension(self.sheer_breadth[s]))
        lines.append(sheer_line)
        # Rest of lines (first find all heights used)
        verticals = set()
        for s in stations:
            for h, v in self.breadths[s]:
                verticals.add(v)
        for v in sorted(verticals, reverse=True):
            line = [self._format_dimension(v, left_align=True)]
            for s in stations:
                h = None
                for hh, vv in self.breadths[s]:
                    if (v == vv):
                        h = hh
                        break
                line.append(self._format_dimension(h))
            lines.append(line)
        return(lines)

    def end_profiles_table(self):
        """Table of end profiles.

        First line will be "Stations #sr #br"
        Remaining          "Height   #l  #l"

        Where sr and br are the reference stations for stern and bow respectively
        and the #l are horizontal distances at the give heights from the stations.
        """
        sr = max(self.station_positions)
        br = min(self.station_positions)
        lines = [[self._format_label('Station'),
                  self._format_label(sr, left_align=False),
                  self._format_label(br, left_align=False)]]
        # Data
        srl = self.station_positions[int(sr)]
        brl = self.station_positions[int(br)]
        verticals = set()
        for x, y in self.stern_profile:
            verticals.add(y)
        for x, y in self.bow_profile:
            verticals.add(y)
        for v in sorted(verticals, reverse=True):
            line = [self._format_dimension(v, left_align=True)]
            xx = None
            for x, y in self.stern_profile:
                if (v == y):
                    xx = srl - x
                    break
            line.append(self._format_dimension(xx))
            xx = None
            for x, y in self.bow_profile:
                if (v == y):
                    xx = x - brl
                    break
            line.append(self._format_dimension(xx))
            lines.append(line)
        return(lines)

    def min_max_length(self, round_out=True):
        """Minimum and maximum length (x) values.

        Either bow or stern are min and max respectively.
        """
        min_x = self.bow_profile[0][0]
        max_x = self.stern_profile[0][0]
        if (min_x > max_x):
            x = min_x
            min_x = max_x
            max_x = x
        if (round_out):
            min_x = -int(-min_x + 1.0)
            max_x = int(max_x + 1.0)
        return(min_x, max_x)

    def min_max_vertical(self, round_out=True):
        """Minimum and maximum vertical (y) values."""
        min_y = None
        max_y = None
        for s in self.stations:
            for y in self.sheer_height[s], self.profile_height[s]:
                if (y is not None):
                    if (min_y is None or y < min_y):
                        min_y = y
                    elif (max_y is None or y > max_y):
                        max_y = y
        if (round_out):
            min_y = -int(-min_y + 1.0)
            max_y = int(max_y + 1.0)
        return(min_y, max_y)

    def sheer_curve_3d(self, bow_to_mid=True, mid_to_stern=True):
        """Tuple of arrays for xx, ww, yy of sheer curve bow to stern in 3d, with labels."""
        xx = []
        ww = []
        yy = []
        labels = []
        # Bow
        if (bow_to_mid):
            x, y = self.bow_profile[0]
            xx.append(x)
            ww.append(0.0)
            yy.append(y)
            labels.append("Bow")
        # Stations
        for s in self.stations:
            if (s <= self.mid_station and bow_to_mid):
                xx.append(self.station_positions[s])
                ww.append(self.sheer_breadth[s])
                yy.append(self.sheer_height[s])
                labels.append(s)
            elif (s >= self.mid_station and mid_to_stern):
                xx.append(self.station_positions[s])
                ww.append(self.sheer_breadth[s])
                yy.append(self.sheer_height[s])
                labels.append(s)
        # Stern
        if (mid_to_stern):
            x, y = self.stern_profile[0]
            xx.append(x)
            ww.append(0.0)
            yy.append(y)
            labels.append("Stern")
        return(xx, ww, yy, labels)

    def sheer_profile_curve(self):
        """Tuple of arrays for sheer profile curve bow to stern, and labels."""
        xx = []
        yy = []
        labels = []
        # Bow
        x, y = self.bow_profile[0]
        xx.append(x)
        yy.append(y)
        labels.append("Bow")
        # Stations
        for s in self.stations:
            xx.append(self.station_positions[s])
            yy.append(self.sheer_height[s])
            labels.append(s)
        # Stern
        x, y = self.stern_profile[0]
        xx.append(x)
        yy.append(y)
        labels.append("Stern")
        return(xx, yy, labels)

    def sheer_breadth_profile_curve(self, bow_to_mid=False, mid_to_stern=False, flip_x=False):
        """Tuple of arrays for sheer profile curve bow to stern, viewed from end."""
        xx, ww, yy, labels = self.sheer_curve_3d(bow_to_mid, mid_to_stern)
        if (flip_x):
            ww = [-w for w in ww]
        return(ww, yy)
        yy = []
        labels = []
        # Bow
        if (bow_to_mid):
            x, y = self.bow_profile[0]
            ww.append(0.0)
            yy.append(y)
        # Stations
        for s in self.stations:
            if (s <= self.mid_station and bow_to_mid):
                ww.append(self.sheer_breadth[s])
                yy.append(self.sheer_height[s])
            elif (s >= self.mid_station and mid_to_stern):
                ww.append(self.sheer_breadth[s])
                yy.append(self.sheer_height[s])
        # Stern
        if (mid_to_stern):
            x, y = self.stern_profile[0]
            ww.append(0.0)
            yy.append(y)
        if (flip_x):
            ww = [-w for w in ww]
        return(ww, yy)

    def profile_curve(self, bow_to_mid=True, mid_to_stern=True, mid_index=False):
        """Tuple of arrays for profile curve of hull bottom from bow to stern.

        Optionally select bow_to_mid or mid_to_stern.
        """
        xx = []
        yy = []
        mi = None
        # Bow profile
        if (bow_to_mid):
            for x, y in self.bow_profile:
                xx.append(x)
                yy.append(y)
        # Stations
        for s in self.stations:
            if (s <= self.mid_station and bow_to_mid):
                xx.append(self.station_positions[s])
                yy.append(self.profile_height[s])
            elif (s >= self.mid_station and mid_to_stern):
                xx.append(self.station_positions[s])
                yy.append(self.profile_height[s])
            if (s == self.mid_station):
                mi = len(xx) - 1
        # Stern profile
        if (mid_to_stern):
            for x, y in reversed(self.stern_profile):
                xx.append(x)
                yy.append(y)
        if (mid_index):
            return(xx, yy, mi)
        else:
            return(xx, yy)

    def sheer_breadth_plan_curve(self):
        """Tuple of arrays for sheer breadth curve bow to stern, with labels."""
        xx = []
        ww = []
        labels = []
        # Bow
        x, y = self.bow_profile[0]
        xx.append(x)
        ww.append(0.0)
        labels.append("Bow")
        # Stations
        for s in self.stations:
            xx.append(self.station_positions[s])
            ww.append(self.sheer_breadth[s])
            labels.append(s)
        # Stern
        x, y = self.stern_profile[0]
        xx.append(x)
        ww.append(0.0)
        labels.append("Stern")
        return(xx, ww, labels)

    def breadth_curve(self, station, flip_x=False):
        """Tuple of arrays for breadth curve at station.

        Kheel to Sheer.
        First array value is horizontal distance from centerline.
        Second array value is vertical distance from baseline.
        """
        xx = []
        yy = []
        # Kheel line
        xx.append(0.0)
        yy.append(self.profile_height[station])
        # Side
        for x, y in reversed(self.breadths[station]):
            if (x is not None and y is not None):
                xx.append(-x if flip_x else x)
                yy.append(y)
        # Sheer
        x = self.sheer_breadth[station]
        xx.append(-x if flip_x else x)
        yy.append(self.sheer_height[station])
        return(xx, yy)

    def breadth_fairer(self, station):
        """Fairing object for breadth curve at given station.

        Sheer to kheel to Sheer again so that we get a continuous curve
        over the kheel line.
        """
        if (station not in self._breadth_fairers):
            ww, yy = self.breadth_curve(station)
            wy = list(zip(ww, yy))
            wy2 = [wy.pop(0)]  # kheel point
            for wy_point in wy:
                wy2.insert(0, wy_point)
                wy2.append([-wy_point[0], wy_point[1]])
            # logging.warn("Fairing " + str(wy2))
            self._breadth_fairers[station] = FairCurve(wy2, mid_index=(len(wy2) // 2))
        return(self._breadth_fairers[station])

    @property
    def profile_fairer(self):
        """Fairing object for profile height."""
        if (self._profile_fairer is None):
            ll, yy, mi = self.profile_curve(mid_index=True)
            self._profile_fairer = FairCurve(zip(ll, yy), mid_index=mi)
        return(self._profile_fairer)

    @property
    def sheer_profile_fairer(self):
        """Fairing object for sheer height given length (l, y)."""
        if (self._sheer_profile_fairer is None):
            ll, yy, labels = self.sheer_profile_curve()
            self._sheer_profile_fairer = FairCurve(zip(ll, yy))
        return(self._sheer_profile_fairer)

    @property
    def sheer_breadth_fairer(self):
        """Fairing object for sheer breadth (l, w)."""
        if (self._sheer_breadth_fairer is None):
            ll, ww, labels = self.sheer_breadth_plan_curve()
            self._sheer_breadth_fairer = FairCurve(zip(ll, ww))
        return(self._sheer_breadth_fairer)

    def bow_profile_interpolated(self, height):
        """Interpolated x value of bow profile for given height.

        Use the portion of the profile_fairer from start to mid-point
        in order to get the bow profile.
        """
        try:
            pf = self.profile_fairer
            return pf.x(height, end=pf.mid_index)
        except ValueError as e:
            logging.warn('bow_profile_interpolated: ' + str(e))
            return self.station_positions[self.mid_station]

    def stern_profile_interpolated(self, height):
        """Interpolated x value of stern profile for height."""
        try:
            pf = self.profile_fairer
            return pf.x(height, start=pf.mid_index)
        except ValueError as e:
            logging.warn('stern_profile_interpolated: ' + str(e))
            return self.station_positions[self.mid_station]

    def outline_at_height(self, height):
        """Return length, width coordinate pairs for hull section at height.

        Start from bow and go to stern, find breadth only for stations with length position
        in this range.
        """
        # Sanity check
        if (self.bow_profile[0][0] <= self.stern_profile[0][0]):
            raise Exception("outline_at_height(%f) configured only to work if x-coord of bow > x-coord of stern" % height)
        if (height < (self.bottom_height + 0.001)):
            raise Exception("outline_at_height(%f) request height value too low" % height)
        xx = []
        ww = []
        # Bow and stern profile lengths
        bow_x = self.bow_profile_interpolated(height)
        stern_x = self.stern_profile_interpolated(height)
        logging.debug('outline_at_height: sx, bx = ' + str(bow_x) + '  ' + str(stern_x))
        # Build curve
        xx.append(stern_x)
        ww.append(0.0)
        # Stations
        for s in reversed(self.stations):
            x = self.station_positions[s]
            if (x > bow_x):
                break
            elif (x < stern_x):
                continue
            else:
                try:
                    w = self.breadth_fairer(s).x(height)
                    xx.append(x)
                    ww.append(w)
                except ValueError as e:
                    logging.debug("outline_at_height: station %d (%s)" %
                                  (s, str(e)))
        xx.append(bow_x)
        ww.append(0.0)
        return(xx, ww)

    def outline_at_height_interpolator(self, height):
        """Interpolator to get width value at given length and given height.

        Relies upon having a set of interpolations at each stations and then
        interpolating the points at the given height.
        """
        if (height not in self._outline_at_height_fairers):
            xx, ww = self.outline_at_height(height)
            # For the middle portion of the hull where height may be above the sheer
            # there will be None entries in ww, strip these (accepting funky curve)
            x2 = []
            w2 = []
            for x, w in zip(xx, ww):
                if (w is not None):
                    x2.append(float(x))
                    w2.append(float(w))
            logging.debug("outline_at_height_interpolator: h=%f x2=%s w2=%s" %
                          (height, str(x2), str(w2)))
            self._outline_at_height_fairers[height] = FairCurve(zip(x2, w2))
        return(self._outline_at_height_fairers[height])

    def area_at_height(self, height):
        """Calculate hull plan areas and center length at given height."""
        if (height < (self.bottom_height + 0.001)):
            area = 0.0
            center = self.station_positions[self.mid_station]
        else:
            xx, ww = self.outline_at_height(height)
            cc = [(x * w) for x, w in zip(xx, ww)]
            area = 2.0 * numpy.trapz(ww, xx)
            center = 2.0 * numpy.trapz(cc, xx) / area
        logging.debug("area_at_height(%.3f) = %.3f sq inches, center = %.3f" %
                      (height, area, center))
        return(area, center)

    def area_depth_table(self, start=0.0, end=5.0, step=0.1):
        """Calculate areas and centers at progressive depths from the lowest point."""
        depths = list(numpy.arange(start, end + step, step))
        areas = []
        centers = []
        for depth in depths:
            area, center = self.area_at_height(self.bottom_height + depth)
            areas.append(area)
            centers.append(center)
        return(depths, areas, centers)

    def insert_breadth_point(self, station, width, height):
        """Insert points into self.breadths[s] list based on height sequence."""
        if (self.breadths[station][0][1] < self.breadths[station][-1][1]):
            raise Exception("insert_breadth_point assumes breadths sorted sheer to bottom, descending y.")
        for j, wy in enumerate(self.breadths[station]):
            if (wy[1] < height):
                self.breadths[station].insert(j, [width, height])
                break
        self.breadths[station].append([width, height])

    def add_breadths_at_height(self, height):
        """Add breadth points at height to every station where height is in range.

        Use faired breadth curves.
        """
        for s in self.stations:
            logging.warn('add_breadths_at_height station %s' % (s))
            if (height >= self.sheer_height[s] or
                    height <= self.profile_height[s]):
                # Not in range of heights for this station, nothing to do
                continue
            try:
                width = self.breadth_fairer(s).x(height)
                logging.warn('Got width %.3f" for height %.3f at at station %s' % (width, height, s))
                self.insert_breadth_point(s, width, height)
            except ValueError as e:
                logging.warn('Failed to get width for height %.3f" at station %s' % (height, s))

    def interpolated_breadths(self, length, heights, max_height):
        """Return a list if [w, h] pairs for h in heights at length."""
        breadths = []
        for h in heights:
            if (h > (max_height - 0.25)):  # don't add a point within 0.25" of sheer, or above
                continue
            try:
                w = self.outline_at_height_interpolator(h).y(length)
                breadths.append([w, h])
            except ValueError as e:
                # Out-of-range so simply skip
                logging.info("interpolated_breadths: height=%.1f length=%.1f (%s)" %
                             (h, length, str(e)))
                pass
        return(breadths)

    def set_stations(self, station_positions, heights):
        """Make a new set of stations at the x positions set in station_positions.

        Sort the new station positions from low to high, bow to stern. Sort the
        new heights from high to low as we want the breadths from the sheer line
        to the bottom.

        For sheer and profile we use interpolations from the faired curves
        directly. For the new set of station breadths we rely upon the
        self.interpolated_breadths() method, which in turn replies upon a
        faired interpolator for a given height.
        """
        station_positions = sorted(station_positions)
        heights = sorted(heights, reverse=True)
        logging.info("set_stations: started")
        new_station_positions = {}
        new_sheer_height = {}
        new_profile_height = {}
        new_breadths = {}
        new_sheer_breadth = {}
        station_index = len(station_positions)
        for l in sorted(station_positions):
            station_index -= 1  # will run from highest at stern (low l) to 0 at bow (high l)
            logging.debug("set_station %d" % station_index)
            new_station_positions[station_index] = l
            new_sheer_height[station_index] = self.sheer_profile_fairer.y(l)
            new_breadths[station_index] = self.interpolated_breadths(l, heights, new_sheer_height[station_index])
            new_sheer_breadth[station_index] = self.sheer_breadth_fairer.y(l)
            new_profile_height[station_index] = self.profile_fairer.y(l)
        # Switch new data into place
        self.station_positions = new_station_positions
        self.breadths = new_breadths
        self.sheer_height = new_sheer_height
        self.sheer_breadth = new_sheer_breadth
        self.profile_height = new_profile_height
        self._reset_lazy_calcs()
        logging.info("set_stations: done")

    def displacement_table(self, start, end, step):
        """Calculate displacement and center of buoyancy for various depths.

        Measure displacement in terms of pounds weight (lbs) based on the
        density of fresh water: 1 in^3 = 0.036127 lb of water

        For each area we also have from the area_depth_table() the center of
        that area. The combined center of buoyancy will be the integral over
        the depth of the area * center, divided by the total volume.

        Return three lists.
        """
        drafts = []
        displacements = []
        cobs = []
        depths, areas, centers = self.area_depth_table(0.0, end, step / 5.0)
        a_x_c = [a * c for a, c in zip(areas, centers)]
        for draft in numpy.arange(start, end + step, step):
            for i, depth in enumerate(depths):
                if (depth >= draft):
                    volume = numpy.trapz(areas[0:(i + 1)], depths[0:(i + 1)])
                    displacement = volume * 0.036127
                    cob = numpy.trapz(a_x_c[0:(i + 1)], depths[0:(i + 1)]) / volume
                    drafts.append(depth)
                    displacements.append(displacement)
                    cobs.append(cob)
                    break
        return(drafts, displacements, cobs)

    def displacement_summary(self, start=2.0, end=6.0, step=0.5):
        """String summary of displacement and center of buoyancy."""
        s = ''
        try:
            depths, displacements, cobs = self.displacement_table(start, end, step)
            for depth, displacement, cob in zip(depths, displacements, cobs):
                s += ('  %.1f" at %.1flbs total weight @ %.1f" (including boat)\n'
                      % (depth, displacement, cob))
        except Exception as e:
            s = "Failed to calculate displacements: " + str(e)
        return(s)

    def parse_dimension(self, s):
        """Read a dimension string and return decimal inches.

        WL#" = # inches
        Butt#" = # inches
        #.###  = #.## inches
        #-##-# = # feet, ## inches + #/8 inches
        """
        if (s == '-'):
            return(None)
        m = re.match(r'''(WL|Butt)(\d+)\"$''', s)
        if (m):
            # Waterline offset or butt (distance from centerline) in inches
            return(float(m.group(2)))
        # try parsing as simple float
        try:
            return(float(s))
        except ValueError:
            pass
        # else use ft-inches-eigths format
        m = re.match(r'''(\d+)\-(\d+)\-(\d)(\d|\+)?''', s)
        if (m):
            return(float(m.group(1)) * 12.0 + float(m.group(2)) +
                   float(m.group(3)) / 8.0 +
                   (0.0625 if m.group(4) == '+' else (0.0 if m.group(4) is None else int(m.group(4)) / 80.0)))
        raise Exception("Bad dimemsion '%s'" % (s))

    def offset_scale_vertical(self, offset=0.0, scale=1.0):
        """Add offset and then scale all vertical coordinates in model."""
        self.transform_vertical(lambda y: ((y + offset) * scale))

    def transform_vertical(self, func):
        """Apply func to all vertical coordinates in model."""
        # Station based measurements
        sb = {}
        for s in self.stations:
            self.sheer_height[s] = func(self.sheer_height[s])
            self.profile_height[s] = func(self.profile_height[s])
            breadths = []
            for x, y in self.breadths[s]:
                breadths.append([x, func(y)])
            sb[s] = breadths
        self.breadths = sb
        # End profiles
        bp = []
        for x, y in self.bow_profile:
            bp.append([x, func(y)])
        self.bow_profile = bp
        sp = []
        for x, y in self.stern_profile:
            sp.append([x, func(y)])
        self.stern_profile = sp
        self._reset_lazy_calcs()

    def offset_scale_length(self, offset=0.0, scale=1.0):
        """Add offset and then scale all length coordinates in model."""
        self.transform_length(lambda x: ((x + offset) * scale))

    def transform_length(self, func):
        """Apply func to all length coordinates in model."""
        # Station positions
        for s in self.stations:
            self.station_positions[s] = func(self.station_positions[s])
        # Bow and stern profiles
        bp = []
        for x, y in self.bow_profile:
            bp.append([func(x), y])
        self.bow_profile = bp
        sp = []
        for x, y in self.stern_profile:
            sp.append([func(x), y])
        self.stern_profile = sp
        self._reset_lazy_calcs()

    def scale_width(self, scale=1.0):
        """Scale all width coordinates in model."""
        self.transform_width(lambda x: (x * scale))

    def transform_width(self, func):
        """Apply func to all width coordinates in model."""
        # Station based measurements
        sb = {}
        for s in self.stations:
            self.sheer_breadth[s] = func(self.sheer_breadth[s])
            breadths = []
            for x, y in self.breadths[s]:
                breadths.append([func(x), y])
            sb[s] = breadths
        self.breadths = sb
        self._reset_lazy_calcs()

    def stern_to_mid_stations(self, include_mid=True):
        """List of stations from stern to the middle station."""
        mid_station = self.mid_station
        s2m = []
        for s in sorted(self.stations, reverse=True):
            s2m.append(s)
            if s <= mid_station:
                break
        return(s2m)

    def bow_to_mid_stations(self, include_mid=True):
        """List of stations from bow to the middle station."""
        mid_station = self.mid_station
        b2m = []
        for s in sorted(self.stations):
            b2m.append(s)
            if s >= mid_station:
                break
        return(b2m)

    def length(self):
        """Canoe length."""
        return(abs(self.bow_profile[0][0] - self.stern_profile[0][0]))

    def sheer_length(self):
        """Length of the sheer line or gunwale."""
        xx, ww, yy, labels = self.sheer_curve_3d()
        l = 0.0
        for i in range(0, len(xx) - 1):
            l += math.sqrt((xx[i] - xx[i + 1]) ** 2 +
                           (ww[i] - ww[i + 1]) ** 2 +
                           (yy[i] - yy[i + 1]) ** 2)
        return(l)

    def beam_sheer(self):
        """Beam at sheer."""
        max_breadth = 0.0
        for k, v in self.sheer_breadth.items():
            if (v > max_breadth):
                max_breadth = v
        return(max_breadth * 2.0)

    def depth(self, station):
        """Depth from sheer to centre hull bottom at station."""
        return(self.sheer_height[station] - self.profile_height[station])

    def sheer_length_extension_through_thickness(self):
        """Sum of bow and stern extension lengths due to hull thickness.

        We want these in order to be able to get boat length from the form
        length. Calculate based on scaling trianngle between centerline, end
        of sheer and sheer width at closest station -- to sheer width + hull
        thickness, extra length is thus extension.
        """
        # bow
        dy = self.sheer_breadth[self.bow_station]
        dx = abs(self.station_positions[self.bow_station] - self.bow_profile[0][0])
        bow_extension = dx * ((dy + self.hull_thickness) / dy - 1.0)
        # stern
        dy = self.sheer_breadth[self.bow_station]
        dx = abs(self.station_positions[self.bow_station] - self.bow_profile[0][0])
        stern_extension = dx * ((dy + self.hull_thickness) / dy - 1.0)
        logging.debug("sheer_length_extension_through_thickness: %.2f %.2f" %
                      (bow_extension, stern_extension))
        return(bow_extension + stern_extension)

    def circumference(self, station=None):
        """Length around outside of hull at station (default is midpoint).

        FIXME - just uses sum of linear interpolation.
        """
        l = 0.0
        last_w = None
        last_y = None
        if (station is None):
            station = self.mid_station
        xx, yy = self.breadth_curve(self.mid_station)
        for w, y in zip(xx, yy):
            if (last_w is not None):
                l += math.sqrt((w - last_w) ** 2 +
                               (y - last_y) ** 2)
            last_w = w
            last_y = y
        return(l * 2.0)

    def hull_outside_area(self):
        """Gouge outside area estimate.

        Use trapezium rule based on circumferences at stations. Result
        in sq inches.
        """
        area = 0.0
        last_circ = 0.0
        last_position = None
        for station in self.stations:
            circ = self.circumference(station)
            position = self.station_positions[station]
            if (last_position is None):
                # Bow to first station
                area += 0.5 * circ * abs(self.bow_profile[0][0] - position)
            else:
                # Station to station
                area += 0.5 * (circ + last_circ) * abs(last_position - position)
            last_circ = circ
            last_position = position
        # Last station to stern
        area += 0.5 * last_circ * abs(self.stern_profile[0][0] - last_position)
        return(area)

    @property
    def outside_length(self):
        """Model length plus extension through hull thickness."""
        return(self.length() + self.sheer_length_extension_through_thickness())

    @property
    def outside_max_beam(self):
        """Model max beam plus two hull thicknesses."""
        return((self.max_width + self.hull_thickness) * 2.0)

    @property
    def outside_sheer_beam(self):
        """Model sheer beam plus two hull thicknesses."""
        return(self.beam_sheer() + self.hull_thickness * 2.0)

    @property
    def outside_center_depth(self):
        """Model depth at mid station plus hull thickness."""
        return(self.depth(self.mid_station) + self.hull_thickness)
