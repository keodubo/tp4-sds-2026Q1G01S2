package ar.edu.itba.sds.tp4.system2.output;

import ar.edu.itba.sds.tp4.system2.model.System2Config;
import ar.edu.itba.sds.tp4.system2.model.System2Geometry;

public record System2OutputMetadata(
        String runId,
        int realization,
        System2Config config,
        String integrator,
        int stateStride,
        int fullContactStride,
        int obstacleContactStride,
        int boundaryForceStride
) {
    public static final String LENGTH_UNIT = "m";
    public static final String MASS_UNIT = "kg";
    public static final String TIME_UNIT = "s";
    public static final String NORMAL_CONVENTION =
            "contacts file stores n_ij from body i to body j; force_on_i = -k * overlap * n_ij";

    public System2OutputMetadata(
            String runId,
            int realization,
            System2Config config,
            String integrator,
            int stateStride,
            int contactStride
    ) {
        this(
                runId,
                realization,
                config,
                integrator,
                stateStride,
                contactStride,
                System2OutputConfig.OBSTACLE_CONTACT_STRIDE,
                contactStride
        );
    }

    public System2OutputMetadata {
        if (runId == null || runId.isBlank()) {
            throw new IllegalArgumentException("runId must not be blank.");
        }
        if (realization < 0) {
            throw new IllegalArgumentException("realization must be non-negative.");
        }
        if (config == null) {
            throw new IllegalArgumentException("config must not be null.");
        }
        if (integrator == null || integrator.isBlank()) {
            throw new IllegalArgumentException("integrator must not be blank.");
        }
        if (stateStride <= 0) {
            throw new IllegalArgumentException("stateStride must be positive.");
        }
        if (fullContactStride <= 0) {
            throw new IllegalArgumentException("fullContactStride must be positive.");
        }
        if (obstacleContactStride <= 0) {
            throw new IllegalArgumentException("obstacleContactStride must be positive.");
        }
        if (boundaryForceStride <= 0) {
            throw new IllegalArgumentException("boundaryForceStride must be positive.");
        }
    }

    public String toJson() {
        System2Geometry geometry = config.geometry();
        String indent = "  ";
        String nestedIndent = "    ";

        return "{\n"
                + jsonField(indent, "system", "system2") + ",\n"
                + jsonField(indent, "run_id", runId) + ",\n"
                + jsonField(indent, "realization", realization) + ",\n"
                + jsonField(indent, "seed", config.seed()) + ",\n"
                + jsonField(indent, "N", config.particleCount()) + ",\n"
                + jsonField(indent, "L", geometry.diameter()) + ",\n"
                + jsonField(indent, "L_meaning", "diameter") + ",\n"
                + jsonField(indent, "R", geometry.outerRadius()) + ",\n"
                + jsonField(indent, "obstacle_radius", geometry.obstacleRadius()) + ",\n"
                + jsonField(indent, "particle_radius", geometry.particleRadius()) + ",\n"
                + jsonField(indent, "particle_mass", config.particleMass()) + ",\n"
                + jsonField(indent, "initial_speed", config.initialSpeed()) + ",\n"
                + jsonField(indent, "k", config.stiffness()) + ",\n"
                + jsonField(indent, "dt", config.dt()) + ",\n"
                + jsonField(indent, "steps", config.steps()) + ",\n"
                + jsonField(indent, "integrator", integrator) + ",\n"
                + jsonField(indent, "state_stride", stateStride) + ",\n"
                + jsonField(indent, "contact_stride", fullContactStride) + ",\n"
                + jsonField(indent, "full_contact_stride", fullContactStride) + ",\n"
                + jsonField(indent, "obstacle_contact_stride", obstacleContactStride) + ",\n"
                + jsonField(indent, "boundary_force_stride", boundaryForceStride) + ",\n"
                + jsonField(
                        indent,
                        "state_sampling",
                        "states.csv includes steps divisible by state_stride or full_contact_stride"
                ) + ",\n"
                + indent + "\"units\": {\n"
                + jsonField(nestedIndent, "length", LENGTH_UNIT) + ",\n"
                + jsonField(nestedIndent, "mass", MASS_UNIT) + ",\n"
                + jsonField(nestedIndent, "time", TIME_UNIT) + "\n"
                + indent + "},\n"
                + jsonField(indent, "normal_convention", NORMAL_CONVENTION) + "\n"
                + "}\n";
    }

    private String jsonField(String indent, String key, String value) {
        return indent + "\"" + escapeJson(key) + "\": \"" + escapeJson(value) + "\"";
    }

    private String jsonField(String indent, String key, int value) {
        return indent + "\"" + escapeJson(key) + "\": " + value;
    }

    private String jsonField(String indent, String key, long value) {
        return indent + "\"" + escapeJson(key) + "\": " + value;
    }

    private String jsonField(String indent, String key, double value) {
        return indent + "\"" + escapeJson(key) + "\": " + Double.toString(value);
    }

    private String escapeJson(String value) {
        StringBuilder builder = new StringBuilder();
        for (int index = 0; index < value.length(); index++) {
            char character = value.charAt(index);
            if (character == '"' || character == '\\') {
                builder.append('\\');
            }
            builder.append(character);
        }
        return builder.toString();
    }
}
