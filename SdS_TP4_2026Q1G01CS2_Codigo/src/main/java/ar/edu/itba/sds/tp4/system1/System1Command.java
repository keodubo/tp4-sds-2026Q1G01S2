package ar.edu.itba.sds.tp4.system1;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class System1Command {
    public void run(String[] args) {
        ParsedArgs parsedArgs = parse(args);
        if (parsedArgs.help()) {
            System.out.println(usage());
            return;
        }
        if (parsedArgs.outputPath() == null) {
            throw new IllegalArgumentException("missing required --output");
        }

        System1Parameters parameters = parsedArgs.toParameters();
        List<TrajectoryCsvWriter.Row> rows = buildRows(parameters, List.of(new EulerIntegrator()));
        new TrajectoryCsvWriter().write(parsedArgs.outputPath(), parameters, rows);
        System.out.println("System 1 parameters validated.");
        System.out.println("Wrote System 1 Euler trajectory CSV to " + parsedArgs.outputPath());
        System.out.println("Remaining required methods are intentionally deferred to the next phase.");
    }

    public static String usage() {
        return """
                Usage:
                  system1 --output <path> [--m <mass>] [--k <spring>] [--gamma <damping>] [--tf <seconds>] [--x0 <position>] [--v0 <velocity>] [--dt <csv>]

                Defaults:
                  --m 70 --k 10000 --gamma 100 --tf 5 --x0 1 --v0 -0.7142857142857143 --dt 0.1,0.01,0.001,0.0001
                """;
    }

    private static ParsedArgs parse(String[] args) {
        ParsedArgs parsed = ParsedArgs.defaults();
        for (int index = 0; index < args.length; index++) {
            String token = args[index];
            switch (token) {
                case "--help", "-h" -> parsed = parsed.withHelp();
                case "--m" -> parsed = parsed.withMass(parseDouble(token, requireValue(args, ++index, token)));
                case "--k" -> parsed = parsed.withSpringConstant(parseDouble(token, requireValue(args, ++index, token)));
                case "--gamma" -> parsed = parsed.withGamma(parseDouble(token, requireValue(args, ++index, token)));
                case "--tf" -> parsed = parsed.withFinalTime(parseDouble(token, requireValue(args, ++index, token)));
                case "--x0" -> parsed = parsed.withInitialPosition(parseDouble(token, requireValue(args, ++index, token)));
                case "--v0" -> parsed = parsed.withInitialVelocity(parseDouble(token, requireValue(args, ++index, token)));
                case "--dt" -> parsed = parsed.withDts(parseDts(requireValue(args, ++index, token)));
                case "--output" -> parsed = parsed.withOutputPath(Path.of(requireValue(args, ++index, token)));
                default -> throw new IllegalArgumentException("unknown flag: " + token);
            }
        }
        return parsed;
    }

    private static String requireValue(String[] args, int index, String flag) {
        if (index >= args.length) {
            throw new IllegalArgumentException(flag + " requires a value");
        }
        String value = args[index];
        if (value.startsWith("--")) {
            throw new IllegalArgumentException(flag + " requires a value");
        }
        return value;
    }

    private static double parseDouble(String flag, String value) {
        try {
            return Double.parseDouble(value);
        } catch (NumberFormatException exception) {
            throw new IllegalArgumentException(flag + " must be a number: " + value, exception);
        }
    }

    private static List<Double> parseDts(String rawValue) {
        String[] parts = rawValue.split(",");
        List<Double> parsed = new ArrayList<>(parts.length);
        for (String part : parts) {
            String value = part.trim();
            if (value.isEmpty()) {
                throw new IllegalArgumentException("--dt contains an empty value");
            }
            parsed.add(parseDouble("--dt", value));
        }
        return parsed;
    }

    private static List<TrajectoryCsvWriter.Row> buildRows(System1Parameters parameters, List<Integrator> integrators) {
        List<TrajectoryCsvWriter.Row> rows = new ArrayList<>();
        for (Integrator integrator : integrators) {
            for (double dt : parameters.dts()) {
                for (OscillatorState state : integrator.integrate(parameters, dt)) {
                    rows.add(new TrajectoryCsvWriter.Row(integrator.methodName(), dt, state));
                }
            }
        }
        return rows;
    }

    private record ParsedArgs(
            boolean help,
            double mass,
            double springConstant,
            double gamma,
            double finalTime,
            double initialPosition,
            double initialVelocity,
            List<Double> dts,
            Path outputPath
    ) {
        static ParsedArgs defaults() {
            System1Parameters defaults = System1Parameters.defaults();
            return new ParsedArgs(
                    false,
                    defaults.mass(),
                    defaults.springConstant(),
                    defaults.gamma(),
                    defaults.finalTime(),
                    defaults.initialPosition(),
                    defaults.initialVelocity(),
                    defaults.dts(),
                    null
            );
        }

        ParsedArgs withHelp() {
            return new ParsedArgs(true, mass, springConstant, gamma, finalTime, initialPosition, initialVelocity, dts, outputPath);
        }

        ParsedArgs withMass(double value) {
            return new ParsedArgs(help, value, springConstant, gamma, finalTime, initialPosition, initialVelocity, dts, outputPath);
        }

        ParsedArgs withSpringConstant(double value) {
            return new ParsedArgs(help, mass, value, gamma, finalTime, initialPosition, initialVelocity, dts, outputPath);
        }

        ParsedArgs withGamma(double value) {
            return new ParsedArgs(help, mass, springConstant, value, finalTime, initialPosition, initialVelocity, dts, outputPath);
        }

        ParsedArgs withFinalTime(double value) {
            return new ParsedArgs(help, mass, springConstant, gamma, value, initialPosition, initialVelocity, dts, outputPath);
        }

        ParsedArgs withInitialPosition(double value) {
            return new ParsedArgs(help, mass, springConstant, gamma, finalTime, value, initialVelocity, dts, outputPath);
        }

        ParsedArgs withInitialVelocity(double value) {
            return new ParsedArgs(help, mass, springConstant, gamma, finalTime, initialPosition, value, dts, outputPath);
        }

        ParsedArgs withDts(List<Double> value) {
            return new ParsedArgs(help, mass, springConstant, gamma, finalTime, initialPosition, initialVelocity, value, outputPath);
        }

        ParsedArgs withOutputPath(Path value) {
            return new ParsedArgs(help, mass, springConstant, gamma, finalTime, initialPosition, initialVelocity, dts, value);
        }

        System1Parameters toParameters() {
            return new System1Parameters(mass, springConstant, gamma, finalTime, initialPosition, initialVelocity, dts);
        }
    }
}
