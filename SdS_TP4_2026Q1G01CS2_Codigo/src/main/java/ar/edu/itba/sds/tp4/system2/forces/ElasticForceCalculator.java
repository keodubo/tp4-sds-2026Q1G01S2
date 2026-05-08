package ar.edu.itba.sds.tp4.system2.forces;

import ar.edu.itba.sds.tp4.common.math.Vector2;
import ar.edu.itba.sds.tp4.system2.contacts.Contact;
import ar.edu.itba.sds.tp4.system2.contacts.ContactType;
import ar.edu.itba.sds.tp4.system2.state.DynamicParticle;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class ElasticForceCalculator {
    private final double stiffness;

    public ElasticForceCalculator(double stiffness) {
        if (stiffness <= 0.0) {
            throw new IllegalArgumentException("stiffness must be positive.");
        }
        this.stiffness = stiffness;
    }

    public ForceSnapshot evaluate(Collection<DynamicParticle> particles, List<Contact> contacts) {
        if (particles == null) {
            throw new IllegalArgumentException("particles must not be null.");
        }
        if (contacts == null) {
            throw new IllegalArgumentException("contacts must not be null.");
        }

        Map<Integer, Vector2> particleForces = new HashMap<>();
        for (DynamicParticle particle : particles) {
            particleForces.put(particle.id(), Vector2.ZERO);
        }

        List<ContactForce> contactForces = new ArrayList<>();
        Vector2 obstacleForce = Vector2.ZERO;
        Vector2 wallForce = Vector2.ZERO;

        for (Contact contact : contacts) {
            Vector2 forceOnParticle = contact.normalFromParticleToOther().multiply(-stiffness * contact.overlap());
            Vector2 forceOnOther = forceOnParticle.multiply(-1.0);
            contactForces.add(new ContactForce(contact, forceOnParticle, forceOnOther));

            particleForces.compute(contact.particleId(), (id, current) -> addToExistingForce(id, current, forceOnParticle));

            if (contact.type() == ContactType.PARTICLE_PARTICLE) {
                particleForces.compute(
                        contact.otherParticleId(),
                        (id, current) -> addToExistingForce(id, current, forceOnOther)
                );
            } else if (contact.type() == ContactType.PARTICLE_OBSTACLE) {
                obstacleForce = obstacleForce.add(forceOnOther);
            } else if (contact.type() == ContactType.PARTICLE_WALL) {
                wallForce = wallForce.add(forceOnOther);
            }
        }

        return new ForceSnapshot(
                Map.copyOf(particleForces),
                List.copyOf(contactForces),
                obstacleForce,
                wallForce
        );
    }

    private Vector2 addToExistingForce(int particleId, Vector2 currentForce, Vector2 forceToAdd) {
        if (currentForce == null) {
            throw new IllegalArgumentException("Contact references unknown particle id " + particleId + ".");
        }
        return currentForce.add(forceToAdd);
    }
}
