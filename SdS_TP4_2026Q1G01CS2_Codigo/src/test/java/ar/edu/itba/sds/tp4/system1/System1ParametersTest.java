package ar.edu.itba.sds.tp4.system1;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class System1ParametersTest {
    @Test
    void defaultsMatchCourseOscillatorValues() {
        System1Parameters parameters = System1Parameters.defaults();

        assertEquals(70.0, parameters.mass());
        assertEquals(10_000.0, parameters.springConstant());
        assertEquals(100.0, parameters.gamma());
        assertEquals(5.0, parameters.finalTime());
        assertEquals(1.0, parameters.initialPosition());
        assertEquals(-100.0 / (2.0 * 70.0), parameters.initialVelocity());
        assertEquals(List.of(0.01, 0.001, 0.0001, 0.00001), parameters.dts());
    }

    @Test
    void rejectsInvalidPhysicalParameters() {
        assertThrows(IllegalArgumentException.class, () -> parametersWithMass(0.0));
        assertThrows(IllegalArgumentException.class, () -> parametersWithSpringConstant(0.0));
        assertThrows(IllegalArgumentException.class, () -> parametersWithGamma(-1.0));
        assertThrows(IllegalArgumentException.class, () -> parametersWithFinalTime(0.0));
    }

    @Test
    void rejectsInvalidDtSweep() {
        assertThrows(IllegalArgumentException.class, () -> parametersWithDts(List.of()));
        assertThrows(IllegalArgumentException.class, () -> parametersWithDts(List.of(0.01, 0.0)));
        assertThrows(IllegalArgumentException.class, () -> parametersWithDts(List.of(0.01, 0.01)));
        assertThrows(IllegalArgumentException.class, () -> parametersWithDts(List.of(0.3)));
    }

    private static System1Parameters parametersWithMass(double mass) {
        System1Parameters defaults = System1Parameters.defaults();
        return new System1Parameters(
                mass,
                defaults.springConstant(),
                defaults.gamma(),
                defaults.finalTime(),
                defaults.initialPosition(),
                defaults.initialVelocity(),
                defaults.dts()
        );
    }

    private static System1Parameters parametersWithSpringConstant(double springConstant) {
        System1Parameters defaults = System1Parameters.defaults();
        return new System1Parameters(
                defaults.mass(),
                springConstant,
                defaults.gamma(),
                defaults.finalTime(),
                defaults.initialPosition(),
                defaults.initialVelocity(),
                defaults.dts()
        );
    }

    private static System1Parameters parametersWithGamma(double gamma) {
        System1Parameters defaults = System1Parameters.defaults();
        return new System1Parameters(
                defaults.mass(),
                defaults.springConstant(),
                gamma,
                defaults.finalTime(),
                defaults.initialPosition(),
                defaults.initialVelocity(),
                defaults.dts()
        );
    }

    private static System1Parameters parametersWithFinalTime(double finalTime) {
        System1Parameters defaults = System1Parameters.defaults();
        return new System1Parameters(
                defaults.mass(),
                defaults.springConstant(),
                defaults.gamma(),
                finalTime,
                defaults.initialPosition(),
                defaults.initialVelocity(),
                defaults.dts()
        );
    }

    private static System1Parameters parametersWithDts(List<Double> dts) {
        System1Parameters defaults = System1Parameters.defaults();
        return new System1Parameters(
                defaults.mass(),
                defaults.springConstant(),
                defaults.gamma(),
                defaults.finalTime(),
                defaults.initialPosition(),
                defaults.initialVelocity(),
                dts
        );
    }
}
