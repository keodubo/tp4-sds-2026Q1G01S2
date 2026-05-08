package ar.edu.itba.sds.tp4.system2.output;

public record System2OutputConfig(
        int stateStride,
        int fullContactStride,
        int boundaryForceStride
) {
    public static final int OBSTACLE_CONTACT_STRIDE = 1;

    public static System2OutputConfig fullResolution() {
        return new System2OutputConfig(1, 1, 1);
    }

    public System2OutputConfig {
        if (stateStride <= 0) {
            throw new IllegalArgumentException("stateStride must be positive.");
        }
        if (fullContactStride <= 0) {
            throw new IllegalArgumentException("fullContactStride must be positive.");
        }
        if (boundaryForceStride <= 0) {
            throw new IllegalArgumentException("boundaryForceStride must be positive.");
        }
    }
}
