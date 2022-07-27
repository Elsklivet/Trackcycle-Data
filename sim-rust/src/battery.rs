/// Represents a generic on-device or external electrical battery.
pub(crate) trait Battery {
    /// Discharge the battery by a specified amount.
    ///
    /// Parameters
    /// ----------
    /// `amt: f32`: mAh amount to discharge from the battery. **The caller is responsible for calculating this amount in units mAh.**
    fn discharge(&mut self, amt: f32);
    /// Charge the battery by a specified amount.
    ///
    /// Parameters
    /// ----------
    /// `amt: f32`: mAh amount to charge to the battery. **The caller is responsible for calculating this amount in units mAh.**
    fn charge(&mut self, amt: f32);
    /// Get the current remaining battery level as mAh.
    fn remaining(&self) -> f32;
    /// Get the battery's total capacity as mAh.
    fn capacity(&self) -> f32;
    /// Get the remaining battery level as a percentage of capacity.
    fn percent_remaining(&self) -> f32;
}

/// 10,000 mAh battery
pub(crate) struct Battery10kmAh {
    charge_left: f32,
}

/// 4,500 mAh battery
pub(crate) struct Battery4kmAh {
    charge_left: f32,
}

impl Battery for Battery10kmAh {
    fn discharge(&mut self, amt: f32) {
        if amt > self.charge_left || amt < -self.charge_left {
            self.charge_left = 0.0f32;
        } else if amt < 0.0f32 {
            self.charge_left += amt;
        } else {
            self.charge_left -= amt;
        }
    }
    fn charge(&mut self, amt: f32) {
        if amt > self.charge_left || amt < -self.charge_left {
            self.charge_left = self.capacity();
        } else if amt < 0.0f32 {
            self.charge_left -= amt;
        } else {
            self.charge_left += amt;
        }
    }
    fn remaining(&self) -> f32 {
        self.charge_left
    }
    fn capacity(&self) -> f32 {
        10000.0f32
    }
    fn percent_remaining(&self) -> f32 {
        (self.remaining() / self.capacity()) * 100.0
    }
}

impl Battery for Battery4kmAh {
    fn discharge(&mut self, amt: f32) {
        if amt > self.charge_left || amt < -self.charge_left {
            self.charge_left = 0.0f32;
        } else if amt < 0.0f32 {
            self.charge_left += amt;
        } else {
            self.charge_left -= amt;
        }
    }
    fn charge(&mut self, amt: f32) {
        if amt > self.charge_left || amt < -self.charge_left {
            self.charge_left = self.capacity();
        } else if amt < 0.0f32 {
            self.charge_left -= amt;
        } else {
            self.charge_left += amt;
        }
    }
    fn remaining(&self) -> f32 {
        self.charge_left
    }
    fn capacity(&self) -> f32 {
        4500.0f32
    }
    fn percent_remaining(&self) -> f32 {
        (self.remaining() / self.capacity()) * 100.0
    }
}
