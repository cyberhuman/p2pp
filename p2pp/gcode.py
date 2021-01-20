__author__ = 'Tom Van den Eede'
__copyright__ = 'Copyright 2018-2021, Palette2 Splicer Post Processing Project'
__credits__ = ['Tom Van den Eede',
               'Tim Brookman'
               ]
__license__ = 'GPLv3 '
__maintainer__ = 'Tom Van den Eede'
__email__ = 'P2PP@pandora.be'

import p2pp.variables as v
import p2pp.bedprojection as bp

X = 0
Y = 1
Z = 2
E = 3
F = 4
S = 5
OTHER = 6
COMMAND = 7
COMMENT = 8
MOVEMENT = 9
EXTRUDE = 10
RETRACT = 11
UNRETRACT = 12
CLASS = 13
INTOWER = 256

# PARAM     A   B   C   D  E  F   G   H   I   J   K   L   M   N   O   P   Q   R  S   T   U  V   W   X  Y  Z
parmidx = [-1, -1, -1, -1, 3, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5, -1, -1, -1, -1, 0, 1, 2]


def create_command(gcode_line, is_comment=False, userclass=0):

    return_value = [None, None, None, None, None, None, "", None, "", 0, False, False, False, userclass]

    if is_comment:
        return_value[COMMENT] = gcode_line
    else:

        comsplit = gcode_line.split(";", 1)
        if len(comsplit) == 2:
            return_value[COMMENT] = ";"+comsplit[1]

        fields = comsplit[0].strip().split(" ")

        if len(fields[0]) > 0:

            return_value[COMMAND] = fields[0]

            param_coefficient = 0
            for i in range(1, len(fields)):
                param = fields[i]

                try:
                    idx = parmidx[ord(param[0])-0x41]
                    if idx >= 0:
                        val = float(param[1:])
                        param_coefficient += 2 ** idx
                        return_value[idx] = val
                    else:
                        return_value[OTHER] = return_value[OTHER] + " " + param
                except (IndexError, ValueError):
                    return_value[OTHER] = return_value[OTHER] + " " + param

            check = (param_coefficient & 31)
            if check and return_value[COMMAND] == "G1":
                return_value[MOVEMENT] = check
                if param_coefficient & 8:
                    if return_value[E] < 0:
                        return_value[RETRACT] = True
                    else:
                        return_value[UNRETRACT] = (return_value[MOVEMENT] & 7) == 0    # no XYZ
                        return_value[EXTRUDE] = True

    return return_value


def create_commandstring(gcode_tupple):
    if gcode_tupple[COMMAND]:
        p = gcode_tupple[COMMAND]
        if gcode_tupple[MOVEMENT]:
            if gcode_tupple[X] is not None:
                p = p + " X{:0.3f}".format(gcode_tupple[X])
            if gcode_tupple[Y] is not None:
                p = p + " Y{:0.3f}".format(gcode_tupple[Y])
            if gcode_tupple[Z] is not None:
                p = p + " Z{:0.3f}".format(gcode_tupple[Z])
        else:
            if gcode_tupple[X] is not None:
                p = p + " X{}".format(gcode_tupple[X])
            if gcode_tupple[Y] is not None:
                p = p + " Y{}".format(gcode_tupple[Y])
            if gcode_tupple[Z] is not None:
                p = p + " Z{}".format(gcode_tupple[Z])

        if gcode_tupple[E] is not None:
            p = p + " E{:0.5f}".format(gcode_tupple[E])
        if gcode_tupple[F] is not None:
            p = p + " F{}".format(int(gcode_tupple[F]))
        if gcode_tupple[S] is not None:
            p = p + " S{}".format(int(gcode_tupple[S]))
        p = p + gcode_tupple[OTHER]
        if gcode_tupple[COMMENT] != "":
            p = p + " " + gcode_tupple[COMMENT]
    else:
        p = gcode_tupple[COMMENT]
    #
    # try:
    #     p = p + ";\t{} - ".format(gcode_tupple[CLASS])+v.classes[gcode_tupple[CLASS]]
    # except KeyError:
    #     p = p + "\tUnknown class {}".format(gcode_tupple[CLASS])
    # p = p + "[ {} {} ]".format(gcode_tupple[CLASS], gcode_tupple[MOVEMENT])

    return p


def move_to_comment(gcode_tupple, text):
    if gcode_tupple[COMMAND]:
        gcode_tupple[COMMENT] = ""
        gcode_tupple[COMMENT] = "; [{}] - {}".format(text, create_commandstring(gcode_tupple))
    else:
        gcode_tupple[COMMENT] = ""
    gcode_tupple[COMMAND] = None
    gcode_tupple[X] = None
    gcode_tupple[Y] = None
    gcode_tupple[Z] = None
    gcode_tupple[E] = None
    gcode_tupple[F] = None
    gcode_tupple[S] = None
    gcode_tupple[OTHER] = ""
    gcode_tupple[RETRACT] = None
    gcode_tupple[UNRETRACT] = None
    gcode_tupple[EXTRUDE] = None
    gcode_tupple[MOVEMENT] = 0


def get_parameter(gcode_tupple, pv, defaultvalue=0):
    if gcode_tupple[pv] is not None:
        return gcode_tupple[pv]
    return defaultvalue


def issue_command(gcode_tupple, speed=0):

    if gcode_tupple[MOVEMENT]:
        if gcode_tupple[MOVEMENT] & 8:  # movement WITH extrusion
            extrusion = gcode_tupple[E] * v.extrusion_multiplier
            v.total_material_extruded += extrusion
            v.material_extruded_per_color[v.current_tool] += extrusion

            if v.absolute_extruder:
                if v.absolute_counter == -9999 or v.absolute_counter > 3000:
                    v.processed_gcode.append("G92 E0.00  ; Extruder counter reset")
                    v.absolute_counter = 0
                v.absolute_counter += gcode_tupple[E]
                gcode_tupple[E] = v.absolute_counter

    elif v.absolute_extruder:
        if gcode_tupple[COMMAND] == "M83":
            gcode_tupple[COMMAND] = "M82"
        if gcode_tupple[COMMAND] == "G92":
            v.absolute_counter = gcode_tupple[E]

    s = create_commandstring(gcode_tupple)
    if speed:
        s = s.replace("%SPEED%", "{:0.0f}".format(speed))

    v.processed_gcode.append(s)


def issue_code(code_string, is_comment=False):
    issue_command(create_command(code_string, is_comment))
