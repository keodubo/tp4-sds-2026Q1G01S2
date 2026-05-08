package ar.edu.itba.sds.tp4.system1;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class IntegratorContractTest {
    @TempDir
    Path tempDir;

    @Test
    void integratorsReturnStatesFromZeroThroughFinalTimeInclusive() {
        System1Parameters parameters = shortRunParameters(0.2, List.of(0.1));
        List<Integrator> integrators = List.of(
                new EulerIntegrator(),
                new VerletIntegrator(),
                new BeemanIntegrator(),
                new Gear5Integrator()
        );

        for (Integrator integrator : integrators) {
            List<OscillatorState> states = integrator.integrate(parameters, 0.1);

            assertEquals(3, states.size(), integrator.methodName());
            assertEquals(0.0, states.get(0).time(), integrator.methodName());
            assertEquals(0.1, states.get(1).time(), 1e-12, integrator.methodName());
            assertEquals(0.2, states.get(2).time(), 1e-12, integrator.methodName());
            assertEquals(parameters.initialPosition(), states.get(0).position(), integrator.methodName());
        }
    }

    @Test
    void eulerUsesCourseFormulaForFirstStep() {
        System1Parameters parameters = new System1Parameters(
                2.0,
                4.0,
                1.0,
                0.1,
                3.0,
                -2.0,
                List.of(0.1)
        );
        Integrator integrator = new EulerIntegrator();

        OscillatorState nextState = integrator.integrate(parameters, 0.1).get(1);

        assertEquals(0.1, nextState.time(), 1e-12);
        assertEquals(2.775, nextState.position(), 1e-12);
        assertEquals(-2.5, nextState.velocity(), 1e-12);
    }

    @Test
    void verletUsesDampedCenteredVelocityRecurrenceForFirstStep() {
        System1Parameters parameters = new System1Parameters(
                2.0,
                4.0,
                1.0,
                0.1,
                3.0,
                -2.0,
                List.of(0.1)
        );
        Oscillator oscillator = new Oscillator(parameters);
        double dt = 0.1;
        double initialAcceleration = oscillator.acceleration(parameters.initialPosition(), parameters.initialVelocity());
        double previousPosition = parameters.initialPosition()
                - parameters.initialVelocity() * dt
                + 0.5 * initialAcceleration * dt * dt;
        double expectedNextPosition = ((2.0 * parameters.mass() - parameters.springConstant() * dt * dt) * parameters.initialPosition()
                + (parameters.gamma() * dt / 2.0 - parameters.mass()) * previousPosition)
                / (parameters.mass() + parameters.gamma() * dt / 2.0);

        OscillatorState nextState = new VerletIntegrator().integrate(parameters, dt).get(1);

        assertEquals("verlet", new VerletIntegrator().methodName());
        assertEquals(expectedNextPosition, nextState.position(), 1e-12);
    }

    @Test
    void verletExportsFinalVelocityUsingOneExtraCenteredPosition() {
        System1Parameters parameters = new System1Parameters(
                2.0,
                4.0,
                1.0,
                0.2,
                3.0,
                -2.0,
                List.of(0.1)
        );
        double dt = 0.1;
        Oscillator oscillator = new Oscillator(parameters);
        double initialAcceleration = oscillator.acceleration(parameters.initialPosition(), parameters.initialVelocity());
        double previousPosition = parameters.initialPosition()
                - parameters.initialVelocity() * dt
                + 0.5 * initialAcceleration * dt * dt;
        double position1 = verletNextPosition(parameters, dt, previousPosition, parameters.initialPosition());
        double position2 = verletNextPosition(parameters, dt, parameters.initialPosition(), position1);
        double position3 = verletNextPosition(parameters, dt, position1, position2);
        double expectedFinalVelocity = (position3 - position1) / (2.0 * dt);

        List<OscillatorState> states = new VerletIntegrator().integrate(parameters, dt);

        assertEquals(0.2, states.get(2).time(), 1e-12);
        assertEquals(expectedFinalVelocity, states.get(2).velocity(), 1e-12);
    }

    @Test
    void beemanUsesVelocityDependentPredictorCorrectorForFirstStep() {
        System1Parameters parameters = new System1Parameters(
                2.0,
                4.0,
                1.0,
                0.1,
                3.0,
                -2.0,
                List.of(0.1)
        );

        OscillatorState nextState = new BeemanIntegrator().integrate(parameters, 0.1).get(1);

        assertEquals("beeman", new BeemanIntegrator().methodName());
        assertEquals(2.776, nextState.position(), 1e-12);
        assertEquals(-2.4672333333333334, nextState.velocity(), 1e-12);
    }

    @Test
    void gear5UsesOrderFivePredictorCorrectorForFirstStep() {
        System1Parameters parameters = new System1Parameters(
                2.0,
                4.0,
                1.0,
                0.1,
                3.0,
                -2.0,
                List.of(0.1)
        );

        OscillatorState nextState = new Gear5Integrator().integrate(parameters, 0.1).get(1);

        assertEquals("gear5", new Gear5Integrator().methodName());
        assertEquals(2.7761100755566406, nextState.position(), 1e-12);
        assertEquals(-2.4664439056614584, nextState.velocity(), 1e-10);
    }

    @Test
    void gear5InitialDerivativesFollowDampedOscillatorRecurrence() {
        System1Parameters parameters = new System1Parameters(
                2.0,
                4.0,
                1.0,
                0.1,
                3.0,
                -2.0,
                List.of(0.1)
        );

        double[] derivatives = Gear5Integrator.initialDerivatives(parameters);

        assertArrayEquals(
                new double[]{3.0, -2.0, -5.0, 6.5, 6.75, -16.375},
                derivatives,
                1e-12
        );
    }

    @Test
    void system1CommandWritesAllRequiredMethodsForEveryDefaultDt() throws IOException {
        Path outputPath = tempDir.resolve("system1.csv");

        new System1Command().run(new String[]{"--output", outputPath.toString()});

        List<String> dataRows = Files.readAllLines(outputPath).stream()
                .filter(line -> !line.startsWith("#"))
                .skip(1)
                .toList();
        assertEquals(222_216, dataRows.size());

        Set<String> methods = new HashSet<>();
        Map<String, Integer> rowsByMethodAndDt = new HashMap<>();
        for (String row : dataRows) {
            String[] columns = row.split(",");
            methods.add(columns[0]);
            rowsByMethodAndDt.merge(columns[0] + ":" + columns[1], 1, Integer::sum);
        }

        assertEquals(Set.of("euler", "verlet", "beeman", "gear5"), methods);
        for (String method : methods) {
            assertEquals(51, rowsByMethodAndDt.get(method + ":0.1"), method);
            assertEquals(501, rowsByMethodAndDt.get(method + ":0.01"), method);
            assertEquals(5_001, rowsByMethodAndDt.get(method + ":0.001"), method);
            assertEquals(50_001, rowsByMethodAndDt.get(method + ":1.0E-4"), method);
        }
    }

    @Test
    void system1CommandRejectsImpracticallyLargeOutputsBeforeWriting() {
        Path outputPath = tempDir.resolve("too-large.csv");

        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () ->
                new System1Command().run(new String[]{
                        "--tf", "1",
                        "--dt", "0.000002",
                        "--output", outputPath.toString()
                })
        );

        assertTrue(exception.getMessage().contains("too many output rows"));
        assertTrue(Files.notExists(outputPath));
    }

    private static System1Parameters shortRunParameters(double finalTime, List<Double> dts) {
        System1Parameters defaults = System1Parameters.defaults();
        return new System1Parameters(
                defaults.mass(),
                defaults.springConstant(),
                defaults.gamma(),
                finalTime,
                defaults.initialPosition(),
                defaults.initialVelocity(),
                dts
        );
    }

    private static double verletNextPosition(System1Parameters parameters, double dt, double previousPosition, double position) {
        double mass = parameters.mass();
        double numerator = (2.0 * mass - parameters.springConstant() * dt * dt) * position
                + (parameters.gamma() * dt / 2.0 - mass) * previousPosition;
        double denominator = mass + parameters.gamma() * dt / 2.0;
        return numerator / denominator;
    }
}
