package ar.edu.itba.sds.tp4.system2.config;

import ar.edu.itba.sds.tp4.system2.model.System2Config;
import ar.edu.itba.sds.tp4.system2.model.System2Geometry;
import ar.edu.itba.sds.tp4.system2.runner.System2RunRequest;
import org.tomlj.Toml;
import org.tomlj.TomlParseError;
import org.tomlj.TomlParseResult;
import org.tomlj.TomlTable;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.stream.Collectors;

public final class System2RunRequestLoader {
    public System2RunRequest load(Path configPath) {
        if (configPath == null) {
            throw new IllegalArgumentException("configPath must not be null.");
        }

        TomlParseResult result;
        try {
            result = Toml.parse(configPath);
        } catch (IOException exception) {
            throw new UncheckedIOException("Could not read System 2 config: " + configPath, exception);
        }
        if (result.hasErrors()) {
            String errors = result.errors().stream()
                    .map(TomlParseError::toString)
                    .collect(Collectors.joining("; "));
            throw new IllegalArgumentException("Invalid TOML config " + configPath + ": " + errors);
        }

        TomlTable run = requiredTable(result, "run");
        TomlTable geometryTable = requiredTable(result, "geometry");
        TomlTable particles = requiredTable(result, "particles");
        TomlTable interaction = requiredTable(result, "interaction");
        TomlTable simulation = requiredTable(result, "simulation");

        String runId = requiredString(run, "run_id");
        int realization = requiredInt(run, "realization");
        Path outputDirectory = resolvePath(configPath, requiredString(run, "output_dir"));

        System2Geometry geometry = new System2Geometry(
                requiredDouble(geometryTable, "diameter"),
                requiredDouble(geometryTable, "obstacle_radius"),
                requiredDouble(geometryTable, "particle_radius")
        );
        System2Config config = new System2Config(
                geometry,
                requiredInt(particles, "count"),
                requiredDouble(particles, "mass"),
                requiredDouble(particles, "initial_speed"),
                requiredDouble(interaction, "k"),
                requiredDouble(simulation, "dt"),
                requiredLong(simulation, "steps"),
                requiredLong(simulation, "seed")
        );

        return new System2RunRequest(runId, realization, config, outputDirectory);
    }

    private TomlTable requiredTable(TomlParseResult result, String tableName) {
        TomlTable table = result.getTable(tableName);
        if (table == null) {
            throw new IllegalArgumentException("Missing required table [" + tableName + "].");
        }
        return table;
    }

    private String requiredString(TomlTable table, String key) {
        String value = table.getString(key);
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Missing required string field '" + key + "'.");
        }
        return value;
    }

    private int requiredInt(TomlTable table, String key) {
        long value = requiredLong(table, key);
        if (value < Integer.MIN_VALUE || value > Integer.MAX_VALUE) {
            throw new IllegalArgumentException("Integer field '" + key + "' is out of range.");
        }
        return (int) value;
    }

    private long requiredLong(TomlTable table, String key) {
        Long value = table.getLong(key);
        if (value == null) {
            throw new IllegalArgumentException("Missing required integer field '" + key + "'.");
        }
        return value;
    }

    private double requiredDouble(TomlTable table, String key) {
        Double value = table.getDouble(key);
        if (value == null) {
            Long integerValue = table.getLong(key);
            if (integerValue != null) {
                return integerValue.doubleValue();
            }
            throw new IllegalArgumentException("Missing required numeric field '" + key + "'.");
        }
        return value;
    }

    private Path resolvePath(Path configPath, String rawPath) {
        Path path = Path.of(rawPath);
        if (path.isAbsolute()) {
            return path.normalize();
        }
        Path parent = configPath.toAbsolutePath().getParent();
        if (parent == null) {
            parent = Path.of(".").toAbsolutePath();
        }
        return parent.resolve(path).normalize();
    }
}
