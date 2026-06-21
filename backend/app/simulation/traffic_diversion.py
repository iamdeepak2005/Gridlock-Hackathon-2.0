"""
Traffic Diversion Simulation Engine.
Uses OSMnx to download road graphs and NetworkX to compute diversions.
"""

import math
from typing import Optional

try:
    import osmnx as ox
    import networkx as nx
    OSMNX_AVAILABLE = True
except ImportError:
    OSMNX_AVAILABLE = False

from app.config import settings


class TrafficDiversionEngine:
    """
    Simulates traffic diversion when events block roads.
    Downloads local road graph, blocks affected segments,
    and computes alternative routes.
    """

    def __init__(self):
        self._graph_cache: dict[str, any] = {}
        if OSMNX_AVAILABLE:
            ox.settings.cache_folder = settings.OSMNX_CACHE_DIR

    def simulate(
        self,
        event_lat: float,
        event_lng: float,
        road_closure: bool = True,
        impact_radius_m: float = 500,
    ) -> dict:
        """
        Run traffic diversion simulation.

        Args:
            event_lat: Event latitude
            event_lng: Event longitude
            road_closure: Whether roads are actually closed
            impact_radius_m: Radius of impact in meters

        Returns:
            Dict with blocked roads, alternative routes, congestion score, etc.
        """
        if not OSMNX_AVAILABLE:
            return self._fallback_simulation(event_lat, event_lng, road_closure, impact_radius_m)

        try:
            # Step 1: Download/cache road graph for the area
            graph = self._get_road_graph(event_lat, event_lng, impact_radius_m)

            # Step 2: Find nearest node to event
            event_node = ox.nearest_nodes(graph, event_lng, event_lat)

            # Step 3: Identify affected edges within impact radius
            affected_edges = self._find_affected_edges(
                graph, event_lat, event_lng, impact_radius_m
            )

            # Step 4: Get blocked road details
            blocked_roads = self._get_blocked_road_info(graph, affected_edges)

            # Step 5: If road_closure, remove edges and compute alternatives
            alternative_routes = []
            extra_travel_time = 0.0

            if road_closure and affected_edges:
                alt_graph = graph.copy()
                for u, v, key in affected_edges:
                    if alt_graph.has_edge(u, v, key):
                        alt_graph.remove_edge(u, v, key)

                alternative_routes, extra_travel_time = self._compute_alternative_routes(
                    graph, alt_graph, event_node, affected_edges
                )

            # Step 6: Compute congestion risk score
            congestion_score = self._compute_congestion_score(
                graph, affected_edges, road_closure, impact_radius_m
            )

            # Step 7: Identify affected junctions
            affected_junctions = self._find_affected_junctions(
                graph, event_lat, event_lng, impact_radius_m
            )

            # Step 8: Get normal roads inside the boundary
            normal_roads = []
            for u, v, k, data in graph.edges(keys=True, data=True):
                if "geometry" in data:
                    coords = [[point[1], point[0]] for point in data["geometry"].coords]
                else:
                    u_data = graph.nodes[u]
                    v_data = graph.nodes[v]
                    coords = [[u_data["y"], u_data["x"]], [v_data["y"], v_data["x"]]]
                
                name = data.get("name", "Unknown Road")
                if isinstance(name, list):
                    name = name[0]
                
                speed = data.get("maxspeed", "40")
                if isinstance(speed, list):
                    speed = speed[0]
                try:
                    speed_val = int("".join(filter(str.isdigit, str(speed))))
                except (ValueError, TypeError):
                    speed_val = 30
                    
                normal_roads.append({
                    "name": name,
                    "coords": coords,
                    "speed_kph": speed_val,
                    "flow_level": "normal" if speed_val >= 35 else "congested",
                })

            return {
                "blocked_roads": blocked_roads,
                "alternative_routes": alternative_routes,
                "normal_roads": normal_roads[:200], # Limit to avoid huge payload
                "estimated_extra_travel_time": round(extra_travel_time, 1),
                "congestion_risk_score": round(congestion_score, 1),
                "affected_junctions": affected_junctions,
            }

        except Exception as e:
            print(f"[DIVERSION] Error in simulation: {e}")
            return self._fallback_simulation(event_lat, event_lng, road_closure, impact_radius_m)

    def _get_road_graph(self, lat: float, lng: float, radius_m: float):
        """Download or retrieve cached road graph."""
        import os
        # Cache key based on rough grid cell
        cache_key = f"{round(lat, 2)}_{round(lng, 2)}"

        if cache_key in self._graph_cache:
            return self._graph_cache[cache_key]

        # Persistent disk cache check
        cache_dir = os.path.join(settings.OSMNX_CACHE_DIR, "graphml")
        os.makedirs(cache_dir, exist_ok=True)
        file_path = os.path.join(cache_dir, f"graph_{cache_key}.graphml")
        
        if os.path.exists(file_path):
            print(f"[DIVERSION] Loading road graph from disk cache: {file_path}")
            try:
                graph = ox.load_graphml(file_path)
                self._graph_cache[cache_key] = graph
                return graph
            except Exception as e:
                print(f"[DIVERSION] Disk cache load failed: {e}")

        print(f"[DIVERSION] Downloading road graph for ({lat:.4f}, {lng:.4f})...")
        graph = ox.graph_from_point(
            (lat, lng),
            dist=max(radius_m * 1.2, 600),
            network_type="drive",
        )
        
        # Save to disk cache for instantaneous future loads
        try:
            ox.save_graphml(graph, file_path)
            print(f"[DIVERSION] Saved road graph to disk cache: {file_path}")
        except Exception as e:
            print(f"[DIVERSION] Disk cache save failed: {e}")

        self._graph_cache[cache_key] = graph
        print(f"[DIVERSION] Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        return graph

    def _find_affected_edges(self, graph, lat, lng, radius_m) -> list:
        """Find all road edges within impact radius of the event."""
        affected = []

        for u, v, key, data in graph.edges(keys=True, data=True):
            u_data = graph.nodes[u]
            v_data = graph.nodes[v]

            # Check if midpoint of edge is within radius
            mid_lat = (u_data["y"] + v_data["y"]) / 2
            mid_lng = (u_data["x"] + v_data["x"]) / 2

            dist = self._haversine(lat, lng, mid_lat, mid_lng)
            if dist <= radius_m:
                affected.append((u, v, key))

        return affected

    def _get_blocked_road_info(self, graph, affected_edges) -> list:
        """Extract road information for blocked edges."""
        roads = []
        seen = set()

        for u, v, key in affected_edges:
            if (u, v) in seen:
                continue
            seen.add((u, v))

            data = graph.edges[u, v, key]
            name = data.get("name", "Unknown Road")
            if isinstance(name, list):
                name = name[0]
            length = data.get("length", None)

            if "geometry" in data:
                coords = [[point[1], point[0]] for point in data["geometry"].coords]
            else:
                u_data = graph.nodes[u]
                v_data = graph.nodes[v]
                coords = [[u_data["y"], u_data["x"]], [v_data["y"], v_data["x"]]]

            roads.append({
                "name": name,
                "from_node": int(u),
                "to_node": int(v),
                "length_m": round(float(length), 1) if length else None,
                "coords": coords,
            })

        return roads[:20]  # Limit output

    def _compute_alternative_routes(self, original, modified, event_node, affected) -> tuple:
        """Compute alternative routes around the blocked area."""
        routes = []
        extra_time_sum = 0.0
        count = 0

        # Get boundary nodes (endpoints of affected edges)
        boundary_nodes = set()
        for u, v, _ in affected:
            boundary_nodes.add(u)
            boundary_nodes.add(v)

        # For a subset of boundary node pairs, find alternative paths
        boundary_list = list(boundary_nodes)[:6]

        for i in range(len(boundary_list)):
            for j in range(i + 1, len(boundary_list)):
                src, dst = boundary_list[i], boundary_list[j]
                try:
                    # Original shortest path length
                    orig_length = nx.shortest_path_length(original, src, dst, weight="length")

                    # Alternative path
                    if nx.has_path(modified, src, dst):
                        alt_path = nx.shortest_path(modified, src, dst, weight="length")
                        alt_length = nx.shortest_path_length(modified, src, dst, weight="length")

                        # Extract coordinates following actual curved road geometries
                        coords = []
                        for idx in range(len(alt_path) - 1):
                            u, v = alt_path[idx], alt_path[idx+1]
                            edge_data = modified.get_edge_data(u, v)
                            if edge_data:
                                key = list(edge_data.keys())[0]
                                data = edge_data[key]
                                if "geometry" in data:
                                    geom_coords = [[pt[1], pt[0]] for pt in data["geometry"].coords]
                                    u_data = modified.nodes[u]
                                    first_dist = math.hypot(geom_coords[0][0] - u_data["y"], geom_coords[0][1] - u_data["x"])
                                    last_dist = math.hypot(geom_coords[-1][0] - u_data["y"], geom_coords[-1][1] - u_data["x"])
                                    if last_dist < first_dist:
                                        geom_coords = geom_coords[::-1]
                                    
                                    for pt in geom_coords:
                                        if not coords or coords[-1] != pt:
                                            coords.append(pt)
                                else:
                                    u_data = modified.nodes[u]
                                    v_data = modified.nodes[v]
                                    if not coords or coords[-1] != [u_data["y"], u_data["x"]]:
                                        coords.append([u_data["y"], u_data["x"]])
                                    coords.append([v_data["y"], v_data["x"]])
                            else:
                                u_data = modified.nodes[u]
                                v_data = modified.nodes[v]
                                if not coords or coords[-1] != [u_data["y"], u_data["x"]]:
                                    coords.append([u_data["y"], u_data["x"]])
                                coords.append([v_data["y"], v_data["x"]])

                        # Estimate time (assuming 30 km/h average urban speed)
                        avg_speed_ms = 30 * 1000 / 3600  # 8.33 m/s
                        time_min = alt_length / avg_speed_ms / 60

                        routes.append({
                            "route_coords": coords,
                            "distance_m": round(alt_length, 1),
                            "estimated_time_min": round(time_min, 1),
                        })

                        extra_time_sum += max(0, (alt_length - orig_length) / avg_speed_ms / 60)
                        count += 1

                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue

        avg_extra = extra_time_sum / count if count > 0 else 0.0
        return routes[:5], round(avg_extra, 1)

    def _compute_congestion_score(self, graph, affected_edges, closure, radius) -> float:
        """
        Estimate congestion risk score (0-100) based on:
        - Number of affected edges
        - Road centrality of affected segments
        - Whether closure is complete
        """
        if not affected_edges:
            return 10.0

        total_edges = graph.number_of_edges()
        affected_ratio = len(affected_edges) / total_edges if total_edges > 0 else 0

        # Edge betweenness centrality (sampled for performance)
        try:
            k = min(8, graph.number_of_nodes())
            centrality = nx.edge_betweenness_centrality(graph, k=k)

            affected_centrality = []
            for u, v, key in affected_edges:
                c = centrality.get((u, v), 0)
                affected_centrality.append(c)

            avg_centrality = sum(affected_centrality) / len(affected_centrality) if affected_centrality else 0
        except Exception:
            avg_centrality = 0.1

        # Score components
        score = 0.0
        score += min(affected_ratio * 500, 30)  # Up to 30 from affected ratio
        score += min(avg_centrality * 1000, 40)  # Up to 40 from centrality
        score += 20 if closure else 5             # 20 for full closure
        score += min(radius / 100, 10)            # Up to 10 from radius

        return min(100, max(0, score))

    def _find_affected_junctions(self, graph, lat, lng, radius_m) -> list[str]:
        """Find named junctions/intersections within impact radius."""
        junctions = []

        for node, data in graph.nodes(data=True):
            dist = self._haversine(lat, lng, data.get("y", 0), data.get("x", 0))
            if dist <= radius_m:
                # Check if node is an intersection (degree > 2)
                if graph.degree(node) > 2:
                    # Try to get nearby street names
                    streets = set()
                    for _, _, edge_data in graph.edges(node, data=True):
                        name = edge_data.get("name", None)
                        if name:
                            if isinstance(name, list):
                                streets.update(name)
                            else:
                                streets.add(name)
                    if streets:
                        junctions.append(" & ".join(list(streets)[:2]))

        return list(set(junctions))[:10]

    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2) -> float:
        """Calculate distance in meters between two lat/lng points."""
        R = 6371000  # Earth radius in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = (math.sin(dphi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def _bend_coords(self, coords: list[list[float]], bend_amount: float = 0.0003) -> list[list[float]]:
        """Add slight smooth sinusoidal curves to straight coordinate paths to simulate realistic roads."""
        if len(coords) < 2:
            return coords
        
        result = []
        for i in range(len(coords) - 1):
            p1, p2 = coords[i], coords[i+1]
            y1, x1 = p1
            y2, x2 = p2
            
            num_sub = 5
            for j in range(num_sub):
                t = j / num_sub
                yt = y1 + (y2 - y1) * t
                xt = x1 + (x2 - x1) * t
                
                offset = bend_amount * math.sin(t * math.pi)
                length = math.hypot(x2 - x1, y2 - y1)
                if length > 0:
                    dy = -(x2 - x1) / length * offset
                    dx = (y2 - y1) / length * offset
                    yt += dy
                    xt += dx
                
                result.append([yt, xt])
        
        result.append(coords[-1])
        return result

    def _fallback_simulation(self, lat, lng, closure, radius) -> dict:
        """Fallback simulation when OSMnx is not available."""
        base_score = 50 if closure else 20
        radius_bonus = min(radius / 100, 20)

        # Generate synthetic road grid centered at lat, lng with realistic curves
        normal_roads = [
            {
                "name": "Outer Ring Road (Main N-S Corridor)",
                "coords": self._bend_coords([[lat - 0.008, lng], [lat, lng], [lat + 0.008, lng]], 0.0004),
                "speed_kph": 50,
                "flow_level": "normal"
            },
            {
                "name": "Hosur Road Bypass (Main E-W)",
                "coords": self._bend_coords([[lat, lng - 0.008], [lat, lng], [lat, lng + 0.008]], -0.0004),
                "speed_kph": 45,
                "flow_level": "normal"
            },
            {
                "name": "1st Cross Road (Bypass East)",
                "coords": self._bend_coords([[lat - 0.008, lng + 0.004], [lat, lng + 0.004], [lat + 0.008, lng + 0.004]], 0.0003),
                "speed_kph": 30,
                "flow_level": "normal"
            },
            {
                "name": "2nd Cross Road (Bypass West)",
                "coords": self._bend_coords([[lat - 0.008, lng - 0.004], [lat, lng - 0.004], [lat + 0.008, lng - 0.004]], -0.0003),
                "speed_kph": 30,
                "flow_level": "normal"
            },
            {
                "name": "80 Feet Road (Link North)",
                "coords": self._bend_coords([[lat + 0.004, lng - 0.008], [lat + 0.004, lng], [lat + 0.004, lng + 0.008]], 0.0002),
                "speed_kph": 40,
                "flow_level": "normal"
            },
            {
                "name": "100 Feet Road (Link South)",
                "coords": self._bend_coords([[lat - 0.004, lng - 0.008], [lat - 0.004, lng], [lat - 0.004, lng + 0.008]], -0.0002),
                "speed_kph": 40,
                "flow_level": "normal"
            }
        ]

        blocked_roads = []
        alternative_routes = []
        affected_junctions = [f"Junction near ({lat:.4f}, {lng:.4f})"]

        if closure:
            blocked_roads = [
                {
                    "name": "Outer Ring Road (Closed Section)",
                    "from_node": 101,
                    "to_node": 102,
                    "length_m": radius,
                    "coords": self._bend_coords([[lat - 0.002, lng], [lat + 0.002, lng]], 0.0001)
                }
            ]
            alternative_routes = [
                {
                    "route_coords": self._bend_coords([
                        [lat - 0.004, lng],
                        [lat - 0.004, lng + 0.004],
                        [lat, lng + 0.004],
                        [lat + 0.004, lng + 0.004],
                        [lat + 0.004, lng],
                    ], 0.0003),
                    "distance_m": radius * 2.5,
                    "estimated_time_min": round((radius * 2.5) / 8.33 / 60, 1)
                }
            ]
            affected_junctions = [
                "Outer Ring Rd & 100 Feet Rd",
                "Outer Ring Rd & 80 Feet Rd",
                "Bypass East & 100 Feet Rd"
            ]

        return {
            "blocked_roads": blocked_roads,
            "alternative_routes": alternative_routes,
            "normal_roads": normal_roads,
            "estimated_extra_travel_time": round(radius / 500 * 5, 1) if closure else 0.0,
            "congestion_risk_score": round(min(100, base_score + radius_bonus), 1),
            "affected_junctions": affected_junctions,
        }


# Global instance
diversion_engine = TrafficDiversionEngine()
