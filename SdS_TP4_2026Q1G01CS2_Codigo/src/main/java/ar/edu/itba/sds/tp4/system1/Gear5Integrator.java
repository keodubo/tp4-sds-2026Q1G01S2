package ar.edu.itba.sds.tp4.system1;

import java.util.ArrayList;
import java.util.List;

public final class Gear5Integrator implements Integrator {
    private static final double[] ALPHA = {
            3.0 / 16.0,
            251.0 / 360.0,
            1.0,
            11.0 / 18.0,
            1.0 / 6.0,
            1.0 / 60.0
    };
    private static final double[] FACTORIAL = {1.0, 1.0, 2.0, 6.0, 24.0, 120.0};

    @Override
    public String methodName() {
        return "gear5";
    }

    @Override
    public List<OscillatorState> integrate(System1Parameters parameters, double dt) {
        Oscillator oscillator = new Oscillator(parameters);
        int steps = (int) Math.round(parameters.finalTime() / dt);
        List<OscillatorState> states = new ArrayList<>(steps + 1);
        double[] derivatives = initialDerivatives(parameters);

        states.add(new OscillatorState(0.0, derivatives[0], derivatives[1]));
        for (int step = 0; step < steps; step++) {
            double[] predicted = predict(derivatives, dt);
            double evaluatedAcceleration = oscillator.acceleration(predicted[0], predicted[1]);
            double deltaR2 = (evaluatedAcceleration - predicted[2]) * dt * dt / 2.0;
            derivatives = correct(predicted, deltaR2, dt);
            states.add(new OscillatorState((step + 1) * dt, derivatives[0], derivatives[1]));
        }

        return states;
    }

    static double[] initialDerivatives(System1Parameters parameters) {
        double[] derivatives = new double[6];
        double c = parameters.gamma() / parameters.mass();
        double w2 = parameters.springConstant() / parameters.mass();
        derivatives[0] = parameters.initialPosition();
        derivatives[1] = parameters.initialVelocity();
        for (int index = 0; index <= 3; index++) {
            derivatives[index + 2] = -c * derivatives[index + 1] - w2 * derivatives[index];
        }
        return derivatives;
    }

    private static double[] predict(double[] derivatives, double dt) {
        double[] predicted = new double[6];
        for (int q = 0; q < predicted.length; q++) {
            double value = 0.0;
            for (int j = q; j < derivatives.length; j++) {
                value += derivatives[j] * Math.pow(dt, j - q) / FACTORIAL[j - q];
            }
            predicted[q] = value;
        }
        return predicted;
    }

    private static double[] correct(double[] predicted, double deltaR2, double dt) {
        double[] corrected = new double[6];
        for (int q = 0; q < corrected.length; q++) {
            corrected[q] = predicted[q] + ALPHA[q] * deltaR2 * FACTORIAL[q] / Math.pow(dt, q);
        }
        return corrected;
    }
}
