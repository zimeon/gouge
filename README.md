# gouge

```
> run-model.py
```

pyscript version that runs in the browser:

* <https://zimeon.github.io/gouge/gouge.html>

## Model & Calculation

This code creates a model of wood turning gouge made from a round section bar with a channel ground in the top for the flute. The coordinate system for the gouge model is defined as follows:

[Gouge Coordinates][!gouge_coords.png]

It is this set of coordinates that is used for display of the resulting grinding profile and gouge shape.

A similar right-handed coordinate system is used to model the grinding jig and the grinding wheel. The grinding jig's fixed point (e.g. tip of OneWay Varigrind) and the grinding wheel are taken to be in a fixed relation to each other. The directions of the axes are the same when the gouge is flute up, centered on the wheel. There is a translation of the origin between the tip of the grinding jig (0,0,0 in jig coordinates) and the tip of the gouge (0,0,0 in gouge or tool coordinates).

When the grinding jig is rotated there is both a translation and a rotation to convert from jig coordinates to tool coordinates.

The following steps are used in calculation:

1. The gouge cutting edge shape is defined by three things: 1) the diameter of the round bar from which it is made, 2) the shape of the flute or channel (which is assumed to be symmetric about the y-axis and constant along the length of the bar (z-axis), and 3) the shape of the cutting edge profile defined in the y-z plan (again, assumed symmetric about the y-axis). The combination of these produces a 3-dimensional spline curve from top of the flute at one side of the gouge to the top of the flute at the other. This is smooth and symmetric; thus the grinding edge at the tip of the tool must be locally horizontal and straight across the bar (ie. parallel to the x axis). The spline curve is parametrized approximately linearly with real-space distance along the edge.

2. The gouge is assumed to be held in a jig for grinding. So far, the model assumes something like the One Way Varigrind, Ellsworth, or other jig that rotates on a fixed point, holding the gouge tip at a fixed length away (jig length) and at a fixed angle to the line between point and tip (jig angle, where 0 degrees would mean tool parallel to the line from fixed point). The Varigrind jig with 1.75" overhang has jig length about 9.4" and jig angle from FIXME 15 to 45 degrees.

3. The remaining parameter to specify the grind is the nose angle -- the angle between the bottom of the flute and the ground edge. This angle is typically between 40 and 70 degrees for bowl gouges, 35 and 45 degrees for spindle gouges. The nose angle allows calculation of the fixed point of the grinding jig by geometry. This is the translation between jig-wheel and tool coordinate systems.

4. Grinding jigs work by rotation of the jig and tool, and for any rotation angle we can use geometry to calculate a rotation matrix from jig-wheel to tool coordinates. The current calculation does not take into account that the translation and rotation will be slightly modified by the exact contact point between tool and grinding wheel -- likely not significant.

5. The basis for calculating the details of the grind is that, at every point along the cutting edge (intersection of flute and ground surface), the tangent to the cutting edge must lie in the plane of the grinding wheel surface at the point of contact. For each point we find the jig rotation angle that satisfies this condition (vector dot product of edge tangent and normal to grinding wheel surface is zero). If no solution is possible then the jig configuration cannot produce the specified edge shape.

6. Given the jig rotation angle the grinding curve from the edge point to the edge of the tool bar can be calculated but following the shape of the grinding wheel (which has a specified diameter, typically 6" or 8").
