# Mantid Repository : https://github.com/mantidproject/mantid
#
# Copyright &copy; 2022 ISIS Rutherford Appleton Laboratory UKRI,
#   NScD Oak Ridge National Laboratory, European Spallation Source,
#   Institut Laue - Langevin & CSNS, Institute of High Energy Physics, CAS
# SPDX - License - Identifier: GPL - 3.0 +

from quasielasticbayes.python.fortran_python import *
from quasielasticbayes.python.constants import *
from quasielasticbayes.python.four import *
from quasielasticbayes.python.bayes import *
from math import pi
import numpy as np
from scipy.interpolate import interp1d
"""
<numerical recipes routines>****************************************
"""
def SPLINE(X,Y,N,YP1,YPN,Y2):
      """
      X,Y are vals
      YP1 is the derivative at start
      YPN is the '' at end
      Y2 is the list of second derivatives
      """
      return interp1d(X.output(), Y.output(), kind='cubic')

      NMAX=10000
      U = vec(NMAX)
      if YP1 > .99E30:
        Y2.set(1,0.)
        U.set(1,0.)
      else:
        Y2.set(1,-0.5)
        U.set(1,(3./(X(2)-X(1)))*((Y(2)-Y(1))/(X(2)-X(1))-YP1))
      
      for I in get_range(2,N-1):
        SIG=(X(I)-X(I-1))/(X(I+1)-X(I-1))
        P=SIG*Y2(I-1)+2.
        Y2.set(I,(SIG-1.)/P)
        U.set(I,(6.*((Y(I+1)-Y(I))/(X(I+1)-X(I))-(Y(I)-Y(I-1))/(X(I)-X(I-1)))/(X(I+1)-X(I-1))-SIG*U(I-1))/P)

      QN, UN = 0,0
      if YPN <= .99E30:
        QN=0.5
        UN=(3./(X(N)-X(N-1)))*(YPN-(Y(N)-Y(N-1))/(X(N)-X(N-1)))

      Y2.set(N,(UN-QN*U(N-1))/(QN*Y2(N-1)+1.))
      for K in get_range(N-1,1,-1):
        Y2.set(K,Y2(K)*Y2(K+1)+U(K))


def SPLINT(X, func):
      return func(X)

      KLO=1
      KHI=N
      while KHI-KLO <= 1:
        K=(KHI+KLO)/2
        if XA(K) > X:
          KHI=K
        else:
          KLO=K

      H=XA(KHI)-XA(KLO)
      if H==0:
         raise ValueError('Bad XA input.')
      A=(XA(KHI)-X)/H
      B=(X-XA(KLO))/H
      Y=A*YA(KLO)+B*YA(KHI)+((A**3-A)*Y2A(KLO)+(B**3-B)*Y2A(KHI))*(H**2)/6.

def XGINIT(XB,YB,NB,YMAX,LST, COMS, store, lptfile):
      #INCLUDE 'res_par.f90'
      #INCLUDE 'mod_files.f90'
      #COMMON /FFTCOM/ FRES(m_d2),FWRK(m_d2),XJ(m_d),TWOPIK(m_d1),NFFT
      #COMMON /DATCOM/ XDAT(m_d),DAT(m_d),SIG(m_d),NDAT
      #REAL    XB(*),YB(*)
      #logical LST
      XDMIN=COMS["DATA"].XDAT(1)
      XDMAX=COMS["DATA"].XDAT(COMS["DATA"].NDAT)
      Y0=YMAX/10.0
      # these two check seem to be finiding the first y value greater than some ref value
      # that is also before the x range
      def check_data_from_below(XB, YB, Y0, XDMIN, I):
           return YB(I)>=Y0 and XB(I)>XDMIN
      I = find_index((XB, YB, Y0, XDMIN),1, NB, check_data_from_below)

      XMIN=XB(I)
      def check_data_from_above(XB, YB, Y0, XDMAX, I):
          return YB(I)>=Y0 and XB(I)<XDMAX
      I = find_index((XB, YB, Y0, XDMAX),NB,1, check_data_from_above, step=-1)
      XMAX=XB(I)

      # this section seems to get values for FFT
      BWIDTH=XMAX-XMIN
      DXJ=BWIDTH/20.0

      AXMAX=abs(COMS["DATA"].XDAT(1))
      if abs(COMS["DATA"].XDAT(COMS["DATA"].NDAT))>AXMAX:
         AXMAX=abs(COMS["DATA"].XDAT(COMS["DATA"].NDAT))
      XNDMAX=500.0
      if COMS["DATA"].NDAT > int(XNDMAX):
         XNDMAX=float(COMS["DATA"].NDAT)

      DXDAT=2.0*AXMAX/XNDMAX
      if DXDAT>DXJ:
         DXJ=DXDAT

      XNGD=(2.0*AXMAX)/DXJ
      NGD=NINT(np.log(XNGD-1.0)/np.log(2.0))+1
      NGD=pow(2,NGD)
      
      if NGD>m_d:
       store.open(53,lptfile)
       store.write(53,' ERROR in XGINIT : too many points')
       store.close(unit=53)
       return
      COMS["FFT"].NFFT=NGD

      # set FFT XJ values
      COMS["FFT"].XJ.set(1, -DXJ*float(COMS["FFT"].NFFT/2))
      for j in get_range(2,COMS["FFT"].NFFT):
          COMS["FFT"].XJ.set(j,COMS["FFT"].XJ(j-1)+DXJ)
      # get the energy range
      XMIN=XMIN-5.0*BWIDTH
      XMAX=XMAX+5.0*BWIDTH
      if XMIN<XB(1):
         XMIN=XB(1)
      if XMAX>XB(NB):
         XMAX=XB(NB)
      if XMIN<XDMIN:
         XMIN=XDMIN
      if XMAX>XDMAX:
         XMAX=XDMAX
      if LST:
       store.open(53,lptfile)

       store.write(53,f' Resolution Range: {XMIN} to {XMAX} ueV')
       store.close(unit=53)
      
      # get x range -> via indices
      def check_data_x_min(XB, XMIN, I):
          return  XB(I)>=XMIN
      I = find_index((XB, XMIN),1,NB, check_data_x_min)
      IMIN=I

      def check_data_x_max(XB, XMAX, I):
          return  XB(I)<=XMAX
      I = find_index((XB, XMAX),NB, 1,check_data_x_max,step=-1)
      IMAX=I

      B1=0.0
      B2=0.0
      # get mean value for 5 bins (that are in range) closest to min/max
      for I in get_range(1,5):
        B1=B1+YB(IMIN+I-1)
        B2=B2+YB(IMAX-I+1)
      B1=B1/5.0
      B2=B2/5.0
      DB=(B2-B1)/float(max(IMAX-IMIN-4,1)) # no idea where the 4 comes from
      B=B1
      # set uniform increase in YB
      for I in get_range(IMIN,IMAX):
        YB.set(I, YB(I)-B)
        B=B+DB
      return XMIN, XMAX, YB

"""
***<set up blur function>**********************************************
"""
def BINBLR(WX,WY,WE,NB,NBIN):
      #INCLUDE 'mod_files.f90'
      #REAL WX(*),WY(*),WE(*),XB(*),YB(*)
      """
      Original dat is W* and the output is *B
      It seems to just be a rebin alg
      """
      XB = vec(NB)
      YB = vec(NB)
      N=0
      SMALL=1.0E-20
      BNORM=1.0/float(NBIN)

      for I in get_range(1,NB,NBIN): # new binning
        N=N+1
        XXD=0.0
        DD=0.0
        K=0
        for J in get_range(0,NBIN-1): # loop over bins in new bin
         IJ=I+J
         if IJ<=NB:

            XXD=XXD+WX(IJ)
            if WE(IJ) > SMALL: # only include non-zero errors
              K=K+1
              DD=DD+WY(IJ)

         XB.set(N,BNORM*XXD)
         YB.set(N,0.0)
         if K>0:
            YB.set(N,BNORM*DD) # normalise data
      NB=N
      return XB, YB

def BLRINT(NB,IREAD,IDUF,COMS,store,lptfile):
      #INCLUDE 'res_par.f90'
      #INCLUDE 'mod_files.f90'
      #COMMON /FFTCOM/ FRES(m_d2),FWRK(m_d2),XJ(m_d),TWOPIK(m_d1),NFFT
      #COMMON /FITCOM/ FIT(m_d),RESID(m_d),NFEW,FITP(m_p),EXPF(m_d1,6)
      #COMMON /DATCOM/ XDAT(m_d),DAT(m_d),SIG(m_d),NDAT
      #COMMON/ModRes/ntr,xres,yres,eres,nrbin,ermin,ermax
      #REAL XB(m_d),YB(m_d),DER2(m_d),xr(m_d),yr(m_d),er(m_d)
      #real xres(m_d),yres(m_d),eres(m_d)
      #LOGICAL  LSTART
      #DATA     LSTART /.FALSE./
      DER2 = vec(m_d)
      LSTART = True
      if IREAD==0:
         LSTART=False

      SMALL=1.0E-20
      COMS["FFT"].NFFT=m_d
      xr = vec(m_d)
      yr = vec(m_d)
      er = vec(m_d)

      xr.copy(COMS["Res"].xres.output_range(1,NB))
      yr.copy(COMS["Res"].yres.output_range(1,NB))
      er.copy(COMS["Res"].eres.output_range(1,NB))
      XB, YB = BINBLR(xr,yr,er,NB,COMS["Res"].nrbin)
     
      XDMIN=COMS["DATA"].XDAT(1)
      XDMAX=COMS["DATA"].XDAT(COMS["DATA"].NDAT)
      YMAX=0.0
      YSUM=0.0
      # get total and max Y binned values within valid x range
      for I in get_range(1,NB):
        if XB(I) >= XDMIN or XB(I)<= XDMAX: 
           if YB(I)>YMAX:
              YMAX=YB(I)
           YSUM=YSUM+YB(I)

      if YSUM<SMALL:
       store.open(53,lptfile)
       store.write(53,' Ysum is too small')
       IDUF=1
       store.close(unit=53)
       return

      XBMIN, XBMAX, YB = XGINIT(XB,YB,NB,YMAX,LSTART, COMS,store, lptfile) # subtracts BG off YB
      # populate FRES with spline of binned data -> data to FFT later
      func=SPLINE(XB,YB,NB,0.0,0.0,DER2)
      TWOPIN=2.0*3.141592654/float(COMS["FFT"].NFFT)
      COMS["FFT"].FRES.fill(0.0, COMS["FFT"].NFFT)
      XX=0.0
      DXJ=COMS["FFT"].XJ(2)-COMS["FFT"].XJ(1)
      COMS["FFT"].FRES.set(1,SPLINT(XX,func))
      SUM=COMS["FFT"].FRES(1)
      for I in get_range(1,int(COMS["FFT"].NFFT/2)):
        XX=XX+DXJ
        if XX < XBMAX:
           COMS["FFT"].FRES.set(I+1,SPLINT(XX,func))
        if -XX > XBMIN:
           COMS["FFT"].FRES.set(COMS["FFT"].NFFT+1-I,SPLINT(-XX,func))
        SUM+=COMS["FFT"].FRES(I+1)+COMS["FFT"].FRES(COMS["FFT"].NFFT+1-I)
        COMS["FFT"].TWOPIK.set(I,TWOPIN*float(I-1)) # looks to be the phase
      COMS["FFT"].TWOPIK.set(int(COMS["FFT"].NFFT/2)+1,TWOPIN*float(COMS["FFT"].NFFT/2))
      BNORM=1./(SUM*float(COMS["FFT"].NFFT))
      #for I in get_range(1,COMS["FFT"].NFFT):
      #  COMS["FFT"].FRES.set(I,BNORM*COMS["FFT"].FRES(I))
      tmp = COMS["FFT"].FRES.output_range(1,COMS["FFT"].NFFT)
      tmp = tmp*BNORM
      COMS["FFT"].FRES.copy(tmp)
      out = FOUR2(COMS["FFT"].FRES, COMS["FFT"].NFFT,1,1,0)
      COMS["FFT"].FRES.copy(flatten(out))
      # some rotations?
      for I in get_range(3,COMS["FFT"].NFFT,4):
        COMS["FFT"].FRES.set(I,-COMS["FFT"].FRES(I))
        COMS["FFT"].FRES.set(I+1, -COMS["FFT"].FRES(I+1))
      
      if not LSTART:
        tmp = COMS["FFT"].FRES.output_range(end=COMS["FFT"].NFFT+2)
        COMS["FFT"].FWRK.copy(tmp)
        #print( COMS["FFT"].FWRK(1), COMS["FFT"].FWRK(2), COMS["FFT"].FWRK(3), COMS["FFT"].FWRK(4))
        out = FOUR2(COMS["FFT"].FWRK,COMS["FFT"].NFFT,1,-1,-1)
        COMS["FFT"].FWRK.copy(flatten(out[0:m_d2]))
        #print( out[0], out[1], out[2], out[3])
        #print( COMS["FFT"].FWRK(1), COMS["FFT"].FWRK(2), COMS["FFT"].FWRK(3), COMS["FFT"].FWRK(4))
      LSTART= True
      return XB, YB