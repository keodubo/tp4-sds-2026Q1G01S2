package ar.edu.itba.sds.tp4.system1;

import java.io.BufferedWriter;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Locale;
import java.util.stream.Collectors;

public final class TrajectoryCsvWriter {
    public void write(Path outputPath, System1Parameters parameters, List<Row> rows) {
        write(outputPath, parameters, writer -> {
            for (Row row : rows) {
                writeRow(writer, row);
            }
        });
    }

    public void writeIntegratedTrajectories(Path outputPath, System1Parameters parameters, List<Integrator> integrators) {
        write(outputPath, parameters, writer -> {
            for (Integrator integrator : integrators) {
                for (double dt : parameters.dts()) {
                    integrator.integrate(parameters, dt, state -> writeRowUnchecked(
                            writer,
                            new Row(integrator.methodName(), dt, state)
                    ));
                }
            }
        });
    }

    private void write(Path outputPath, System1Parameters parameters, ThrowingWriterConsumer rowWriter) {
        if (outputPath == null) {
            throw new IllegalArgumentException("output path must be present");
        }
        try {
            Path parent = outputPath.toAbsolutePath().getParent();
            if (parent != null) {
                Files.createDirectories(parent);
            }
            try (BufferedWriter writer = Files.newBufferedWriter(outputPath, StandardCharsets.UTF_8)) {
                writeMetadata(writer, parameters);
                writer.write("method,dt,time,x,v");
                writer.newLine();
                rowWriter.accept(writer);
            }
        } catch (IOException exception) {
            throw new UncheckedIOException("could not write trajectory CSV to " + outputPath, exception);
        }
    }

    private static void writeMetadata(BufferedWriter writer, System1Parameters parameters) throws IOException {
        writer.write("# system=system1");
        writer.newLine();
        writer.write("# m=" + Double.toString(parameters.mass()));
        writer.newLine();
        writer.write("# k=" + Double.toString(parameters.springConstant()));
        writer.newLine();
        writer.write("# gamma=" + Double.toString(parameters.gamma()));
        writer.newLine();
        writer.write("# tf=" + Double.toString(parameters.finalTime()));
        writer.newLine();
        writer.write("# x0=" + Double.toString(parameters.initialPosition()));
        writer.newLine();
        writer.write("# v0=" + Double.toString(parameters.initialVelocity()));
        writer.newLine();
        writer.write("# dts=" + parameters.dts().stream()
                .map(value -> Double.toString(value))
                .collect(Collectors.joining(",")));
        writer.newLine();
    }

    private static String formatRow(Row row) {
        return String.format(
                Locale.ROOT,
                "%s,%s,%s,%s,%s",
                row.method(),
                Double.toString(row.dt()),
                Double.toString(row.state().time()),
                Double.toString(row.state().position()),
                Double.toString(row.state().velocity())
        );
    }

    private static void writeRow(BufferedWriter writer, Row row) throws IOException {
        writer.write(formatRow(row));
        writer.newLine();
    }

    private static void writeRowUnchecked(BufferedWriter writer, Row row) {
        try {
            writeRow(writer, row);
        } catch (IOException exception) {
            throw new UncheckedIOException(exception);
        }
    }

    @FunctionalInterface
    private interface ThrowingWriterConsumer {
        void accept(BufferedWriter writer) throws IOException;
    }

    public record Row(String method, double dt, OscillatorState state) {
        public Row {
            if (method == null || method.isBlank()) {
                throw new IllegalArgumentException("method must be present");
            }
            if (!Double.isFinite(dt) || dt <= 0.0) {
                throw new IllegalArgumentException("dt must be > 0");
            }
            if (state == null) {
                throw new IllegalArgumentException("state must be present");
            }
        }
    }
}
