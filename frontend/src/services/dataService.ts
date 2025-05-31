import { 
  GraphData, 
  AnalysisResults, 
  Node, 
  Edge, 
  AttackPath, 
  Statistics,
  NodeType,
  EdgeType
} from '../types';

export class DataService {
  private baseUrl: string;
  private forceMockData: boolean;

  constructor() {
    // Use environment variables or default values
    this.baseUrl = import.meta.env.VITE_DATA_PATH || '/data';
    // Only use mock data if explicitly forced, not by default in dev
    this.forceMockData = import.meta.env.VITE_FORCE_MOCK_DATA === 'true';
  }

  /**
   * Load graph data from JSON file or return mock data
   */
  async loadGraphData(): Promise<GraphData> {
    try {
      // If forced to use mock data, return it immediately
      if (this.forceMockData) {
        console.log('Using forced mock graph data');
        return this.getMockGraphData();
      }

      // Try to load test data first if in development and explicitly enabled
      if (import.meta.env.DEV && import.meta.env.VITE_USE_TEST_DATA === 'true') {
        console.log('Loading test graph data...');
        const response = await fetch('/data/test-graph.json');
        if (response.ok) {
          const data = await response.json();
          return this.validateGraphData(data);
        }
      }
      
      // Always try to load real data first
      console.log('Loading real graph data from:', `${this.baseUrl}/graph/latest.json`);
      const response = await fetch(`${this.baseUrl}/graph/latest.json`);
      if (!response.ok) {
        throw new Error(`Failed to load graph data: ${response.statusText}`);
      }
      
      const data = await response.json();
      const validatedData = this.validateGraphData(data);
      
      // If data is empty but valid, return it (don't fall back to mock)
      if (validatedData.nodes.length === 0) {
        console.log('Real graph data is empty (no nodes collected)');
      } else {
        console.log(`Loaded real graph data: ${validatedData.nodes.length} nodes, ${validatedData.edges.length} edges`);
      }
      
      return validatedData;
    } catch (error) {
      console.error('Failed to load real graph data:', error);
      console.log('Falling back to mock graph data');
      return this.getMockGraphData();
    }
  }

  /**
   * Load analysis results from JSON file or return mock data
   */
  async loadAnalysisData(): Promise<AnalysisResults> {
    try {
      // If forced to use mock data, return it immediately
      if (this.forceMockData) {
        console.log('Using forced mock analysis data');
        return this.getMockAnalysisData();
      }

      // Try to load test data first if in development and explicitly enabled
      if (import.meta.env.DEV && import.meta.env.VITE_USE_TEST_DATA === 'true') {
        console.log('Loading test analysis data...');
        const response = await fetch('/data/test-analysis.json');
        if (response.ok) {
          const data = await response.json();
          return this.validateAnalysisData(data);
        }
      }
      
      // Always try to load real data first
      console.log('Loading real analysis data from:', `${this.baseUrl}/analysis/latest.json`);
      const response = await fetch(`${this.baseUrl}/analysis/latest.json`);
      if (!response.ok) {
        throw new Error(`Failed to load analysis data: ${response.statusText}`);
      }
      
      const data = await response.json();
      const validatedData = this.validateAnalysisData(data);
      
      // If analysis shows no attack paths but is valid, return it (don't fall back to mock)
      if (validatedData.statistics.attack_paths === 0) {
        console.log('Real analysis data shows no attack paths found');
      } else {
        console.log(`Loaded real analysis data: ${validatedData.statistics.attack_paths} attack paths`);
      }
      
      return validatedData;
    } catch (error) {
      console.error('Failed to load real analysis data:', error);
      console.log('Falling back to mock analysis data');
      return this.getMockAnalysisData();
    }
  }

  /**
   * Search nodes by query
   */
  async searchNodes(query: string, nodeTypes?: NodeType[]): Promise<Node[]> {
    const graphData = await this.loadGraphData();
    
    const filtered = graphData.nodes.filter(node => {
      const matchesQuery = !query || 
        node.name.toLowerCase().includes(query.toLowerCase()) ||
        node.id.toLowerCase().includes(query.toLowerCase()) ||
        (node.properties.email && node.properties.email.toLowerCase().includes(query.toLowerCase()));
      
      const matchesType = !nodeTypes || nodeTypes.length === 0 || nodeTypes.includes(node.type);
      
      return matchesQuery && matchesType;
    });

    return filtered.slice(0, 50); // Limit results
  }

  /**
   * Get attack paths by category
   */
  async getAttackPathsByCategory(category?: string): Promise<AttackPath[]> {
    const analysisData = await this.loadAnalysisData();
    
    if (!category) {
      return [
        ...analysisData.attack_paths.critical,
        ...analysisData.attack_paths.critical_multi_step,
        ...analysisData.attack_paths.privilege_escalation,
        ...analysisData.attack_paths.lateral_movement,
        ...analysisData.attack_paths.high,
        ...analysisData.attack_paths.medium,
        ...analysisData.attack_paths.low
      ];
    }

    return analysisData.attack_paths[category as keyof typeof analysisData.attack_paths] || [];
  }

  /**
   * Validate graph data structure
   */
  private validateGraphData(data: any): GraphData {
    if (!data || !Array.isArray(data.nodes) || !Array.isArray(data.edges)) {
      throw new Error('Invalid graph data structure');
    }
    
    // Basic validation
    data.nodes.forEach((node: any, index: number) => {
      if (!node.id || !node.type || !node.name) {
        throw new Error(`Invalid node at index ${index}: missing required fields`);
      }
    });

    data.edges.forEach((edge: any, index: number) => {
      if (!edge.source || !edge.target || !edge.type) {
        throw new Error(`Invalid edge at index ${index}: missing required fields`);
      }
      // Auto-generate ID if missing
      if (!edge.id) {
        edge.id = `edge_${index}_${edge.source.replace(/[^a-zA-Z0-9]/g, '_')}_to_${edge.target.replace(/[^a-zA-Z0-9]/g, '_')}`;
      }
    });

    return data as GraphData;
  }

  /**
   * Validate analysis data structure
   */
  private validateAnalysisData(data: any): AnalysisResults {
    if (!data || !data.statistics || !data.attack_paths) {
      throw new Error('Invalid analysis data structure');
    }
    
    return data as AnalysisResults;
  }

  /**
   * Get mock graph data for development
   */
  private getMockGraphData(): GraphData {
    return {
      nodes: [
        {
          id: "user:alice@example.com",
          type: NodeType.USER,
          name: "alice@example.com",
          properties: {
            email: "alice@example.com",
            domain: "example.com",
            is_external: false,
            groups: ["group:developers@example.com"]
          }
        },
        {
          id: "user:contractor@external.com",
          type: NodeType.USER,
          name: "contractor@external.com",
          properties: {
            email: "contractor@external.com",
            domain: "external.com",
            is_external: true,
            groups: [],
            last_seen: "2024-01-15T10:30:00Z"
          }
        },
        {
          id: "group:developers@example.com",
          type: NodeType.GROUP,
          name: "developers@example.com",
          properties: {
            email: "developers@example.com",
            display_name: "Developers Group",
            description: "Development team members"
          }
        },
        {
          id: "sa:web-app-sa@production-project.iam.gserviceaccount.com",
          type: NodeType.SERVICE_ACCOUNT,
          name: "web-app-sa@production-project.iam.gserviceaccount.com",
          properties: {
            email: "web-app-sa@production-project.iam.gserviceaccount.com",
            project_id: "production-project",
            display_name: "Web Application Service Account",
            description: "Service account for web application",
            is_default: false,
            key_count: 2,
            disabled: false,
            last_used: "2024-01-20T15:45:00Z"
          }
        },
        {
          id: "project:production-project",
          type: NodeType.PROJECT,
          name: "production-project",
          properties: {
            project_id: "production-project",
            display_name: "Production Web Application",
            parent: "folder:web-apps",
            state: "ACTIVE",
            labels: {
              environment: "production",
              team: "web-development"
            },
            create_time: "2023-06-15T09:00:00Z"
          }
        },
        {
          id: "role:roles/editor",
          type: NodeType.ROLE,
          name: "roles/editor",
          properties: {
            title: "Editor",
            description: "Read/write access to all resources",
            is_custom: false,
            permissions: ["compute.*", "storage.*", "cloudsql.*"],
            is_dangerous: true,
            stage: "GA"
          }
        }
      ],
      edges: [
        {
          id: "edge_1",
          source: "user:alice@example.com",
          target: "group:developers@example.com",
          type: EdgeType.MEMBER_OF,
          properties: {
            roles: ["MEMBER"],
            create_time: "2023-06-15T09:00:00Z"
          }
        },
        {
          id: "edge_2",
          source: "group:developers@example.com",
          target: "role:roles/editor",
          type: EdgeType.HAS_ROLE,
          properties: {
            resource: "projects/production-project",
            role: "roles/editor",
            inherited: false
          }
        },
        {
          id: "edge_3",
          source: "user:contractor@external.com",
          target: "sa:web-app-sa@production-project.iam.gserviceaccount.com",
          type: EdgeType.CAN_IMPERSONATE_SA,
          properties: {
            technique: "Service Account Impersonation",
            via_role: "roles/iam.serviceAccountTokenCreator",
            permission: "iam.serviceAccounts.getAccessToken",
            resource_scope: "projects/production-project",
            confidence: 0.95
          }
        }
      ],
      metadata: {
        total_nodes: 6,
        total_edges: 3,
        collection_time: "2024-01-20T16:00:00Z",
        gcp_projects: ["production-project"],
        gcp_organization: "123456789",
        generator_version: "1.0.0"
      }
    };
  }

  /**
   * Get mock analysis data for development
   */
  private getMockAnalysisData(): AnalysisResults {
    return {
      statistics: {
        total_nodes: 6,
        total_edges: 3,
        attack_paths: 2,
        high_risk_nodes: 2,
        dangerous_roles: 1,
        privilege_escalation_paths: 1,
        lateral_movement_paths: 0,
        critical_nodes: 1,
        vulnerabilities: 1
      },
      attack_paths: {
        critical: [
          {
            source: {
              id: "user:contractor@external.com",
              type: NodeType.USER,
              name: "contractor@external.com"
            },
            target: {
              id: "sa:web-app-sa@production-project.iam.gserviceaccount.com",
              type: NodeType.SERVICE_ACCOUNT,
              name: "web-app-sa@production-project.iam.gserviceaccount.com"
            },
            path_nodes: [
              {
                id: "user:contractor@external.com",
                type: NodeType.USER,
                name: "contractor@external.com"
              },
              {
                id: "sa:web-app-sa@production-project.iam.gserviceaccount.com",
                type: NodeType.SERVICE_ACCOUNT,
                name: "web-app-sa@production-project.iam.gserviceaccount.com"
              }
            ],
            path_edges: [
              {
                id: "edge_attack_1",
                source: "user:contractor@external.com",
                target: "sa:web-app-sa@production-project.iam.gserviceaccount.com",
                type: EdgeType.CAN_IMPERSONATE_SA,
                properties: {
                  technique: "Service Account Impersonation",
                  via_role: "roles/iam.serviceAccountTokenCreator",
                  permission: "iam.serviceAccounts.getAccessToken",
                  confidence: 0.95
                }
              }
            ],
            risk_score: 0.92,
            description: "External contractor can impersonate privileged service account",
            length: 1,
            category: "critical"
          }
        ],
        critical_multi_step: [],
        privilege_escalation: [],
        lateral_movement: [],
        high: [],
        medium: [],
        low: []
      },
      risk_scores: {
        "user:contractor@external.com": {
          base: 0.7,
          centrality: 0.3,
          total: 0.85,
          factors: [
            {
              type: "external_user",
              impact: 0.4,
              description: "External domain user with privileged access"
            },
            {
              type: "dangerous_role",
              impact: 0.5,
              description: "Has Service Account Token Creator role"
            }
          ]
        },
        "sa:web-app-sa@production-project.iam.gserviceaccount.com": {
          base: 0.8,
          centrality: 0.6,
          total: 0.92,
          factors: [
            {
              type: "dangerous_role",
              impact: 0.6,
              description: "Has Editor role on production project"
            },
            {
              type: "impersonation_target",
              impact: 0.4,
              description: "Target of privilege escalation attack"
            }
          ]
        }
      },
      vulnerabilities: [
        {
          id: "vuln-001",
          title: "External User with Service Account Impersonation",
          description: "External contractor has roles/iam.serviceAccountTokenCreator role allowing impersonation of production service account",
          severity: "CRITICAL",
          risk_score: 0.95,
          category: "privilege_escalation",
          affected_resources: [
            "user:contractor@external.com",
            "sa:web-app-sa@production-project.iam.gserviceaccount.com"
          ],
          remediation: [
            "Remove Service Account Token Creator role from external user",
            "Use IAM conditions to restrict impersonation scope",
            "Implement time-based access controls"
          ],
          cve_references: [],
          mitre_techniques: ["T1078.004"],
          detection_rules: [
            "Monitor iam.serviceAccounts.getAccessToken calls from external users"
          ]
        }
      ],
      critical_nodes: [
        {
          id: "sa:web-app-sa@production-project.iam.gserviceaccount.com",
          type: NodeType.SERVICE_ACCOUNT,
          name: "web-app-sa@production-project.iam.gserviceaccount.com",
          risk_score: 0.92,
          criticality_factors: [
            "Target of privilege escalation attack",
            "Has dangerous Editor role",
            "Used by production workloads"
          ]
        }
      ],
      dangerous_roles: [
        {
          role: "roles/editor",
          assignees: [
            "group:developers@example.com",
            "sa:web-app-sa@production-project.iam.gserviceaccount.com"
          ],
          risk_score: 0.8,
          permissions_count: 2847,
          reasons: [
            "Provides extensive write access to resources",
            "Can modify IAM policies",
            "Assigned to production service account"
          ]
        }
      ]
    };
  }
}

// Export singleton instance
export const dataService = new DataService(); 