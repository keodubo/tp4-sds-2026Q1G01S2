package ar.edu.itba.sds.tp4;

import ar.edu.itba.sds.tp4.system2.model.System2Config;
import ar.edu.itba.sds.tp4.system2.model.System2Geometry;
import ar.edu.itba.sds.tp4.system2.config.System2RunRequestLoader;
import ar.edu.itba.sds.tp4.system2.runner.System2RunRequest;
import ar.edu.itba.sds.tp4.system2.runner.System2Runner;
import ar.edu.itba.sds.tp4.system2.runner.System2RunnerResult;

import java.nio.file.Path;

public final class Tp4Application {
    private Tp4Application() {
    }

    public static void main(String[] args) {
        if (args.length == 0) {
            printUsage();
            return;
        }

        if ("system2-smoke".equals(args[0])) {
            runSystem2Smoke(args);
            return;
        }
        if ("system2".equals(args[0])) {
            runSystem2FromConfig(args);
            return;
        }

        throw new IllegalArgumentException("Unknown command: " + args[0]);
    }

    private static void runSystem2FromConfig(String[] args) {
        if (args.length != 2) {
            throw new IllegalArgumentException("Usage: system2 <config_path>");
        }
        System2RunRequest request = new System2RunRequestLoader().load(Path.of(args[1]));
        System2RunnerResult result = new System2Runner().run(request);

        System.out.println("System 2 run completed.");
        System.out.println("Run id: " + request.runId());
        System.out.println("Output directory: " + result.outputDirectory().toAbsolutePath());
        System.out.println("Final step: " + result.runResult().finalState().step());
        System.out.println("Final time: " + result.runResult().finalState().time());
        System.out.println("Snapshots written: " + result.runResult().snapshotsWritten());
    }

    private static void runSystem2Smoke(String[] args) {
        Path outputDirectory = args.length >= 2
                ? Path.of(args[1])
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
        System.out.println("Usage:");
        System.out.println("  system2 <config_path>");
        System.out.println("  system2-smoke [output_dir]");
    }
}
