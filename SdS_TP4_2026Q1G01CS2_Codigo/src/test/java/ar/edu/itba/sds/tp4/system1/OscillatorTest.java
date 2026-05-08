package ar.edu.itba.sds.tp4.system1;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class OscillatorTest {
    @Test
    void accelerationUsesPositionAndVelocityTerms() {
        Oscillator oscillator = new Oscillator(70.0, 10_000.0, 100.0);

        double acceleration = oscillator.acceleration(1.0, -100.0 / (2.0 * 70.0));

        assertEquals((-10_000.0 * 1.0 - 100.0 * (-100.0 / (2.0 * 70.0))) / 70.0, acceleration);
    }

    @Test
    void accelerationChangesWhenVelocityChanges() {
        Oscillator oscillator = new Oscillator(70.0, 10_000.0, 100.0);

        double slower = oscillator.acceleration(1.0, -1.0);
        double faster = oscillator.acceleration(1.0, 1.0);

        assertEquals(200.0 / 70.0, slower - faster, 1e-12);
    }
}
