package ar.edu.itba.sds.tp4.system2.forces;

import ar.edu.itba.sds.tp4.common.math.Vector2;

import java.util.List;
import java.util.Map;

public record ForceSnapshot(
        Map<Integer, Vector2> particleForces,
        List<ContactForce> contactForces,
        Vector2 obstacleForce,
        Vector2 wallForce
) {
    public ForceSnapshot {
        if (particleForces == null) {
            throw new IllegalArgumentException("particleForces must not be null.");
        }
        if (contactForces == null) {
            throw new IllegalArgumentException("contactForces must not be null.");
        }
        if (obstacleForce == null) {
            throw new IllegalArgumentException("obstacleForce must not be null.");
        }
        if (wallForce == null) {
            throw new IllegalArgumentException("wallForce must not be null.");
        }
        particleForces = Map.copyOf(particleForces);
        contactForces = List.copyOf(contactForces);
    }
}
