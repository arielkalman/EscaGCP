"""
Configuration management for GCPHound
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from .logger import get_logger


logger = get_logger(__name__)


@dataclass
class Config:
    """
    Configuration for GCPHound
    """
    # Authentication settings
    authentication_method: str = 'adc'  # 'adc' or 'service_account'
    authentication_service_account_key_file: Optional[str] = None
    authentication_impersonate_service_account: Optional[str] = None
    authentication_scopes: List[str] = field(default_factory=lambda: [
        'https://www.googleapis.com/auth/cloud-platform.read-only',
        'https://www.googleapis.com/auth/cloudidentity.groups.readonly'
    ])
    
    # Collection settings
    collection_max_projects: int = 0  # 0 = no limit
    collection_max_resources_per_type: int = 1000
    collection_page_size: int = 100
    collection_timeout: int = 30
    collection_max_retries: int = 3
    collection_max_workers: int = 10
    collection_max_pages: Optional[int] = None
    collection_include_organization: bool = True
    collection_include_folders: bool = True
    collection_include_role_definitions: bool = True
    collection_show_progress: bool = True
    collection_resource_types: List[str] = field(default_factory=lambda: [
        'buckets',
        'compute_instances',
        'functions',
        'pubsub_topics',
        'bigquery_datasets',
        'kms_keys',
        'secrets'
    ])
    
    # Analysis settings
    analysis_max_path_length: int = 5
    analysis_dangerous_roles: List[str] = field(default_factory=lambda: [
        'roles/owner',
        'roles/editor',
        'roles/iam.securityAdmin',
        'roles/resourcemanager.organizationAdmin'
    ])
    analysis_risk_thresholds_critical: float = 0.8
    analysis_risk_thresholds_high: float = 0.6
    analysis_risk_thresholds_medium: float = 0.4
    analysis_risk_thresholds_low: float = 0.2
    
    # Performance settings
    performance_max_concurrent_requests: int = 10
    performance_rate_limit_requests_per_second: float = 10.0
    performance_rate_limit_burst_size: int = 20
    
    # Visualization settings
    visualization_html_physics: bool = True
    visualization_html_node_colors: Dict[str, str] = field(default_factory=lambda: {
        'user': '#4285F4',
        'service_account': '#34A853',
        'group': '#FBBC04',
        'project': '#EA4335',
        'folder': '#FF6D00',
        'organization': '#9C27B0',
        'role': '#757575',
        'custom_role': '#616161',
        'resource': '#00ACC1'
    })
    visualization_html_edge_colors: Dict[str, str] = field(default_factory=lambda: {
        'has_role': '#757575',
        'member_of': '#9E9E9E',
        'can_impersonate': '#F44336',
        'can_admin': '#FF5722',
        'can_write': '#FF9800',
        'can_read': '#FFC107'
    })
    visualization_html_attack_path_color: str = '#FF0000'
    visualization_graphml_risk_colors: Dict[str, str] = field(default_factory=lambda: {
        'critical': '#D32F2F',
        'high': '#F44336',
        'medium': '#FF9800',
        'low': '#FFC107',
        'info': '#4CAF50'
    })
    
    # Monitoring settings
    monitoring_enabled: bool = False
    monitoring_interval: int = 86400  # 24 hours
    monitoring_history_dir: str = './history'
    monitoring_alerts_enabled: bool = False
    monitoring_alerts_channels: List[str] = field(default_factory=lambda: ['file'])
    monitoring_alerts_file_path: str = './alerts.json'
    monitoring_alerts_slack_webhook_url: Optional[str] = None
    monitoring_alerts_email_smtp_server: Optional[str] = None
    monitoring_alerts_email_smtp_port: int = 587
    monitoring_alerts_email_username: Optional[str] = None
    monitoring_alerts_email_password: Optional[str] = None
    monitoring_alerts_email_from_address: Optional[str] = None
    monitoring_alerts_email_to_addresses: List[str] = field(default_factory=list)
    
    # Logging settings
    logging_level: str = 'INFO'
    logging_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging_file: Optional[str] = None
    logging_max_size: int = 100
    logging_backup_count: int = 5
    
    # Output settings
    output_directory: str = './output'
    output_timestamp: bool = True
    output_compress: bool = False
    output_json_pretty: bool = True
    output_json_include_metadata: bool = True
    output_csv_include_headers: bool = True
    output_csv_delimiter: str = ','
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'Config':
        """
        Create Config instance from YAML file
        
        Args:
            yaml_path: Path to YAML configuration file
            
        Returns:
            Config instance
        """
        import yaml
        import os
        
        # Check if file exists
        if not os.path.exists(yaml_path):
            logger.warning(f"Config file not found: {yaml_path}, using defaults")
            return cls()
        
        try:
            with open(yaml_path, 'r') as f:
                config_dict = yaml.safe_load(f) or {}
            
            # Flatten nested configuration
            flat_config = {}
            for section, values in config_dict.items():
                if isinstance(values, dict):
                    for key, value in values.items():
                        flat_key = f"{section}_{key}"
                        flat_config[flat_key] = value
                else:
                    flat_config[section] = values
            
            # Filter out unknown fields
            valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
            filtered_config = {k: v for k, v in flat_config.items() if k in valid_fields}
            
            # Log any ignored fields
            ignored_fields = set(flat_config.keys()) - set(filtered_config.keys())
            if ignored_fields:
                logger.debug(f"Ignoring unknown config fields: {ignored_fields}")
            
            return cls(**filtered_config)
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary
        
        Returns:
            Configuration as dictionary
        """
        return asdict(self)


def load_config(config_file: Optional[str] = None) -> Config:
    """
    Load configuration from file or use defaults
    
    Args:
        config_file: Optional path to configuration file
        
    Returns:
        Config instance
    """
    if config_file:
        return Config.from_yaml(config_file)
    return Config()


def save_config(config: Config, config_path: str) -> None:
    """
    Save configuration to file
    
    Args:
        config: Config instance
        config_path: Path to save configuration
    """
    logger.info(f"Saving configuration to: {config_path}")
    
    try:
        # Ensure directory exists
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dictionary and save
        data = config.to_dict()
        with open(config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        raise 