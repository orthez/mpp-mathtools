import sys
import numpy as np
from numpy import dot
from itertools import combinations
from cvxpy import *
from math import acos,cos,sin,atan2
from mathtools.polytope import Polytope
from scipy.spatial import ConvexHull
import psutil
import os

def memory_usage_psutil():
    # return the memory usage in MB
    process = psutil.Process(os.getpid())
    mem = process.get_memory_info()[0] / float(2 ** 20)
    return mem

def PCAprojectionOnList(X):
        return PCAprojection(specialListToNumpy(X))

def specialListToNumpy(X):
        N = len(X[0][0])
        M = len(X)

        xx = np.zeros((N,M))
        for j in range(0,M):
                for i in range(0,N):
                        xx[i,j] = X[j][0][i]
        return xx

def listToNumpy(X):
        N = len(X[0])
        M = len(X)

        xx = np.zeros((N,M))
        for j in range(0,M):
                for i in range(0,N):
                        xx[i,j] = X[j][i]
        return xx

def findProjectionMatrixArray(XL,XR):

        objfunc = 0
        ## M: number of points, N: dimension
        M = XL.shape[0] 
        N = XL.shape[1]
        A = Variable(N,N)
        for i in range(0,M):
                objfunc += sum_squares(A*XL[i,:]-XR[i,:])
        objective = Minimize(objfunc)

        prob = Problem(objective, [])

        d = sqrt(pow(prob.solve(solver=SCS),2)).value
        return [np.array(A.value),d]

def findProjectionMatrix(xl,xr):
        N = len(xl)
        A = Variable(N,N)
        objfunc = sum_squares(A*xl-xr)
        objective = Minimize(objfunc)
        constraints = []

        prob = Problem(objective, constraints)
        d = sqrt(abs(prob.solve())).value
        return [np.array(A.value),d]

def projectOnSmallestSubspace(X):
        X=specialListToNumpy(X)
        N = X.shape[0]
        M = X.shape[1]

        if M<=2:
                ## only one or two points
                return X
        else:
                ## try to find one hyperplane which fits
                V = 1
                A = Variable(V,N)
                b = Variable(V)


                objfunc = sum_squares(A*X[:,0]-b)
                for i in range(0,M):
                        objfunc = objfunc+sum_squares(A*X[:,i]-b)
                objective = Minimize(objfunc)
                constraints = []

                prob = Problem(objective, constraints)
                d = sqrt(abs(prob.solve())).value
                print "2d projection:",d


def PCAprojection(xx):

        N = xx.shape[0]
        M = xx.shape[1]

        ## normalize and centering
        for i in range(0,N):
                xd = 0
                for j in range(0,M):
                        xd = xd+xx[i,j]
                xd = xd/N
                for j in range(0,M):
                        xx[i,j]=xx[i,j]-xd

        [U,S,V]=np.linalg.svd(xx)
        uu = np.around(U,2)

        #print "size xx:",xx.shape
        #print "eigenvalues:",np.around(S,2)
        ##take the first three orthonormal bases
        X1 = uu[:,0]
        X2 = uu[:,1]
        X3 = uu[:,2]

        Xproj = np.zeros((3,M))
        for i in range(0,M):
                xtmp = np.dot(X1.T,xx[:,i])
                ytmp = np.dot(X2.T,xx[:,i])
                ztmp = np.dot(X3.T,xx[:,i])
                Xproj[0,i] = xtmp
                Xproj[1,i] = ytmp
                Xproj[2,i] = ztmp

        X = Xproj[0,:]
        Y = Xproj[1,:]
        Z = Xproj[2,:]

        return [X,Y,Z,np.around(S,2)]



def intersection(p1, p2):
        N1=p1.numberOfHalfspaces()
        N2=p2.numberOfHalfspaces()
        ##A intersection object box A_iob
        A_iob = np.zeros((N1+N2,3))
        b_iob = np.zeros((N1+N2,1))

        for j in range(0,N1):
                A_iob[j,:]=p1.A[j]
                b_iob[j]=p1.b[j]

        for j in range(0,N2):
                A_iob[j+N1,:]=p2.A[j]
                b_iob[j+N1] = p2.b[j]

        return Polytope(A_iob, b_iob)

def maxDistanceBetweenVertices(V):
        maxD = 0
        for i in range(0,len(V)):
                for j in range(i+1,len(V)):
                        vi = V[i]
                        vj = V[j]
                        d=np.linalg.norm(vi-vj)
                        if d>maxD:
                                maxD = d
        return maxD


def sortVertices2D(vertices):
        mean = np.zeros((2,1))
        V = np.zeros((len(vertices),2))
        theta = np.zeros((len(vertices),1))
        for i in range(0,len(vertices)):
                mean[0] = mean[0]+vertices[i][0]
                mean[1] = mean[1]+vertices[i][1]
        mean[0]=mean[0]/len(vertices)
        mean[1]=mean[1]/len(vertices)

        for i in range(0,len(vertices)):
                V[i,0]=vertices[i][0]
                V[i,1]=vertices[i][1]
                theta[i] = atan2(V[i,1]-mean[1],V[i,0]-mean[0])
        ## sort vertices clockwise order:
        Iv = np.argsort(theta.T)
        return V[Iv][0]

def getRotationMatrixAligningHyperplaneAndXYPlane(ap, bp):
        z=np.zeros((3,1))
        z[2]=1
        y=np.zeros((3,1))
        y[1]=1
        x=np.zeros((3,1))
        x[0]=1
        #########################
        axy = ap - (dot(ap.T,z))*z
        axynorm = np.linalg.norm(axy)
        if axynorm > 0:
                axy = axy/axynorm
                dya = dot(y.T,axy)
                if dya > 0.01:
                        txy = acos(dya)
                else:
                        txy = 0
        else:
                txy = 0
        #########################
        azy = ap - (dot(ap.T,x))*x
        azynorm = np.linalg.norm(azy)
        if azynorm > 0:
                azy = azy/azynorm
                dza = dot(z.T,azy)
                if dza > 0.01:
                        tzy = acos(dza)
                else:
                        tzy = 0
        else:
                tzy = 0
        #########################
        RX = np.zeros((3,3))
        RX[0,0]=1
        RX[1,1]=cos(txy)
        RX[1,2]=-sin(txy)
        RX[2,1]=sin(txy)
        RX[2,2]=cos(txy)

        RZ = np.zeros((3,3))
        RZ[2,2]=1
        RZ[0,0]=cos(tzy)
        RZ[0,1]=-sin(tzy)
        RZ[1,0]=sin(tzy)
        RZ[1,1]=cos(tzy)
        R = dot(RX,RZ)
        return R

def getMeanFromVerticesList(V):
        M = len(V[0])
        N = len(V)
        mean = np.zeros((M,1))
        for i in range(0,N):
                for j in range(0,M):
                        mean[j] += V[i][j]
        mean /= N
        return mean

def getMeanFromVerticesNumpy(V):
        mean = np.zeros((V.shape[1],1))
        for i in range(0,V.shape[0]):
                for j in range(0,V.shape[1]):
                        mean[j] += V[i,j]

        mean /= V.shape[0]
        return mean

def projectPointOntoHyperplane(v, a, b):
        #a=a[0]
        assert len(a)==3
        return v - (dot(v,a) - b)*a

def distancePointHyperplane(v, a, b):
        assert len(a)==3
        vprime = v - (dot(v,a) - b)*a
        return np.linalg.norm(vprime-v)

def distancePointWalkableSurface(v, W):
        xob = Variable(3)
        objective = Minimize(sum_squares(xob  - v ))

        AsurfaceX = W.ap
        bsurfaceX = W.bp
        ApolyX =    W.A
        bpolyX =    W.b

        constraints = []

        constraints.append(np.matrix(ApolyX)*xob <= bpolyX)
        constraints.append(np.matrix(AsurfaceX)*xob == bsurfaceX)

        prob = Problem(objective, constraints)
        return sqrt(abs(prob.solve())).value

def getNearestWalkableSurfacesFromStartGoalPoint(xstart, xgoal, Wsurfaces):
        startWS = -1
        goalWS = -1
        ds = 10000
        dg = 10000
        for i in range(0,len(Wsurfaces)):
                W = Wsurfaces[i]
                dds = distancePointWalkableSurface(xstart, W)
                ddg = distancePointWalkableSurface(xgoal, W)
                if dds < ds:
                        ds = dds
                        startWS = i
                if ddg < dg:
                        dg = ddg
                        goalWS = i

        dg = np.around(dg,3)
        ds = np.around(ds,3)
        if dg>0.5 or ds>0.5:
                print "=============================================================="
                print "[ERROR]"
                print "=============================================================="
                print "start or goal contact too far away from walkable surfaces:"
                print "goal:",xgoal,"mindist:",dg
                print "start:",xstart,"mindist:",ds
                print "=============================================================="
                sys.exit(0)
        return [startWS,goalWS]

def projectPointOntoPolytopeNdim(X, Ai, bi):
        xob = Variable(X.shape[0],1)
        objective = Minimize(sum_squares(xob  - X))
        constraints = [np.matrix(Ai)*xob <= bi]
        prob = Problem(objective, constraints)
        d = prob.solve(solver=SCS)
        return np.array(xob.value)

def projectPointOntoPolytope(v, Ai, bi):
        xob = Variable(3)
        objective = Minimize(sum_squares(xob  - v))
        constraints = [np.matrix(Ai)*xob <= bi]
        prob = Problem(objective, constraints)
        prob.solve()
        return xob.value

def projectPointOntoWalkableSurface(v, W):
        xob = Variable(3)
        objective = Minimize(sum_squares(xob  - v ))

        AsurfaceX = W.ap
        bsurfaceX = W.bp
        ApolyX =    W.A
        bpolyX =    W.b

        constraints = []

        constraints.append(np.matrix(ApolyX)*xob <= bpolyX)
        constraints.append(np.matrix(AsurfaceX)*xob == bsurfaceX)

        prob = Problem(objective, constraints)
        prob.solve()
        return xob.value

def distancePointPolytope(v, A, b):
        xob = Variable(3)
        objective = Minimize(sum_squares(xob  - v ))
        constraints = [np.matrix(A)*xob <= b]
        prob = Problem(objective, constraints)
        return sqrt(abs(prob.solve())).value

#def distancePolytopePolytope(Ai, bi, Aj, bj):
def distancePolytopePolytope(Pi, Pj):
        N = Pi.A.shape[1]
        Ai = Pi.A
        bi = Pi.b
        Aj = Pj.A
        bj = Pj.b
        xob = Variable(N)
        yob = Variable(N)
        objective = Minimize(sum_squares(xob  - yob ))
        #constraints = [np.dot(Ai,xob)<= bi,np.dot(Aj,yob) <= bj]
        constraints = [np.matrix(Ai)*xob<= bi,np.matrix(Aj)*yob <= bj]
        prob = Problem(objective, constraints)
        d= sqrt(pow(prob.solve(solver=SCS),2)).value
        return d

def distancePolytopePolytopeNdim(Pi, Pj):
        Ai = Pi.A
        bi = Pi.b
        Aj = Pj.A
        bj = Pj.b
        N = Ai.shape[1]
        xob = Variable(N,1)
        yob = Variable(N,1)
        objective = Minimize(sum_squares(xob  - yob ))
        #constraints = [np.dot(Ai,xob)<= bi,np.dot(Aj,yob) <= bj]
        constraints = [np.matrix(Ai)*xob<= bi,np.matrix(Aj)*yob <= bj]
        prob = Problem(objective, constraints)
        return sqrt(abs(prob.solve())).value

def distanceWalkableSurfacePolytope(W, A, b):
        xob = Variable(3)
        yob = Variable(3)
        objective = Minimize(sum_squares(xob  - yob ))

        AsurfaceX = W.ap
        bsurfaceX = W.bp
        ApolyX =    W.A
        bpolyX =    W.b

        constraints = []

        constraints.append(np.matrix(ApolyX)*xob <= bpolyX)
        constraints.append(np.matrix(AsurfaceX)*xob == bsurfaceX)

        constraints.append(np.matrix(A)*yob <= b)

        prob = Problem(objective, constraints)
        return sqrt(abs(prob.solve())).value

def distanceWalkableSurfaceWalkableSurface(Wi, Wj):

        xob = Variable(3)
        yob = Variable(3)
        objective = Minimize(sum_squares(xob  - yob ))

        AsurfaceX = Wi.ap
        bsurfaceX = Wi.bp
        ApolyX =    Wi.A
        bpolyX =    Wi.b

        AsurfaceY = Wj.ap
        bsurfaceY = Wj.bp
        ApolyY =    Wj.A
        bpolyY =    Wj.b

        constraints = []

        constraints.append(np.matrix(ApolyX)*xob <= bpolyX)
        constraints.append(np.matrix(AsurfaceX)*xob == bsurfaceX)

        constraints.append(np.matrix(ApolyY)*yob <= bpolyY)
        constraints.append(np.matrix(AsurfaceY)*yob == bsurfaceY)

        prob = Problem(objective, constraints)
        return sqrt(abs(prob.solve())).value

def distanceWalkableSurfaceHyperplane(W, ai, bi):
        xob = Variable(3)
        yob = Variable(3)
        objective = Minimize(sum_squares(xob  - yob ))

        AsurfaceX = W.ap
        bsurfaceX = W.bp
        ApolyX =    W.A
        bpolyX =    W.b

        constraints = []

        constraints.append(np.matrix(ApolyX)*xob <= bpolyX)
        constraints.append(np.matrix(AsurfaceX)*xob == bsurfaceX)

        #constraints.append(ai[0]*yob[0]+ai[1]*yob[1]+ai[2]*yob[2]== bi)
        constraints.append(np.matrix(ai)*yob == bi)

        prob = Problem(objective, constraints)
        d = sqrt(abs(prob.solve())).value
        xx = None
        if xob.value is not None:
                xx = np.zeros((3,1))
                x=xob.value
                xx[0]=x[0]
                xx[1]=x[1]
                xx[2]=x[2]
        return [d,xx]

def hyperplanesToVertices(A,b):
        M = A.shape[0]
        N = A.shape[1]

        vertices = []
        for rowlist in combinations(range(M), N):
                Ap = A[np.ix_(rowlist,range(0,N))]
                bp = b[np.ix_(rowlist)]
                if np.linalg.det(Ap) != 0:
                        xp = np.linalg.solve(Ap,bp)
                        #keep care of numerical instabilities 
                        # by adding an offset to b
                        P = np.less_equal(dot(A,xp),b+0.0001)
                        if P.all():
                                vertices.append(xp)

        if len(vertices)==0:
                #print "[WARNING] number of vertices for object is NULL"
                return []

        return vertices


def Rz(t):
        return np.array([[cos(t),-sin(t),0],[sin(t),cos(t),0],[0,0,1]])
def Ry(t):
        return np.array([[cos(t),0,sin(t)],[0,1,0],[-sin(t),0,cos(t)]])
def Rx(t):
        return np.array([[1,0,0],[0,cos(t),-sin(t)],[0,sin(t),cos(t)]])

def R_RPY(r,p,y):
        R_y = Rz(y)
        R_p = Ry(p)
        R_r = Rx(r)
        return np.dot(R_r,np.dot(R_p,R_y))


def boxToPts(x,y,z,ro,po,yo,sx,sy,sz):
        R = R_RPY(ro,po,yo)

        p = np.zeros((8,3))
        p[0,:] = [x+sx/2, y+sy/2, z+sz/2]
        p[1,:] = [x+sx/2, y+sy/2, z-sz/2]
        p[2,:] = [x+sx/2, y-sy/2, z+sz/2]
        p[3,:] = [x+sx/2, y-sy/2, z-sz/2]
        p[4,:] = [x-sx/2, y+sy/2, z+sz/2]
        p[5,:] = [x-sx/2, y+sy/2, z-sz/2]
        p[6,:] = [x-sx/2, y-sy/2, z+sz/2]
        p[7,:] = [x-sx/2, y-sy/2, z-sz/2]


        for i in range(0,p.shape[0]):
                p[i,:] = np.dot(R,p[i,:])

        return p

def ptsToPolytope(pts):
        hull = ConvexHull(pts)
        E=hull.equations[0::2]
        Ah = np.array(E[0:,0:3])
        bh = np.zeros((len(Ah),1))
        #bh = np.array((-E[0:,3]))
        for k in range(0,len(Ah)):
                bh[k] = -E[k,3]
        #bh = -E[0:,3]
        ###normalize
        for at in range(0,len(Ah)):
                normA = np.linalg.norm(Ah[at])
                Ah[at] = Ah[at]/normA
                bh[at] = bh[at]/normA
        p = Polytope(Ah,bh,np.mean(pts))
        return p
