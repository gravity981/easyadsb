

class GDL90HeartBeatMessage:
    def __init__(self):
        pass


class GDL90OwnshipMessage:
    def __init__(self, 
        status, 
        addrType, 
        address, 
        latitude, 
        longitude, 
        altitude, 
        misc, 
        navIntegrityCat, 
        navAccuracyCat, 
        hVelocity, 
        vVelocity, 
        trackHeading, 
        emitterCat, 
        callSign, 
        code):
        self.status=status
        self.addrType=addrType
        self.address=address
        self.latitude=latitude
        self.longitude=longitude
        self.altitude=altitude
        self.misc=misc
        self.navIntegrityCat=navIntegrityCat
        self.navAccuracyCat=navAccuracyCat
        self.hVelocity=hVelocity
        self.vVelocity=vVelocity
        self.trackHeading=trackHeading
        self.emitterCat=emitterCat
        self.callSign=callSign
        self.code=code
    

class GDL90OwnshipAltitudeMessage:
    def __init__(self, altitude, merit, warning):
        self.altitude=altitude
        self.merit=merit
        self.warning=warning

class GDL90TrafficMessage:
    def __init__(self,
        status,
        addrType,
        address,
        latitude,
        longitude,
        altitude,
        misc,
        navIntegrityCat,
        navAccuracyCat,
        hVelocity,
        vVelocity,
        trackHeading,
        emitterCat,
        callSign,
        code
        ):