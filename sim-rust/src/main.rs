/// Device simulation
mod dev;
/// Battery simulation.
mod battery;
/// GPS-related structs and functionality. 
mod gps;

fn main() {
    let test_location = gps::GPSLocation{ lat: 4.0, lon: 5.0 };
    println!("Hello, world!\nLat={}\nLon={}",test_location.lat, test_location.lon);
}