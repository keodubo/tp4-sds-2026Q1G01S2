package ar.edu.itba.sds.tp4.system1;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class IntegratorContractTest {
    @TempDir
    Path tempDir;

    @Test
    void eulerReturnsStatesFromZeroThroughFinalTimeInclusive() {
        System1Parameters parameters = shortRunParameters(0.2, List.of(0.1));
        Integrator integrator = new EulerIntegrator();

        List<OscillatorState> states = integrator.integrate(parameters, 0.1);

        assertEquals("euler", integrator.methodName());
        assertEquals(3, states.size());
        assertEquals(0.0, states.get(0).time());
        assertEquals(0.1, states.get(1).time(), 1e-12);
        assertEquals(0.2, states.get(2).time(), 1e-12);
        assertEquals(parameters.initialPosition(), states.get(0).position());
        assertEquals(parameters.initialVelocity(), states.get(0).velocity());
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
    void system1CommandWritesEulerRowsForEveryDefaultDt() throws IOException {
        Path outputPath = tempDir.resolve("system1.csv");

        new System1Command().run(new String[]{"--output", outputPath.toString()});

        List<String> dataRows = Files.readAllLines(outputPath).stream()
                .filter(line -> !line.startsWith("#"))
                .skip(1)
                .toList();
        assertEquals(55_554, dataRows.size());
        assertTrue(dataRows.stream().allMatch(line -> line.startsWith("euler,")));

        Map<Double, Integer> rowsByDt = new HashMap<>();
        for (String row : dataRows) {
            String[] columns = row.split(",");
            rowsByDt.merge(Double.parseDouble(columns[1]), 1, Integer::sum);
        }

        assertEquals(51, rowsByDt.get(0.1));
        assertEquals(501, rowsByDt.get(0.01));
        assertEquals(5_001, rowsByDt.get(0.001));
        assertEquals(50_001, rowsByDt.get(0.0001));
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
}
