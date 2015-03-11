
import re


re_findall_floats = re.compile('(-?[0-9]+\.?[0-9]*(?:e-?[0-9]*)?)').findall
re_scalar_unit = re.compile('(-?[0-9]+\.?[0-9]*(?:e-?[0-9]*)?)([a-z]*)').findall


def parseFloats(float_strings):
	"""Convert a list of float strings to an actual list of floats.

	The function can deal with pretty much any separation chars.
	"""
	float_strings = re_findall_floats(float_strings)
	for i in range(len(float_strings)):  # use index so we can edit in-place
		float_strings[i] = float(float_strings[i])
	return float_strings


def parseScalar(scalar_unit_string):
	"""Parse one scalar string with (optional) unit and return both."""
	num, unit = re_scalar_unit(scalar_unit_string)[0]
	num = float(num)
	return (num, unit)


def matrixMult(mA, mB):
    return [ mA[0]*mB[0] + mA[2]*mB[1],
             mA[1]*mB[0] + mA[3]*mB[1],
             mA[0]*mB[2] + mA[2]*mB[3],
             mA[1]*mB[2] + mA[3]*mB[3],
             mA[0]*mB[4] + mA[2]*mB[5] + mA[4],
             mA[1]*mB[4] + mA[3]*mB[5] + mA[5] ]


def matrixApply(mat, vec):
    vec0 = mat[0]*vec[0] + mat[2]*vec[1] + mat[4]
    vec[1] = mat[1]*vec[0] + mat[3]*vec[1] + mat[5]
    vec[0] = vec0


def matrixApplyScale(mat, vec):
    # POSSIBLE BUG: not sure the scale can be extracted
    # this easily for compound matices
    vec[0] *= mat[0]
    vec[1] *= mat[3]


def vertexScale(v, f):
    v[0] *= f
    v[1] *= f
