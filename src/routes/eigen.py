import numpy as np
def to_js_complex_array(arr):
	return [[{"re": z.real, "im": z.imag, "ang": np.angle(z), "mag": np.abs(z)} for z in row] for row in arr]
L = np.array(L)
vals, vecs = np.linalg.eig(L)
vals_list = [{"re": z.real, "im": z.imag, "ang": np.angle(z), "mag": np.abs(z)} for z in vals]
vecs_list = to_js_complex_array(vecs)