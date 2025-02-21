# -*- coding: utf-8 -*-
"""PyNav module containing coordinate transformation utilities.

Description of module coming soon...

"""

# System imports:
import numpy as np

class Ellipsoid(object):
    r"""Class for handling definition of reference ellipsoids.

    Args:
        semiMajorAxis (float): Semi-major axis of ellipsoid [distance units]
        flattening (float): Flattening factor of ellipsoid [unitless]
        rotationRate (float): Rotation rate of ellipsoid [radians/time units]

    Attributes:
        a (float): Semi-major axis of ellipsoid [distance units]
        f (float): Flattening factor of ellipsoid [unitless]
        w (float): Rotation rate of ellipsoid [radians/time units]

    """
    def __init__(self,semiMajorAxis=0,flattening=0,rotationRate=0):

        # Store defining parameters:
        self.a = semiMajorAxis  # Semi-major axis [distance units]
        self.f = flattening     # Flattening (oblateness) [-]
        self.w = rotationRate   # Rotation rate [radians/time units]

        # Compute derived parameters:
        self.b  = self.a - self.a*self.f               # Semi-minor axis         [distance units]
        self.e  = np.sqrt(1 - (self.b**2/self.a**2))   # First eccentricity      [-]
        self.ee = np.sqrt((self.a**2/self.b**2) - 1)   # Second eccentricity     [-]
        self.r  = (self.a**2*self.b)**( 1./3)          # Geometric mean radius   [distance units]

WGS84 = Ellipsoid(semiMajorAxis=6378137.0,flattening=1/298.257223563,rotationRate=7292115.0e-11)
"""Ellipsoid: Module-level variable defining World Geodetic System 1984 (WGS84) ellipsoid.

Note:
    Defined in Department of Defense (DoD) Tech Report NIMA TR8350.2 (revised in 2000), WGS84 is
    the official ellipsoid standard for all mapping, charting, navigation, and geodetic products
    used throughout the DoD.

        WGS84 is a realization of the conventional terrestrial reference
        system (CTRS) developed by the Defense Mapping Agency (DMA), which became in 1996 a part of
        the National Imagery and Mapping Agency (NIMA), of the U.S. [DoD], and reorganized in 2004 as
        the National Geospatial-Intelligence Agency (NGA)...the widespread use of GPS is turning WGS84
        from a global datum into an international datum, a *de facto* world standard.

        -- Misra, P. and Enge, P., "Global Positioning System: Signals, Measurements,
        and Performance," Revised Second Edition, Ganga-Jamuna Press, 2012, Sec. 4.1.3.

"""

def llh2ecef(llh,degrees=True,ellipsoid=WGS84):
    r"""Convert latitude/longitude/height (LLH) ellipsoid coordinates to Earth-centered,
    Earth-fixed (ECEF) Cartesian coordinates via the coordinate transformation :cite:`MiEn12`:

    .. math::
        x &= (N + h)\cos(\phi)\cos(\lambda) \\
        y &= (N + h)\cos(\phi)\sin(\lambda) \\
        z &= [N(1 - e^2) + h]\sin(\phi)

    where :math:`(\phi,\lambda,h)` are geodetic latitude, longitude, and ellipsoid
    height, :math:`e` is the ellipsoid eccentricity, and :math:`N` is the meridian
    ellipse distance given by :cite:`MiEn12`:

    .. math:: N = \frac{a}{\sqrt{1 - e^2\sin^2(\phi)}}

    where :math:`a` is the semi-major axis of the ellipsoid (e.g., 6378137.0 m for WGS84).

    Args:
        llh_0 (np.ndarray): LLH coordinates [height in ellipsoid distance units]
        degrees (bool): Toggles whether latitude/longitude are input in degrees
        ellipsoid (Ellipsoid): Ellipsoid definition to use for coordinate conversion

    Returns:
        np.ndarray: ECEF coordinates [ellipsoid distance units]

    """
    # Extract latitude/longitude/height:
    if degrees: llh = [np.deg2rad(llh[0]),np.deg2rad(llh[1]),llh[2]]
    lat,lon,h = llh

    # Radius of curvature in prime vertical [Misra/Enge, Eq. 4.A.1]:
    N = ellipsoid.a/np.sqrt(1 - ellipsoid.e**2*np.sin(lat)**2)

    # Compute ECEF coordinates [Misra/Enge, Eq. 4.A.2]:
    x = (N + h)*np.cos(lat)*np.cos(lon)
    y = (N + h)*np.cos(lat)*np.sin(lon)
    z = (N*(1 - ellipsoid.e**2) + h)*np.sin(lat)

    # Return result as np.ndarray:
    ecef = np.array([x,y,z])
    return ecef

def ecef2llh(ecef,degrees=True,ellipsoid=WGS84):
    r"""Convert Earth-centered, Earth-fixed (ECEF) Cartesian coordinates to
    latitude/longitude/height (LLH) ellipsoid coordinates.

    Note:
        Uses direct (non-iterative) algorithm from Bowring, B., "The
        accuracy of geodetic latitude and height equations," Survey Review,
        Volume 28, No. 218, October 1985, pp. 202-206.

    Args:
        ecef (np.ndarray): ECEF coordinates [ellipsoid distance units]
        degrees (bool): Toggles whether latitude/longitude are output in degrees
        ellipsoid (Ellipsoid): Ellipsoid definition to use for coordinate conversion

    Returns:
        np.ndarray: Earth-centered, Earth-fixed (ECEF) coordinates [ellipsoid distance units]

    """
    # Ellipsoid parameters:
    a  = ellipsoid.a
    b  = ellipsoid.b
    e2 = ellipsoid.e**2

    # Compute longitude:
    x,y,z = ecef
    lon   = np.arctan2(y,x)

    # Compute latitude and height:
    p   = np.sqrt(x**2 + y**2)
    r   = np.sqrt(p**2 + z**2)
    e   = e2*(a/b)**2
    u   = np.arctan2(b*z*(1 + e*b/r),a*p)
    lat = np.arctan2(z + e*b*np.sin(u)**3,p - e2*a*np.cos(u)**3)
    N   = a/np.sqrt(1 - e2*np.sin(lat)**2)
    h   = p*np.cos(lat) + z*np.sin(lat) - a**2/N

    # Return result as np.ndarray:
    if degrees:
        llh = np.array([np.rad2deg(lat),np.rad2deg(lon),h])
    else:
        llh = np.array([lat,lon,h])
    return llh

def ecef2enu(ecef,llh_0,degrees=True):
    r"""Convert Earth-centered, Earth-fixed (ECEF) Cartesian coordinates
    to locally-defined east/north/up (ENU) Cartesian coordinates.

    Letting the ECEF coordinates of interest be denoted :math:`^\mathcal{E}\boldsymbol{r}`, and the origin of
    the local ENU frame be defined by the non-linear transformation from latitude/longitude/height ellipsoid
    coordinates :math:`(\phi,\lambda,h)` to ECEF coordinates :math:`^\mathcal{E}\boldsymbol{r}_0`, then the
    locally-defined ENU representation :math:`^\mathcal{L}\boldsymbol{r}` of the ECEF coordinates of interest
    is given by :cite:`MiEn12`:

    .. math:: ^\mathcal{L}\boldsymbol{r} = [\mathcal{LE}](^\mathcal{E}\boldsymbol{r} - ^\mathcal{E}\boldsymbol{r}_0)

    where the direction cosine matrix (DCM) mapping from the ECEF frame to locally-defined ENU frame is given by :cite:`MiEn12`:

    .. math:: [\mathcal{LE}] \equiv
       \left[\array{-\sin(\lambda) & \cos(\lambda) & 0 \\
       -\sin(\phi)\cos(\lambda) & -\sin(\phi)\sin(\lambda) & \cos(\phi) \\
       \cos(\phi)\cos(\lambda) & \cos(\phi)\sin(\lambda) & \sin(\phi)}\right]

    Args:
        ecef (np.ndarray): ECEF coordinates [distance units]
        llh_0 (np.ndarray): LLH coordinates defining origin of local ENU frame
        degrees (bool): Toggles whether latitude/longitude are input in degrees

    Returns:
        np.ndarray: ENU coordinates [distance units]

    """
    # Extract latitude/longitude of frame origin:
    if degrees: llh_0 = [np.deg2rad(llh_0[0]),np.deg2rad(llh_0[1]),llh_0[2]]
    lat,lon,h = llh_0

    # Compute ECEF coordinates of frame origin
    # and DCM from ECEF to the local ENU frame:
    ecef_0   = llh2ecef(llh_0,degrees=False)
    ECEF2ENU = ecef2enu_dcm(llh_0,degrees=False)

    # Perform coordinate transformation:
    diff = np.array(ecef) - ecef_0
    enu  = ECEF2ENU.dot(diff)
    return enu

def enu2ecef(enu,llh_0,degrees=True):
    r"""Convert locally-defined east/north/up (ENU) Cartesian coordinates
    to Earth-centered, Earth-fixed (ECEF) Cartesian coordinates.

    Letting the ENU coordinates of interest be denoted :math:`^\mathcal{L}\boldsymbol{r}`, and the origin of
    the local ENU frame be defined by the non-linear transformation from latitude/longitude/height ellipsoid
    coordinates :math:`(\phi,\lambda,h)` to ECEF coordinates :math:`^\mathcal{E}\boldsymbol{r}_0`, then the
    ECEF representation :math:`^\mathcal{E}\boldsymbol{r}` of the locally-defined ENU coordinates of interest
    is given by :cite:`MiEn12`:

    .. math:: ^\mathcal{E}\boldsymbol{r} = [\mathcal{LE}]^{T}(^\mathcal{L}\boldsymbol{r}) + ^\mathcal{E}\boldsymbol{r}_0

    where the direction cosine matrix (DCM) mapping from the ECEF frame to locally-defined ENU frame is given by :cite:`MiEn12`:

    .. math:: [\mathcal{LE}] \equiv
       \left[\array{-\sin(\lambda) & \cos(\lambda) & 0 \\
       -\sin(\phi)\cos(\lambda) & -\sin(\phi)\sin(\lambda) & \cos(\phi) \\
       \cos(\phi)\cos(\lambda) & \cos(\phi)\sin(\lambda) & \sin(\phi)}\right]

    Args:
        enu (np.ndarray): ENU coordinates [distance units]
        llh_0 (np.ndarray): LLH coordinates defining origin of local ENU frame
        degrees (bool): Toggles whether latitude/longitude are input in degrees

    Returns:
        np.ndarray: ECEF coordinates [distance units]

    """
    # Extract latitude/longitude of frame origin:
    if degrees: llh_0 = [np.deg2rad(llh_0[0]),np.deg2rad(llh_0[1]),llh_0[2]]
    lat,lon,h = llh_0

    # Compute ECEF coordinates of frame origin
    # and DCM from ECEF to the local ENU frame:
    ecef_0   = llh2ecef(llh_0,degrees=False)
    ECEF2ENU = ecef2enu_dcm(llh_0,degrees=False)

    # Perform coordinate transformation and shift from origin:
    ecef = ECEF2ENU.T.dot(enu) + ecef_0
    return ecef

def llh2enu(llh,llh_0,degrees=True,ellipsoid=WGS84):
    r"""Convert latitude/longitude/height (LLH) ellipsoid coordinates
    to locally-defined east/north/up (ENU) Cartesian coordinates.

    Note:
        This function is a wrapper around calls to :func:`llh2ecef` and then :func:`ecef2enu`.

    Args:
        llh (np.ndarray): LLH coordinates [height in ellipsoid distance units]
        llh_0 (np.ndarray): LLH coordinates defining origin of local ENU frame
        degrees (bool): Toggles whether latitude/longitude are input in degrees
        ellipsoid (Ellipsoid): Ellipsoid definition to use for coordinate conversion

    Returns:
        np.ndarray: ENU coordinates [ellipsoid distance units]

    """
    return ecef2enu(llh2ecef(llh,degrees=degrees,ellipsoid=ellipsoid),llh_0,degrees=degrees)

def enu2llh(enu,llh_0,degrees=True,ellipsoid=WGS84):
    r"""Convert locally-defined east/north/up (ENU) Cartesian coordinates
    to latitude/longitude/height (LLH) ellipsoid coordinates.

    Note:
        This function is a wrapper around calls to :func:`enu2ecef` and then :func:`ecef2llh`.

    Args:
        enu (np.ndarray): ENU coordinates [distance units]
        llh_0 (np.ndarray): LLH coordinates defining origin of local ENU frame
        degrees (bool): Toggles whether latitude/longitude are input in degrees
        ellipsoid (Ellipsoid): Ellipsoid definition to use for coordinate conversion

    Returns:
        np.ndarray: LLH coordinates [height in distance units]

    """
    return ecef2llh(enu2ecef(enu,llh_0,degrees=degrees),degrees=degrees,ellipsoid=ellipsoid)


def eci2ric_dcm(posVecECI,velVecECI):
    r"""Return DCM from Earth-centered inertial (ECI) frame to radial/in-track/cross-track (RIC) orbit frame.

    Given inertial position :math:`\boldsymbol{r}` and velocity :math:`\dot{\boldsymbol{r}}` vectors expressed
    in ECI coordinates, the direction cosine matrix mapping from the ECI frame to local RIC frame is given by:

    .. math:: [\mathcal{ON}] = \left[\array{\hat{\boldsymbol{o}}_r^T \\ \hat{\boldsymbol{o}}_i^T \\ \hat{\boldsymbol{o}}_c^T}\right]

    where the unit vectors :math:`\hat{\boldsymbol{o}}_r`, :math:`\hat{\boldsymbol{o}}_i`, and :math:`\hat{\boldsymbol{o}}_c`
    are given by:

    .. math::

       \hat{\boldsymbol{o}}_r &= \frac{\boldsymbol{r}}{\|\boldsymbol{r}\|} \\
       \hat{\boldsymbol{o}}_c &= \frac{\boldsymbol{r} \times \dot{\boldsymbol{r}}}{\|\boldsymbol{r} \times \dot{\boldsymbol{r}}\|} \\
       \hat{\boldsymbol{o}}_i &= \hat{\boldsymbol{o}}_c \times \hat{\boldsymbol{o}}_r

    Args:
        posVecECI (np.ndarray): ECI position coordinates defining local RIC frame [distance units]
        velVecECI (np.ndarray): ECI velocity coordinates defining local RIC frame [distance/time units]

    Returns:
        np.ndarray: Direction cosine matrix (DCM) mapping from ECI frame to RIC frame

    """
    # Radial direction:
    R = posVecECI/np.linalg.norm(posVecECI)

    # Cross-track direction:
    H = np.cross(posVecECI,velVecECI)
    C = H/np.linalg.norm(H)

    # In-track direction:
    I  = np.cross(C,R)
    I /= np.linalg.norm(I)

    # Stack arrays to form DCM:
    ECI2RIC = np.vstack((R,I,C))
    return ECI2RIC


def llh2ecef_dcm(llh_0,degrees=True,ellipsoid=WGS84):
    r"""Return DCM from latitude/longitude/height (LLH) ellipsoid frame
    to Earth-centered, Earth-fixed (ECEF) frame.

    LLH coordinates are converted to ECEF coordinates via the non-linear
    transformation :math:`(\phi,\lambda,h) \rightarrow (x,y,z)` :cite:`MiEn12`:

    .. math::
        x &= (N + h)\cos(\phi)\cos(\lambda) \\
        y &= (N + h)\cos(\phi)\sin(\lambda) \\
        z &= [N(1 - e^2) + h]\sin(\phi)

    where :math:`(\phi,\lambda,h)` are geodetic latitude, longitude, and ellipsoid
    height, :math:`e` is the ellipsoid eccentricity, and :math:`N` is the meridian
    ellipse distance given by :cite:`MiEn12`:

    .. math:: N = \frac{a}{\sqrt{1 - e^2\sin^2(\phi)}}

    The DCM from the LLH frame to ECEF frame is given to first-order by the Jacobian
    matrix containing the partial derivatives of the ECEF coordinates with respect to
    the LLH coordinates, i.e. :cite:`IGP97`,

    .. math:: \frac{\partial (x,y,z)}{\partial (\phi,\lambda,h)} \equiv
       \left[\array{\frac{\partial x}{\partial \phi} & \frac{\partial x}{\partial \lambda} & \frac{\partial x}{\partial h} \\
       \frac{\partial y}{\partial \phi} & \frac{\partial y}{\partial \lambda} & \frac{\partial y}{\partial h} \\
       \frac{\partial z}{\partial \phi} & \frac{\partial z}{\partial \lambda} & \frac{\partial y}{\partial h}}\right]

    Using the non-linear transformation given above, the partial derivatives with
    respect to geodetic latitude :math:`\phi` are given by:

    .. math::
       \frac{\partial x}{\partial \phi} &= -(N + h)\sin(\phi)\cos(\lambda) + \frac{\partial N}{\partial \phi}\cos(\phi)\cos(\lambda) \\
       \frac{\partial y}{\partial \phi} &= -(N + h)\sin(\phi)\sin(\lambda) + \frac{\partial N}{\partial \phi}\cos(\phi)\sin(\lambda) \\
       \frac{\partial z}{\partial \phi} &= [N(1 - e^2) + h]\cos(\phi) + \frac{\partial N}{\partial \phi}(1 - e^2)\sin(\phi) \\

    where

    .. math:: \frac{\partial N}{\partial \phi} = \frac{ae^2\sin(\phi)\cos(\phi)}{\left[1 - e^2\sin^2(\phi)\right]^{3/2}}

    The partial derivatives with respect to geodetic longitude :math:`\lambda` are given by:

    .. math::
       \frac{\partial x}{\partial \lambda} &= -(N + h)\cos(\phi)\sin(\lambda) \\
       \frac{\partial y}{\partial \lambda} &= (N + h)\cos(\phi)\cos(\lambda) \\
       \frac{\partial z}{\partial \lambda} &= 0 \\

    The partial derivatives with respect to ellipsoid height :math:`h` are given by:

    .. math::
       \frac{\partial x}{\partial h} &= \cos(\phi)\cos(\lambda) \\
       \frac{\partial y}{\partial h} &= \cos(\phi)\sin(\lambda) \\
       \frac{\partial z}{\partial h} &= \sin(\phi) \\

    Args:
        llh_0 (np.ndarray): LLH coordinates defining origin of local ENU frame
        degrees (bool): Toggles whether latitude/longitude are input in degrees
        ellipsoid (Ellipsoid): Ellipsoid definition to use for coordinate conversion

    Returns:
        np.ndarray: Direction cosine matrix (DCM) mapping from LLH frame to ECEF frame

    """
    # Extract latitude/longitude of frame origin:
    if degrees: llh_0 = [np.deg2rad(llh_0[0]),np.deg2rad(llh_0[1]),llh_0[2]]
    lat,lon,h = llh_0

    # Radius of curvature in prime vertical [Misra/Enge, Eq. 4.A.1]:
    N        = ellipsoid.a/np.sqrt(1 - ellipsoid.e**2*np.sin(lat)**2)
    dN_dlat  = ellipsoid.a*ellipsoid.e**2*np.sin(lat)*np.cos(lat)/(1 - ellipsoid.e**2*np.sin(lat)**2)**(1.5)
    LLH2ECEF = np.zeros((3,3))

    # Partial derivatives of ellipsoid to Cartesian (x,y,z) conversion WRT latitude:
    LLH2ECEF[0,0] = -(N + h)*np.sin(lat)*np.cos(lon) + dN_dlat*np.cos(lat)*np.cos(lon)
    LLH2ECEF[1,0] = -(N + h)*np.sin(lat)*np.sin(lon) + dN_dlat*np.cos(lat)*np.sin(lon)
    LLH2ECEF[2,0] =  (N*(1 - ellipsoid.e**2) + h)*np.cos(lat) + dN_dlat*(1 - ellipsoid.e**2)*np.sin(lat)

    # Partial derivatives of ellipsoid to Cartesian (x,y,z) conversion WRT longitude:
    LLH2ECEF[0,1] = -(N + h)*np.cos(lat)*np.sin(lon)
    LLH2ECEF[1,1] =  (N + h)*np.cos(lat)*np.cos(lon)
    LLH2ECEF[2,1] =  0

    # Partial derivatives of ellipsoid to Cartesian (x,y,z) conversion WRT height:
    LLH2ECEF[0,2] = np.cos(lat)*np.cos(lon)
    LLH2ECEF[1,2] = np.cos(lat)*np.sin(lon)
    LLH2ECEF[2,2] = np.sin(lat)
    return LLH2ECEF

def ecef2enu_dcm(llh_0,degrees=True):
    r"""Return DCM from Earth-centered, Earth-fixed (ECEF) frame to locally-defined east/north/up (ENU) frame.

    Given the origin of the locally-defined ENU frame as defined by geodetic latitude, longitude, and ellipsoid height coordinates
    :math:`(\phi,\lambda,h)`, the direction cosine matrix mapping from the ECEF frame to ENU frame is given by a third-axis rotation
    by angle :math:`\lambda + 90^\circ` followed by a first-axis rotation by angle :math:`90^\circ - \phi`, yielding the result :cite:`MiEn12`:

    .. math:: [\mathcal{LE}] \equiv
       \left[\array{-\sin(\lambda) & \cos(\lambda) & 0 \\
       -\sin(\phi)\cos(\lambda) & -\sin(\phi)\sin(\lambda) & \cos(\phi) \\
       \cos(\phi)\cos(\lambda) & \cos(\phi)\sin(\lambda) & \sin(\phi)}\right]

    Args:
        llh_0 (np.ndarray): LLH coordinates defining origin of local ENU frame
        degrees (bool): Toggles whether latitude/longitude are input in degrees

    Returns:
        np.ndarray: Direction cosine matrix (DCM) mapping from ECEF frame to ENU frame

    """
    # Extract latitude/longitude of frame origin:
    if degrees: llh_0 = [np.deg2rad(llh_0[0]),np.deg2rad(llh_0[1]),llh_0[2]]
    lat,lon,h = llh_0

    # Construct DCM from ECEF to ENU
    # [source: Misra/Enge, pp. 137]:
    ECEF2ENU      =  np.zeros((3,3))
    ECEF2ENU[0,0] = -np.sin(lon)
    ECEF2ENU[0,1] =  np.cos(lon)
    ECEF2ENU[0,2] =  0
    ECEF2ENU[1,0] = -np.sin(lat)*np.cos(lon)
    ECEF2ENU[1,1] = -np.sin(lat)*np.sin(lon)
    ECEF2ENU[1,2] =  np.cos(lat)
    ECEF2ENU[2,0] =  np.cos(lat)*np.cos(lon)
    ECEF2ENU[2,1] =  np.cos(lat)*np.sin(lon)
    ECEF2ENU[2,2] =  np.sin(lat)
    return ECEF2ENU

def llh2enu_dcm(llh_0,degrees=True,ellipsoid=WGS84):
    r"""Return DCM from latitude/longitude/height (LLH) ellipsoid frame
    to locally-defined east/north/up (ENU) frame.

    Note:
        This function is a wrapper around calls to :func:`llh2ecef_dcm` and :func:`ecef2enu_dcm`.

    Args:
        llh_0 (np.ndarray): LLH coordinates defining origin of local ENU frame
        degrees (bool): Toggles whether latitude/longitude are input in degrees
        ellipsoid (Ellipsoid): Ellipsoid definition to use for coordinate conversion

    Returns:
        np.ndarray: Direction cosine matrix (DCM) mapping from LLH frame to ENU frame

    """
    LLH2ECEF = llh2ecef_dcm(llh_0,degrees=degrees,ellipsoid=ellipsoid)
    ECEF2ENU = ecef2enu_dcm(llh_0,degrees=degrees)
    return ECEF2ENU.dot(LLH2ECEF)