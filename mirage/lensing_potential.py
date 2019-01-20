from sympy import symbols
from sympy import atan, atanh
from sympy import sin, cos, sqrt
from sympy import simplify
from sympy import diff

t1, t2 = symbols('t1 t2')
X = t1
Y = t2
b, q, E_theta = symbols('b q E')
gam, gam_phi = symbols('g p')
E = E_theta
# X = t1*sin(E)+t2*cos(E)
# Y = t2*sin(E) - t1*cos(E)
a2E = simplify(b*atanh(Y*sqrt(1-q*q)/sqrt(X*X*q*q+Y*Y))/sqrt(1-q*q))
a1E = simplify(b*atan(X*sqrt(1-q*q)/sqrt(X*X*q*q+Y*Y))/sqrt(1-q*q))
r2 = t1*t1+t2*t2
phi = atan(t2/t1)
psi = t1*a1E + t2*a2E + gam*r2*cos(phi - (gam_phi - E))/2
psi_sim = simplify(psi) 
d2psid2t1 = simplify(diff(psi_sim,t1,2))
d2psid2t2 = simplify(diff(psi_sim,t2,2))
d2psidt1dt2 = simplify(diff(diff(psi_sim,t1),t2))
kap = simplify((d2psid2t2 + d2psid2t1)/2)
g1 = simplify((d2psid2t1 - d2psid2t2)/2)
g2 = simplify(d2psidt1dt2)
shear = sqrt(g1*g1 + g2*g2)


#CONVERGENCE RESULT SIMPLIFIED:
# (-2*b*q*sqrt(-q**2 + 1)*sqrt(q**2*t1**2 + t2**2) + 3*g*q**4*t1**2*cos(E - p + atan(t2/t1)) - 3*g*q**2*t1**2*cos(E - p + atan(t2/t1)) + 3*g*q**2*t2**2*cos(E - p + atan(t2/t1)) - 3*g*t2**2*cos(E - p + atan(t2/t1)))/(4*(q**4*t1**2 - q**2*t1**2 + q**2*t2**2 - t2**2))


#SHEAR RESULT:
	# NOT SIMPLIFIED:
	# sqrt(t1**2*(2*b*q*t2*sqrt(-q**2 + 1)*(t1**2 + t2**2)*sqrt(q**2*t1**2 + t2**2) + g*sqrt((t1**2 + t2**2)/t1**2)*(t1**2*(-q**4*t1**3*sin(E - p) + q**4*t2**3*cos(E - p) + q**2*t1**3*sin(E - p) - q**2*t1*t2**2*sin(E - p) - q**2*t2**3*cos(E - p) + t1*t2**2*sin(E - p)) + t2**5*(q**2 - 1)*cos(E - p)))**2/(4*(t1**2 + t2**2)**2*(q**4*t1**4 + q**4*t1**2*t2**2 - q**2*t1**4 + q**2*t2**4 - t1**2*t2**2 - t2**4)**2) + (b*q*t1**2*sqrt(-q**2 + 1)*sqrt(q**2*t1**2 + t2**2)/2 - b*q*t2**2*sqrt(-q**2 + 1)*sqrt(q**2*t1**2 + t2**2)/2 + g*q**4*t1**4*cos(E - p + atan(t2/t1))/4 + g*q**4*t1**3*t2*sin(E - p + atan(t2/t1)) - g*q**4*t1**2*t2**2*cos(E - p + atan(t2/t1))/4 - g*q**2*t1**4*cos(E - p + atan(t2/t1))/4 - g*q**2*t1**3*t2*sin(E - p + atan(t2/t1)) + g*q**2*t1**2*t2**2*cos(E - p + atan(t2/t1))/2 + g*q**2*t1*t2**3*sin(E - p + atan(t2/t1)) - g*q**2*t2**4*cos(E - p + atan(t2/t1))/4 - g*t1**2*t2**2*cos(E - p + atan(t2/t1))/4 - g*t1*t2**3*sin(E - p + atan(t2/t1)) + g*t2**4*cos(E - p + atan(t2/t1))/4)**2/(q**4*t1**4 + q**4*t1**2*t2**2 - q**2*t1**4 + q**2*t2**4 - t1**2*t2**2 - t2**4)**2)
	# SIMPLIFIED	
	# sqrt((4*t1**2*(2*b*q*t2*sqrt(-q**2 + 1)*(t1**2 + t2**2)*sqrt(q**2*t1**2 + t2**2) - g*sqrt((t1**2 + t2**2)/t1**2)*(t1**2*(q**4*t1**3*sin(E - p) - q**4*t2**3*cos(E - p) - q**2*t1**3*sin(E - p) + q**2*t1*t2**2*sin(E - p) + q**2*t2**3*cos(E - p) - t1*t2**2*sin(E - p)) - t2**5*(q**2 - 1)*cos(E - p)))**2 + (t1**2 + t2**2)**2*(-2*b*q*t1**2*sqrt(-q**2 + 1)*sqrt(q**2*t1**2 + t2**2) + 2*b*q*t2**2*sqrt(-q**2 + 1)*sqrt(q**2*t1**2 + t2**2) - g*q**4*t1**4*cos(E - p + atan(t2/t1)) - 4*g*q**4*t1**3*t2*sin(E - p + atan(t2/t1)) + g*q**4*t1**2*t2**2*cos(E - p + atan(t2/t1)) + g*q**2*t1**4*cos(E - p + atan(t2/t1)) + 4*g*q**2*t1**3*t2*sin(E - p + atan(t2/t1)) - 2*g*q**2*t1**2*t2**2*cos(E - p + atan(t2/t1)) - 4*g*q**2*t1*t2**3*sin(E - p + atan(t2/t1)) + g*q**2*t2**4*cos(E - p + atan(t2/t1)) + g*t1**2*t2**2*cos(E - p + atan(t2/t1)) + 4*g*t1*t2**3*sin(E - p + atan(t2/t1)) - g*t2**4*cos(E - p + atan(t2/t1)))**2)/((t1**2 + t2**2)**2*(q**4*t1**4 + q**4*t1**2*t2**2 - q**2*t1**4 + q**2*t2**4 - t1**2*t2**2 - t2**4)**2))/4
