package ar.edu.itba.sds.tp4;

import ar.edu.itba.sds.tp4.system1.System1Command;

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
                case "--help", "-h", "help" -> printUsage();
                default -> {
                    System.err.println("Unknown command: " + command);
                    printUsage();
                    System.exit(1);
                }
            }
        } catch (IllegalArgumentException exception) {
            System.err.println("Invalid arguments: " + exception.getMessage());
            System.err.println(System1Command.usage());
            System.exit(1);
        } catch (RuntimeException exception) {
            System.err.println("Command failed: " + exception.getMessage());
            System.exit(1);
        }
    }

    private static void printUsage() {
        System.out.println("SdS TP4 Java engine");
        System.out.println("Available commands:");
        System.out.println("  system1    Validate System 1 parameters and write the raw CSV contract scaffold");
        System.out.println();
        System.out.println(System1Command.usage());
    }
}
