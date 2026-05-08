package ar.edu.itba.sds.tp4;

import ar.edu.itba.sds.tp4.system1.System1Command;
import ar.edu.itba.sds.tp4.system2.config.System2RunRequestLoader;
import ar.edu.itba.sds.tp4.system2.model.System2Config;
import ar.edu.itba.sds.tp4.system2.model.System2Geometry;
import ar.edu.itba.sds.tp4.system2.runner.System2RunRequest;
import ar.edu.itba.sds.tp4.system2.runner.System2Runner;
import ar.edu.itba.sds.tp4.system2.runner.System2RunnerResult;

import java.nio.file.Path;
import java.util.Arrays;

public final class Tp4Application {
    private Tp4Application() {
    }

    public static void main(String[] args) {
        if (args.length == 0) {
            printUsage();
            return;
        }

        String command = args[0];
        String[] commandArgs = Arrays.copyOfRange(args, 1, args.length);
        try {
            switch (command) {
                case "system1" -> new System1Command().run(commandArgs);
                case "system2" -> runSystem2FromConfig(commandArgs);
                case "system2-smoke" -> runSystem2Smoke(commandArgs);
                case "--help", "-h", "help" -> printUsage();
                default -> {
                    System.err.println("Unknown command: " + command);
                    printUsage();
                    System.exit(1);
                }
            }
        } catch (IllegalArgumentException exception) {
            System.err.println("Invalid arguments: " + exception.getMessage());
            printCommandUsage(command);
            System.exit(1);
        } catch (RuntimeException exception) {
            System.err.println("Command failed: " + exception.getMessage());
            System.exit(1);
        }
    }

    private static void runSystem2FromConfig(String[] args) {
        if (args.length != 1) {
            throw new IllegalArgumentException("Usage: system2 <config_path>");
        }
        System2RunRequest request = new System2RunRequestLoader().load(Path.of(args[0]));
        System2RunnerResult result = new System2Runner().run(request);

        System.out.println("System 2 run completed.");
        System.out.println("Run id: " + request.runId());
        System.out.println("Output directory: " + result.outputDirectory().toAbsolutePath());
        System.out.println("Final step: " + result.runResult().finalState().step());
        System.out.println("Final time: " + result.runResult().finalState().time());
        System.out.println("Snapshots written: " + result.runResult().snapshotsWritten());
    }

    private static void runSystem2Smoke(String[] args) {
        if (args.length > 1) {
            throw new IllegalArgumentException("Usage: system2-smoke [output_dir]");
        }
        Path outputDirectory = args.length == 1
                ? Path.of(args[0])
                : Path.of("outputs", "system2", "smoke");

        System2Config config = new System2Config(
                new System2Geometry(80.0, 1.0, 1.0),
                25,
                1.0,
                1.0,
                10_000.0,
                1.0e-4,
                10,
                12345L
        );
        System2RunnerResult result = new System2Runner().run(new System2RunRequest(
                "smoke",
                0,
                config,
                outputDirectory
        ));

        System.out.println("System 2 smoke run completed.");
        System.out.println("Output directory: " + result.outputDirectory().toAbsolutePath());
        System.out.println("Final step: " + result.runResult().finalState().step());
        System.out.println("Final time: " + result.runResult().finalState().time());
        System.out.println("Snapshots written: " + result.runResult().snapshotsWritten());
    }

    private static void printUsage() {
        System.out.println("SdS TP4 Java engine");
        System.out.println("Available commands:");
        System.out.println("  system1    Generate System 1 raw trajectory CSV");
        System.out.println("  system2    Run System 2 from a TOML config");
        System.out.println("  system2-smoke [output_dir]");
        System.out.println();
        System.out.println(System1Command.usage());
        System.out.println();
        printSystem2Usage();
    }

    private static void printCommandUsage(String command) {
        switch (command) {
            case "system1" -> System.err.println(System1Command.usage());
            case "system2", "system2-smoke" -> printSystem2Usage();
            default -> printUsage();
        }
    }

    private static void printSystem2Usage() {
        System.out.println("  system2 <config_path>");
        System.out.println("  system2-smoke [output_dir]");
    }
}
