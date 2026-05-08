package ar.edu.itba.sds.tp4.system2.model;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class System2GeometryTest {
    @Test
    void geometryUsesDiameterAsInputAndComputesTravelRadii() {
        System2Geometry geometry = new System2Geometry(80.0, 1.0, 1.0);

        assertEquals(40.0, geometry.outerRadius());
        assertEquals(2.0, geometry.innerTravelRadius());
        assertEquals(39.0, geometry.outerTravelRadius());
    }
}
