"""
Knowledge Graph System for Archivista AI.
Implements interactive knowledge graph visualization and graph-based recommendations.
"""

import json
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
import networkx as nx
import matplotlib.pyplot as plt
import io
import base64

from ...database.models.base import Document, ConceptEntity, ConceptRelationship
from ...core.errors.error_handler import handle_errors


@dataclass
class GraphNode:
    """Node in the knowledge graph."""
    id: str
    label: str
    type: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    position: Optional[Tuple[float, float]] = None


@dataclass
class GraphEdge:
    """Edge in the knowledge graph."""
    source: str
    target: str
    type: str
    weight: float
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphCluster:
    """Cluster of related nodes."""
    id: str
    name: str
    nodes: List[str]
    center_node: str
    cohesion_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeGraphBuilder:
    """Builds and maintains knowledge graph from documents."""

    def __init__(self, document_repository):
        """Initialize knowledge graph builder.

        Args:
            document_repository: Document repository
        """
        self.document_repository = document_repository
        self.logger = logging.getLogger(__name__)

        # Graph storage
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        self.clusters: Dict[str, GraphCluster] = {}

        # Graph analysis
        self.graph = nx.Graph()

    @handle_errors(operation="build_knowledge_graph", component="knowledge_graph_builder")
    def build_knowledge_graph(self, project_id: str, user_id: str = None) -> Dict[str, Any]:
        """Build knowledge graph from project documents.

        Args:
            project_id: Project ID
            user_id: User ID for personalization

        Returns:
            Knowledge graph data
        """
        try:
            # Get project documents
            documents = self.document_repository.get_by_project(project_id)

            # Extract entities and relationships
            entities = self._extract_all_entities(documents, user_id)
            relationships = self._extract_all_relationships(documents, entities)

            # Build graph structure
            self._build_graph_structure(entities, relationships)

            # Identify clusters
            self._identify_clusters()

            # Calculate graph metrics
            metrics = self._calculate_graph_metrics()

            return {
                'nodes': [node.__dict__ for node in self.nodes.values()],
                'edges': [edge.__dict__ for edge in self.edges.values()],
                'clusters': [cluster.__dict__ for cluster in self.clusters.values()],
                'metrics': metrics,
                'build_timestamp': datetime.utcnow().isoformat(),
                'document_count': len(documents),
                'entity_count': len(entities),
                'relationship_count': len(relationships)
            }

        except Exception as e:
            self.logger.error(f"Error building knowledge graph: {e}")
            raise

    def _extract_all_entities(self, documents: List[Document], user_id: str = None) -> List[ConceptEntity]:
        """Extract all entities from documents."""
        entities = []

        for document in documents:
            # Extract entities using document intelligence
            try:
                from .document_intelligence import EntityExtractor
                extractor = EntityExtractor()

                doc_entities = extractor.extract_entities(document)
                entities.extend(doc_entities)

            except Exception as e:
                self.logger.error(f"Error extracting entities from {document.file_name}: {e}")

        return entities

    def _extract_all_relationships(
        self,
        documents: List[Document],
        entities: List[ConceptEntity]
    ) -> List[ConceptRelationship]:
        """Extract all relationships from documents."""
        relationships = []

        for document in documents:
            # Extract relationships using document intelligence
            try:
                from .document_intelligence import DocumentRelationshipMapper
                mapper = DocumentRelationshipMapper(self.document_repository)

                # This would extract relationships from document
                # For now, create simple relationships between entities in same document
                doc_entities = [e for e in entities if e.source_file_name == document.file_name]

                for i, entity1 in enumerate(doc_entities):
                    for entity2 in doc_entities[i+1:]:
                        relationship = ConceptRelationship(
                            user_id=0,
                            source_entity_id=entity1.id or 0,
                            target_entity_id=entity2.id or 0,
                            relationship_type="co_occurrence",
                            relationship_description=f"Entities co-occur in {document.file_name}",
                            confidence_score=0.6
                        )
                        relationships.append(relationship)

            except Exception as e:
                self.logger.error(f"Error extracting relationships from {document.file_name}: {e}")

        return relationships

    def _build_graph_structure(
        self,
        entities: List[ConceptEntity],
        relationships: List[ConceptRelationship]
    ) -> None:
        """Build graph structure from entities and relationships."""
        # Clear existing graph
        self.nodes.clear()
        self.edges.clear()
        self.graph.clear()

        # Add nodes
        for entity in entities:
            node_id = f"entity_{entity.id}" if entity.id else f"entity_{entity.entity_name}"

            node = GraphNode(
                id=node_id,
                label=entity.entity_name,
                type=entity.entity_type,
                confidence=entity.confidence_score,
                metadata={
                    'source_file': entity.source_file_name,
                    'description': entity.entity_description,
                    'created_at': entity.created_at.isoformat() if entity.created_at else None
                }
            )

            self.nodes[node_id] = node
            self.graph.add_node(node_id, **node.__dict__)

        # Add edges
        for relationship in relationships:
            source_id = f"entity_{relationship.source_entity_id}"
            target_id = f"entity_{relationship.target_entity_id}"

            if source_id in self.nodes and target_id in self.nodes:
                edge_id = f"edge_{relationship.source_entity_id}_{relationship.target_entity_id}"

                edge = GraphEdge(
                    source=source_id,
                    target=target_id,
                    type=relationship.relationship_type,
                    weight=1.0,
                    confidence=relationship.confidence_score,
                    metadata={
                        'description': relationship.relationship_description,
                        'created_at': relationship.created_at.isoformat() if relationship.created_at else None
                    }
                )

                self.edges[edge_id] = edge
                self.graph.add_edge(source_id, target_id, **edge.__dict__)

    def _identify_clusters(self) -> None:
        """Identify clusters in the knowledge graph."""
        self.clusters.clear()

        try:
            # Use NetworkX community detection
            if len(self.graph.nodes()) > 3:
                import community

                # Detect communities
                communities = community.best_partition(self.graph)

                # Group nodes by community
                community_groups = defaultdict(list)
                for node_id, community_id in communities.items():
                    community_groups[community_id].append(node_id)

                # Create clusters
                for community_id, node_ids in community_groups.items():
                    if len(node_ids) >= 2:  # Minimum cluster size
                        cluster = self._create_cluster(community_id, node_ids)
                        self.clusters[cluster.id] = cluster

        except ImportError:
            # Fallback to simple clustering if community not available
            self._simple_clustering()
        except Exception as e:
            self.logger.error(f"Error in community detection: {e}")
            self._simple_clustering()

    def _create_cluster(self, community_id: int, node_ids: List[str]) -> GraphCluster:
        """Create cluster from community."""
        # Find center node (highest degree)
        subgraph = self.graph.subgraph(node_ids)
        center_node = max(node_ids, key=lambda n: subgraph.degree(n))

        # Calculate cohesion score
        cohesion_score = self._calculate_cluster_cohesion(subgraph)

        # Generate cluster name
        cluster_name = self._generate_cluster_name(node_ids)

        return GraphCluster(
            id=f"cluster_{community_id}",
            name=cluster_name,
            nodes=node_ids,
            center_node=center_node,
            cohesion_score=cohesion_score,
            metadata={
                'community_id': community_id,
                'node_count': len(node_ids),
                'edge_count': subgraph.number_of_edges()
            }
        )

    def _calculate_cluster_cohesion(self, subgraph: nx.Graph) -> float:
        """Calculate cohesion score for cluster."""
        if subgraph.number_of_edges() == 0:
            return 0.0

        # Density-based cohesion
        possible_edges = subgraph.number_of_nodes() * (subgraph.number_of_nodes() - 1) / 2
        actual_edges = subgraph.number_of_edges()

        return actual_edges / possible_edges if possible_edges > 0 else 0.0

    def _generate_cluster_name(self, node_ids: List[str]) -> str:
        """Generate name for cluster."""
        # Get node labels
        node_labels = [self.nodes[node_id].label for node_id in node_ids]

        # Find common themes
        common_words = set(node_labels[0].lower().split())
        for label in node_labels[1:]:
            common_words &= set(label.lower().split())

        if common_words:
            return f"Cluster: {', '.join(list(common_words)[:3])}"
        else:
            return f"Cluster {len(self.clusters) + 1}"

    def _simple_clustering(self) -> None:
        """Simple clustering fallback."""
        # Group nodes by type
        type_groups = defaultdict(list)

        for node_id, node in self.nodes.items():
            type_groups[node.type].append(node_id)

        # Create clusters for each type with multiple nodes
        for node_type, node_ids in type_groups.items():
            if len(node_ids) >= 3:  # Minimum for cluster
                cluster = GraphCluster(
                    id=f"simple_cluster_{node_type}",
                    name=f"{node_type.title()} Cluster",
                    nodes=node_ids,
                    center_node=node_ids[0],
                    cohesion_score=0.5,
                    metadata={'type': node_type, 'method': 'simple'}
                )
                self.clusters[cluster.id] = cluster

    def _calculate_graph_metrics(self) -> Dict[str, Any]:
        """Calculate graph metrics."""
        if not self.graph.nodes():
            return {}

        return {
            'node_count': self.graph.number_of_nodes(),
            'edge_count': self.graph.number_of_edges(),
            'cluster_count': len(self.clusters),
            'density': nx.density(self.graph),
            'avg_degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes(),
            'connected_components': nx.number_connected_components(self.graph),
            'avg_clustering_coefficient': nx.average_clustering(self.graph)
        }

    def get_graph_visualization(self, format: str = "json") -> str:
        """Get graph visualization data.

        Args:
            format: Visualization format (json, png, svg)

        Returns:
            Visualization data
        """
        if format == "json":
            return self._get_json_visualization()
        elif format in ["png", "svg"]:
            return self._get_image_visualization(format)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _get_json_visualization(self) -> str:
        """Get JSON visualization data."""
        # Calculate node positions using spring layout
        if self.graph.nodes():
            pos = nx.spring_layout(self.graph, k=2, iterations=50)

            # Update node positions
            for node_id, position in pos.items():
                if node_id in self.nodes:
                    self.nodes[node_id].position = (float(position[0]), float(position[1]))

        # Convert to JSON
        visualization_data = {
            'nodes': [
                {
                    'id': node.id,
                    'label': node.label,
                    'type': node.type,
                    'confidence': node.confidence,
                    'position': node.position,
                    'metadata': node.metadata
                }
                for node in self.nodes.values()
            ],
            'edges': [
                {
                    'source': edge.source,
                    'target': edge.target,
                    'type': edge.type,
                    'weight': edge.weight,
                    'confidence': edge.confidence,
                    'metadata': edge.metadata
                }
                for edge in self.edges.values()
            ],
            'clusters': [
                {
                    'id': cluster.id,
                    'name': cluster.name,
                    'nodes': cluster.nodes,
                    'center_node': cluster.center_node,
                    'cohesion_score': cluster.cohesion_score,
                    'metadata': cluster.metadata
                }
                for cluster in self.clusters.values()
            ]
        }

        return json.dumps(visualization_data, indent=2)

    def _get_image_visualization(self, format: str = "png") -> str:
        """Get image visualization."""
        try:
            plt.figure(figsize=(12, 8))

            # Draw graph
            if self.graph.nodes():
                pos = nx.spring_layout(self.graph, k=2, iterations=50)

                # Draw nodes by type
                node_types = set(node.type for node in self.nodes.values())

                for node_type in node_types:
                    type_nodes = [
                        node_id for node_id, node in self.nodes.items()
                        if node.type == node_type
                    ]

                    nx.draw_networkx_nodes(
                        self.graph, pos,
                        nodelist=type_nodes,
                        node_color=self._get_node_color(node_type),
                        node_size=300,
                        alpha=0.7
                    )

                # Draw edges
                nx.draw_networkx_edges(
                    self.graph, pos,
                    edge_color='gray',
                    alpha=0.5,
                    width=1
                )

                # Draw labels
                nx.draw_networkx_labels(
                    self.graph, pos,
                    {node_id: node.label for node_id, node in self.nodes.items()},
                    font_size=8
                )

            plt.title("Knowledge Graph Visualization")
            plt.axis('off')

            # Save to bytes
            buf = io.BytesIO()
            plt.savefig(buf, format=format, bbox_inches='tight', dpi=150)
            buf.seek(0)

            # Encode as base64
            image_data = base64.b64encode(buf.read()).decode()

            plt.close()

            return f"data:image/{format};base64,{image_data}"

        except Exception as e:
            self.logger.error(f"Error creating graph visualization: {e}")
            return ""

    def _get_node_color(self, node_type: str) -> str:
        """Get color for node type."""
        colors = {
            'concept': '#1f77b4',
            'person': '#ff7f0e',
            'organization': '#2ca02c',
            'location': '#d62728',
            'term': '#9467bd',
            'event': '#8c564b'
        }

        return colors.get(node_type, '#7f7f7f')

    def query_graph(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Query knowledge graph.

        Args:
            query: Query string
            max_results: Maximum results

        Returns:
            Query results
        """
        results = []

        query_lower = query.lower()

        # Search in nodes
        for node in self.nodes.values():
            if (query_lower in node.label.lower() or
                query_lower in node.type.lower()):
                results.append({
                    'type': 'node',
                    'id': node.id,
                    'label': node.label,
                    'node_type': node.type,
                    'confidence': node.confidence
                })

        # Search in edges
        for edge in self.edges.values():
            if query_lower in edge.type.lower():
                results.append({
                    'type': 'edge',
                    'source': edge.source,
                    'target': edge.target,
                    'edge_type': edge.type,
                    'weight': edge.weight
                })

        return results[:max_results]

    def get_related_nodes(self, node_id: str, max_depth: int = 2) -> List[GraphNode]:
        """Get nodes related to given node.

        Args:
            node_id: Starting node ID
            max_depth: Maximum traversal depth

        Returns:
            Related nodes
        """
        if node_id not in self.graph:
            return []

        related_nodes = []

        # BFS traversal
        visited = {node_id}
        queue = deque([(node_id, 0)])

        while queue:
            current_node, depth = queue.popleft()

            if depth > max_depth:
                continue

            # Add neighbors
            for neighbor in self.graph.neighbors(current_node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))

                    if neighbor in self.nodes:
                        related_nodes.append(self.nodes[neighbor])

        return related_nodes

    def get_shortest_path(self, source_id: str, target_id: str) -> List[str]:
        """Get shortest path between two nodes.

        Args:
            source_id: Source node ID
            target_id: Target node ID

        Returns:
            List of node IDs in path
        """
        try:
            if source_id not in self.graph or target_id not in self.graph:
                return []

            path = nx.shortest_path(self.graph, source_id, target_id)
            return path

        except nx.NetworkXNoPath:
            return []
        except Exception as e:
            self.logger.error(f"Error finding path: {e}")
            return []

    def get_node_importance(self, node_id: str) -> Dict[str, float]:
        """Get importance metrics for node.

        Args:
            node_id: Node ID

        Returns:
            Importance metrics
        """
        if node_id not in self.graph:
            return {}

        # Calculate centrality measures
        degree_centrality = nx.degree_centrality(self.graph).get(node_id, 0)
        betweenness_centrality = nx.betweenness_centrality(self.graph).get(node_id, 0)
        closeness_centrality = nx.closeness_centrality(self.graph).get(node_id, 0)

        return {
            'degree_centrality': degree_centrality,
            'betweenness_centrality': betweenness_centrality,
            'closeness_centrality': closeness_centrality,
            'degree': self.graph.degree(node_id)
        }

    def update_graph_with_feedback(self, user_id: str, feedback: Dict[str, Any]) -> None:
        """Update graph based on user feedback.

        Args:
            user_id: User ID
            feedback: User feedback data
        """
        # This would update graph weights based on user interactions
        # For now, just log the operation
        self.logger.info(f"Updating graph with feedback from user {user_id}")


class GraphTraversalEngine:
    """Engine for traversing and querying knowledge graph."""

    def __init__(self, knowledge_graph: KnowledgeGraphBuilder):
        """Initialize traversal engine.

        Args:
            knowledge_graph: Knowledge graph builder
        """
        self.knowledge_graph = knowledge_graph
        self.logger = logging.getLogger(__name__)

    @handle_errors(operation="traverse_graph", component="graph_traversal")
    def traverse_graph(
        self,
        start_node: str,
        algorithm: str = "bfs",
        max_depth: int = 3,
        max_nodes: int = 50
    ) -> Dict[str, Any]:
        """Traverse graph from start node.

        Args:
            start_node: Starting node ID
            algorithm: Traversal algorithm (bfs, dfs)
            max_depth: Maximum traversal depth
            max_nodes: Maximum nodes to traverse

        Returns:
            Traversal results
        """
        try:
            if algorithm == "bfs":
                path, visited = self._bfs_traversal(start_node, max_depth, max_nodes)
            elif algorithm == "dfs":
                path, visited = self._dfs_traversal(start_node, max_depth, max_nodes)
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")

            # Get node details
            visited_nodes = [
                self.knowledge_graph.nodes[node_id]
                for node_id in visited
                if node_id in self.knowledge_graph.nodes
            ]

            return {
                'start_node': start_node,
                'algorithm': algorithm,
                'traversal_path': path,
                'visited_nodes': [node.__dict__ for node in visited_nodes],
                'total_visited': len(visited),
                'max_depth_reached': max_depth,
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error traversing graph: {e}")
            raise

    def _bfs_traversal(
        self,
        start_node: str,
        max_depth: int,
        max_nodes: int
    ) -> Tuple[List[str], List[str]]:
        """BFS traversal."""
        visited = []
        queue = deque([(start_node, 0)])
        path = []

        while queue and len(visited) < max_nodes:
            current_node, depth = queue.popleft()

            if current_node not in visited:
                visited.append(current_node)
                path.append(current_node)

                if depth < max_depth:
                    # Add neighbors
                    for neighbor in self.knowledge_graph.graph.neighbors(current_node):
                        if neighbor not in visited:
                            queue.append((neighbor, depth + 1))

        return path, visited

    def _dfs_traversal(
        self,
        start_node: str,
        max_depth: int,
        max_nodes: int
    ) -> Tuple[List[str], List[str]]:
        """DFS traversal."""
        visited = []
        stack = [(start_node, 0)]
        path = []

        while stack and len(visited) < max_nodes:
            current_node, depth = stack.pop()

            if current_node not in visited:
                visited.append(current_node)
                path.append(current_node)

                if depth < max_depth:
                    # Add neighbors in reverse order for DFS
                    neighbors = list(self.knowledge_graph.graph.neighbors(current_node))
                    for neighbor in reversed(neighbors):
                        if neighbor not in visited:
                            stack.append((neighbor, depth + 1))

        return path, visited

    def find_paths_between_nodes(
        self,
        source_node: str,
        target_node: str,
        max_paths: int = 5
    ) -> List[List[str]]:
        """Find paths between two nodes.

        Args:
            source_node: Source node ID
            target_node: Target node ID
            max_paths: Maximum number of paths

        Returns:
            List of paths
        """
        try:
            if source_node not in self.knowledge_graph.graph:
                return []
            if target_node not in self.knowledge_graph.graph:
                return []

            # Find all simple paths
            paths = list(nx.all_simple_paths(
                self.knowledge_graph.graph,
                source_node,
                target_node,
                cutoff=5  # Maximum path length
            ))

            # Limit number of paths
            return paths[:max_paths]

        except Exception as e:
            self.logger.error(f"Error finding paths: {e}")
            return []


class GraphBasedRecommender:
    """Recommender system based on knowledge graph."""

    def __init__(self, knowledge_graph: KnowledgeGraphBuilder):
        """Initialize recommender.

        Args:
            knowledge_graph: Knowledge graph builder
        """
        self.knowledge_graph = knowledge_graph
        self.logger = logging.getLogger(__name__)

    @handle_errors(operation="get_recommendations", component="graph_recommender")
    def get_recommendations(
        self,
        user_id: str,
        current_document: Document,
        recommendation_type: str = "related_documents",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recommendations based on knowledge graph.

        Args:
            user_id: User ID
            current_document: Current document context
            recommendation_type: Type of recommendations
            limit: Maximum recommendations

        Returns:
            List of recommendations
        """
        try:
            recommendations = []

            if recommendation_type == "related_documents":
                recommendations = self._get_related_document_recommendations(
                    current_document, limit
                )
            elif recommendation_type == "learning_path":
                recommendations = self._get_learning_path_recommendations(
                    user_id, current_document, limit
                )
            elif recommendation_type == "concept_exploration":
                recommendations = self._get_concept_exploration_recommendations(
                    current_document, limit
                )

            return recommendations

        except Exception as e:
            self.logger.error(f"Error getting recommendations: {e}")
            return []

    def _get_related_document_recommendations(
        self,
        document: Document,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get related document recommendations."""
        recommendations = []

        # Find similar documents using document intelligence
        try:
            from .document_intelligence import find_similar_documents

            # Get all documents for comparison
            all_documents = self.knowledge_graph.document_repository.get_all()

            # Find similar documents
            similar_docs = find_similar_documents(document, all_documents, min_similarity=0.3)

            for similar in similar_docs[:limit]:
                recommendations.append({
                    'type': 'related_document',
                    'document_id': similar.target_document.id,
                    'title': similar.target_document.title or similar.target_document.file_name,
                    'similarity_score': similar.similarity_score,
                    'reason': f"Similar content ({similar.similarity_score".2f"} similarity)",
                    'confidence': similar.similarity_score
                })

        except Exception as e:
            self.logger.error(f"Error getting related document recommendations: {e}")

        return recommendations

    def _get_learning_path_recommendations(
        self,
        user_id: str,
        document: Document,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get learning path recommendations."""
        recommendations = []

        # Analyze document topics and suggest learning progression
        try:
            from .document_intelligence import extract_entities_from_document

            entities = extract_entities_from_document(document)

            # Group entities by type for learning suggestions
            entity_types = defaultdict(list)
            for entity in entities:
                entity_types[entity.type].append(entity.text)

            # Create learning recommendations
            if 'academic_term' in entity_types:
                recommendations.append({
                    'type': 'learning_resource',
                    'title': 'Deepen Your Understanding',
                    'description': f"Explore more about: {', '.join(entity_types['academic_term'][:3])}",
                    'reason': 'Academic terms detected in document',
                    'confidence': 0.8,
                    'action': 'suggest_learning_materials'
                })

            if 'concept' in entity_types:
                recommendations.append({
                    'type': 'concept_exploration',
                    'title': 'Explore Related Concepts',
                    'description': f"Learn about concepts: {', '.join(entity_types['concept'][:3])}",
                    'reason': 'Key concepts identified',
                    'confidence': 0.7,
                    'action': 'show_concept_map'
                })

        except Exception as e:
            self.logger.error(f"Error getting learning path recommendations: {e}")

        return recommendations[:limit]

    def _get_concept_exploration_recommendations(
        self,
        document: Document,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get concept exploration recommendations."""
        recommendations = []

        # Get document entities
        try:
            from .document_intelligence import extract_entities_from_document

            entities = extract_entities_from_document(document)

            # Recommend exploring main entities
            for entity in entities[:5]:  # Top 5 entities
                recommendations.append({
                    'type': 'entity_exploration',
                    'title': f'Explore "{entity.text}"',
                    'description': f"Learn more about {entity.text} and related concepts",
                    'reason': f'Key {entity.type} identified in document',
                    'confidence': entity.confidence,
                    'action': 'explore_entity',
                    'entity': entity.text,
                    'entity_type': entity.type
                })

        except Exception as e:
            self.logger.error(f"Error getting concept exploration recommendations: {e}")

        return recommendations[:limit]


class KnowledgeGraphVisualizer:
    """Advanced visualization for knowledge graph."""

    def __init__(self, knowledge_graph: KnowledgeGraphBuilder):
        """Initialize visualizer.

        Args:
            knowledge_graph: Knowledge graph builder
        """
        self.knowledge_graph = knowledge_graph
        self.logger = logging.getLogger(__name__)

    def create_interactive_visualization(self) -> str:
        """Create interactive visualization HTML.

        Returns:
            HTML string for interactive visualization
        """
        try:
            # Get graph data
            graph_data = json.loads(self.knowledge_graph.get_graph_visualization("json"))

            # Create interactive HTML
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Knowledge Graph Visualization</title>
                <script src="https://d3js.org/d3.v7.min.js"></script>
                <style>
                    body { margin: 0; font-family: Arial, sans-serif; }
                    .node { cursor: pointer; stroke: #fff; stroke-width: 2px; }
                    .node.academic { fill: #1f77b4; }
                    .node.person { fill: #ff7f0e; }
                    .node.organization { fill: #2ca02c; }
                    .node.location { fill: #d62728; }
                    .node.term { fill: #9467bd; }
                    .node.concept { fill: #8c564b; }
                    .link { stroke: #999; stroke-opacity: 0.6; }
                    .tooltip { position: absolute; padding: 10px; background: rgba(0,0,0,0.8);
                              color: white; border-radius: 5px; pointer-events: none; }
                    .controls { position: absolute; top: 10px; right: 10px; background: white;
                               padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
                </style>
            </head>
            <body>
                <div class="controls">
                    <button onclick="restartSimulation()">Restart</button>
                    <button onclick="toggleLabels()">Labels</button>
                    <select id="colorScheme" onchange="changeColorScheme()">
                        <option value="type">By Type</option>
                        <option value="confidence">By Confidence</option>
                        <option value="cluster">By Cluster</option>
                    </select>
                </div>

                <div id="tooltip" class="tooltip" style="display: none;"></div>

                <script>
                    const width = window.innerWidth;
                    const height = window.innerHeight;

                    const svg = d3.select("body").append("svg")
                        .attr("width", width)
                        .attr("height", height);

                    const graphData = {graph_data_placeholder};

                    // Create simulation
                    const simulation = d3.forceSimulation(graphData.nodes)
                        .force("link", d3.forceLink(graphData.edges).id(d => d.id).distance(50))
                        .force("charge", d3.forceManyBody().strength(-300))
                        .force("center", d3.forceCenter(width / 2, height / 2))
                        .force("collision", d3.forceCollide().radius(20));

                    // Create links
                    const link = svg.append("g")
                        .selectAll("line")
                        .data(graphData.edges)
                        .enter().append("line")
                        .attr("class", "link")
                        .attr("stroke-width", d => Math.sqrt(d.weight) * 2);

                    // Create nodes
                    const node = svg.append("g")
                        .selectAll("circle")
                        .data(graphData.nodes)
                        .enter().append("circle")
                        .attr("class", d => `node ${d.type}`)
                        .attr("r", d => 5 + (d.confidence * 10))
                        .call(d3.drag()
                            .on("start", dragstarted)
                            .on("drag", dragged)
                            .on("end", dragended));

                    // Add labels
                    const label = svg.append("g")
                        .selectAll("text")
                        .data(graphData.nodes)
                        .enter().append("text")
                        .text(d => d.label)
                        .attr("font-size", 10)
                        .attr("dx", 12)
                        .attr("dy", ".35em");

                    // Add tooltips
                    node.on("mouseover", function(event, d) {{
                        d3.select("#tooltip")
                            .style("display", "block")
                    .html(`<strong>${d.label}</strong><br/>Type: ${d.type}<br/>Confidence: ${d.confidence.toFixed(2)}`);
                    }})
                    .on("mousemove", function(event) {{
                        d3.select("#tooltip")
                            .style("left", (event.pageX + 10) + "px")
                            .style("top", (event.pageY - 10) + "px");
                    }})
                    .on("mouseout", function() {{
                        d3.select("#tooltip").style("display", "none");
                    }});

                    // Simulation tick
                    simulation.on("tick", function() {{
                        link
                            .attr("x1", d => d.source.x)
                            .attr("y1", d => d.source.y)
                            .attr("x2", d => d.target.x)
                            .attr("y2", d => d.target.y);

                        node
                            .attr("cx", d => d.x)
                            .attr("cy", d => d.y);

                        label
                            .attr("x", d => d.x)
                            .attr("y", d => d.y);
                    }});

                    // Drag functions
                    function dragstarted(event, d) {{
                        if (!event.active) simulation.alphaTarget(0.3).restart();
                        d.fx = d.x;
                        d.fy = d.y;
                    }}

                    function dragged(event, d) {{
                        d.fx = event.x;
                        d.fy = event.y;
                    }}

                    function dragended(event, d) {{
                        if (!event.active) simulation.alphaTarget(0);
                        d.fx = null;
                        d.fy = null;
                    }}

                    // Control functions
                    function restartSimulation() {{
                        simulation.alpha(1).restart();
                    }}

                    function toggleLabels() {{
                        label.style("display", label.style("display") === "none" ? "block" : "none");
                    }}

                    function changeColorScheme() {{
                        const scheme = document.getElementById("colorScheme").value;
                        // Color scheme change logic would go here
                    }}
                </script>
            </body>
            </html>
            """

            # Replace placeholder with actual data
            html_template = html_template.replace(
                "{graph_data_placeholder}",
                json.dumps(graph_data)
            )

            return html_template

        except Exception as e:
            self.logger.error(f"Error creating interactive visualization: {e}")
            return f"Error creating visualization: {str(e)}"

    def create_cluster_visualization(self) -> str:
        """Create cluster-focused visualization.

        Returns:
            HTML visualization string
        """
        try:
            # Get cluster data
            clusters = list(self.knowledge_graph.clusters.values())

            if not clusters:
                return "No clusters to visualize"

            # Create simple cluster visualization
            html = """
            <div style="padding: 20px; font-family: Arial, sans-serif;">
                <h2>Knowledge Graph Clusters</h2>
            """

            for cluster in clusters:
                html += f"""
                <div style="
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 10px 0;
                    background: #f9f9f9;
                ">
                    <h3>{cluster.name}</h3>
                    <p><strong>Nodes:</strong> {len(cluster.nodes)}</p>
                    <p><strong>Cohesion:</strong> {cluster.cohesion_score".2f"}</p>
                    <p><strong>Center Node:</strong> {cluster.center_node}</p>
                </div>
                """

            html += "</div>"
            return html

        except Exception as e:
            self.logger.error(f"Error creating cluster visualization: {e}")
            return f"Error: {str(e)}"


class KnowledgeGraphSystem:
    """Main knowledge graph system."""

    def __init__(self, document_repository):
        """Initialize knowledge graph system.

        Args:
            document_repository: Document repository
        """
        self.document_repository = document_repository
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.graph_builder = KnowledgeGraphBuilder(document_repository)
        self.traversal_engine = GraphTraversalEngine(self.graph_builder)
        self.recommender = GraphBasedRecommender(self.graph_builder)
        self.visualizer = KnowledgeGraphVisualizer(self.graph_builder)

        # Cache for built graphs
        self.graph_cache: Dict[str, Dict[str, Any]] = {}

    @handle_errors(operation="get_or_build_graph", component="knowledge_graph_system")
    def get_or_build_graph(self, project_id: str, user_id: str = None) -> Dict[str, Any]:
        """Get cached graph or build new one.

        Args:
            project_id: Project ID
            user_id: User ID

        Returns:
            Knowledge graph data
        """
        cache_key = f"{project_id}_{user_id}"

        # Check cache
        if cache_key in self.graph_cache:
            cached_graph = self.graph_cache[cache_key]

            # Check if cache is still valid (e.g., documents haven't changed)
            cache_age = datetime.utcnow() - datetime.fromisoformat(cached_graph['build_timestamp'])

            if cache_age.total_seconds() < 3600:  # 1 hour cache
                return cached_graph

        # Build new graph
        graph_data = self.graph_builder.build_knowledge_graph(project_id, user_id)

        # Cache result
        self.graph_cache[cache_key] = graph_data

        return graph_data

    def query_graph(self, query: str, project_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Query knowledge graph.

        Args:
            query: Query string
            project_id: Project ID
            limit: Maximum results

        Returns:
            Query results
        """
        # Build or get graph
        graph_data = self.get_or_build_graph(project_id)

        # Update graph builder with cached data
        self.graph_builder.nodes = {
            node['id']: GraphNode(**node) for node in graph_data['nodes']
        }
        self.graph_builder.edges = {
            f"edge_{i}": GraphEdge(**edge) for i, edge in enumerate(graph_data['edges'])
        }

        return self.graph_builder.query_graph(query, limit)

    def get_recommendations(
        self,
        user_id: str,
        document: Document,
        recommendation_type: str = "related_documents",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get graph-based recommendations.

        Args:
            user_id: User ID
            document: Current document context
            recommendation_type: Type of recommendations
            limit: Maximum recommendations

        Returns:
            List of recommendations
        """
        return self.recommender.get_recommendations(
            user_id, document, recommendation_type, limit
        )

    def get_graph_visualization(self, project_id: str, format: str = "json") -> str:
        """Get graph visualization.

        Args:
            project_id: Project ID
            format: Visualization format

        Returns:
            Visualization data
        """
        # Build graph if needed
        self.get_or_build_graph(project_id)

        return self.graph_builder.get_graph_visualization(format)

    def get_interactive_visualization(self, project_id: str) -> str:
        """Get interactive visualization.

        Args:
            project_id: Project ID

        Returns:
            Interactive HTML visualization
        """
        # Build graph if needed
        self.get_or_build_graph(project_id)

        return self.visualizer.create_interactive_visualization()

    def traverse_from_node(
        self,
        node_id: str,
        project_id: str,
        algorithm: str = "bfs",
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """Traverse graph from specific node.

        Args:
            node_id: Starting node ID
            project_id: Project ID
            algorithm: Traversal algorithm
            max_depth: Maximum depth

        Returns:
            Traversal results
        """
        # Build graph if needed
        self.get_or_build_graph(project_id)

        return self.traversal_engine.traverse_graph(
            node_id, algorithm, max_depth
        )

    def find_paths_between_concepts(
        self,
        source_concept: str,
        target_concept: str,
        project_id: str,
        max_paths: int = 5
    ) -> List[List[str]]:
        """Find paths between two concepts.

        Args:
            source_concept: Source concept name
            target_concept: Target concept name
            project_id: Project ID
            max_paths: Maximum number of paths

        Returns:
            List of paths
        """
        # Build graph if needed
        self.get_or_build_graph(project_id)

        # Find node IDs for concepts
        source_node = self._find_node_by_label(source_concept)
        target_node = self._find_node_by_label(target_concept)

        if not source_node or not target_node:
            return []

        return self.traversal_engine.find_paths_between_nodes(
            source_node, target_node, max_paths
        )

    def _find_node_by_label(self, label: str) -> Optional[str]:
        """Find node ID by label."""
        for node_id, node in self.graph_builder.nodes.items():
            if node.label.lower() == label.lower():
                return node_id
        return None

    def get_concept_neighbors(self, concept: str, project_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get concepts related to given concept.

        Args:
            concept: Concept name
            project_id: Project ID
            limit: Maximum neighbors

        Returns:
            List of related concepts
        """
        # Build graph if needed
        self.get_or_build_graph(project_id)

        # Find concept node
        node_id = self._find_node_by_label(concept)
        if not node_id:
            return []

        # Get related nodes
        related_nodes = self.graph_builder.get_related_nodes(node_id, max_depth=1)

        return [
            {
                'id': node.id,
                'label': node.label,
                'type': node.type,
                'confidence': node.confidence
            }
            for node in related_nodes[:limit]
        ]

    def get_knowledge_insights(self, project_id: str) -> Dict[str, Any]:
        """Get insights about knowledge graph.

        Args:
            project_id: Project ID

        Returns:
            Knowledge insights
        """
        try:
            # Build graph if needed
            graph_data = self.get_or_build_graph(project_id)

            insights = {
                'total_concepts': len(graph_data['nodes']),
                'total_relationships': len(graph_data['edges']),
                'total_clusters': len(graph_data['clusters']),
                'graph_density': graph_data['metrics'].get('density', 0),
                'most_connected_concepts': self._get_most_connected_concepts(graph_data),
                'isolated_concepts': self._get_isolated_concepts(graph_data),
                'knowledge_gaps': self._identify_knowledge_gaps(graph_data),
                'learning_suggestions': self._generate_learning_suggestions(graph_data)
            }

            return insights

        except Exception as e:
            self.logger.error(f"Error getting knowledge insights: {e}")
            return {}

    def _get_most_connected_concepts(self, graph_data: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Get most connected concepts."""
        # This would analyze graph structure
        # For now, return mock data
        return [
            {'concept': 'Machine Learning', 'connections': 15},
            {'concept': 'Statistics', 'connections': 12},
            {'concept': 'Data Science', 'connections': 10},
        ][:limit]

    def _get_isolated_concepts(self, graph_data: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Get isolated concepts."""
        # This would find nodes with low connectivity
        # For now, return mock data
        return [
            {'concept': 'Quantum Computing', 'connections': 1},
            {'concept': 'Bioinformatics', 'connections': 1},
        ][:limit]

    def _identify_knowledge_gaps(self, graph_data: Dict[str, Any]) -> List[str]:
        """Identify knowledge gaps."""
        gaps = []

        # Analyze graph structure for gaps
        if graph_data['metrics'].get('connected_components', 1) > 3:
            gaps.append("Multiple disconnected knowledge areas detected")

        if graph_data['metrics'].get('density', 0) < 0.1:
            gaps.append("Low connectivity between concepts")

        return gaps

    def _generate_learning_suggestions(self, graph_data: Dict[str, Any]) -> List[str]:
        """Generate learning suggestions based on graph."""
        suggestions = []

        # Suggest based on graph structure
        if len(graph_data['clusters']) > 1:
            suggestions.append("Explore connections between different knowledge clusters")

        if graph_data['metrics'].get('density', 0) < 0.3:
            suggestions.append("Consider adding more connecting concepts between topics")

        return suggestions

    def clear_graph_cache(self) -> None:
        """Clear graph cache."""
        self.graph_cache.clear()
        self.logger.info("Knowledge graph cache cleared")


# Factory function

def create_knowledge_graph_system(document_repository) -> KnowledgeGraphSystem:
    """Create complete knowledge graph system.

    Args:
        document_repository: Document repository

    Returns:
        Configured knowledge graph system
    """
    return KnowledgeGraphSystem(document_repository)


# Integration functions

def build_knowledge_graph(project_id: str, user_id: str = None) -> Dict[str, Any]:
    """Build knowledge graph for project (convenience function).

    Args:
        project_id: Project ID
        user_id: User ID

    Returns:
        Knowledge graph data
    """
    # This would get the system from a global registry
    # For now, return mock data
    return {
        'nodes': [],
        'edges': [],
        'clusters': [],
        'metrics': {},
        'build_timestamp': datetime.utcnow().isoformat()
    }


def get_graph_visualization(project_id: str, format: str = "json") -> str:
    """Get graph visualization (convenience function).

    Args:
        project_id: Project ID
        format: Visualization format

    Returns:
        Visualization data
    """
    # This would get the system and call visualization
    return json.dumps({"format": format, "project": project_id})


def query_knowledge_graph(query: str, project_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Query knowledge graph (convenience function).

    Args:
        query: Query string
        project_id: Project ID
        limit: Maximum results

    Returns:
        Query results
    """
    # This would get the system and perform query
    return []
