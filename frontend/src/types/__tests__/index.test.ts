import { getRiskLevel, getNodeTypeColor, NodeType, RiskLevel } from '../index';

describe('getRiskLevel utility function', () => {
  it('should return critical for scores >= 0.8', () => {
    expect(getRiskLevel(0.8)).toBe('critical');
    expect(getRiskLevel(0.9)).toBe('critical');
    expect(getRiskLevel(1.0)).toBe('critical');
    expect(getRiskLevel(0.99)).toBe('critical');
  });

  it('should return high for scores >= 0.6 and < 0.8', () => {
    expect(getRiskLevel(0.6)).toBe('high');
    expect(getRiskLevel(0.7)).toBe('high');
    expect(getRiskLevel(0.79)).toBe('high');
  });

  it('should return medium for scores >= 0.4 and < 0.6', () => {
    expect(getRiskLevel(0.4)).toBe('medium');
    expect(getRiskLevel(0.5)).toBe('medium');
    expect(getRiskLevel(0.59)).toBe('medium');
  });

  it('should return low for scores >= 0.2 and < 0.4', () => {
    expect(getRiskLevel(0.2)).toBe('low');
    expect(getRiskLevel(0.3)).toBe('low');
    expect(getRiskLevel(0.39)).toBe('low');
  });

  it('should return info for scores < 0.2', () => {
    expect(getRiskLevel(0)).toBe('info');
    expect(getRiskLevel(0.1)).toBe('info');
    expect(getRiskLevel(0.19)).toBe('info');
  });

  it('should handle edge cases and boundary values', () => {
    expect(getRiskLevel(0.19999)).toBe('info');
    expect(getRiskLevel(0.39999)).toBe('low');
    expect(getRiskLevel(0.59999)).toBe('medium');
    expect(getRiskLevel(0.79999)).toBe('high');
  });

  it('should handle negative values', () => {
    expect(getRiskLevel(-0.1)).toBe('info');
    expect(getRiskLevel(-1)).toBe('info');
  });

  it('should handle values above 1', () => {
    expect(getRiskLevel(1.1)).toBe('critical');
    expect(getRiskLevel(2)).toBe('critical');
  });
});

describe('getNodeTypeColor utility function', () => {
  it('should return correct colors for all node types', () => {
    expect(getNodeTypeColor(NodeType.USER)).toBe('#4285F4');
    expect(getNodeTypeColor(NodeType.SERVICE_ACCOUNT)).toBe('#34A853');
    expect(getNodeTypeColor(NodeType.GROUP)).toBe('#FBBC04');
    expect(getNodeTypeColor(NodeType.PROJECT)).toBe('#EA4335');
    expect(getNodeTypeColor(NodeType.FOLDER)).toBe('#FF6D00');
    expect(getNodeTypeColor(NodeType.ORGANIZATION)).toBe('#9C27B0');
    expect(getNodeTypeColor(NodeType.ROLE)).toBe('#757575');
    expect(getNodeTypeColor(NodeType.CUSTOM_ROLE)).toBe('#8E24AA');
    expect(getNodeTypeColor(NodeType.BUCKET)).toBe('#00ACC1');
    expect(getNodeTypeColor(NodeType.INSTANCE)).toBe('#FF7043');
    expect(getNodeTypeColor(NodeType.FUNCTION)).toBe('#26A69A');
    expect(getNodeTypeColor(NodeType.SECRET)).toBe('#AB47BC');
    expect(getNodeTypeColor(NodeType.KMS_KEY)).toBe('#FFA726');
    expect(getNodeTypeColor(NodeType.DATASET)).toBe('#42A5F5');
    expect(getNodeTypeColor(NodeType.TOPIC)).toBe('#66BB6A');
    expect(getNodeTypeColor(NodeType.CLOUD_RUN_SERVICE)).toBe('#29B6F6');
    expect(getNodeTypeColor(NodeType.GKE_CLUSTER)).toBe('#5C6BC0');
    expect(getNodeTypeColor(NodeType.CLOUD_BUILD_TRIGGER)).toBe('#FF8A65');
    expect(getNodeTypeColor(NodeType.COMPUTE_INSTANCE)).toBe('#FF7043');
  });

  it('should return all valid hex color codes', () => {
    const hexColorRegex = /^#[0-9A-F]{6}$/i;
    
    Object.values(NodeType).forEach(nodeType => {
      const color = getNodeTypeColor(nodeType);
      expect(color).toMatch(hexColorRegex);
    });
  });

  it('should return consistent colors for the same node type', () => {
    const color1 = getNodeTypeColor(NodeType.USER);
    const color2 = getNodeTypeColor(NodeType.USER);
    expect(color1).toBe(color2);
  });

  it('should return different colors for different node types', () => {
    const userColor = getNodeTypeColor(NodeType.USER);
    const projectColor = getNodeTypeColor(NodeType.PROJECT);
    const serviceAccountColor = getNodeTypeColor(NodeType.SERVICE_ACCOUNT);
    
    expect(userColor).not.toBe(projectColor);
    expect(userColor).not.toBe(serviceAccountColor);
    expect(projectColor).not.toBe(serviceAccountColor);
  });

  it('should handle all enum values without errors', () => {
    Object.values(NodeType).forEach(nodeType => {
      expect(() => getNodeTypeColor(nodeType)).not.toThrow();
    });
  });
});

describe('NodeType enum', () => {
  it('should contain all expected node types', () => {
    const expectedTypes = [
      'user',
      'service_account',
      'group',
      'project',
      'folder',
      'organization',
      'role',
      'custom_role',
      'bucket',
      'instance',
      'function',
      'secret',
      'kms_key',
      'dataset',
      'topic',
      'cloud_run_service',
      'gke_cluster',
      'cloud_build_trigger',
      'compute_instance'
    ];

    const actualTypes = Object.values(NodeType);
    expectedTypes.forEach(type => {
      expect(actualTypes).toContain(type);
    });
  });

  it('should have consistent value format', () => {
    Object.values(NodeType).forEach(nodeType => {
      expect(nodeType).toMatch(/^[a-z_]+$/);
    });
  });
}); 