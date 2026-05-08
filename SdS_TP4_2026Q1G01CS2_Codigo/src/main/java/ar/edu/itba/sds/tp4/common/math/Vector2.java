package ar.edu.itba.sds.tp4.common.math;

public record Vector2(double x, double y) {
    public static final Vector2 ZERO = new Vector2(0.0, 0.0);

    public Vector2 add(Vector2 other) {
        return new Vector2(x + other.x, y + other.y);
    }

    public Vector2 subtract(Vector2 other) {
        return new Vector2(x - other.x, y - other.y);
    }

    public Vector2 multiply(double scalar) {
        return new Vector2(x * scalar, y * scalar);
    }

    public double dot(Vector2 other) {
        return x * other.x + y * other.y;
    }

    public double normSquared() {
        return this.dot(this);
    }

    public double norm() {
        return Math.hypot(x, y);
    }

    public Vector2 normalized() {
        double norm = norm();
        if (norm == 0.0) {
            throw new IllegalArgumentException("Cannot normalize the zero vector.");
        }
        return new Vector2(x / norm, y / norm);
    }

    public double distanceTo(Vector2 other) {
        return subtract(other).norm();
    }
}
