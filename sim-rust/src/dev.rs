use crate::gps;
use crate::battery;

struct Device {
    gps_unit: Box<dyn gps::GPSLocator>,
    battery: Box<dyn battery::Battery>
}
