use crate::battery;

#[derive(Clone, Copy)]
/// Struct to store a GPS Location as latitude and longitude.
pub(crate) struct GPSLocation {
    pub(crate) lat: f64,
    pub(crate) lon: f64,
}

/// Represents simualated, generic onboard GPS Locator.
pub(crate) trait GPSLocator {
    /// Attempt to get the user's location.
    ///
    /// Returns
    /// -------
    /// A return result of `None` indicates that an issue occurred and the current location could not be fetched,
    /// whether due to permissions or a lack of available power.
    ///
    /// Otherwise, the user's current location (a [`GPSLocation`]) should be returned wrapped in `Some`.
    fn get_current_location(&mut self) -> Option<GPSLocation>;
    /// Attempt to get the user's last known location.
    ///
    /// Returns
    /// -------
    /// A return result of `None` indicates that an issue occurred and the current location could not be fetched,
    /// whether due to permissions or a lack of available power.
    ///
    /// Otherwise, the user's current location (a [`GPSLocation`]) should be returned wrapped in `Some`.  
    ///
    /// Notes
    /// -----
    /// Battery usage is generally negligible when polling for the last known location, because there does not
    /// need to be any communication with a GPS satellite.
    fn get_last_location(&mut self) -> Option<GPSLocation>;
}

/// An embedded machine use GPS unit, this does not have any sort
/// of permissions schema. Thus, the device will only fail to return current or last location
/// if doing so costs too much power.
pub(crate) struct NEO7M {
    current_location: Option<GPSLocation>,
    last_location: Option<GPSLocation>,
    power_source: Box<dyn battery::Battery>,
}

impl GPSLocator for NEO7M {
    fn get_current_location(&mut self) -> Option<GPSLocation> {
        /// TODO: The discharge amount is not decided yet. This needs
        /// to be calculated as time(hours) * current(mA) = drain(mAh).
        /// Consider adding a `time` module to convert times to hours for this purpose. 
        self.power_source.as_mut().discharge(35.0);
        match self.power_source.as_ref().remaining() {
            charge if charge == 0f32 => None,
            _ => {
                if let Some(loc) = self.current_location {
                    self.last_location = self.current_location;
                    Some(loc)
                } else {
                    None
                }
            }
        }
    }
    fn get_last_location(&mut self) -> Option<GPSLocation> {
        if let Some(loc) = self.last_location {
            Some(loc)
        } else {
            None
        }
    }
}
