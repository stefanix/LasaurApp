
import re



def parseFloats(float_strings):
	"""Convert a list of float strings to an actual list of floats.

	The function can deal with pretty much any separation chars.
	"""
	float_strings = re.findall('(-?[0-9]+\.?[0-9]*(?:e-?[0-9]*)?)', float_strings)
	for i in range(len(float_strings)):  # use index so we can edit in-place
		float_strings[i] = float(float_strings[i])
	return float_strings


def matrixMult(mA, mB):
    return [ mA[0]*mB[0] + mA[2]*mB[1],
                     mA[1]*mB[0] + mA[3]*mB[1],
                     mA[0]*mB[2] + mA[2]*mB[3],
                     mA[1]*mB[2] + mA[3]*mB[3],
                     mA[0]*mB[4] + mA[2]*mB[5] + mA[4],
                     mA[1]*mB[4] + mA[3]*mB[5] + mA[5] ]


def matrixApply(mat, vec):
    return [ mat[0]*vec[0] + mat[2]*vec[1] + mat[4],
                     mat[1]*vec[0] + mat[3]*vec[1] + mat[5] ]


def vertexScale(v, f):
    return [ v[0]*f, v[1]*f ]




