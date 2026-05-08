package ar.edu.itba.sds.tp4.system2.contacts;

import ar.edu.itba.sds.tp4.common.math.Vector2;
import ar.edu.itba.sds.tp4.system2.model.System2Geometry;
import ar.edu.itba.sds.tp4.system2.state.DynamicParticle;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public final class CellIndexParticleContactFinder {
    private static final double CELL_SIZE_EPSILON = 1e-9;
    private static final int[] NEIGHBOR_DX = {1, -1, 0, 1};
    private static final int[] NEIGHBOR_DY = {0, 1, 1, 1};

    public List<Contact> findContacts(List<DynamicParticle> particles, System2Geometry geometry) {
        if (particles == null) {
            throw new IllegalArgumentException("particles must not be null.");
        }
        if (geometry == null) {
            throw new IllegalArgumentException("geometry must not be null.");
        }
        if (particles.size() < 2) {
            return List.of();
        }

        double maxRadius = maxRadius(particles);
        double boxSide = 2.0 * geometry.outerRadius();
        int cellsPerSide = Math.max(1, (int) Math.floor(boxSide / (2.0 * maxRadius + CELL_SIZE_EPSILON)));
        double cellSize = boxSide / cellsPerSide;
        List<List<Integer>> cells = new ArrayList<>(cellsPerSide * cellsPerSide);
        for (int index = 0; index < cellsPerSide * cellsPerSide; index++) {
            cells.add(new ArrayList<>());
        }

        for (int index = 0; index < particles.size(); index++) {
            DynamicParticle particle = particles.get(index);
            int cx = coordinateToCell(particle.position().x(), geometry.outerRadius(), cellSize, cellsPerSide);
            int cy = coordinateToCell(particle.position().y(), geometry.outerRadius(), cellSize, cellsPerSide);
            cells.get(cellIndex(cx, cy, cellsPerSide)).add(index);
        }

        List<Contact> contacts = new ArrayList<>();
        for (int cy = 0; cy < cellsPerSide; cy++) {
            for (int cx = 0; cx < cellsPerSide; cx++) {
                List<Integer> cell = cells.get(cellIndex(cx, cy, cellsPerSide));
                addSameCellContacts(particles, cell, contacts);
                addNeighborCellContacts(particles, cells, cellsPerSide, cx, cy, cell, contacts);
            }
        }

        contacts.sort(Comparator
                .comparingInt(Contact::particleId)
                .thenComparingInt(Contact::otherParticleId));
        return List.copyOf(contacts);
    }

    private void addSameCellContacts(List<DynamicParticle> particles, List<Integer> cell, List<Contact> contacts) {
        for (int i = 0; i < cell.size(); i++) {
            for (int j = i + 1; j < cell.size(); j++) {
                addContactIfOverlapping(particles.get(cell.get(i)), particles.get(cell.get(j)), contacts);
            }
        }
    }

    private void addNeighborCellContacts(
            List<DynamicParticle> particles,
            List<List<Integer>> cells,
            int cellsPerSide,
            int cx,
            int cy,
            List<Integer> cell,
            List<Contact> contacts
    ) {
        for (int offset = 0; offset < NEIGHBOR_DX.length; offset++) {
            int nx = cx + NEIGHBOR_DX[offset];
            int ny = cy + NEIGHBOR_DY[offset];
            if (nx < 0 || nx >= cellsPerSide || ny < 0 || ny >= cellsPerSide) {
                continue;
            }
            List<Integer> neighborCell = cells.get(cellIndex(nx, ny, cellsPerSide));
            for (int particleIndex : cell) {
                for (int otherIndex : neighborCell) {
                    addContactIfOverlapping(particles.get(particleIndex), particles.get(otherIndex), contacts);
                }
            }
        }
    }

    private void addContactIfOverlapping(DynamicParticle first, DynamicParticle second, List<Contact> contacts) {
        DynamicParticle particle = first.id() <= second.id() ? first : second;
        DynamicParticle other = first.id() <= second.id() ? second : first;
        Vector2 separation = other.position().subtract(particle.position());
        double distance = separation.norm();
        double overlap = particle.radius() + other.radius() - distance;
        if (overlap <= 0.0) {
            return;
        }
        contacts.add(Contact.particleParticle(
                particle.id(),
                other.id(),
                distance,
                overlap,
                separation.normalized()
        ));
    }

    private double maxRadius(List<DynamicParticle> particles) {
        double maxRadius = 0.0;
        for (DynamicParticle particle : particles) {
            maxRadius = Math.max(maxRadius, particle.radius());
        }
        return maxRadius;
    }

    private int coordinateToCell(double coordinate, double outerRadius, double cellSize, int cellsPerSide) {
        int cell = (int) Math.floor((coordinate + outerRadius) / cellSize);
        if (cell < 0) {
            return 0;
        }
        if (cell >= cellsPerSide) {
            return cellsPerSide - 1;
        }
        return cell;
    }

    private int cellIndex(int cx, int cy, int cellsPerSide) {
        return cy * cellsPerSide + cx;
    }
}
