package ar.edu.itba.sds.tp4.system2.model;

public record System2Geometry(double diameter, double obstacleRadius, double particleRadius) {
    public System2Geometry {
        if (diameter <= 0.0) {
            throw new IllegalArgumentException("diameter must be positive.");
        }
        if (obstacleRadius <= 0.0) {
            throw new IllegalArgumentException("obstacleRadius must be positive.");
        }
        if (particleRadius <= 0.0) {
            throw new IllegalArgumentException("particleRadius must be positive.");
        }
        if (diameter / 2.0 - particleRadius <= obstacleRadius + particleRadius) {
            throw new IllegalArgumentException("The annulus available to particle centers must have positive width.");
        }
    }

    public double outerRadius() {
        return diameter / 2.0;
    }

    public double innerTravelRadius() {
        return obstacleRadius + particleRadius;
    }

    public double outerTravelRadius() {
        return outerRadius() - particleRadius;
    }
}
