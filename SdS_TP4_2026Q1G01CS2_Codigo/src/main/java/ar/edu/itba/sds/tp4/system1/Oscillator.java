package ar.edu.itba.sds.tp4.system1;

public final class Oscillator {
    private final double mass;
    private final double springConstant;
    private final double gamma;

    public Oscillator(System1Parameters parameters) {
        this(parameters.mass(), parameters.springConstant(), parameters.gamma());
    }

    public Oscillator(double mass, double springConstant, double gamma) {
        this.mass = mass;
        this.springConstant = springConstant;
        this.gamma = gamma;
    }

    public double acceleration(double position, double velocity) {
        return (-springConstant * position - gamma * velocity) / mass;
    }
}
