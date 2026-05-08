package ar.edu.itba.sds.tp4.system1;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

class TrajectoryCsvWriterTest {
    @TempDir
    Path tempDir;

    @Test
    void writesMetadataHeaderAndRows() throws IOException {
        Path outputPath = tempDir.resolve("system1.csv");
        System1Parameters parameters = System1Parameters.defaults();
        List<TrajectoryCsvWriter.Row> rows = List.of(
                new TrajectoryCsvWriter.Row("euler", 0.01, new OscillatorState(0.0, 1.0, parameters.initialVelocity()))
        );

        new TrajectoryCsvWriter().write(outputPath, parameters, rows);

        List<String> lines = Files.readAllLines(outputPath);
        assertEquals("# system=system1", lines.get(0));
        assertEquals("# m=70.0", lines.get(1));
        assertEquals("# k=10000.0", lines.get(2));
        assertEquals("# gamma=100.0", lines.get(3));
        assertEquals("# tf=5.0", lines.get(4));
        assertEquals("# x0=1.0", lines.get(5));
        assertEquals("# v0=-0.7142857142857143", lines.get(6));
        assertEquals("# dts=0.01,0.001,1.0E-4,1.0E-5,1.0E-6", lines.get(7));
        assertEquals("method,dt,time,x,v", lines.get(8));
        assertEquals("euler,0.01,0.0,1.0,-0.7142857142857143", lines.get(9));
    }
}
