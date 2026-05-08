package ar.edu.itba.sds.tp4.system1;

import java.util.List;

public interface Integrator {
    String methodName();

    List<OscillatorState> integrate(System1Parameters parameters, double dt);
}
